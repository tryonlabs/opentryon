"""
LTX official video API adapter (first-party).

Supports LTX-2.5 Fast / Pro text-to-video and image-to-video via the LTX
hosted API (https://api.ltx.io). Defaults to the async V2 job API
(submit → poll → download), which is recommended for production.

Docs:
  https://docs.ltx.video/
  https://docs.ltx.video/models/ltx-2-5
  https://docs.ltx.video/async-jobs

Model ids:
  - ltx-2-5-fast
  - ltx-2-5-pro

Env:
  LTX_API_KEY
  LTX_API_BASE_URL (default https://api.ltx.io)

Examples:
    >>> from tryon.api.ltx import LTXVideoAdapter
    >>> adapter = LTXVideoAdapter()
    >>> video = adapter.generate_text_to_video(
    ...     prompt="A fashion model walking a runway, soft studio light, camera tracking",
    ...     model="ltx-2-5-pro",
    ...     duration=8,
    ...     resolution="1920x1080",
    ... )
    >>> open("out.mp4", "wb").write(video)

    >>> video = adapter.generate_image_to_video(
    ...     image="look.jpg",
    ...     prompt="Gentle turn, fabric motion, ambient atelier sound",
    ...     duration=8,
    ...     resolution="1280x720",
    ... )
"""

from __future__ import annotations

import base64
import io
import os
import time
from typing import Any, Dict, List, Optional, Union

import requests
from PIL import Image

DEFAULT_BASE_URL = "https://api.ltx.io"

MODEL_ALIASES = {
    "ltx-2.5-fast": "ltx-2-5-fast",
    "ltx-2.5-pro": "ltx-2-5-pro",
    "fast": "ltx-2-5-fast",
    "pro": "ltx-2-5-pro",
}

CAMERA_MOTIONS = {
    "dolly_in",
    "dolly_out",
    "dolly_left",
    "dolly_right",
    "jib_up",
    "jib_down",
    "static",
    "focus_shift",
}


