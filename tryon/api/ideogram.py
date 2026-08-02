"""
Ideogram 4.0 image generation adapter.

  POST https://api.ideogram.ai/v1/ideogram-v4/generate

Rendering speed tiers (pricing):
  TURBO / DEFAULT / QUALITY

Docs:
  https://developer.ideogram.ai/ideogram-api/api-overview
  https://ideogram.ai/models/4.0/

Env:
  IDEOGRAM_API_KEY
"""

from __future__ import annotations

import io
import os
from typing import Any, Dict, List, Optional

import requests
from PIL import Image

DEFAULT_BASE_URL = "https://api.ideogram.ai"

VALID_SPEEDS = {"TURBO", "DEFAULT", "QUALITY"}
VALID_ASPECT = {
    "1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3",
    "10:16", "16:10", "1:3", "3:1",
}


class IdeogramAdapter:
    """Ideogram 4.0 text-to-image adapter."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.api_key = api_key or os.getenv("IDEOGRAM_API_KEY")
        if not self.api_key:
            raise ValueError("IDEOGRAM_API_KEY is required (or pass api_key=).")
        self.base_url = (
            base_url or os.getenv("IDEOGRAM_BASE_URL") or DEFAULT_BASE_URL
        ).rstrip("/")
        self.headers = {
            "Api-Key": self.api_key,
            "Content-Type": "application/json",
        }

    def generate_text_to_image(
        self,
        prompt: str,
        rendering_speed: str = "DEFAULT",
        aspect_ratio: Optional[str] = None,
        magic_prompt: Optional[str] = None,
        seed: Optional[int] = None,
        num_images: int = 1,
        style_type: Optional[str] = None,
    ) -> List[Image.Image]:
        if not prompt:
            raise ValueError("prompt is required.")
        speed = rendering_speed.upper()
        if speed not in VALID_SPEEDS:
            raise ValueError(f"rendering_speed must be one of {sorted(VALID_SPEEDS)}")
        if aspect_ratio and aspect_ratio not in VALID_ASPECT:
            raise ValueError(f"Invalid aspect_ratio '{aspect_ratio}'.")

        payload: Dict[str, Any] = {
            "text_prompt": prompt,
            "rendering_speed": speed,
            "num_images": int(num_images),
        }
        # Ideogram 3.x used `prompt`; 4.0 prefers `text_prompt`. Send both for compat.
        payload["prompt"] = prompt
        if aspect_ratio:
            payload["aspect_ratio"] = aspect_ratio
        if magic_prompt:
            payload["magic_prompt"] = magic_prompt
        if seed is not None:
            payload["seed"] = int(seed)
        if style_type:
            payload["style_type"] = style_type

        resp = requests.post(
            f"{self.base_url}/v1/ideogram-v4/generate",
            headers=self.headers,
            json=payload,
            timeout=180,
        )
        if resp.status_code >= 400:
            raise RuntimeError(f"Ideogram 4.0 failed ({resp.status_code}): {resp.text}")
        data = resp.json()
        items = data.get("data") or data.get("images") or []
        if not items:
            raise RuntimeError(f"Ideogram returned no images: {data}")

        images: List[Image.Image] = []
        for item in items:
            url = item.get("url") or item.get("image_url")
            if not url:
                raise RuntimeError(f"Ideogram item missing url: {item}")
            r = requests.get(url, timeout=60)
            r.raise_for_status()
            images.append(Image.open(io.BytesIO(r.content)).convert("RGB"))
        return images
