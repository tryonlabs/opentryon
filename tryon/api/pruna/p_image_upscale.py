"""
Pruna P-Image-Upscale — AI image upscaling.

  Model header: p-image-upscale
  Docs: https://docs.api.pruna.ai/guides/models/p-image-upscale
"""

from __future__ import annotations

import io
from typing import Any, Dict, List, Optional

from PIL import Image

from .client import MediaInput, PrunaClient

VALID_FORMATS = {"jpg", "png", "webp"}


class PImageUpscaleAdapter:
    """Pruna P-Image-Upscale adapter (target resolution in megapixels)."""

    MODEL = "p-image-upscale"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self._client = PrunaClient(api_key=api_key, base_url=base_url)

    def upscale(
        self,
        image: MediaInput,
        target: int = 4,
        output_format: str = "jpg",
        output_quality: int = 80,
        enhance_details: bool = False,
        enhance_realism: bool = False,
        disable_safety_checker: bool = False,
        wait: bool = True,
        max_wait_time: int = 180,
        **kwargs: Any,
    ) -> List[Image.Image]:
        if image is None:
            raise ValueError("image is required.")
        if not (1 <= int(target) <= 128):
            raise ValueError("target must be an integer megapixel value between 1 and 128.")
        if output_format not in VALID_FORMATS:
            raise ValueError(
                f"Invalid output_format '{output_format}'. Must be one of: {sorted(VALID_FORMATS)}"
            )

        image_url = self._client.prepare_url(image, default_filename="image.png")
        payload: Dict[str, Any] = {
            "image": image_url,
            "target": int(target),
            "output_format": output_format,
            "output_quality": int(output_quality),
            "enhance_details": bool(enhance_details),
            "enhance_realism": bool(enhance_realism),
            "disable_safety_checker": bool(disable_safety_checker),
        }
        payload.update(kwargs)

        url = self._client.predict(
            self.MODEL,
            payload,
            wait=wait,
            max_wait_time=max_wait_time,
            label="P-Image-Upscale",
        )
        return [Image.open(io.BytesIO(self._client.download(url)))]
