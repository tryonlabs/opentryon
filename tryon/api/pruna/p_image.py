"""
Pruna P-Image — ultra-fast text-to-image.

  Model header: p-image
  Docs: https://docs.api.pruna.ai/guides/models/p-image
"""

from __future__ import annotations

import io
from typing import Any, Dict, List, Optional

from PIL import Image

from .client import PrunaClient

VALID_ASPECT = {"1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3", "custom"}


class PImageAdapter:
    """Pruna P-Image text-to-image adapter."""

    MODEL = "p-image"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self._client = PrunaClient(api_key=api_key, base_url=base_url)

    def generate_text_to_image(
        self,
        prompt: str,
        aspect_ratio: str = "16:9",
        width: Optional[int] = None,
        height: Optional[int] = None,
        seed: Optional[int] = None,
        prompt_upsampling: bool = False,
        lora_weights: Optional[str] = None,
        lora_scale: Optional[float] = None,
        hf_api_token: Optional[str] = None,
        disable_safety_checker: bool = False,
        wait: bool = True,
        max_wait_time: int = 120,
        **kwargs: Any,
    ) -> List[Image.Image]:
        if not prompt:
            raise ValueError("prompt is required.")
        if aspect_ratio not in VALID_ASPECT:
            raise ValueError(
                f"Invalid aspect_ratio '{aspect_ratio}'. Must be one of: {sorted(VALID_ASPECT)}"
            )
        if aspect_ratio == "custom" and (width is None or height is None):
            raise ValueError("width and height are required when aspect_ratio='custom'.")

        payload: Dict[str, Any] = {
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "prompt_upsampling": bool(prompt_upsampling),
            "disable_safety_checker": bool(disable_safety_checker),
        }
        if width is not None:
            payload["width"] = int(width)
        if height is not None:
            payload["height"] = int(height)
        if seed is not None:
            payload["seed"] = int(seed)
        if lora_weights:
            payload["lora_weights"] = lora_weights
        if lora_scale is not None:
            payload["lora_scale"] = float(lora_scale)
        if hf_api_token:
            payload["hf_api_token"] = hf_api_token
        payload.update(kwargs)

        url = self._client.predict(
            self.MODEL,
            payload,
            wait=wait,
            max_wait_time=max_wait_time,
            label="P-Image",
        )
        return [Image.open(io.BytesIO(self._client.download(url)))]
