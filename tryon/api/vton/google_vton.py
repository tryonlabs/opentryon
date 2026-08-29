"""Google Vertex AI Virtual Try-On (``virtual-try-on-001``).

Dedicated person + product try-on via the first-party Vertex / Gemini
Enterprise ``recontext_image`` API. This is **not** Gemini Developer API
composition (Nano Banana) and does **not** use ``GEMINI_API_KEY``.

Official docs:
    https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/imagen/virtual-try-on-001
    https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/capabilities/generate-virtual-try-on-images

Auth:
    Application Default Credentials + a GCP project.
    ``gcloud auth application-default login`` or ``GOOGLE_APPLICATION_CREDENTIALS``.
    Set ``GOOGLE_CLOUD_PROJECT`` (required) and optionally ``GOOGLE_CLOUD_LOCATION``
    (default ``global``).

Example:
    >>> import os
    >>> os.environ["GOOGLE_CLOUD_PROJECT"] = "my-gcp-project"
    >>> from tryon.api.vton.google_vton import GoogleVTONAdapter
    >>> adapter = GoogleVTONAdapter()
    >>> images = adapter.generate_and_decode(
    ...     person="person.jpg",
    ...     garment="sweater.jpg",
    ... )
    >>> images[0].save("worn.png")
"""

from __future__ import annotations

import io
import os
from typing import List, Optional, Union

import requests
from PIL import Image as PILImage

try:
    from google import genai
    from google.genai.types import (
        Image as GenaiImage,
        ProductImage,
        RecontextImageConfig,
        RecontextImageSource,
    )

    GOOGLE_GENAI_AVAILABLE = True
except ImportError:  # pragma: no cover - optional at import time
    GOOGLE_GENAI_AVAILABLE = False

ImageInput = Union[str, io.BytesIO, PILImage.Image, bytes]

DEFAULT_MODEL = "virtual-try-on-001"
DEFAULT_LOCATION = "global"
MAX_IMAGE_BYTES = 10 * 1024 * 1024
VALID_MIME = {"image/jpeg", "image/png"}
PERSON_GENERATION = ("dont_allow", "allow_adult", "allow_all")
SAFETY_LEVELS = (
    "block_low_and_above",
    "block_medium_and_above",
    "block_only_high",
    "block_none",
)


