"""
Fal MiniMax H3 Max video adapter (third-party hoster).

First OpenTryOn third-party hoster path. MiniMax and Fal jointly released
H3 Max; Fal post-trained the open H3 base and hosts T2V, I2V, and
reference-to-video. Official MiniMax V2 remains ``--model minimax-h3-max``
(T2V / I2V only, ``MINIMAX_API_KEY``).

Docs:
  https://fal.ai/models/minimax/h3-max/text-to-video/api
  https://fal.ai/models/minimax/h3-max/image-to-video/api
  https://fal.ai/models/minimax/h3-max/reference-to-video/api
  https://docs.fal.ai/model-apis/inference/queue

Env:
  FAL_KEY (alias FAL_API_KEY)
  FAL_QUEUE_BASE_URL (default https://queue.fal.run)

Examples:
    >>> from tryon.api.fal import FalH3MaxAdapter
    >>> adapter = FalH3MaxAdapter()
    >>> open("t2v.mp4", "wb").write(adapter.generate_text_to_video(
    ...     prompt="A fashion model walking a runway at dusk",
    ...     duration=5, resolution="768P", ratio="16:9",
    ... ))
    >>> open("i2v.mp4", "wb").write(adapter.generate_image_to_video(
    ...     image="look.jpg", prompt="Gentle fabric motion",
    ... ))
    >>> open("r2v.mp4", "wb").write(adapter.generate_text_to_video(
    ...     prompt="Image 1 is the model. Keep her identity while she walks.",
    ...     reference_image=["look.jpg"],
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

DEFAULT_QUEUE_URL = "https://queue.fal.run"
T2V_ENDPOINT = "minimax/h3-max/text-to-video"
I2V_ENDPOINT = "minimax/h3-max/image-to-video"
R2V_ENDPOINT = "minimax/h3-max/reference-to-video"
RESOLUTIONS = ("480P", "768P")
T2V_RATIOS = ("21:9", "16:9", "4:3", "1:1", "3:4", "9:16")
R2V_RATIOS = ("adaptive",) + T2V_RATIOS
PROMPT_EXPANSION = ("balanced", "quality")
DURATION_MIN = 5
DURATION_MAX = 15
MAX_REFERENCE_FILES = 12

ImageLike = Union[str, io.BytesIO, Image.Image, bytes]
MediaLike = Union[str, bytes, io.BytesIO]


class FalH3MaxAdapter:
    """Fal-hosted MiniMax H3 Max — T2V / I2V / R2V via the queue API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        queue_url: Optional[str] = None,
        poll_interval: float = 2.0,
        timeout: float = 900.0,
    ):
        self.api_key = (
            api_key
            or os.getenv("FAL_KEY")
            or os.getenv("FAL_API_KEY")
        )
        if not self.api_key:
            raise ValueError(
                "Fal API key is required. Set FAL_KEY "
                "(https://fal.ai/dashboard/keys). FAL_API_KEY is an alias."
            )
        self.queue_url = (
            queue_url or os.getenv("FAL_QUEUE_BASE_URL") or DEFAULT_QUEUE_URL
        ).rstrip("/")
        self.poll_interval = float(poll_interval)
        self.timeout = float(timeout)

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Key {self.api_key}",
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
                f"Fal H3 Max {context} failed ({resp.status_code}): {resp.text}"
            ) from None
        detail = data.get("detail") or data.get("error") or data
        raise RuntimeError(
            f"Fal H3 Max {context} failed ({resp.status_code}): {detail}"
        )

    def _prepare_image_uri(self, image: ImageLike) -> str:
        if isinstance(image, str):
            if image.startswith(("http://", "https://", "data:")):
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
        raise ValueError("Unsupported image input for Fal H3 Max.")

    def _prepare_media_uri(self, media: MediaLike, *, kind: str) -> str:
        if isinstance(media, str):
            if media.startswith(("http://", "https://", "data:")):
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
        raise ValueError(f"Unsupported {kind} input for Fal H3 Max.")

    @staticmethod
    def _as_list(value: Optional[Union[MediaLike, Sequence[MediaLike]]]) -> List[MediaLike]:
        if value is None:
            return []
        if isinstance(value, (bytes, bytearray, str)):
            return [value]
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            return list(value)
        return [value]

    @staticmethod
    def _validate_prompt(prompt: str) -> str:
        text = (prompt or "").strip()
        if not text:
            raise ValueError("prompt is required.")
        return text

    def _validate_duration(self, duration: Optional[int]) -> int:
        duration_i = int(duration if duration is not None else 5)
        if duration_i < DURATION_MIN or duration_i > DURATION_MAX:
            raise ValueError(
                f"duration must be an integer between {DURATION_MIN} and "
                f"{DURATION_MAX} seconds (got {duration_i})."
            )
        return duration_i

    def _validate_resolution(self, resolution: Optional[str]) -> str:
        res = (resolution or "768P").strip()
        if res not in RESOLUTIONS:
            raise ValueError(
                f"resolution must be one of {list(RESOLUTIONS)} (got {res!r})."
            )
        return res

    def _submit(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.queue_url}/{endpoint}"
        resp = requests.post(url, headers=self._headers(), json=payload, timeout=60)
        self._raise_http(resp, "submit")
        data = resp.json()
        if not data.get("request_id"):
            raise RuntimeError(f"Fal H3 Max submit missing request_id: {data}")
        return data

    def _poll(self, submitted: Dict[str, Any]) -> Dict[str, Any]:
        request_id = submitted["request_id"]
        status_url = submitted.get("status_url") or (
            f"{self.queue_url}/{T2V_ENDPOINT}/requests/{request_id}/status"
        )
        deadline = time.time() + self.timeout
        while time.time() < deadline:
            resp = requests.get(
                status_url, headers=self._headers(), timeout=60, params={"logs": 0}
            )
            self._raise_http(resp, "poll")
            body = resp.json()
            status = (body.get("status") or "").upper()
            if status == "COMPLETED":
                return body
            if status in {"FAILED", "ERROR", "CANCELLED", "CANCELED"}:
                raise RuntimeError(
                    f"Fal H3 Max task {request_id} {status.lower()}: "
                    f"{body.get('error') or body}"
                )
            time.sleep(self.poll_interval)
        raise TimeoutError(
            f"Fal H3 Max task {request_id} timed out after {self.timeout}s"
        )

    def _download(self, submitted: Dict[str, Any], polled: Dict[str, Any]) -> bytes:
        request_id = submitted["request_id"]
        result_url = (
            submitted.get("response_url")
            or polled.get("response_url")
            or f"{self.queue_url}/{T2V_ENDPOINT}/requests/{request_id}"
        )
        resp = requests.get(result_url, headers=self._headers(), timeout=60)
        self._raise_http(resp, "result")
        data = resp.json()
        video = data.get("video") or {}
        download_url = video.get("url") if isinstance(video, dict) else None
        if not download_url:
            raise RuntimeError(f"Fal H3 Max result missing video.url: {data}")
        video_resp = requests.get(download_url, stream=True, timeout=180)
        if video_resp.status_code != 200:
            raise RuntimeError(
                f"Failed to download Fal H3 Max video ({video_resp.status_code})"
            )
        return video_resp.content

    def _run_endpoint(self, endpoint: str, payload: Dict[str, Any]) -> bytes:
        submitted = self._submit(endpoint, payload)
        polled = self._poll(submitted)
        return self._download(submitted, polled)

    def _common_payload(
        self,
        prompt: str,
        *,
        duration: Optional[int],
        resolution: Optional[str],
        prompt_expansion_mode: str,
        enable_safety_checker: bool,
        seed: Optional[int],
    ) -> Dict[str, Any]:
        mode = (prompt_expansion_mode or "balanced").strip().lower()
        if mode not in PROMPT_EXPANSION:
            raise ValueError(
                f"prompt_expansion_mode must be one of {list(PROMPT_EXPANSION)} "
                f"(got {prompt_expansion_mode!r})."
            )
        payload: Dict[str, Any] = {
            "prompt": self._validate_prompt(prompt),
            "duration": self._validate_duration(duration),
            "resolution": self._validate_resolution(resolution),
            "prompt_expansion_mode": mode,
            "enable_safety_checker": bool(enable_safety_checker),
        }
        if seed is not None:
            payload["seed"] = int(seed)
        return payload

    def generate_text_to_video(
        self,
        prompt: str,
        duration: int = 5,
        resolution: str = "768P",
        ratio: str = "16:9",
        last_frame: Optional[ImageLike] = None,
        reference_image: Optional[Union[ImageLike, Sequence[ImageLike]]] = None,
        reference_video: Optional[Union[MediaLike, Sequence[MediaLike]]] = None,
        reference_audio: Optional[Union[MediaLike, Sequence[MediaLike]]] = None,
        prompt_expansion_mode: str = "balanced",
        enable_safety_checker: bool = True,
        seed: Optional[int] = None,
    ) -> bytes:
        """Text-to-video, last-frame I2V, or reference-to-video."""
        refs_img = self._as_list(reference_image)
        refs_vid = self._as_list(reference_video)
        refs_aud = self._as_list(reference_audio)
        has_refs = bool(refs_img or refs_vid or refs_aud)
        if has_refs and last_frame is not None:
            raise ValueError(
                "Fal H3 Max image-to-video (first/last frame) and "
                "reference-to-video are mutually exclusive."
            )
        payload = self._common_payload(
            prompt,
            duration=duration,
            resolution=resolution,
            prompt_expansion_mode=prompt_expansion_mode,
            enable_safety_checker=enable_safety_checker,
            seed=seed,
        )
        if has_refs:
            total = len(refs_img) + len(refs_vid) + len(refs_aud)
            if total > MAX_REFERENCE_FILES:
                raise ValueError(
                    f"Fal H3 Max allows at most {MAX_REFERENCE_FILES} reference "
                    f"files in total (got {total})."
                )
            if refs_aud and not (refs_img or refs_vid):
                raise ValueError(
                    "Audio cannot be the only reference input; provide at least "
                    "one reference image or video."
                )
            if refs_img:
                payload["reference_image_urls"] = [
                    self._prepare_image_uri(item) for item in refs_img
                ]
            if refs_vid:
                payload["reference_video_urls"] = [
                    self._prepare_media_uri(item, kind="video") for item in refs_vid
                ]
            if refs_aud:
                payload["reference_audio_urls"] = [
                    self._prepare_media_uri(item, kind="audio") for item in refs_aud
                ]
            chosen = (ratio or "adaptive").strip()
            if chosen not in R2V_RATIOS:
                raise ValueError(
                    f"ratio must be one of {list(R2V_RATIOS)} for reference-to-video "
                    f"(got {chosen!r})."
                )
            payload["aspect_ratio"] = chosen
            return self._run_endpoint(R2V_ENDPOINT, payload)

        if last_frame is not None:
            payload["end_image_url"] = self._prepare_image_uri(last_frame)
            return self._run_endpoint(I2V_ENDPOINT, payload)

        chosen = (ratio or "16:9").strip()
        if chosen == "adaptive" or chosen not in T2V_RATIOS:
            raise ValueError(
                "Text-to-video ratio is required and cannot be 'adaptive'. "
                f"Use one of {T2V_RATIOS}."
            )
        payload["aspect_ratio"] = chosen
        return self._run_endpoint(T2V_ENDPOINT, payload)

    def generate_image_to_video(
        self,
        image: ImageLike,
        prompt: str,
        duration: int = 5,
        resolution: str = "768P",
        last_frame: Optional[ImageLike] = None,
        ratio: Optional[str] = None,
        reference_image: Optional[Union[ImageLike, Sequence[ImageLike]]] = None,
        reference_video: Optional[Union[MediaLike, Sequence[MediaLike]]] = None,
        reference_audio: Optional[Union[MediaLike, Sequence[MediaLike]]] = None,
        prompt_expansion_mode: str = "balanced",
        enable_safety_checker: bool = True,
        seed: Optional[int] = None,
    ) -> bytes:
        """First-frame (and optional last-frame) image-to-video."""
        if self._as_list(reference_image) or self._as_list(reference_video) or self._as_list(reference_audio):
            raise ValueError(
                "Fal H3 Max image-to-video and reference-to-video are mutually "
                "exclusive. Drop --image to use --reference-image / video / audio."
            )
        payload = self._common_payload(
            prompt,
            duration=duration,
            resolution=resolution,
            prompt_expansion_mode=prompt_expansion_mode,
            enable_safety_checker=enable_safety_checker,
            seed=seed,
        )
        payload["image_url"] = self._prepare_image_uri(image)
        if last_frame is not None:
            payload["end_image_url"] = self._prepare_image_uri(last_frame)
        return self._run_endpoint(I2V_ENDPOINT, payload)
