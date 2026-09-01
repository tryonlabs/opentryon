"""
BytePlus ModelArk — Seedance video generation adapters.

Seedance is ByteDance's audio-video joint generation family, exposed via
BytePlus ModelArk async content-generation tasks:

  POST {base}/contents/generations/tasks
  GET  {base}/contents/generations/tasks/{id}

Official catalog (as of 2026):
  - Seedance 2.5  — up to 30s single-pass storytelling
    (ModelArk id ``dreamina-seedance-2-5-260628``)
  - Seedance 2.0  — Standard / Fast / Mini variants

Product: https://seed.bytedance.com/en/seedance2_5
Docs:    https://docs.byteplus.com/en/docs/ModelArk/1520757
         https://docs.byteplus.com/en/docs/ModelArk/1901652

Env:
  ARK_API_KEY or BYTEPLUS_ARK_API_KEY
  BYTEPLUS_ARK_BASE_URL (optional, default ap-southeast ModelArk)
"""

from __future__ import annotations

import io
import os
import time
from typing import Any, Dict, List, Optional, Union

import requests
from PIL import Image

DEFAULT_BASE_URL = "https://ark.ap-southeast.bytepluses.com/api/v3"

# ModelArk model IDs. Seedance 2.5 production id is dreamina-seedance-2-5-260628
# (BytePlus ModelArk / LAS video-gen docs, 2026).
SEEDANCE_MODELS = {
    "seedance-2-5": "dreamina-seedance-2-5-260628",
    "seedance-2.5": "dreamina-seedance-2-5-260628",
    "dreamina-seedance-2-5-260628": "dreamina-seedance-2-5-260628",
    "dreamina-seedance-2-0-260128": "dreamina-seedance-2-0-260128",
    "dreamina-seedance-2-0-fast-260128": "dreamina-seedance-2-0-fast-260128",
    "dreamina-seedance-2-0-mini-260615": "dreamina-seedance-2-0-mini-260615",
    "seedance-2-0": "dreamina-seedance-2-0-260128",
    "seedance-2-0-fast": "dreamina-seedance-2-0-fast-260128",
    "seedance-2-0-mini": "dreamina-seedance-2-0-mini-260615",
}

VALID_RATIOS = {"21:9", "16:9", "4:3", "1:1", "3:4", "9:16"}
VALID_RESOLUTIONS = {"480p", "720p", "1080p", "2k", "4k"}


