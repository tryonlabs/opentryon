"""
xAI Grok Imagine — image and video adapters.

Models:
  - grok-imagine-image-quality  — text-to-image (also turbo/default variants)
  - grok-imagine-video-1.5      — text/image/reference-to-video (up to 1080p)

Docs:
  https://docs.x.ai/developers/model-capabilities/images/generation
  https://docs.x.ai/developers/model-capabilities/video/generation
  https://docs.x.ai/developers/models/grok-imagine-video-1.5

Env:
  XAI_API_KEY
"""

from __future__ import annotations

import base64
import io
import os
import time
from typing import Any, Dict, List, Optional, Union

import requests
from PIL import Image

DEFAULT_BASE_URL = "https://api.x.ai/v1"

IMAGE_MODELS = {
    "grok-imagine-image-quality": "grok-imagine-image-quality",
    "grok-imagine-image": "grok-imagine-image",
    "grok-imagine-image-pro": "grok-imagine-image-pro",
}

VIDEO_MODELS = {
    "grok-imagine-video-1.5": "grok-imagine-video-1.5",
    "grok-imagine-video-1.5-preview": "grok-imagine-video-1.5",
}


class GrokImagineImageAdapter:
    """xAI Grok Imagine image generation adapter."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "grok-imagine-image-quality",
    ):
        self.api_key = api_key or os.getenv("XAI_API_KEY")
        if not self.api_key:
            raise ValueError("XAI_API_KEY is required (or pass api_key=).")
        self.base_url = (base_url or os.getenv("XAI_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.model = IMAGE_MODELS.get(model, model)
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def generate_text_to_image(
        self,
        prompt: str,
        model: Optional[str] = None,
        n: int = 1,
        aspect_ratio: Optional[str] = None,
        resolution: Optional[str] = None,
        response_format: str = "b64_json",
    ) -> List[Image.Image]:
        if not prompt:
            raise ValueError("prompt is required.")
        payload: Dict[str, Any] = {
            "model": IMAGE_MODELS.get(model, model) if model else self.model,
            "prompt": prompt,
            "n": int(n),
            "response_format": response_format,
        }
        if aspect_ratio:
            payload["aspect_ratio"] = aspect_ratio
        if resolution:
            payload["resolution"] = resolution

        resp = requests.post(
            f"{self.base_url}/images/generations",
            headers=self.headers,
            json=payload,
            timeout=180,
        )
        if resp.status_code >= 400:
            raise RuntimeError(f"Grok Imagine image failed ({resp.status_code}): {resp.text}")
        data = resp.json()
        items = data.get("data") or []
        if not items:
            raise RuntimeError(f"Grok Imagine returned no images: {data}")

        images: List[Image.Image] = []
        for item in items:
            if item.get("b64_json"):
                raw = base64.b64decode(item["b64_json"])
                images.append(Image.open(io.BytesIO(raw)).convert("RGB"))
            elif item.get("url"):
                r = requests.get(item["url"], timeout=60)
                r.raise_for_status()
                images.append(Image.open(io.BytesIO(r.content)).convert("RGB"))
            else:
                raise RuntimeError(f"Grok Imagine item missing url/b64_json: {item}")
        return images


class GrokImagineVideoAdapter:
    """xAI Grok Imagine Video 1.5 adapter (T2V / I2V)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "grok-imagine-video-1.5",
        poll_interval: float = 3.0,
        timeout: float = 900.0,
    ):
        self.api_key = api_key or os.getenv("XAI_API_KEY")
        if not self.api_key:
            raise ValueError("XAI_API_KEY is required (or pass api_key=).")
        self.base_url = (base_url or os.getenv("XAI_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.model = VIDEO_MODELS.get(model, model)
        self.poll_interval = poll_interval
        self.timeout = timeout
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _prepare_image_field(self, image: Union[str, io.BytesIO, Image.Image, bytes]) -> Dict[str, str]:
        if isinstance(image, str):
            if image.startswith(("http://", "https://")):
                return {"url": image}
            if image.startswith("data:"):
                return {"url": image}
            if os.path.exists(image):
                with open(image, "rb") as f:
                    raw = f.read()
                return {"url": f"data:image/png;base64,{base64.b64encode(raw).decode('ascii')}"}
            raise ValueError(f"Image path does not exist: {image}")
        if isinstance(image, Image.Image):
            buf = io.BytesIO()
            image.save(buf, format="PNG")
            raw = buf.getvalue()
        elif isinstance(image, (bytes, bytearray)):
            raw = bytes(image)
        elif hasattr(image, "read"):
            image.seek(0)
            raw = image.read()
        else:
            raise ValueError("Unsupported image input for Grok video.")
        return {"url": f"data:image/png;base64,{base64.b64encode(raw).decode('ascii')}"}

    def _create(self, payload: Dict[str, Any]) -> str:
        resp = requests.post(
            f"{self.base_url}/videos/generations",
            headers=self.headers,
            json=payload,
            timeout=60,
        )
        if resp.status_code >= 400:
            raise RuntimeError(f"Grok video create failed ({resp.status_code}): {resp.text}")
        data = resp.json()
        req_id = data.get("request_id") or data.get("id")
        if not req_id:
            # Some SDK shapes return the video URL immediately
            if data.get("url"):
                return f"__done__:{data['url']}"
            raise RuntimeError(f"Grok video create missing request_id: {data}")
        return req_id

    def _poll(self, request_id: str) -> str:
        if request_id.startswith("__done__:"):
            return request_id.split(":", 1)[1]
        url = f"{self.base_url}/videos/{request_id}"
        deadline = time.time() + self.timeout
        while time.time() < deadline:
            resp = requests.get(url, headers=self.headers, timeout=60)
            if resp.status_code >= 400:
                # Fallback poll path used by some xAI revisions
                alt = requests.get(
                    f"{self.base_url}/videos/generations/{request_id}",
                    headers=self.headers,
                    timeout=60,
                )
                if alt.status_code >= 400:
                    raise RuntimeError(
                        f"Grok video poll failed ({resp.status_code}/{alt.status_code}): "
                        f"{resp.text} | {alt.text}"
                    )
                data = alt.json()
            else:
                data = resp.json()
            status = (data.get("status") or data.get("state") or "").lower()
            if status in {"completed", "succeeded", "success", "done"}:
                video_url = data.get("url") or (data.get("video") or {}).get("url")
                if not video_url:
                    raise RuntimeError(f"Grok video completed without url: {data}")
                return video_url
            if status in {"failed", "error"}:
                raise RuntimeError(f"Grok video failed: {data}")
            time.sleep(self.poll_interval)
        raise TimeoutError(f"Grok video {request_id} timed out after {self.timeout}s")

    def _download(self, video_url: str) -> bytes:
        resp = requests.get(video_url, stream=True, timeout=120)
        if resp.status_code != 200:
            raise RuntimeError(f"Failed to download Grok video ({resp.status_code})")
        return resp.content

    def generate_text_to_video(
        self,
        prompt: str,
        model: Optional[str] = None,
        duration: int = 6,
        aspect_ratio: str = "16:9",
        resolution: str = "720p",
    ) -> bytes:
        if not prompt:
            raise ValueError("prompt is required.")
        payload = {
            "model": VIDEO_MODELS.get(model, model) if model else self.model,
            "prompt": prompt,
            "duration": int(duration),
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
        }
        req_id = self._create(payload)
        return self._download(self._poll(req_id))

    def generate_image_to_video(
        self,
        image: Union[str, io.BytesIO, Image.Image, bytes],
        prompt: str,
        model: Optional[str] = None,
        duration: int = 6,
        aspect_ratio: Optional[str] = None,
        resolution: str = "720p",
        reference_images: Optional[List[Union[str, io.BytesIO, Image.Image, bytes]]] = None,
    ) -> bytes:
        if not prompt:
            raise ValueError("prompt is required.")
        payload: Dict[str, Any] = {
            "model": VIDEO_MODELS.get(model, model) if model else self.model,
            "prompt": prompt,
            "image": self._prepare_image_field(image),
            "duration": int(duration),
            "resolution": resolution,
        }
        if aspect_ratio:
            payload["aspect_ratio"] = aspect_ratio
        if reference_images:
            payload["reference_images"] = [
                self._prepare_image_field(img) for img in reference_images
            ]
        req_id = self._create(payload)
        return self._download(self._poll(req_id))
