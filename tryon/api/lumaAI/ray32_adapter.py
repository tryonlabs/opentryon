"""
Luma Agents API — Ray 3.2 video generation.

Ray 3.2 is Luma's professional video model with T2V, I2V (start/end frames),
multi-keyframe control, HDR, and EXR export via the Agents API:

  POST https://agents.lumalabs.ai/v1/generations

Docs:
  https://docs.agents.lumalabs.ai/guides/videos/
  https://lumalabs.ai/news/introducing-ray-3-2

Env:
  LUMA_AGENTS_API_KEY (preferred) or LUMA_AI_API_KEY
"""

from __future__ import annotations

import base64
import io
import os
import time
from typing import Any, Dict, List, Optional, Union

import requests
from PIL import Image

DEFAULT_BASE_URL = "https://agents.lumalabs.ai/v1"

RAY_MODELS = {
    "ray-3.2": "ray-3.2",
    "ray-3-2": "ray-3.2",
}


class LumaRay32Adapter:
    """Luma Agents API adapter for Ray 3.2 video."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "ray-3.2",
        poll_interval: float = 2.0,
        timeout: float = 900.0,
    ):
        self.api_key = (
            api_key
            or os.getenv("LUMA_AGENTS_API_KEY")
            or os.getenv("LUMA_AI_API_KEY")
        )
        if not self.api_key:
            raise ValueError(
                "Luma Agents API key is required. Set LUMA_AGENTS_API_KEY "
                "(or LUMA_AI_API_KEY) or pass api_key=."
            )
        self.base_url = (
            base_url or os.getenv("LUMA_AGENTS_BASE_URL") or DEFAULT_BASE_URL
        ).rstrip("/")
        self.model = RAY_MODELS.get(model, model)
        self.poll_interval = poll_interval
        self.timeout = timeout
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _image_ref(self, image: Union[str, io.BytesIO, Image.Image, bytes]) -> Dict[str, Any]:
        if isinstance(image, str):
            if image.startswith(("http://", "https://")):
                return {"url": image}
            if image.startswith("data:"):
                # data:image/png;base64,...
                header, _, data = image.partition(",")
                media = "image/png"
                if "image/" in header:
                    media = header.split(";")[0].split(":")[-1]
                return {"data": data, "media_type": media}
            if os.path.exists(image):
                with open(image, "rb") as f:
                    raw = f.read()
                return {
                    "data": base64.b64encode(raw).decode("ascii"),
                    "media_type": "image/png",
                }
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
            raise ValueError("Unsupported image input for Ray 3.2.")
        return {
            "data": base64.b64encode(raw).decode("ascii"),
            "media_type": "image/png",
        }

    def _create(self, payload: Dict[str, Any]) -> str:
        url = f"{self.base_url}/generations"
        resp = requests.post(url, headers=self.headers, json=payload, timeout=60)
        if resp.status_code >= 400:
            raise RuntimeError(f"Luma Ray 3.2 create failed ({resp.status_code}): {resp.text}")
        data = resp.json()
        gen_id = data.get("id")
        if not gen_id:
            raise RuntimeError(f"Luma Ray 3.2 create missing id: {data}")
        return gen_id

    def _poll(self, gen_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/generations/{gen_id}"
        deadline = time.time() + self.timeout
        while time.time() < deadline:
            resp = requests.get(url, headers=self.headers, timeout=60)
            if resp.status_code >= 400:
                raise RuntimeError(f"Luma Ray 3.2 poll failed ({resp.status_code}): {resp.text}")
            data = resp.json()
            state = (data.get("state") or data.get("status") or "").lower()
            if state in {"completed", "succeeded", "success"}:
                return data
            if state in {"failed", "error"}:
                raise RuntimeError(f"Luma Ray 3.2 failed: {data.get('failure_reason') or data}")
            time.sleep(self.poll_interval)
        raise TimeoutError(f"Luma Ray 3.2 generation {gen_id} timed out after {self.timeout}s")

    def _download(self, data: Dict[str, Any]) -> bytes:
        assets = data.get("assets") or {}
        video_url = assets.get("video") or data.get("video_url") or data.get("url")
        if isinstance(video_url, dict):
            video_url = video_url.get("url")
        if not video_url:
            raise RuntimeError(f"Luma Ray 3.2 response missing video URL: {data}")
        resp = requests.get(video_url, stream=True, timeout=120)
        if resp.status_code != 200:
            raise RuntimeError(f"Failed to download Ray 3.2 video ({resp.status_code})")
        return resp.content

    def generate_text_to_video(
        self,
        prompt: str,
        resolution: str = "720p",
        duration: str = "5s",
        aspect_ratio: str = "16:9",
        loop: bool = False,
        hdr: bool = False,
        model: Optional[str] = None,
    ) -> bytes:
        if not prompt:
            raise ValueError("prompt is required.")
        video: Dict[str, Any] = {
            "resolution": resolution,
            "duration": duration,
        }
        if loop:
            video["loop"] = True
        if hdr:
            video["hdr"] = True
        payload = {
            "model": RAY_MODELS.get(model, model) if model else self.model,
            "type": "video",
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "video": video,
        }
        gen_id = self._create(payload)
        return self._download(self._poll(gen_id))

    def generate_image_to_video(
        self,
        start_image: Optional[Union[str, io.BytesIO, Image.Image, bytes]] = None,
        end_image: Optional[Union[str, io.BytesIO, Image.Image, bytes]] = None,
        prompt: Optional[str] = None,
        resolution: str = "720p",
        duration: str = "5s",
        aspect_ratio: str = "16:9",
        loop: bool = False,
        hdr: bool = False,
        model: Optional[str] = None,
        keyframes: Optional[List[Union[str, io.BytesIO, Image.Image, bytes]]] = None,
        keyframe_indexes: Optional[List[int]] = None,
    ) -> bytes:
        if not start_image and not end_image and not keyframes:
            raise ValueError("Provide start_image, end_image, and/or keyframes.")
        video: Dict[str, Any] = {
            "resolution": resolution,
            "duration": duration,
        }
        if loop:
            video["loop"] = True
        if hdr:
            video["hdr"] = True
        if keyframes is not None:
            if keyframe_indexes is None or len(keyframes) != len(keyframe_indexes):
                raise ValueError("keyframes and keyframe_indexes must be same-length lists.")
            video["keyframes"] = [self._image_ref(k) for k in keyframes]
            video["keyframe_indexes"] = list(keyframe_indexes)
        else:
            if start_image is not None:
                video["start_frame"] = self._image_ref(start_image)
            if end_image is not None:
                video["end_frame"] = self._image_ref(end_image)
        payload: Dict[str, Any] = {
            "model": RAY_MODELS.get(model, model) if model else self.model,
            "type": "video",
            "aspect_ratio": aspect_ratio,
            "video": video,
        }
        if prompt:
            payload["prompt"] = prompt
        gen_id = self._create(payload)
        return self._download(self._poll(gen_id))