class GoogleVTONAdapter:
    """Vertex AI Virtual Try-On adapter (``virtual-try-on-001``)."""

    def __init__(
        self,
        project: Optional[str] = None,
        location: Optional[str] = None,
        model: Optional[str] = None,
    ):
        """
        Args:
            project: GCP project id. Defaults to ``GOOGLE_CLOUD_PROJECT``.
            location: Vertex location. Defaults to ``GOOGLE_CLOUD_LOCATION``
                or ``global``.
            model: Upstream model id. Defaults to ``virtual-try-on-001``.
        """
        if not GOOGLE_GENAI_AVAILABLE:
            raise ImportError(
                "google-genai is required for Google Virtual Try-On. "
                "Install with: pip install google-genai"
            )

        self.project = project or os.getenv("GOOGLE_CLOUD_PROJECT")
        if not self.project:
            raise ValueError(
                "GOOGLE_CLOUD_PROJECT is required for Google Virtual Try-On "
                "(Vertex AI). This is not GEMINI_API_KEY. Set the GCP project "
                "id and authenticate with `gcloud auth application-default login` "
                "or GOOGLE_APPLICATION_CREDENTIALS."
            )
        self.location = (
            location
            or os.getenv("GOOGLE_CLOUD_LOCATION")
            or DEFAULT_LOCATION
        )
        self.model = model or DEFAULT_MODEL
        # Force Vertex. A stray GEMINI_API_KEY must not send this to the
        # Gemini Developer API, which does not host virtual-try-on-001.
        self.client = genai.Client(
            vertexai=True,
            project=self.project,
            location=self.location,
        )

    def _load_bytes(self, image_input: ImageInput) -> tuple[bytes, str]:
        """Return PNG/JPEG (bytes, mime_type) for a path, URL, PIL image, or raw bytes."""
        if isinstance(image_input, PILImage.Image):
            return self._pil_to_png_or_jpeg(image_input)

        if isinstance(image_input, (bytes, bytearray)):
            return self._as_png_or_jpeg(bytes(image_input))

        if hasattr(image_input, "read"):
            image_input.seek(0)
            data = image_input.read()
            image_input.seek(0)
            return self._as_png_or_jpeg(data)

        if isinstance(image_input, str):
            if image_input.startswith("gs://"):
                raise ValueError(
                    "Pass GCS URIs through a downloaded path or https URL. "
                    "Local files and http(s) URLs are supported."
                )
            if image_input.startswith(("http://", "https://")):
                response = requests.get(image_input, timeout=60)
                response.raise_for_status()
                return self._as_png_or_jpeg(response.content)
            with open(image_input, "rb") as fh:
                return self._as_png_or_jpeg(fh.read())

        raise ValueError(
            "Invalid image input: must be a file path, URL, PIL Image, "
            "bytes, or file-like object."
        )

    @staticmethod
    def _pil_to_png_or_jpeg(image: PILImage.Image) -> tuple[bytes, str]:
        fmt = (image.format or "PNG").upper()
        buf = io.BytesIO()
        if fmt in ("JPEG", "JPG"):
            image.convert("RGB").save(buf, format="JPEG")
            return buf.getvalue(), "image/jpeg"
        image.save(buf, format="PNG")
        return buf.getvalue(), "image/png"

    @classmethod
    def _as_png_or_jpeg(cls, data: bytes) -> tuple[bytes, str]:
        if data.startswith(b"\x89PNG"):
            return data, "image/png"
        if data.startswith(b"\xff\xd8"):
            return data, "image/jpeg"
        return cls._pil_to_png_or_jpeg(PILImage.open(io.BytesIO(data)))

    def _to_genai_image(self, image_input: ImageInput) -> GenaiImage:
        data, mime = self._load_bytes(image_input)
        if len(data) > MAX_IMAGE_BYTES:
            raise ValueError(
                f"Image is {len(data):,} bytes; Vertex Virtual Try-On allows "
                f"at most {MAX_IMAGE_BYTES:,} bytes (10MB) as PNG or JPEG."
            )
        return GenaiImage(image_bytes=data, mime_type=mime)

    def generate_and_decode(
        self,
        person: Optional[ImageInput] = None,
        garment: Optional[ImageInput] = None,
        *,
        source_image: Optional[ImageInput] = None,
        reference_image: Optional[ImageInput] = None,
        model_image: Optional[ImageInput] = None,
        cloth_image: Optional[ImageInput] = None,
        person_image: Optional[ImageInput] = None,
        garment_image: Optional[ImageInput] = None,
        number_of_images: int = 1,
        seed: Optional[int] = None,
        person_generation: str = "allow_adult",
        safety_filter_level: Optional[str] = None,
        add_watermark: bool = True,
        output_mime_type: str = "image/png",
        output_gcs_uri: Optional[str] = None,
        **kwargs,
    ) -> List[PILImage.Image]:
        """Generate try-on images and return PIL Images.

        Vertex Virtual Try-On does **not** accept a text prompt. Person and
        product images are the only inputs.

        Args:
            person / garment: Person and product images (path, URL, PIL, bytes).
            Aliases match other VTON adapters (source_image, model_image, …).
            number_of_images: 1–4 samples.
            seed: Optional reproducibility seed.
            person_generation: ``dont_allow``, ``allow_adult`` (default),
                or ``allow_all``. Shopper photos need ``allow_adult``.
            safety_filter_level: Optional Vertex safety enum (lowercase).
            add_watermark: SynthID / C2PA watermark (default True).
            output_mime_type: ``image/png`` or ``image/jpeg``.
            output_gcs_uri: Optional ``gs://`` prefix to also store outputs.
        """
        resolved_person = person or source_image or person_image or model_image
        resolved_garment = garment or reference_image or garment_image or cloth_image
        if resolved_person is None:
            raise ValueError(
                "Person image is required. Pass person, source_image, "
                "person_image, or model_image."
            )
        if resolved_garment is None:
            raise ValueError(
                "Garment/product image is required. Pass garment, "
                "reference_image, garment_image, or cloth_image."
            )
        if not 1 <= int(number_of_images) <= 4:
            raise ValueError("number_of_images must be between 1 and 4.")
        pg = (person_generation or "allow_adult").lower()
        if pg not in PERSON_GENERATION:
            raise ValueError(
                f"person_generation must be one of {list(PERSON_GENERATION)}"
            )
        if output_mime_type not in VALID_MIME:
            raise ValueError("output_mime_type must be image/png or image/jpeg.")

        config_kwargs = {
            "number_of_images": int(number_of_images),
            "person_generation": pg.upper(),
            "add_watermark": bool(add_watermark),
            "output_mime_type": output_mime_type,
        }
        if seed is not None:
            config_kwargs["seed"] = seed
        if safety_filter_level:
            level = safety_filter_level.lower()
            if level not in SAFETY_LEVELS:
                raise ValueError(
                    f"safety_filter_level must be one of {list(SAFETY_LEVELS)}"
                )
            config_kwargs["safety_filter_level"] = level.upper()
        if output_gcs_uri:
            config_kwargs["output_gcs_uri"] = output_gcs_uri

        try:
            response = self.client.models.recontext_image(
                model=self.model,
                source=RecontextImageSource(
                    person_image=self._to_genai_image(resolved_person),
                    product_images=[
                        ProductImage(
                            product_image=self._to_genai_image(resolved_garment)
                        )
                    ],
                ),
                config=RecontextImageConfig(**config_kwargs),
            )
        except Exception as exc:
            raise ValueError(
                f"Google Virtual Try-On failed ({self.model} @ "
                f"{self.project}/{self.location}): {exc}"
            ) from exc

        images: List[PILImage.Image] = []
        for generated in response.generated_images or []:
            gimg = getattr(generated, "image", None)
            if gimg is None:
                continue
            raw = getattr(gimg, "image_bytes", None)
            if raw:
                images.append(PILImage.open(io.BytesIO(raw)))
                continue
            pil = getattr(gimg, "_pil_image", None)
            if pil is not None:
                images.append(pil)
        if not images:
            raise ValueError(
                "Google Virtual Try-On returned no images. "
                f"Response: {response!r}"
            )
        return images
