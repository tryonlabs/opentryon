"""
Recraft V3 — first-party image API.

Raster generate, image-to-image, and background removal on
``https://external.api.recraft.ai/v1``. Auth is ``RECRAFT_API_TOKEN``.

Reference:
https://www.recraft.ai/docs/api-reference/models/recraft-v3
https://www.recraft.ai/docs/api-reference/tools/image-to-image
https://www.recraft.ai/docs/api-reference/tools/remove-background

Env:
  RECRAFT_API_TOKEN (required; RECRAFT_API_KEY is an alias)
  RECRAFT_BASE_URL — default https://external.api.recraft.ai/v1

Examples:
    >>> from tryon.api.recraft import RecraftAdapter
    >>> adapter = RecraftAdapter()
    >>> images = adapter.generate_text_to_image(prompt="linen trench on a terrace")
    >>> images[0].save("look.png")
"""

from __future__ import annotations

import base64
import io
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import requests
from PIL import Image

ImageInput = Union[str, Path, io.BytesIO, bytes, Image.Image]

DEFAULT_BASE_URL = "https://external.api.recraft.ai/v1"
DEFAULT_MODEL = "recraftv3"
VALID_MODELS = {"recraftv3"}
VALID_STYLES = {
    "Photorealism",
    "Illustration",
    "Vector art",
    "Recraft V3 Raw",
}
VALID_SIZES = {
    "1:1",
    "16:9",
    "9:16",
    "4:3",
    "3:4",
    "3:2",
    "2:3",
    "4:5",
    "5:4",
    "1024x1024",
    "1365x1024",
    "1024x1365",
    "1536x1024",
    "1024x1536",
    "1820x1024",
    "1024x1820",
    "1024x1280",
    "1280x1024",
    "1024x1707",
    "1707x1024",
}
VALID_IMAGE_FORMATS = {"png", "webp"}


