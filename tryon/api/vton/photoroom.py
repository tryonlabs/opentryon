"""Photoroom Virtual Try-On and Virtual Model.

First-party Image Editing API (Plus / Enterprise). Same
``POST /v2/edit`` endpoint; the difference is how
``virtualModel.model`` is set:

- **Virtual Try-On** — garment + shopper photo
  (``virtualModel.model.custom.imageFile`` / ``imageUrl``)
- **Virtual Model** — garment only, optional preset or custom model
  (``virtualModel.model.preset.name``, default ``avery``)

Official docs:
    https://docs.photoroom.com/image-editing-api-plus-plan/virtual-try-on
    https://docs.photoroom.com/image-editing-api-plus-plan/virtual-model
    Product: https://www.photoroom.com/tools/virtual-model

Auth: ``x-api-key`` header. Prefix the key with ``sandbox_`` for
watermarked test calls (or set ``PHOTOROOM_SANDBOX=1``).

Env:
    PHOTOROOM_API_KEY (required)
    PHOTOROOM_BASE_URL — default https://image-api.photoroom.com
    PHOTOROOM_SANDBOX — if ``1``/``true``, prefix ``sandbox_`` on the key

Example:
    >>> from tryon.api.vton.photoroom import PhotoroomVTONAdapter
    >>> adapter = PhotoroomVTONAdapter()
    >>> worn = adapter.generate_and_decode(person="selfie.jpg", garment="dress.jpg")
    >>> catalog = adapter.generate_virtual_model(garment="flatlay.jpg", preset_model="avery")
"""

from __future__ import annotations

import io
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import requests
from PIL import Image as PILImage

ImageInput = Union[str, Path, io.BytesIO, bytes, PILImage.Image]

DEFAULT_BASE_URL = "https://image-api.photoroom.com"
EDIT_PATH = "/v2/edit"

PRESET_MODELS = (
    "avery",
    "sam",
    "taylor",
    "kendall",
    "jordan",
    "casey",
    "maya",
    "reece",
    "lena",
    "julia",
    "jackson",
    "sophia",
    "emma",
    "ava",
    "zoe",
    "fiona",
)
PRESET_SCENES = (
    "random",
    "street",
    "bedroom",
    "sunset",
    "factory",
    "studio",
    "coloredstudio",
    "concretestudio",
    "beach",
    "tropical",
    "library",
    "forest",
    "businessdistrict",
    "countryside",
    "flowers",
    "goldenlight",
    "mountain",
    "pool",
    "latincity",
    "cafe",
    "asiancity",
    "nightlights",
    "desert",
)
PRESET_POSES = (
    "random",
    "standing",
    "34turn",
    "powerstance",
    "walkingforward",
    "handinpocket",
    "crossedarms",
    "back",
    "overtheshoulder",
    "seated",
    "adjustingclothing",
    "playfulspin",
)
OUTPUT_SIZES = (
    "PORTRAIT_HD_16_9",
    "PORTRAIT_HD_4_3",
    "PORTRAIT_HD_3_2",
    "SQUARE_HD",
    "LANDSCAPE_HD_3_2",
    "LANDSCAPE_HD_4_3",
    "LANDSCAPE_HD_16_9",
)
MODES = ("try-on", "virtual-model")


