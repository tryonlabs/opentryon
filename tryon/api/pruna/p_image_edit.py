"""
Pruna P-Image-Edit — multi-image composition and editing.

  Model header: p-image-edit
  Docs: https://docs.api.pruna.ai/guides/models/p-image-edit
"""

from __future__ import annotations

import io
from typing import Any, Dict, List, Optional, Sequence, Union

from PIL import Image

from .client import MediaInput, PrunaClient

VALID_ASPECT = {
    "match_input_image",
    "1:1",
    "16:9",
    "9:16",
    "4:3",
    "3:4",
    "3:2",
    "2:3",
}


class PImageEditAdapter:
    """Pruna P-Image-Edit adapter (1–5 reference images + text instruction)."""

    MODEL = "p-image-edit"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self._client = PrunaClient(api_key=api_key, base_url=base_url)

    def generate_image_edit(
        self,
        prompt: str,
        image: Optional[Union[MediaInput, Sequence[MediaInput]]] = None,
        images: Optional[Union[MediaInput, Sequence[MediaInput]]] = None,
        aspect_ratio: str = "match_input_image",
        turbo: bool = True,
        seed: Optional[int] = None,
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

        resolved = images if images is not None else image
        if not resolved:
            raise ValueError("At least one image is required (pass image= or images=).")

        if isinstance(resolved, (list, tuple)):
            image_list = list(resolved)
        else:
            image_list = [resolved]
        if not (1 <= len(image_list) <= 5):
            raise ValueError("P-Image-Edit accepts 1–5 reference images.")

        image_urls = [
            self._client.prepare_url(img, default_filename="image.png")
            for img in image_list
        ]

        payload: Dict[str, Any] = {
            "prompt": prompt,
            "images": image_urls,
            "aspect_ratio": aspect_ratio,
            "turbo": bool(turbo),
            "disable_safety_checker": bool(disable_safety_checker),
        }
        if seed is not None:
            payload["seed"] = int(seed)
        payload.update(kwargs)

        url = self._client.predict(
            self.MODEL,
            payload,
            wait=wait,
            max_wait_time=max_wait_time,
            label="P-Image-Edit",
        )
        return [Image.open(io.BytesIO(self._client.download(url)))]
