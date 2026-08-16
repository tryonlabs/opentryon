"""
Runway Gen-4.5 video API adapter (first-party).

Official Runway public API for text-to-video and image-to-video with model
``gen4.5``. Async create → poll task → download signed output URL.

Docs:
  https://docs.dev.runwayml.com/
  Base URL: https://api.dev.runwayml.com
  Header: X-Runway-Version: 2024-11-06

Env:
  RUNWAYML_API_SECRET (or RUNWAY_API_KEY)
  RUNWAY_API_BASE_URL (optional)

Examples:
    >>> from tryon.api.runway import RunwayVideoAdapter
    >>> adapter = RunwayVideoAdapter()
    >>> video = adapter.generate_text_to_video(
    ...     prompt="A fashion model walking through mist [dolly]",
    ...     duration=5,
    ...     ratio="1280:720",
    ... )
"""

from __future__ import annotations

import base64
import io
import os
import time
from typing import Any, Dict, Optional, Union

import requests
from PIL import Image

DEFAULT_BASE_URL = "https://api.dev.runwayml.com"
RUNWAY_VERSION = "2024-11-06"

MODEL_ALIASES = {
    "gen4.5": "gen4.5",
    "gen-4.5": "gen4.5",
    "runway-gen4.5": "gen4.5",
}


class RunwayVideoAdapter:
    """Official Runway API adapter focused on Gen-4.5 T2V / I2V."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "gen4.5",
        poll_interval: float = 5.0,
        timeout: float = 900.0,
    ):
        self.api_key = (
            api_key
            or os.getenv("RUNWAYML_API_SECRET")
            or os.getenv("RUNWAY_API_KEY")
        )
        if not self.api_key:
            raise ValueError(
                "Runway API key is required. Set RUNWAYML_API_SECRET "
                "(https://dev.runwayml.com/)."
            )
        self.base_url = (
            base_url or os.getenv("RUNWAY_API_BASE_URL") or DEFAULT_BASE_URL
        ).rstrip("/")
        self.model = MODEL_ALIASES.get((model or "").strip(), model)
        self.poll_interval = float(poll_interval)
        self.timeout = float(timeout)

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "X-Runway-Version": RUNWAY_VERSION,
            "Content-Type": "application/json",
        }

    def _prepare_image_uri(
        self, image: Union[str, io.BytesIO, Image.Image, bytes]
    ) -> str:
        if isinstance(image, str):
            if image.startswith(("http://", "https://", "data:", "runway://")):
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
        raise ValueError("Unsupported image input for Runway.")

    def _create(self, path: str, payload: Dict[str, Any]) -> str:
        url = f"{self.base_url}{path}"
        resp = requests.post(url, headers=self._headers(), json=payload, timeout=60)
        if resp.status_code >= 400:
            raise RuntimeError(
                f"Runway create failed ({resp.status_code}): {resp.text}"
            )
        data = resp.json()
        task_id = data.get("id")
        if not task_id:
            raise RuntimeError(f"Runway create missing id: {data}")
        return task_id

    def _poll(self, task_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/v1/tasks/{task_id}"
        deadline = time.time() + self.timeout
        while time.time() < deadline:
            resp = requests.get(url, headers=self._headers(), timeout=60)
            if resp.status_code >= 400:
                raise RuntimeError(
                    f"Runway poll failed ({resp.status_code}): {resp.text}"
                )
            data = resp.json()
            status = (data.get("status") or "").upper()
            if status == "SUCCEEDED":
                return data
            if status == "FAILED":
                raise RuntimeError(
                    f"Runway task failed: {data.get('failure') or data}"
                )
            # PENDING / RUNNING / THROTTLED — keep polling
            time.sleep(self.poll_interval)
        raise TimeoutError(f"Runway task {task_id} timed out after {self.timeout}s")

    def _download_output(self, task: Dict[str, Any]) -> bytes:
        output = task.get("output") or []
        if isinstance(output, str):
            output = [output]
        if not output:
            raise RuntimeError(f"Runway task missing output: {task}")
        video_url = output[0]
        if isinstance(video_url, dict):
            video_url = video_url.get("url") or video_url.get("uri")
        resp = requests.get(video_url, stream=True, timeout=180)
        if resp.status_code != 200:
            raise RuntimeError(
                f"Failed to download Runway video ({resp.status_code})"
            )
        return resp.content

    def generate_text_to_video(
        self,
        prompt: str,
        model: Optional[str] = None,
        duration: int = 5,
        ratio: str = "1280:720",
        seed: Optional[int] = None,
    ) -> bytes:
        if not prompt:
            raise ValueError("prompt is required.")
        payload: Dict[str, Any] = {
            "model": MODEL_ALIASES.get(model, model) if model else self.model,
            "promptText": prompt,
            "duration": int(duration),
            "ratio": ratio,
        }
        if seed is not None:
            payload["seed"] = int(seed)
        task_id = self._create("/v1/text_to_video", payload)
        return self._download_output(self._poll(task_id))

    def generate_image_to_video(
        self,
        image: Union[str, io.BytesIO, Image.Image, bytes],
        prompt: Optional[str] = None,
        model: Optional[str] = None,
        duration: int = 5,
        ratio: str = "1280:720",
        seed: Optional[int] = None,
    ) -> bytes:
        payload: Dict[str, Any] = {
            "model": MODEL_ALIASES.get(model, model) if model else self.model,
            "promptImage": self._prepare_image_uri(image),
            "duration": int(duration),
            "ratio": ratio,
        }
        if prompt:
            payload["promptText"] = prompt
        if seed is not None:
            payload["seed"] = int(seed)
        task_id = self._create("/v1/image_to_video", payload)
        return self._download_output(self._poll(task_id))
