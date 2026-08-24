"""Turn specialist-agent image/video payloads into MCP-friendly base64."""

from __future__ import annotations

import base64
import io
from typing import Any, Iterable, List, Optional, Tuple

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    Image = None  # type: ignore[assignment,misc]


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


def media_from_specialist(result: dict) -> Tuple[List[str], Optional[str]]:
    """Pull images/video out of a specialist ``generate()`` dict, including cache."""
    images = list(result.get("images") or [])
    video = result.get("video_bytes") or result.get("video")
    cache_key = result.get("cache_key")
    if cache_key and (not images or video is None):
        try:
            from tryon.tools import get_tool_output_cache

            cached = get_tool_output_cache().get(cache_key) or {}
            if not images:
                images = list(cached.get("images") or [])
            if video is None:
                video = cached.get("video_bytes")
        except Exception:
            pass
    tool_output = result.get("tool_output") or {}
    if not images:
        images = list(tool_output.get("images") or [])
    return encode_images(images), encode_video(video)
