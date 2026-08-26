"""Turn invoke_model image/video payloads into MCP-friendly base64."""

from __future__ import annotations

import base64
import io
import os
import re
import tempfile
from typing import Any, Iterable, List, Optional, Tuple

try:
    from PIL import Image, ImageOps
except ImportError:  # pragma: no cover
    Image = None  # type: ignore[assignment,misc]
    ImageOps = None  # type: ignore[assignment,misc]

# Long-edge cap before invoke_model sees the file. Chat used to paste
# full-resolution base64 into gpt-4o and blow the 30k TPM budget (~140k tokens
# for two phone photos). 2048px is enough for VTON APIs; originals stay in Studio.
LLM_MAX_IMAGE_SIDE = 2048


def _strip_data_url(raw: str) -> str:
    trimmed = raw.strip()
    comma = trimmed.find(",")
    if trimmed.startswith("data:") and comma != -1:
        return trimmed[comma + 1 :]
    return trimmed


def encode_one_image(item: Any) -> Optional[str]:
    if item is None:
        return None
    if Image is not None and isinstance(item, Image.Image):
        buf = io.BytesIO()
        item.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")
    if isinstance(item, (bytes, bytearray)):
        return base64.b64encode(bytes(item)).decode("utf-8")
    if isinstance(item, str):
        if item.startswith(("http://", "https://")):
            return None  # leave URLs to the caller; MCP prefers base64
        raw = _strip_data_url(item)
        try:
            base64.b64decode(raw)
            return raw
        except Exception:
            return None
    if hasattr(item, "save") and Image is not None:
        buf = io.BytesIO()
        item.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")
    return None


def encode_images(items: Optional[Iterable[Any]]) -> List[str]:
    encoded: List[str] = []
    for item in items or []:
        value = encode_one_image(item)
        if value:
            encoded.append(value)
    return encoded


def encode_video(item: Any) -> Optional[str]:
    if item is None:
        return None
    if isinstance(item, (bytes, bytearray)):
        return base64.b64encode(bytes(item)).decode("utf-8")
    if isinstance(item, str) and not item.startswith(("http://", "https://")):
        raw = _strip_data_url(item)
        try:
            base64.b64decode(raw)
            return raw
        except Exception:
            return None
    return None


def media_from_invoke(result: dict) -> Tuple[List[str], Optional[str]]:
    """Pull images/video out of an ``invoke_model`` result dict."""
    images = list(result.get("images_base64") or result.get("images") or [])
    video = result.get("video_base64") or result.get("video_bytes") or result.get("video")
    return encode_images(images), encode_video(video)


def media_from_specialist(result: dict) -> Tuple[List[str], Optional[str]]:
    """Backward-compatible alias for ``media_from_invoke``."""
    return media_from_invoke(result)


def cleanup_materialized(paths: Iterable[str]) -> None:
    for path in paths:
        try:
            os.unlink(path)
        except OSError:
            pass


def _image_bytes(value: str) -> Optional[bytes]:
    raw = _strip_data_url(value)
    try:
        data = base64.b64decode(raw, validate=False)
    except Exception:
        return None
    if len(data) < 24:
        return None
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return data
    if data[:3] == b"\xff\xd8\xff":
        return data
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return data
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return data
    return None


def _downscale(img: Any, max_side: int) -> Any:
    longest = max(img.size)
    if longest <= max_side:
        return img
    scale = max_side / float(longest)
    return img.resize(
        (max(1, int(img.size[0] * scale)), max(1, int(img.size[1] * scale))),
        Image.Resampling.LANCZOS,
    )


def _write_bytes(data: bytes, suffix: str, sink: Optional[List[str]]) -> str:
    fd, path = tempfile.mkstemp(prefix="opentryon-", suffix=suffix)
    os.close(fd)
    with open(path, "wb") as handle:
        handle.write(data)
    if sink is not None:
        sink.append(path)
    return path


