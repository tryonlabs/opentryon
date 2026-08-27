"""
Meta Muse Image adapter (first-party Model API).

Generates and edits images via Meta Model API (`muse-image-1.0`). One model
covers text-to-image, image-to-image, and multi-reference composition.
Muse Video is **not** on this surface yet (consumer preview only).

Docs:
  https://ai.developer.meta.com/docs/image-generation
  https://ai.meta.com/blog/introducing-muse-image-muse-video-msl/
  https://dev.meta.ai/docs/api-reference/images/create-image
  https://dev.meta.ai/docs/api-reference/images/edit-image

Env:
  MODEL_API_KEY          (official Meta name)
  META_MODEL_API_KEY     (OpenTryOn alias)
  MUSE_API_KEY           (alias)
  META_MODEL_API_BASE_URL (default https://api.meta.ai/v1)

Examples:
    >>> from tryon.api.muse import MuseImageAdapter
    >>> adapter = MuseImageAdapter()
    >>> images = adapter.generate_text_to_image(
    ...     prompt="A fashion model walking a runway at dusk, editorial lighting",
    ...     size="1024x1536",
    ... )
    >>> images[0].save("muse.png")
"""

from __future__ import annotations

import base64
import io
import os
from typing import Any, Dict, List, Optional, Sequence, Union

import requests
from PIL import Image

DEFAULT_BASE_URL = "https://api.meta.ai/v1"
DEFAULT_MODEL = "muse-image-1.0"
OUTPUT_FORMATS = ("webp", "png", "jpeg")
REASONING = ("high", "low")

ImageLike = Union[str, io.BytesIO, Image.Image, bytes]

DEFAULT_TRYON_PROMPT = (
    "The person in the first image, keeping their face, pose and background "
    "unchanged, wearing the garment shown in the second image."
)