class PhotoroomVTONAdapter:
    """Photoroom Image Editing API — Virtual Try-On and Virtual Model."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 180.0,
    ):
        """
        Args:
            api_key: Photoroom API key. Defaults to ``PHOTOROOM_API_KEY``.
            base_url: API host. Defaults to ``PHOTOROOM_BASE_URL`` or
                ``https://image-api.photoroom.com``.
            timeout: HTTP timeout in seconds for the edit call.
        """
        raw = api_key or os.getenv("PHOTOROOM_API_KEY")
        if not raw:
            raise ValueError(
                "Photoroom API key is required. Set PHOTOROOM_API_KEY "
                "(https://app.photoroom.com/api) or pass api_key. "
                "Prefix the key with sandbox_ for watermarked test calls."
            )
        sandbox = os.getenv("PHOTOROOM_SANDBOX", "").strip().lower()
        if sandbox in {"1", "true", "yes"} and not raw.startswith("sandbox_"):
            raw = f"sandbox_{raw}"
        self.api_key = raw
        self.base_url = (
            base_url or os.getenv("PHOTOROOM_BASE_URL") or DEFAULT_BASE_URL
        ).rstrip("/")
        self.timeout = float(timeout)

    def _headers(self) -> Dict[str, str]:
        return {"x-api-key": self.api_key}

    def _load_bytes(self, image_input: ImageInput) -> tuple[bytes, str]:
        if isinstance(image_input, PILImage.Image):
            return self._pil_to_png_or_jpeg(image_input)
        if isinstance(image_input, (bytes, bytearray)):
            return self._as_png_or_jpeg(bytes(image_input))
        if hasattr(image_input, "read"):
            image_input.seek(0)
            data = image_input.read()
            image_input.seek(0)
            return self._as_png_or_jpeg(data)
        if isinstance(image_input, Path):
            image_input = str(image_input)
        if isinstance(image_input, str):
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

    @staticmethod
    def _is_url(value: Any) -> bool:
        return isinstance(value, str) and value.startswith(("http://", "https://"))

    def _file_part(
        self, image_input: ImageInput, filename: str
    ) -> Tuple[str, io.BytesIO, str]:
        data, mime = self._load_bytes(image_input)
        ext = ".png" if mime == "image/png" else ".jpg"
        if not filename.endswith((".png", ".jpg", ".jpeg")):
            filename = f"{filename}{ext}"
        return filename, io.BytesIO(data), mime

    def _edit(
        self,
        *,
        product: ImageInput,
        person: Optional[ImageInput],
        preset_model: str,
        scene: str,
        pose: str,
        size: str,
        prompt: Optional[str],
        scene_image: Optional[ImageInput],
        additional_product_images: Optional[Sequence[ImageInput]],
        remove_background: bool,
        reference_box: str,
    ) -> PILImage.Image:
        url = f"{self.base_url}{EDIT_PATH}"
        data: Dict[str, str] = {
            "removeBackground": "true" if remove_background else "false",
            "referenceBox": reference_box,
            "virtualModel.mode": "ai.auto",
            "virtualModel.pose": pose,
            "virtualModel.size": size,
        }
        files: Dict[str, Any] = {}

        if self._is_url(product):
            data["imageUrl"] = str(product)
        else:
            files["imageFile"] = self._file_part(product, "product")

        if person is not None:
            if self._is_url(person):
                data["virtualModel.model.custom.imageUrl"] = str(person)
            else:
                files["virtualModel.model.custom.imageFile"] = self._file_part(
                    person, "person"
                )
        else:
            data["virtualModel.model.preset.name"] = preset_model

        if scene_image is not None:
            if self._is_url(scene_image):
                data["virtualModel.scene.custom.imageUrl"] = str(scene_image)
            else:
                files["virtualModel.scene.custom.imageFile"] = self._file_part(
                    scene_image, "scene"
                )
        else:
            data["virtualModel.scene.preset.name"] = scene

        if prompt:
            data["virtualModel.prompt"] = prompt

        for index, extra in enumerate(additional_product_images or []):
            if extra is None:
                continue
            if self._is_url(extra):
                data[f"virtualModel.additionalProductImages[{index}].imageUrl"] = str(
                    extra
                )
            else:
                files[f"virtualModel.additionalProductImages[{index}].imageFile"] = (
                    self._file_part(extra, f"extra-{index}")
                )

        resp = requests.post(
            url,
            headers=self._headers(),
            data=data,
            files=files or None,
            timeout=self.timeout,
        )
        if resp.status_code >= 400:
            raise ValueError(
                f"Photoroom Virtual Model/Try-On failed ({resp.status_code}): "
                f"{resp.text[:2000]}"
            )
        content_type = (resp.headers.get("Content-Type") or "").lower()
        if "image/" not in content_type and not resp.content.startswith(
            (b"\x89PNG", b"\xff\xd8")
        ):
            raise ValueError(
                f"Photoroom did not return an image: {resp.text[:2000]}"
            )
        return PILImage.open(io.BytesIO(resp.content))

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
        mode: str = "try-on",
        preset_model: str = "avery",
        scene: str = "random",
        pose: str = "standing",
        size: str = "PORTRAIT_HD_3_2",
        prompt: Optional[str] = None,
        scene_image: Optional[ImageInput] = None,
        additional_product_images: Optional[Sequence[ImageInput]] = None,
        remove_background: bool = False,
        reference_box: str = "originalImage",
        **kwargs,
    ) -> List[PILImage.Image]:
        """Generate a Photoroom try-on or virtual-model still.

        Args:
            person / garment: Shopper and product images (path, URL, PIL, bytes).
            mode: ``try-on`` (person required) or ``virtual-model`` (garment
                required; person is an optional custom model).
            preset_model: Photoroom preset when no custom person is passed.
            scene / pose / size: Official Virtual Model enums.
            prompt: Optional style hint (e.g. ``street style``).
            scene_image: Optional custom scene photo.
            additional_product_images: Extra angles of the same SKU.
            remove_background: Official default is false so the generated
                scene is kept (pair with ``referenceBox=originalImage``).
        """
        resolved_person = person or source_image or person_image or model_image
        resolved_garment = garment or reference_image or garment_image or cloth_image
        kind = (mode or "try-on").strip().lower()
        if kind not in MODES:
            raise ValueError(f"mode must be one of {list(MODES)}")
        preset = (preset_model or "avery").strip().lower()
        if preset not in PRESET_MODELS:
            raise ValueError(f"preset_model must be one of {list(PRESET_MODELS)}")
        scene_name = (scene or "random").strip().lower()
        if scene_name not in PRESET_SCENES:
            raise ValueError(f"scene must be one of {list(PRESET_SCENES)}")
        pose_name = (pose or "standing").strip().lower()
        if pose_name not in PRESET_POSES:
            raise ValueError(f"pose must be one of {list(PRESET_POSES)}")
        size_name = (size or "PORTRAIT_HD_3_2").strip().upper()
        if size_name not in OUTPUT_SIZES:
            raise ValueError(f"size must be one of {list(OUTPUT_SIZES)}")

        extras = additional_product_images or kwargs.get("additional_images")
        if isinstance(extras, (str, Path, bytes, bytearray, PILImage.Image)):
            extras = [extras]

        if kind == "try-on":
            if resolved_person is None:
                raise ValueError(
                    "Person image is required for Photoroom Virtual Try-On. "
                    "Pass person / person_image / model_image."
                )
            if resolved_garment is None:
                raise ValueError(
                    "Garment/product image is required. Pass garment, "
                    "garment_image, or cloth_image."
                )
            product, custom = resolved_garment, resolved_person
        else:
            # Catalog job: product is the garment. A lone person attachment
            # (planner maps a single photo to person) is treated as the SKU.
            product = resolved_garment or resolved_person
            if product is None:
                raise ValueError(
                    "Garment/product image is required for Photoroom Virtual "
                    "Model. Pass garment or garment_image."
                )
            custom = resolved_person if resolved_garment is not None else None

        image = self._edit(
            product=product,
            person=custom,
            preset_model=preset,
            scene=scene_name,
            pose=pose_name,
            size=size_name,
            prompt=prompt,
            scene_image=scene_image,
            additional_product_images=extras,
            remove_background=bool(remove_background),
            reference_box=reference_box or "originalImage",
        )
        return [image]

    def generate_virtual_model(
        self,
        garment: Optional[ImageInput] = None,
        *,
        person: Optional[ImageInput] = None,
        **kwargs,
    ) -> List[PILImage.Image]:
        """Flat-lay / product photo → on-model catalog shot."""
        return self.generate_and_decode(
            person=person,
            garment=garment,
            mode="virtual-model",
            **kwargs,
        )
