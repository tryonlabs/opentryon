"""
MiniMax H3 video API adapter (first-party V2).

Hailuo 3 / MiniMax-H3 via the official MiniMax Open Platform V2 endpoints
(async create → poll → download). Distinct from Hailuo 2.3 (`HailuoVideoAdapter`),
which uses the V1 `/v1/video_generation` surface.

Docs:
  https://platform.minimax.io/docs/api-reference/video-generation-v2-create
  https://platform.minimax.io/docs/api-reference/video-generation-v2-query

Switch H3 vs H3 Max with the ``model`` field (``MiniMax-H3`` / ``MiniMax-H3-Max``).
H3 Max is the fast variant: T2V and first/last-frame I2V only (no reference-to-video),
``480P`` / ``768P`` (no ``2K``), duration 5–15s (not 4s).

Env:
  MINIMAX_API_KEY
  MINIMAX_API_BASE_URL (default https://api.minimax.io)

Examples:
    >>> from tryon.api.minimax import MiniMaxH3Adapter
    >>> adapter = MiniMaxH3Adapter()
    >>> video = adapter.generate_text_to_video(
    ...     prompt="A fashion model walking a runway at dusk, camera tracking",
    ...     duration=5,
    ...     resolution="2K",
    ...     ratio="16:9",
    ... )
    >>> open("out.mp4", "wb").write(video)
    >>> fast = MiniMaxH3Adapter(model="MiniMax-H3-Max")
    >>> open("h3-max.mp4", "wb").write(fast.generate_text_to_video(
    ...     prompt="Runway walk at dusk", duration=5, resolution="768P",
    ... ))
"""

from __future__ import annotations

import base64
import io
import os
import time
from typing import Any, Dict, List, Optional, Sequence, Union

import requests
from PIL import Image

DEFAULT_BASE_URL = "https://api.minimax.io"
DEFAULT_MODEL = "MiniMax-H3"
H3_MAX_MODEL = "MiniMax-H3-Max"
MAX_PROMPT_CHARS = 7000
T2V_RATIOS = ("21:9", "16:9", "4:3", "1:1", "3:4", "9:16")

# Official V2 constraints (platform.minimax.io video-generation-v2-create).
_MODEL_LIMITS = {
    DEFAULT_MODEL: {
        "resolutions": ("768P", "2K"),
        "default_resolution": "2K",
        "duration_min": 4,
        "duration_max": 15,
        "allow_reference": True,
    },
    H3_MAX_MODEL: {
        "resolutions": ("480P", "768P"),
        "default_resolution": "768P",
        "duration_min": 5,
        "duration_max": 15,
        "allow_reference": False,
    },
}

MODEL_ALIASES = {
    "minimax-h3-max": H3_MAX_MODEL,
    "MiniMax-H3-Max": H3_MAX_MODEL,
    "h3-max": H3_MAX_MODEL,
    "minimax-h3": DEFAULT_MODEL,
    "MiniMax-H3": DEFAULT_MODEL,
    "hailuo-h3": DEFAULT_MODEL,
    "hailuo-3": DEFAULT_MODEL,
    "Hailuo-03": DEFAULT_MODEL,
}

ImageLike = Union[str, io.BytesIO, Image.Image, bytes]
MediaLike = Union[str, bytes, io.BytesIO]