def _save_temp(img: Any, sink: Optional[List[str]]) -> str:
    has_alpha = img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info)
    suffix = ".png" if has_alpha else ".jpg"
    fd, path = tempfile.mkstemp(prefix="opentryon-", suffix=suffix)
    os.close(fd)
    if has_alpha:
        img.save(path, format="PNG", optimize=True)
    else:
        img.convert("RGB").save(path, format="JPEG", quality=90, optimize=True)
    if sink is not None:
        sink.append(path)
    return path


def _from_pil(img: Any, sink: Optional[List[str]], max_side: int) -> str:
    if ImageOps is not None:
        img = ImageOps.exif_transpose(img) or img
    return _save_temp(_downscale(img, max_side), sink)


def materialize_image(
    value: Optional[str],
    sink: Optional[List[str]] = None,
    *,
    max_side: int = LLM_MAX_IMAGE_SIDE,
) -> Optional[str]:
    """Write Studio base64 / oversized local files to a 2048px temp path.

    Paths and http(s) URLs that are already short enough are left as-is so
    ``invoke_model`` can read them. Oversized local files are copied to a
    2048px temp so VTON APIs stay in range.
    """
    if not value:
        return value
    trimmed = value.strip()
    if trimmed.startswith(("http://", "https://")):
        return trimmed
    if os.path.isfile(trimmed):
        if Image is None:
            return trimmed
        try:
            with Image.open(trimmed) as img:
                img.load()
                if max(img.size) <= max_side:
                    return trimmed
                return _from_pil(img.copy(), sink, max_side)
        except Exception:
            return trimmed
    data = _image_bytes(trimmed)
    if not data:
        return trimmed
    if Image is None:
        return _write_bytes(data, ".bin", sink)
    try:
        with Image.open(io.BytesIO(data)) as img:
            img.load()
            return _from_pil(img.copy(), sink, max_side)
    except Exception:
        return _write_bytes(data, ".img", sink)


def specialist_error_message(raw: str) -> str:
    text = (raw or "").strip() or "Registry tool failed."
    lowered = text.lower()
    if "request too large" in lowered or (
        "rate_limit_exceeded" in lowered and "token" in lowered
    ):
        return (
            "The attached photos were too large for the language model that "
            "classifies the request (not the image API itself). Restart the "
            "OpenTryOn MCP server so uploads are downscaled to 2048px, then retry. "
            "If it still fails, attach images around 2000px on the long edge."
        )
    if "moonshot" in lowered or "moonshot_api_key" in lowered:
        return (
            "Image understanding needs a Moonshot key. Add MOONSHOT_API_KEY "
            "to opentryon/.env, restart MCP, attach a photo, and ask again. "
            "You can also name another understand model (for example qwen3.8-max) "
            "if that key is set."
        )
    env_match = re.search(r"\b([A-Z][A-Z0-9_]+_API_KEY)\b", text)
    if env_match and ("must be provided" in lowered or "environment variable" in lowered):
        env_name = env_match.group(1)
        return (
            f"This model needs {env_name} in opentryon/.env. Add the key, "
            "restart MCP, then try again."
        )
    return _pretty_provider_error(text)


def _pretty_provider_error(text: str) -> str:
    """Unescape and indent ClientError / dict payloads so chat can show the full log."""
    import ast
    import json

    brace = text.find("{")
    if brace == -1:
        return text.replace("\\n", "\n").replace("\\t", "\t")
    prefix = text[:brace].strip().rstrip(".:")
    blob = text[brace:]
    try:
        parsed = ast.literal_eval(blob)
    except Exception:
        try:
            parsed = json.loads(blob)
        except Exception:
            return text.replace("\\n", "\n").replace("\\t", "\t")
    body = json.dumps(parsed, indent=2, default=str, ensure_ascii=False)
    return f"{prefix}\n\n{body}" if prefix else body