class RecraftAdapter:
    """Recraft V3 generate / edit / background-remove."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.api_key = (
            api_key
            or os.getenv("RECRAFT_API_TOKEN")
            or os.getenv("RECRAFT_API_KEY")
        )
        if not self.api_key:
            raise ValueError(
                "Recraft API token must be provided either as a parameter or "
                "through the RECRAFT_API_TOKEN environment variable."
            )
        self.base_url = (
            base_url or os.getenv("RECRAFT_BASE_URL") or DEFAULT_BASE_URL
        ).rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def generate_text_to_image(
        self,
        prompt: str,
        style: str = "Recraft V3 Raw",
        size: Optional[str] = None,
        n: int = 1,
        negative_prompt: Optional[str] = None,
        image_format: str = "png",
        model: str = DEFAULT_MODEL,
    ) -> List[Image.Image]:
        if not (prompt or "").strip():
            raise ValueError("prompt is required.")
        upstream = self._model(model)
        payload: Dict[str, Any] = {
            "prompt": prompt.strip(),
            "model": upstream,
            "style": self._style(style),
            "n": self._n(n),
            "response_format": "b64_json",
            "image_format": self._image_format(image_format),
        }
        if size:
            payload["size"] = self._size(size)
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt
        data = self._post("/images/generations", payload)
        return self._images_from_data(data, keep_alpha=False)

    def generate_image_edit(
        self,
        image: ImageInput,
        prompt: str,
        strength: float = 0.2,
        style: str = "Recraft V3 Raw",
        n: int = 1,
        negative_prompt: Optional[str] = None,
        seed: Optional[int] = None,
        image_format: str = "png",
        model: str = DEFAULT_MODEL,
    ) -> List[Image.Image]:
        if image is None:
            raise ValueError("image is required.")
        if not (prompt or "").strip():
            raise ValueError("prompt is required for edit.")
        try:
            strength_f = float(strength)
        except (TypeError, ValueError) as exc:
            raise ValueError("strength must be a number between 0 and 1.") from exc
        if not 0.0 <= strength_f <= 1.0:
            raise ValueError("strength must be between 0 and 1.")
        payload: Dict[str, Any] = {
            "image_url": self._image_url(image),
            "prompt": prompt.strip(),
            "strength": strength_f,
            "model": self._model(model),
            "style": self._style(style),
            "n": self._n(n),
            "response_format": "b64_json",
            "image_format": self._image_format(image_format),
        }
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt
        if seed is not None:
            payload["random_seed"] = int(seed)
        data = self._post("/images/imageToImage", payload)
        return self._images_from_data(data, keep_alpha=False)

    def remove_background(
        self,
        image: ImageInput,
        image_format: str = "png",
    ) -> List[Image.Image]:
        if image is None:
            raise ValueError("image is required.")
        payload: Dict[str, Any] = {
            "image_url": self._image_url(image),
            "response_format": "b64_json",
            "image_format": self._image_format(image_format),
        }
        data = self._post("/images/removeBackground", payload)
        return self._images_from_data(data, keep_alpha=True)

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        resp = requests.post(
            f"{self.base_url}{path}",
            headers=self.headers,
            json=payload,
            timeout=180,
        )
        if resp.status_code >= 400:
            raise RuntimeError(f"Recraft failed ({resp.status_code}): {resp.text}")
        try:
            return resp.json()
        except ValueError as exc:
            raise RuntimeError(f"Recraft returned non-JSON: {resp.text[:400]}") from exc

    @staticmethod
    def _model(model: str) -> str:
        value = (model or DEFAULT_MODEL).strip()
        if value not in VALID_MODELS:
            raise ValueError(
                f"Invalid Recraft model: {model!r}. Supported: {sorted(VALID_MODELS)}"
            )
        return value

    @staticmethod
    def _style(style: str) -> str:
        value = (style or "Recraft V3 Raw").strip()
        if value not in VALID_STYLES:
            raise ValueError(
                f"Invalid style: {style!r}. Supported: {sorted(VALID_STYLES)}"
            )
        return value

    @staticmethod
    def _size(size: str) -> str:
        value = size.strip()
        if value not in VALID_SIZES:
            raise ValueError(
                f"Invalid size: {size!r}. Supported: {sorted(VALID_SIZES)}"
            )
        return value

    @staticmethod
    def _n(n: int) -> int:
        count = int(n)
        if not 1 <= count <= 6:
            raise ValueError("n must be between 1 and 6.")
        return count

    @staticmethod
    def _image_format(image_format: str) -> str:
        value = (image_format or "png").strip().lower()
        if value not in VALID_IMAGE_FORMATS:
            raise ValueError(
                f"image_format must be one of {sorted(VALID_IMAGE_FORMATS)}"
            )
        return value

    @staticmethod
    def _load_bytes(source: ImageInput, default_ext: str = "png") -> tuple[bytes, str]:
        if isinstance(source, Image.Image):
            buf = io.BytesIO()
            source.save(buf, format="PNG")
            return buf.getvalue(), "png"
        if isinstance(source, (bytes, bytearray)):
            return bytes(source), default_ext
        if isinstance(source, io.BytesIO):
            source.seek(0)
            return source.read(), default_ext
        source_str = str(source)
        if source_str.startswith("data:"):
            header, _, b64 = source_str.partition(",")
            ext = "png"
            if "image/" in header:
                ext = header.split("image/", 1)[1].split(";", 1)[0] or "png"
            return base64.b64decode(b64), ext
        if source_str.startswith("http://") or source_str.startswith("https://"):
            resp = requests.get(source_str, timeout=60)
            resp.raise_for_status()
            ext = Path(source_str.split("?", 1)[0]).suffix.lstrip(".").lower() or default_ext
            return resp.content, ext
        path = Path(source_str)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {source_str}")
        ext = path.suffix.lstrip(".").lower() or default_ext
        with open(path, "rb") as handle:
            return handle.read(), ext

    def _image_url(self, image: ImageInput) -> str:
        source_str = str(image) if isinstance(image, (str, Path)) else ""
        if source_str.startswith("http://") or source_str.startswith("https://"):
            return source_str
        if source_str.startswith("data:"):
            return source_str
        data, ext = self._load_bytes(image)
        mime = "jpeg" if ext in {"jpg", "jpeg"} else ext or "png"
        return f"data:image/{mime};base64,{base64.b64encode(data).decode('utf-8')}"

    @staticmethod
    def _decode_b64(raw: str) -> Image.Image:
        return Image.open(io.BytesIO(base64.b64decode(raw)))

    def _images_from_data(self, data: Dict[str, Any], *, keep_alpha: bool) -> List[Image.Image]:
        items = data.get("data")
        if items is None and isinstance(data.get("image"), dict):
            items = [data["image"]]
        if not items:
            raise RuntimeError(f"Recraft returned no images: {data}")
        images: List[Image.Image] = []
        for item in items:
            if not isinstance(item, dict):
                raise RuntimeError(f"Recraft item missing image payload: {item}")
            b64 = item.get("b64_json") or item.get("b64")
            if b64:
                img = self._decode_b64(b64)
            else:
                url = item.get("url") or item.get("image_url")
                if not url:
                    raise RuntimeError(f"Recraft item missing url/b64: {item}")
                resp = requests.get(url, timeout=60)
                resp.raise_for_status()
                img = Image.open(io.BytesIO(resp.content))
            images.append(img.convert("RGBA" if keep_alpha else "RGB"))
        return images