class SeedanceAdapter:
    """BytePlus ModelArk Seedance video adapter (T2V / I2V)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "seedance-2-5",
        poll_interval: float = 3.0,
        timeout: float = 900.0,
    ):
        self.api_key = (
            api_key
            or os.getenv("ARK_API_KEY")
            or os.getenv("BYTEPLUS_ARK_API_KEY")
        )
        if not self.api_key:
            raise ValueError(
                "BytePlus ModelArk API key is required. Set ARK_API_KEY "
                "(or BYTEPLUS_ARK_API_KEY) or pass api_key=."
            )
        self.base_url = (
            base_url
            or os.getenv("BYTEPLUS_ARK_BASE_URL")
            or DEFAULT_BASE_URL
        ).rstrip("/")
        self.model = self._resolve_model(model)
        self.poll_interval = poll_interval
        self.timeout = timeout
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def _resolve_model(model: str) -> str:
        key = model.strip()
        if key in SEEDANCE_MODELS:
            return SEEDANCE_MODELS[key]
        # Allow raw ModelArk IDs through unchanged.
        return key

    def _image_to_url_or_data(self, image: Union[str, io.BytesIO, Image.Image, bytes]) -> str:
        if isinstance(image, str):
            if image.startswith(("http://", "https://", "data:")):
                return image
            if os.path.exists(image):
                import base64
                with open(image, "rb") as f:
                    raw = f.read()
                b64 = base64.b64encode(raw).decode("ascii")
                return f"data:image/png;base64,{b64}"
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
            raise ValueError("Unsupported image input type for Seedance.")
        import base64
        b64 = base64.b64encode(raw).decode("ascii")
        return f"data:image/png;base64,{b64}"

    def _create_task(self, payload: Dict[str, Any]) -> str:
        url = f"{self.base_url}/contents/generations/tasks"
        resp = requests.post(url, headers=self.headers, json=payload, timeout=60)
        if resp.status_code >= 400:
            raise RuntimeError(f"Seedance create failed ({resp.status_code}): {resp.text}")
        data = resp.json()
        task_id = data.get("id") or data.get("task_id") or (data.get("data") or {}).get("id")
        if not task_id:
            raise RuntimeError(f"Seedance create response missing task id: {data}")
        return task_id

    def _poll(self, task_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/contents/generations/tasks/{task_id}"
        deadline = time.time() + self.timeout
        while time.time() < deadline:
            resp = requests.get(url, headers=self.headers, timeout=60)
            if resp.status_code >= 400:
                raise RuntimeError(f"Seedance poll failed ({resp.status_code}): {resp.text}")
            data = resp.json()
            status = (data.get("status") or data.get("task_status") or "").lower()
            if status in {"succeeded", "success", "completed", "done"}:
                return data
            if status in {"failed", "error", "cancelled", "canceled"}:
                raise RuntimeError(f"Seedance task failed: {data}")
            time.sleep(self.poll_interval)
        raise TimeoutError(f"Seedance task {task_id} timed out after {self.timeout}s")

    def _extract_video_url(self, data: Dict[str, Any]) -> str:
        content = data.get("content") or {}
        if isinstance(content, dict):
            for key in ("video_url", "url"):
                if content.get(key):
                    return content[key]
        if data.get("video_url"):
            return data["video_url"]
        # Nested ModelArk shapes
        for key in ("output", "result", "data"):
            nested = data.get(key)
            if isinstance(nested, dict):
                for k in ("video_url", "url"):
                    if nested.get(k):
                        return nested[k]
        raise RuntimeError(f"Seedance response missing video URL: {data}")

    def _download(self, video_url: str) -> bytes:
        resp = requests.get(video_url, stream=True, timeout=120)
        if resp.status_code != 200:
            raise RuntimeError(f"Failed to download Seedance video ({resp.status_code})")
        return resp.content

    def _build_payload(
        self,
        prompt: Optional[str],
        *,
        image: Optional[Union[str, io.BytesIO, Image.Image, bytes]] = None,
        end_image: Optional[Union[str, io.BytesIO, Image.Image, bytes]] = None,
        duration: int = 5,
        ratio: str = "16:9",
        resolution: str = "720p",
        generate_audio: bool = True,
        seed: Optional[int] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        if ratio not in VALID_RATIOS:
            raise ValueError(f"Invalid ratio '{ratio}'. Valid: {sorted(VALID_RATIOS)}")
        if resolution not in VALID_RESOLUTIONS:
            raise ValueError(f"Invalid resolution '{resolution}'. Valid: {sorted(VALID_RESOLUTIONS)}")

        content: List[Dict[str, Any]] = []
        if prompt:
            content.append({"type": "text", "text": prompt})
        if image is not None:
            content.append({
                "type": "image_url",
                "image_url": {"url": self._image_to_url_or_data(image)},
                "role": "first_frame",
            })
        if end_image is not None:
            content.append({
                "type": "image_url",
                "image_url": {"url": self._image_to_url_or_data(end_image)},
                "role": "last_frame",
            })
        if not content:
            raise ValueError("At least a prompt or an image is required.")

        payload: Dict[str, Any] = {
            "model": self._resolve_model(model) if model else self.model,
            "content": content,
            "ratio": ratio,
            "resolution": resolution,
            "duration": int(duration),
            "generate_audio": bool(generate_audio),
        }
        if seed is not None:
            payload["seed"] = int(seed)
        return payload

    def generate_text_to_video(
        self,
        prompt: str,
        duration: int = 5,
        ratio: str = "16:9",
        resolution: str = "720p",
        generate_audio: bool = True,
        seed: Optional[int] = None,
        model: Optional[str] = None,
    ) -> bytes:
        if not prompt:
            raise ValueError("prompt is required for text-to-video.")
        payload = self._build_payload(
            prompt,
            duration=duration,
            ratio=ratio,
            resolution=resolution,
            generate_audio=generate_audio,
            seed=seed,
            model=model,
        )
        task_id = self._create_task(payload)
        data = self._poll(task_id)
        return self._download(self._extract_video_url(data))

    def generate_image_to_video(
        self,
        image: Union[str, io.BytesIO, Image.Image, bytes],
        prompt: Optional[str] = None,
        end_image: Optional[Union[str, io.BytesIO, Image.Image, bytes]] = None,
        duration: int = 5,
        ratio: str = "16:9",
        resolution: str = "720p",
        generate_audio: bool = True,
        seed: Optional[int] = None,
        model: Optional[str] = None,
    ) -> bytes:
        payload = self._build_payload(
            prompt,
            image=image,
            end_image=end_image,
            duration=duration,
            ratio=ratio,
            resolution=resolution,
            generate_audio=generate_audio,
            seed=seed,
            model=model,
        )
        task_id = self._create_task(payload)
        data = self._poll(task_id)
        return self._download(self._extract_video_url(data))