class LTXVideoAdapter:
    """Official LTX API adapter for LTX-2.5 Fast / Pro video generation."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "ltx-2-5-pro",
        poll_interval: float = 5.0,
        timeout: float = 900.0,
        use_async: bool = True,
    ):
        self.api_key = api_key or os.getenv("LTX_API_KEY")
        if not self.api_key:
            raise ValueError(
                "LTX API key is required. Set LTX_API_KEY "
                "(https://console.ltx.io)."
            )
        self.base_url = (
            base_url or os.getenv("LTX_API_BASE_URL") or DEFAULT_BASE_URL
        ).rstrip("/")
        self.model = self._resolve_model(model)
        self.poll_interval = float(poll_interval)
        self.timeout = float(timeout)
        self.use_async = bool(use_async)

    @staticmethod
    def _resolve_model(model: str) -> str:
        key = (model or "").strip()
        resolved = MODEL_ALIASES.get(key, key)
        if resolved not in {"ltx-2-5-fast", "ltx-2-5-pro"}:
            # Allow forward-compat ids the API may add; warn via ValueError only
            # for empty / obviously wrong aliases we mapped incorrectly.
            if not resolved:
                raise ValueError("model is required.")
        return resolved

    def _headers(self, json_body: bool = True) -> Dict[str, str]:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        if json_body:
            headers["Content-Type"] = "application/json"
        return headers

    def _prepare_image_uri(
        self, image: Union[str, io.BytesIO, Image.Image, bytes]
    ) -> str:
        if isinstance(image, str):
            if image.startswith(("http://", "https://", "ltx://", "data:")):
                return image
            if os.path.exists(image):
                with open(image, "rb") as f:
                    raw = f.read()
                b64 = base64.b64encode(raw).decode("ascii")
                # Guess mime from extension; PNG is a safe default
                ext = os.path.splitext(image)[1].lower()
                mime = {
                    ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg",
                    ".png": "image/png",
                    ".webp": "image/webp",
                }.get(ext, "image/png")
                return f"data:{mime};base64,{b64}"
            raise ValueError(f"Image path does not exist: {image}")
        if isinstance(image, Image.Image):
            buf = io.BytesIO()
            image.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode("ascii")
            return f"data:image/png;base64,{b64}"
        if isinstance(image, (bytes, bytearray)):
            b64 = base64.b64encode(bytes(image)).decode("ascii")
            return f"data:image/png;base64,{b64}"
        if hasattr(image, "read"):
            image.seek(0)
            b64 = base64.b64encode(image.read()).decode("ascii")
            return f"data:image/png;base64,{b64}"
        raise ValueError("Unsupported image input for LTX video.")

    @staticmethod
    def _normalize_duration(duration: Optional[Union[str, int]]) -> Any:
        """Map CLI-friendly values to API duration (int or null)."""
        if duration is None:
            return None
        if isinstance(duration, str):
            cleaned = duration.strip().lower()
            if cleaned in {"", "auto", "null", "none"}:
                return None
            return int(cleaned)
        return int(duration)

    def _build_payload(
        self,
        *,
        prompt: str,
        model: Optional[str],
        duration: Optional[Union[str, int]],
        resolution: str,
        fps: Optional[int],
        generate_audio: bool,
        camera_motion: Optional[str],
        image_uri: Optional[str] = None,
        last_frame_uri: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not prompt:
            raise ValueError("prompt is required.")
        if not resolution:
            raise ValueError("resolution is required (e.g. 1920x1080).")

        payload: Dict[str, Any] = {
            "prompt": prompt,
            "model": self._resolve_model(model) if model else self.model,
            "duration": self._normalize_duration(duration),
            "resolution": resolution,
            "generate_audio": bool(generate_audio),
        }
        # API requires the duration field even when null (automatic duration).
        if fps is not None:
            payload["fps"] = int(fps)
        if camera_motion:
            motion = camera_motion.strip()
            if motion not in CAMERA_MOTIONS:
                raise ValueError(
                    f"Invalid camera_motion {camera_motion!r}. "
                    f"Allowed: {sorted(CAMERA_MOTIONS)}"
                )
            payload["camera_motion"] = motion
        if image_uri is not None:
            payload["image_uri"] = image_uri
        if last_frame_uri is not None:
            payload["last_frame_uri"] = last_frame_uri
            if payload["duration"] is None:
                raise ValueError(
                    "Automatic duration cannot be combined with last_frame_uri."
                )
        return payload

    def _raise_api_error(self, resp: requests.Response, context: str) -> None:
        try:
            data = resp.json()
        except Exception:
            data = {"message": resp.text}
        message = (
            data.get("message")
            or (data.get("error") or {}).get("message")
            or data.get("type")
            or resp.text
        )
        raise RuntimeError(f"LTX {context} failed ({resp.status_code}): {message}")

    def _submit_async(self, endpoint: str, payload: Dict[str, Any]) -> str:
        url = f"{self.base_url}/v2/{endpoint}"
        resp = requests.post(
            url, headers=self._headers(), json=payload, timeout=60
        )
        if resp.status_code >= 400:
            self._raise_api_error(resp, f"async create {endpoint}")
        data = resp.json()
        job_id = data.get("id")
        if not job_id:
            raise RuntimeError(f"LTX async create missing id: {data}")
        return job_id

    def _poll_async(self, endpoint: str, job_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/v2/{endpoint}/{job_id}"
        deadline = time.time() + self.timeout
        last_error: Optional[Exception] = None
        while time.time() < deadline:
            try:
                resp = requests.get(url, headers=self._headers(json_body=False), timeout=60)
                if resp.status_code >= 500:
                    last_error = RuntimeError(
                        f"LTX poll transient error ({resp.status_code})"
                    )
                    time.sleep(self.poll_interval)
                    continue
                if resp.status_code >= 400:
                    self._raise_api_error(resp, f"async poll {endpoint}")
                data = resp.json()
            except requests.RequestException as exc:
                last_error = exc
                time.sleep(self.poll_interval)
                continue

            status = (data.get("status") or "").lower()
            if status == "completed":
                return data
            if status == "failed":
                err = data.get("error") or {}
                raise RuntimeError(
                    f"LTX job failed: {err.get('message') or err or data}"
                )
            time.sleep(self.poll_interval)

        detail = f" last error: {last_error}" if last_error else ""
        raise TimeoutError(
            f"LTX job {job_id} timed out after {self.timeout}s.{detail}"
        )

    def _download_result(self, job: Dict[str, Any]) -> bytes:
        result = job.get("result") or {}
        video_url = result.get("video_url")
        if not video_url:
            raise RuntimeError(f"LTX completed job missing video_url: {job}")
        resp = requests.get(video_url, stream=True, timeout=180)
        if resp.status_code != 200:
            raise RuntimeError(
                f"Failed to download LTX video ({resp.status_code})"
            )
        return resp.content

    def _run_sync(self, endpoint: str, payload: Dict[str, Any]) -> bytes:
        url = f"{self.base_url}/v1/{endpoint}"
        resp = requests.post(
            url, headers=self._headers(), json=payload, timeout=self.timeout
        )
        if resp.status_code >= 400:
            self._raise_api_error(resp, f"sync {endpoint}")
        content_type = (resp.headers.get("Content-Type") or "").lower()
        if "json" in content_type:
            # Some error paths return JSON with 200; treat as failure.
            raise RuntimeError(f"LTX sync {endpoint} returned JSON: {resp.text[:500]}")
        return resp.content

    def _generate(self, endpoint: str, payload: Dict[str, Any]) -> bytes:
        if self.use_async:
            job_id = self._submit_async(endpoint, payload)
            job = self._poll_async(endpoint, job_id)
            return self._download_result(job)
        return self._run_sync(endpoint, payload)

    def generate_text_to_video(
        self,
        prompt: str,
        model: Optional[str] = None,
        duration: Optional[Union[str, int]] = 8,
        resolution: str = "1920x1080",
        fps: Optional[int] = 24,
        generate_audio: bool = True,
        camera_motion: Optional[str] = None,
    ) -> bytes:
        payload = self._build_payload(
            prompt=prompt,
            model=model,
            duration=duration,
            resolution=resolution,
            fps=fps,
            generate_audio=generate_audio,
            camera_motion=camera_motion,
        )
        return self._generate("text-to-video", payload)

    def generate_image_to_video(
        self,
        image: Union[str, io.BytesIO, Image.Image, bytes],
        prompt: str,
        model: Optional[str] = None,
        duration: Optional[Union[str, int]] = 8,
        resolution: str = "1920x1080",
        fps: Optional[int] = 24,
        generate_audio: bool = True,
        camera_motion: Optional[str] = None,
        last_frame: Optional[Union[str, io.BytesIO, Image.Image, bytes]] = None,
    ) -> bytes:
        image_uri = self._prepare_image_uri(image)
        last_frame_uri = (
            self._prepare_image_uri(last_frame) if last_frame is not None else None
        )
        payload = self._build_payload(
            prompt=prompt,
            model=model,
            duration=duration,
            resolution=resolution,
            fps=fps,
            generate_audio=generate_audio,
            camera_motion=camera_motion,
            image_uri=image_uri,
            last_frame_uri=last_frame_uri,
        )
        return self._generate("image-to-video", payload)
