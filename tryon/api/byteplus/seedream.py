"""
BytePlus ModelArk — Seedream image generation adapters.

Seedream 5.0 Pro is ByteDance's precision image model for text-to-image,
single-image editing, and multi-reference fusion (up to 10 refs).

  POST {base}/images/generations

Product / docs:
  https://docs.byteplus.com/en/docs/ModelArk/
  https://ai.byteplus.com/en/product/Seedream

Env:
  ARK_API_KEY or BYTEPLUS_ARK_API_KEY
  BYTEPLUS_ARK_BASE_URL (optional)
"""

from __future__ import annotations

import base64
import io
import os
from typing import Any, Dict, List, Optional, Union

import requests
from PIL import Image

DEFAULT_BASE_URL = "https://ark.ap-southeast.bytepluses.com/api/v3"

SEEDREAM_MODELS = {
    "seedream-5-0-pro": "seedream-5-0-pro-260628",
    "seedream-5.0-pro": "seedream-5-0-pro-260628",
    "seedream-5-0-pro-260628": "seedream-5-0-pro-260628",
    "seedream-5-0-lite": "seedream-5-0-lite",
    "seedream-4-0": "seedream-4-0-250828",
    "seedream-4-5": "seedream-4-5",
}


class SeedreamAdapter:
    """BytePlus ModelArk Seedream image adapter (T2I / edit / multi-ref)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "seedream-5-0-pro",
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
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def _resolve_model(model: str) -> str:
        key = model.strip()
        return SEEDREAM_MODELS.get(key, key)

    def _prepare_image(self, image: Union[str, io.BytesIO, Image.Image, bytes]) -> str:
        if isinstance(image, str):
            if image.startswith(("http://", "https://", "data:")):
                return image
            if os.path.exists(image):
                with open(image, "rb") as f:
                    raw = f.read()
                return f"data:image/png;base64,{base64.b64encode(raw).decode('ascii')}"
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
            raise ValueError("Unsupported image input type for Seedream.")
        return f"data:image/png;base64,{base64.b64encode(raw).decode('ascii')}"

    def _request(self, payload: Dict[str, Any]) -> List[Image.Image]:
        url = f"{self.base_url}/images/generations"
        resp = requests.post(url, headers=self.headers, json=payload, timeout=180)
        if resp.status_code >= 400:
            raise RuntimeError(f"Seedream request failed ({resp.status_code}): {resp.text}")
        data = resp.json()
        items = data.get("data") or data.get("images") or []
        if not items:
            raise RuntimeError(f"Seedream returned no images: {data}")

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
                raise RuntimeError(f"Seedream item missing url/b64_json: {item}")
        return images

    def generate_text_to_image(
        self,
        prompt: str,
        size: str = "2K",
        output_format: str = "png",
        watermark: bool = False,
        response_format: str = "url",
        seed: Optional[int] = None,
        model: Optional[str] = None,
    ) -> List[Image.Image]:
        if not prompt:
            raise ValueError("prompt is required.")
        payload: Dict[str, Any] = {
            "model": self._resolve_model(model) if model else self.model,
            "prompt": prompt,
            "size": size,
            "output_format": output_format,
            "watermark": watermark,
            "response_format": response_format,
        }
        if seed is not None:
            payload["seed"] = int(seed)
        return self._request(payload)

    def generate_image_edit(
        self,
        prompt: str,
        image: Union[str, io.BytesIO, Image.Image, bytes, List[Any]],
        size: str = "2K",
        output_format: str = "png",
        watermark: bool = False,
        response_format: str = "url",
        seed: Optional[int] = None,
        model: Optional[str] = None,
    ) -> List[Image.Image]:
        if not prompt:
            raise ValueError("prompt is required.")
        if isinstance(image, list):
            prepared: Any = [self._prepare_image(img) for img in image]
        else:
            prepared = self._prepare_image(image)
        payload: Dict[str, Any] = {
            "model": self._resolve_model(model) if model else self.model,
            "prompt": prompt,
            "image": prepared,
            "size": size,
            "output_format": output_format,
            "watermark": watermark,
            "response_format": response_format,
        }
        if seed is not None:
            payload["seed"] = int(seed)
        return self._request(payload)
