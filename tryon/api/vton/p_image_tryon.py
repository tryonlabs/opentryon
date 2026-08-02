"""
Pruna AI P-Image-Try-On API Adapter

Adapter for Pruna AI's P-Image-Try-On model: virtually fits one or more
garments onto a person's photo. Unlike single-garment VTON APIs (Nova Canvas,
Kling AI, Segmind), this endpoint accepts up to 11 garment reference images
in a single call (multi-garment try-on) and also doubles as a general
garment-composition/image-editing tool.

Reference: https://docs.api.pruna.ai/guides/models/p-image-try-on

Uses the shared :class:`tryon.api.pruna.client.PrunaClient` for upload /
predict / poll / download.
"""

from __future__ import annotations

import io
from typing import Any, Dict, List, Optional, Union

from PIL import Image

from tryon.api.pruna.client import MediaInput, PrunaClient


class PImageTryOnAdapter:
    """
    Adapter for Pruna AI's P-Image-Try-On API.

    Fits one or more garment reference images onto a person's photo.
    Supports up to 11 garment reference images (up to 6 recommended) in a
    single call, an experimental ``prompt`` for disambiguating non-flatlay
    garment images, and an experimental ``reference_pose`` to repose the
    person before compositing.

    Reference: https://docs.api.pruna.ai/guides/models/p-image-try-on
    """

    MODEL = "p-image-try-on"
    VALID_OUTPUT_FORMATS = {"jpg", "png", "webp"}

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self._client = PrunaClient(api_key=api_key, base_url=base_url)

    def generate(
        self,
        person_image: Optional[MediaInput] = None,
        garment_images: Optional[Union[MediaInput, List[Any]]] = None,
        *,
        person: Optional[MediaInput] = None,
        garments: Optional[Union[MediaInput, List[Any]]] = None,
        source_image: Optional[MediaInput] = None,
        model_image: Optional[MediaInput] = None,
        prompt: str = "",
        seed: Optional[int] = None,
        turbo: bool = False,
        output_format: str = "jpg",
        output_quality: int = 95,
        reference_pose: Optional[MediaInput] = None,
        preserve_input_size: bool = True,
        wait: bool = True,
        max_wait_time: int = 120,
        **kwargs,
    ) -> str:
        """Generate a virtual try-on result; return the result image URL."""
        resolved_person = person_image or person or source_image or model_image
        resolved_garments = garment_images if garment_images is not None else garments

        if resolved_person is None:
            raise ValueError(
                "Person image is required. Pass person_image "
                "(or person/source_image/model_image)."
            )
        if not resolved_garments:
            raise ValueError(
                "At least one garment image is required. Pass garment_images (or garments)."
            )

        if isinstance(resolved_garments, (list, tuple)):
            garment_list = list(resolved_garments)
        else:
            garment_list = [resolved_garments]

        if output_format not in self.VALID_OUTPUT_FORMATS:
            raise ValueError(
                f"Invalid output_format '{output_format}'. "
                f"Must be one of: {sorted(self.VALID_OUTPUT_FORMATS)}"
            )

        person_url = self._client.prepare_url(
            resolved_person, default_filename="person.png"
        )
        garment_urls = [
            self._client.prepare_url(g, default_filename="garment.png")
            for g in garment_list
        ]

        input_payload: Dict[str, Any] = {
            "person_image": person_url,
            "garment_images": garment_urls,
            "prompt": prompt,
            "output_format": output_format,
            "output_quality": output_quality,
            "preserve_input_size": preserve_input_size,
        }
        if seed is not None:
            input_payload["seed"] = seed
        if turbo:
            input_payload["turbo"] = True
        if reference_pose is not None:
            input_payload["reference_pose"] = self._client.prepare_url(
                reference_pose, default_filename="pose.png"
            )
        input_payload.update(kwargs)

        return self._client.predict(
            self.MODEL,
            input_payload,
            wait=wait,
            max_wait_time=max_wait_time,
            label="P-Image-Try-On",
        )

    def generate_and_decode(
        self,
        person_image: Optional[MediaInput] = None,
        garment_images: Optional[Union[MediaInput, List[Any]]] = None,
        **kwargs,
    ) -> List[Image.Image]:
        """Generate a virtual try-on result and decode it to a PIL Image list."""
        url = self.generate(
            person_image=person_image, garment_images=garment_images, **kwargs
        )
        return [Image.open(io.BytesIO(self._client.download(url)))]