class MuseImageAdapter:
    """Official Meta Muse Image adapter (T2I / I2I / multi-ref / composition VTON)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        timeout: float = 600.0,
    ):
        self.api_key = (
            api_key
            or os.getenv("MODEL_API_KEY")
            or os.getenv("META_MODEL_API_KEY")
            or os.getenv("MUSE_API_KEY")
        )
        if not self.api_key:
            raise ValueError(
                "Meta Model API key is required. Set MODEL_API_KEY "
                "(https://dev.meta.ai/docs/authentication) or META_MODEL_API_KEY."
            )
        self.base_url = (
            base_url
            or os.getenv("META_MODEL_API_BASE_URL")
            or DEFAULT_BASE_URL
        ).rstrip("/")
        self.model = (model or DEFAULT_MODEL).strip() or DEFAULT_MODEL
        self.timeout = float(timeout)

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def _raise_http(resp: requests.Response, context: str) -> None:
        if resp.status_code < 400:
            return
        try:
            data = resp.json()
        except Exception:
            raise RuntimeError(
                f"Muse Image {context} failed ({resp.status_code}): {resp.text}"
            ) from None
        err = data.get("error") if isinstance(data, dict) else None
        if isinstance(err, dict):
            msg = err.get("message") or err
        else:
            msg = data
        raise RuntimeError(f"Muse Image {context} failed ({resp.status_code}): {msg}")

    def _prepare_image_uri(self, image: ImageLike) -> str:
        if isinstance(image, str):
            if image.startswith(("http://", "https://", "data:")):
                return image
            if os.path.exists(image):
                with open(image, "rb") as f:
                    raw = f.read()
                b64 = base64.b64encode(raw).decode("ascii")
                ext = os.path.splitext(image)[1].lower()
                mime = {
                    ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg",
                    ".png": "image/png",
                    ".webp": "image/webp",
                }.get(ext, "image/png")
                return f"data:{mime};base64,{b64}"
            raise ValueError(f"Image path does not exist: {image}")
        if isinstance(image, Image.Image):
            buf = io.BytesIO()
            image.convert("RGB").save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode("ascii")
            return f"data:image/png;base64,{b64}"
        if isinstance(image, (bytes, bytearray)):
            b64 = base64.b64encode(bytes(image)).decode("ascii")
            return f"data:image/png;base64,{b64}"
        if hasattr(image, "read"):
            image.seek(0)
            b64 = base64.b64encode(image.read()).decode("ascii")
            return f"data:image/png;base64,{b64}"
        raise ValueError("Unsupported image input for Muse Image.")

    @staticmethod
    def _as_list(value: Union[ImageLike, Sequence[ImageLike]]) -> List[ImageLike]:
        if isinstance(value, (bytes, bytearray, str)):
            return [value]
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            return list(value)
        return [value]

    def _tool_enablement(
        self,
        enable_image_search: bool,
        enable_web_search: bool,
        enable_shell: bool,
    ) -> Optional[Dict[str, bool]]:
        if enable_image_search and enable_web_search and enable_shell:
            return None
        return {
            "enable_image_search": bool(enable_image_search),
            "enable_web_search": bool(enable_web_search),
            "enable_shell": bool(enable_shell),
        }

    def _decode(self, data: Dict[str, Any]) -> List[Image.Image]:
        items = data.get("data") or []
        if not items:
            raise RuntimeError(f"Muse Image response missing data: {data}")
        out: List[Image.Image] = []
        for item in items:
            b64 = item.get("b64_json")
            url = item.get("url")
            raw: Optional[bytes] = None
            if b64:
                raw = base64.b64decode(b64)
            elif url:
                resp = requests.get(url, timeout=120)
                if resp.status_code != 200:
                    raise RuntimeError(
                        f"Failed to download Muse Image URL ({resp.status_code})"
                    )
                raw = resp.content
            if not raw:
                raise RuntimeError(f"Muse Image item has neither b64_json nor url: {item}")
            out.append(Image.open(io.BytesIO(raw)).convert("RGB"))
        return out

    def _post(self, path: str, payload: Dict[str, Any], context: str) -> List[Image.Image]:
        url = f"{self.base_url}{path}"
        resp = requests.post(
            url, headers=self._headers(), json=payload, timeout=self.timeout
        )
        self._raise_http(resp, context)
        return self._decode(resp.json())

    def _common_payload(
        self,
        prompt: str,
        *,
        n: int,
        size: Optional[str],
        output_format: str,
        reasoning_strength: str,
        enable_image_search: bool,
        enable_web_search: bool,
        enable_shell: bool,
    ) -> Dict[str, Any]:
        text = (prompt or "").strip()
        if not text:
            raise ValueError("prompt is required.")
        n_i = int(n)
        if n_i < 1 or n_i > 10:
            raise ValueError("n must be between 1 and 10.")
        fmt = (output_format or "webp").lower()
        if fmt not in OUTPUT_FORMATS:
            raise ValueError(f"output_format must be one of {OUTPUT_FORMATS} (got {fmt!r}).")
        strength = (reasoning_strength or "high").lower()
        if strength not in REASONING:
            raise ValueError(f"reasoning_strength must be one of {REASONING} (got {strength!r}).")

        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": text,
            "n": n_i,
            "output_format": fmt,
            "response_format": "b64_json",
            "reasoning_strength": strength,
        }
        if size:
            payload["size"] = size
        tools = self._tool_enablement(
            enable_image_search, enable_web_search, enable_shell
        )
        if tools is not None:
            payload["tool_enablement"] = tools
        return payload

    def generate_text_to_image(
        self,
        prompt: str,
        n: int = 1,
        size: Optional[str] = None,
        output_format: str = "webp",
        reasoning_strength: str = "high",
        enable_image_search: bool = True,
        enable_web_search: bool = True,
        enable_shell: bool = True,
    ) -> List[Image.Image]:
        payload = self._common_payload(
            prompt,
            n=n,
            size=size,
            output_format=output_format,
            reasoning_strength=reasoning_strength,
            enable_image_search=enable_image_search,
            enable_web_search=enable_web_search,
            enable_shell=enable_shell,
        )
        return self._post("/images/generations", payload, "generate")

    def generate_image_edit(
        self,
        image: Union[ImageLike, Sequence[ImageLike]],
        prompt: str,
        n: int = 1,
        size: Optional[str] = None,
        output_format: str = "webp",
        reasoning_strength: str = "high",
        enable_image_search: bool = True,
        enable_web_search: bool = True,
        enable_shell: bool = True,
    ) -> List[Image.Image]:
        images = self._as_list(image)
        if not images:
            raise ValueError("At least one input image is required.")
        payload = self._common_payload(
            prompt,
            n=n,
            size=size,
            output_format=output_format,
            reasoning_strength=reasoning_strength,
            enable_image_search=enable_image_search,
            enable_web_search=enable_web_search,
            enable_shell=enable_shell,
        )
        payload["images"] = [{"image_url": self._prepare_image_uri(item)} for item in images]
        return self._post("/images/edits", payload, "edit")

    def generate_multi_image(
        self,
        images: Sequence[ImageLike],
        prompt: str,
        **kwargs: Any,
    ) -> List[Image.Image]:
        return self.generate_image_edit(image=images, prompt=prompt, **kwargs)

    def build_tryon_prompt(
        self,
        prompt: Optional[str] = None,
        garment_description: Optional[str] = None,
    ) -> str:
        if prompt and prompt.strip():
            return prompt.strip()
        if garment_description and garment_description.strip():
            return (
                "The person in the first image, keeping their face, pose and background "
                f"unchanged, wearing {garment_description.strip()}."
            )
        return DEFAULT_TRYON_PROMPT

    def generate_virtual_tryon(
        self,
        person: Optional[ImageLike],
        garment: Optional[ImageLike],
        prompt: Optional[str] = None,
        garment_description: Optional[str] = None,
        **kwargs: Any,
    ) -> List[Image.Image]:
        """Composition try-on via multi-image edit — not a dedicated garment-fit model."""
        if person is None:
            raise ValueError("Person image is required.")
        if garment is None:
            raise ValueError("Garment image is required.")
        styling = self.build_tryon_prompt(
            prompt=prompt, garment_description=garment_description
        )
        return self.generate_image_edit(
            image=[person, garment], prompt=styling, **kwargs
        )
