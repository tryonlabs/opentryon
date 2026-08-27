"""
Pruna P-Image-Ideogram — text-to-image (Pruna × Ideogram).

  Model header: p-image-ideogram
  Docs: https://docs.pruna.ai/en/stable/docs_pruna_endpoints/performance_models/p-image-ideogram.html
  API:  POST https://api.pruna.ai/v1/predictions  (header Model: p-image-ideogram)

Thinking levels: very low / low / medium / high (default) / very high.
Resolution: 1K (default) or 2K. Prompt upsampling is on by default.

Ideogram also publishes a first-party ``POST /v1/text-to-image/p-image-ideogram``
surface (Api-Key, four Quality levels). This adapter follows the Pruna
predictions API the rest of the P-Image family uses.

Examples::

    adapter = PImageIdeogramAdapter()
    images = adapter.generate_text_to_image(
        prompt='Lookbook cover. Exact visible text only: "ATELIER NOIR"',
        thinking="high",
        image_size="2K",
        aspect_ratio="3:4",
    )
"""

from __future__ import annotations

import io
from typing import Any, Dict, List, Optional

from PIL import Image

from .client import PrunaClient

VALID_ASPECT = {"1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3", "custom"}
VALID_IMAGE_SIZE = {"1K", "2K"}
VALID_OUTPUT_FORMAT = {"jpg", "png", "webp"}
VALID_THINKING = {
    "very low",
    "low",
    "medium",
    "high",
    "very high",
}

_THINKING_ALIASES = {
    "very_low": "very low",
    "verylow": "very low",
    "VERY_LOW": "very low",
    "very-low": "very low",
    "very high": "very high",
    "very_high": "very high",
    "veryhigh": "very high",
    "VERY_HIGH": "very high",
    "very-high": "very high",
    "HIGH": "high",
    "LOW": "low",
    "MEDIUM": "medium",
}


def _normalize_thinking(value: str) -> str:
    raw = (value or "").strip()
    mapped = _THINKING_ALIASES.get(raw) or _THINKING_ALIASES.get(raw.lower()) or raw.lower()
    if mapped not in VALID_THINKING:
        raise ValueError(
            f"Invalid thinking '{value}'. Must be one of: {sorted(VALID_THINKING)}"
        )
    return mapped


def _validate_custom_dim(value: int, name: str) -> None:
    n = int(value)
    if n < 0 or n > 2560 or n % 16 != 0:
        raise ValueError(
            f"{name} must be 0–2560 and a multiple of 16 when aspect_ratio='custom' (got {value})."
        )


class PImageIdeogramAdapter:
    """Pruna P-Image-Ideogram text-to-image adapter."""

    MODEL = "p-image-ideogram"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self._client = PrunaClient(api_key=api_key, base_url=base_url)

    def generate_text_to_image(
        self,
        prompt: str,
        thinking: str = "high",
        aspect_ratio: str = "1:1",
        image_size: str = "1K",
        width: Optional[int] = None,
        height: Optional[int] = None,
        seed: Optional[int] = None,
        prompt_upsampling: bool = True,
        output_format: str = "jpg",
        output_quality: Optional[int] = None,
        wait: bool = True,
        max_wait_time: int = 180,
        **kwargs: Any,
    ) -> List[Image.Image]:
        if not prompt:
            raise ValueError("prompt is required.")
        thinking_n = _normalize_thinking(thinking)
        if aspect_ratio not in VALID_ASPECT:
            raise ValueError(
                f"Invalid aspect_ratio '{aspect_ratio}'. Must be one of: {sorted(VALID_ASPECT)}"
            )
        size = (image_size or "1K").upper()
        if size not in VALID_IMAGE_SIZE:
            raise ValueError(
                f"Invalid image_size '{image_size}'. Must be one of: {sorted(VALID_IMAGE_SIZE)}"
            )
        if aspect_ratio == "custom":
            if width is None or height is None:
                raise ValueError("width and height are required when aspect_ratio='custom'.")
            _validate_custom_dim(width, "width")
            _validate_custom_dim(height, "height")
        elif width is not None or height is not None:
            raise ValueError("width and height are only valid when aspect_ratio='custom'.")
        fmt = (output_format or "jpg").lower()
        if fmt == "jpeg":
            fmt = "jpg"
        if fmt not in VALID_OUTPUT_FORMAT:
            raise ValueError(
                f"Invalid output_format '{output_format}'. Must be jpg, png, or webp."
            )

        payload: Dict[str, Any] = {
            "prompt": prompt,
            "thinking": thinking_n,
            "aspect_ratio": aspect_ratio,
            "prompt_upsampling": bool(prompt_upsampling),
            "output_format": fmt,
        }
        if aspect_ratio == "custom":
            payload["width"] = int(width)
            payload["height"] = int(height)
        else:
            payload["image_size"] = size
        if seed is not None:
            payload["seed"] = int(seed)
        if output_quality is not None:
            payload["output_quality"] = int(output_quality)
        payload.update(kwargs)

        url = self._client.predict(
            self.MODEL,
            payload,
            wait=wait,
            max_wait_time=max_wait_time,
            label="P-Image-Ideogram",
        )
        return [Image.open(io.BytesIO(self._client.download(url)))]