class MiniMaxH3Adapter:
    """Official MiniMax H3 (Hailuo 3) video adapter — T2V / I2V / R2V via V2."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        poll_interval: float = 5.0,
        timeout: float = 900.0,
    ):
        self.api_key = api_key or os.getenv("MINIMAX_API_KEY")
        if not self.api_key:
            raise ValueError(
                "MiniMax API key is required. Set MINIMAX_API_KEY "
                "(https://platform.minimax.io/user-center/basic-information/interface-key)."
            )
        self.base_url = (
            base_url or os.getenv("MINIMAX_API_BASE_URL") or DEFAULT_BASE_URL
        ).rstrip("/")
        self.model = self._resolve_model(model)
        self.poll_interval = float(poll_interval)
        self.timeout = float(timeout)

    @staticmethod
    def _resolve_model(model: str) -> str:
        key = (model or "").strip()
        return MODEL_ALIASES.get(key, key) or DEFAULT_MODEL

    @classmethod
    def _limits(cls, model: str) -> dict:
        resolved = cls._resolve_model(model)
        limits = _MODEL_LIMITS.get(resolved)
        if limits is None:
            raise ValueError(
                f"Unknown MiniMax V2 model {resolved!r}. "
                f"Use {DEFAULT_MODEL} or {H3_MAX_MODEL}."
            )
        return limits

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def _raise_http(resp: requests.Response, context: str) -> None:
        if resp.status_code < 400:
            return
        try:
            data = resp.json()
        except Exception:
            raise RuntimeError(
                f"MiniMax H3 {context} failed ({resp.status_code}): {resp.text}"
            ) from None
        err = data.get("error") if isinstance(data, dict) else None
        if isinstance(err, dict):
            msg = err.get("message") or err
        else:
            msg = data
        raise RuntimeError(f"MiniMax H3 {context} failed ({resp.status_code}): {msg}")

    def _prepare_image_uri(self, image: ImageLike) -> str:
        if isinstance(image, str):
            if image.startswith(("http://", "https://", "data:", "mm_file://")):
                return image
            if os.path.exists(image):
                with open(image, "rb") as f:
                    raw = f.read()
                b64 = base64.b64encode(raw).decode("ascii")
                ext = os.path.splitext(image)[1].lower()
                mime = {
                    ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg",
                    ".png": "image/png",
                    ".webp": "image/webp",
                    ".heic": "image/heic",
                    ".heif": "image/heif",
                }.get(ext, "image/jpeg")
                return f"data:{mime};base64,{b64}"
            raise ValueError(f"Image path does not exist: {image}")
        if isinstance(image, Image.Image):
            buf = io.BytesIO()
            image.convert("RGB").save(buf, format="JPEG", quality=95)
            b64 = base64.b64encode(buf.getvalue()).decode("ascii")
            return f"data:image/jpeg;base64,{b64}"
        if isinstance(image, (bytes, bytearray)):
            b64 = base64.b64encode(bytes(image)).decode("ascii")
            return f"data:image/jpeg;base64,{b64}"
        if hasattr(image, "read"):
            image.seek(0)
            b64 = base64.b64encode(image.read()).decode("ascii")
            return f"data:image/jpeg;base64,{b64}"
        raise ValueError("Unsupported image input for MiniMax H3.")

    def _prepare_media_uri(
        self, media: MediaLike, *, kind: str
    ) -> str:
        if isinstance(media, str):
            if media.startswith(("http://", "https://", "data:", "mm_file://")):
                return media
            if os.path.exists(media):
                with open(media, "rb") as f:
                    raw = f.read()
                b64 = base64.b64encode(raw).decode("ascii")
                ext = os.path.splitext(media)[1].lower()
                if kind == "video":
                    mime = {".mp4": "video/mp4", ".mov": "video/quicktime"}.get(
                        ext, "video/mp4"
                    )
                else:
                    mime = {".wav": "audio/wav", ".mp3": "audio/mpeg"}.get(
                        ext, "audio/mpeg"
                    )
                return f"data:{mime};base64,{b64}"
            raise ValueError(f"{kind.title()} path does not exist: {media}")
        if isinstance(media, (bytes, bytearray)):
            b64 = base64.b64encode(bytes(media)).decode("ascii")
            mime = "video/mp4" if kind == "video" else "audio/mpeg"
            return f"data:{mime};base64,{b64}"
        if hasattr(media, "read"):
            media.seek(0)
            b64 = base64.b64encode(media.read()).decode("ascii")
            mime = "video/mp4" if kind == "video" else "audio/mpeg"
            return f"data:{mime};base64,{b64}"
        raise ValueError(f"Unsupported {kind} input for MiniMax H3.")

    @staticmethod
    def _as_list(value: Optional[Union[MediaLike, Sequence[MediaLike]]]) -> List[MediaLike]:
        if value is None:
            return []
        if isinstance(value, (bytes, bytearray, str)):
            return [value]
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            return list(value)
        return [value]

    def _validate_prompt(self, prompt: str) -> str:
        text = (prompt or "").strip()
        if not text:
            raise ValueError("prompt is required.")
        if len(text) > MAX_PROMPT_CHARS:
            raise ValueError(
                f"prompt exceeds MiniMax H3 limit of {MAX_PROMPT_CHARS} characters "
                f"(got {len(text)})."
            )
        return text

    def _build_content(
        self,
        prompt: str,
        *,
        image: Optional[ImageLike] = None,
        last_frame: Optional[ImageLike] = None,
        reference_image: Optional[Union[ImageLike, Sequence[ImageLike]]] = None,
        reference_video: Optional[Union[MediaLike, Sequence[MediaLike]]] = None,
        reference_audio: Optional[Union[MediaLike, Sequence[MediaLike]]] = None,
        for_model: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        refs_img = self._as_list(reference_image)
        refs_vid = self._as_list(reference_video)
        refs_aud = self._as_list(reference_audio)
        has_refs = bool(refs_img or refs_vid or refs_aud)
        has_frames = image is not None or last_frame is not None
        if has_refs and has_frames:
            raise ValueError(
                "MiniMax H3 image-to-video (first/last frame) and reference-to-video "
                "are mutually exclusive."
            )
        chosen = self._resolve_model(for_model or self.model)
        if has_refs and not self._limits(chosen)["allow_reference"]:
            raise ValueError(
                f"{chosen} does not support reference-to-video "
                "(reference image / video / audio). Use --model minimax-h3."
            )

        content: List[Dict[str, Any]] = [{"type": "text", "text": prompt}]
        if has_refs:
            for item in refs_img:
                content.append(
                    {
                        "type": "image_url",
                        "image_url": {"url": self._prepare_image_uri(item)},
                        "role": "reference_image",
                    }
                )
            for item in refs_vid:
                content.append(
                    {
                        "type": "video_url",
                        "video_url": {"url": self._prepare_media_uri(item, kind="video")},
                        "role": "reference_video",
                    }
                )
            for item in refs_aud:
                content.append(
                    {
                        "type": "audio_url",
                        "audio_url": {"url": self._prepare_media_uri(item, kind="audio")},
                        "role": "reference_audio",
                    }
                )
            return content

        if image is not None:
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": self._prepare_image_uri(image)},
                    "role": "first_frame",
                }
            )
        if last_frame is not None:
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": self._prepare_image_uri(last_frame)},
                    "role": "last_frame",
                }
            )
        return content

    def _create_task(self, payload: Dict[str, Any]) -> str:
        url = f"{self.base_url}/v2/video_generation"
        resp = requests.post(url, headers=self._headers(), json=payload, timeout=60)
        self._raise_http(resp, "create")
        data = resp.json()
        task_id = data.get("task_id") or (data.get("task") or {}).get("id")
        if not task_id:
            raise RuntimeError(f"MiniMax H3 create missing task_id: {data}")
        return str(task_id)

    def _poll(self, task_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/v2/query/video_generation/{task_id}"
        deadline = time.time() + self.timeout
        while time.time() < deadline:
            resp = requests.get(url, headers=self._headers(), timeout=60)
            self._raise_http(resp, "poll")
            data = resp.json()
            task = data.get("task") if isinstance(data.get("task"), dict) else data
            status = (task.get("status") or "").lower()
            if status == "succeeded":
                return task
            if status in ("failed", "cancelled"):
                raise RuntimeError(f"MiniMax H3 task {status}: {task}")
            time.sleep(self.poll_interval)
        raise TimeoutError(f"MiniMax H3 task {task_id} timed out after {self.timeout}s")

    def _download(self, task: Dict[str, Any]) -> bytes:
        content = task.get("content") or {}
        download_url = content.get("url") if isinstance(content, dict) else None
        if not download_url:
            raise RuntimeError(f"MiniMax H3 success response missing content.url: {task}")
        video_resp = requests.get(download_url, stream=True, timeout=180)
        if video_resp.status_code != 200:
            raise RuntimeError(
                f"Failed to download MiniMax H3 video ({video_resp.status_code})"
            )
        return video_resp.content

    def _run(
        self,
        prompt: str,
        *,
        duration: Optional[int],
        resolution: Optional[str],
        ratio: Optional[str],
        image: Optional[ImageLike] = None,
        last_frame: Optional[ImageLike] = None,
        reference_image: Optional[Union[ImageLike, Sequence[ImageLike]]] = None,
        reference_video: Optional[Union[MediaLike, Sequence[MediaLike]]] = None,
        reference_audio: Optional[Union[MediaLike, Sequence[MediaLike]]] = None,
        model: Optional[str] = None,
    ) -> bytes:
        text = self._validate_prompt(prompt)
        chosen_model = self._resolve_model(model) if model else self.model
        limits = self._limits(chosen_model)
        duration_i = int(duration if duration is not None else 5)
        dmin, dmax = limits["duration_min"], limits["duration_max"]
        if duration_i < dmin or duration_i > dmax:
            raise ValueError(
                f"duration must be an integer between {dmin} and {dmax} seconds "
                f"for {chosen_model} (got {duration_i})."
            )
        res = (resolution or limits["default_resolution"]).strip()
        allowed = limits["resolutions"]
        if res not in allowed:
            raise ValueError(
                f"resolution must be one of {allowed} for {chosen_model} (got {res!r})."
            )

        content = self._build_content(
            text,
            image=image,
            last_frame=last_frame,
            reference_image=reference_image,
            reference_video=reference_video,
            reference_audio=reference_audio,
            for_model=chosen_model,
        )
        is_t2v = len(content) == 1
        is_i2v = any(
            item.get("role") in ("first_frame", "last_frame") for item in content
        )

        payload: Dict[str, Any] = {
            "model": chosen_model,
            "content": content,
            "resolution": res,
            "duration": duration_i,
        }
        if is_t2v:
            chosen = (ratio or "16:9").strip()
            if chosen not in T2V_RATIOS:
                raise ValueError(
                    "Text-to-video ratio is required and cannot be 'adaptive'. "
                    f"Use one of {T2V_RATIOS}."
                )
            payload["ratio"] = chosen
        elif is_i2v:
            payload["ratio"] = "adaptive"
        elif ratio:
            payload["ratio"] = ratio

        task_id = self._create_task(payload)
        result = self._poll(task_id)
        return self._download(result)

    def generate_text_to_video(
        self,
        prompt: str,
        model: Optional[str] = None,
        duration: int = 5,
        resolution: Optional[str] = None,
        ratio: str = "16:9",
        last_frame: Optional[ImageLike] = None,
        reference_image: Optional[Union[ImageLike, Sequence[ImageLike]]] = None,
        reference_video: Optional[Union[MediaLike, Sequence[MediaLike]]] = None,
        reference_audio: Optional[Union[MediaLike, Sequence[MediaLike]]] = None,
    ) -> bytes:
        """Text-to-video, last-frame I2V, or reference-to-video."""
        return self._run(
            prompt,
            duration=duration,
            resolution=resolution,
            ratio=ratio,
            last_frame=last_frame,
            reference_image=reference_image,
            reference_video=reference_video,
            reference_audio=reference_audio,
            model=model,
        )

    def generate_image_to_video(
        self,
        image: ImageLike,
        prompt: str,
        model: Optional[str] = None,
        duration: int = 5,
        resolution: Optional[str] = None,
        last_frame: Optional[ImageLike] = None,
        ratio: Optional[str] = None,
    ) -> bytes:
        """First-frame (and optional last-frame) image-to-video. Ratio is ignored."""
        return self._run(
            prompt,
            duration=duration,
            resolution=resolution,
            ratio=ratio,
            image=image,
            last_frame=last_frame,
            model=model,
        )
