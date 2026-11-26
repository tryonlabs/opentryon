"""
MiniMax H3-Image API adapter (first-party).

Text-to-image and reference-image editing via MiniMax Open Platform:
  POST {base}/v1/images/generations
  POST {base}/v1/images/edits

Docs:
  https://platform.minimax.io/docs/api-reference/image-generation-h3-generations
  https://platform.minimax.io/docs/api-reference/image-generation-h3-edits

Env:
  MINIMAX_API_KEY
  MINIMAX_API_BASE_URL (default https://api.minimax.io)

The server may block up to 600s; requests are not idempotent (disable HTTP retries).
"""

from __future__ import annotations

import base64
import io
import os
import warnings
from typing import Any, Dict, List, Optional, Union

import requests
from PIL import Image

DEFAULT_BASE_URL = "https://api.minimax.io"
REQUEST_TIMEOUT = 600

MODEL_ALIASES = {
    "h3-image": "MiniMax-H3-Image",
    "h3-image-highspeed": "MiniMax-H3-Image-Highspeed",
    "minimax-h3-image": "MiniMax-H3-Image",
    "MiniMax-H3-Image": "MiniMax-H3-Image",
    "MiniMax-H3-Image-Highspeed": "MiniMax-H3-Image-Highspeed",
}


class MiniMaxH3ImageAdapter:
    """Official MiniMax H3-Image adapter (T2I + 1–16 reference edits)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "h3-image",
    ):
        self.api_key = api_key or os.getenv("MINIMAX_API_KEY")
        if not self.api_key:
            raise ValueError(
                "MiniMax API key is required. Set MINIMAX_API_KEY or pass api_key=."
            )
        self.base_url = (
            base_url or os.getenv("MINIMAX_API_BASE_URL") or DEFAULT_BASE_URL
        ).rstrip("/")
        self.model = self._resolve_model(model)
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def _resolve_model(model: str) -> str:
        key = (model or "").strip()
        return MODEL_ALIASES.get(key, key)

    def _prepare_image_url(self, image: Union[str, io.BytesIO, Image.Image, bytes]) -> str:
        if isinstance(image, str):
            if image.startswith(("http://", "https://", "data:", "mm_file://")):
                return image
            if os.path.exists(image):
                with open(image, "rb") as f:
                    raw = f.read()
                return f"data:image/png;base64,{base64.b64encode(raw).decode('ascii')}"
            raise ValueError(f"Image path does not exist: {image}")
        if isinstance(image, Image.Image):
            buf = io.BytesIO()
            image.save(buf, format="PNG")
            raw = buf.getvalue()
        elif isinstance(image, (bytes, bytearray)):
            raw = bytes(image)
        elif hasattr(image, "read"):
            image.seek(0)
            raw = image.read()
        else:
            raise ValueError("Unsupported image input type for MiniMax H3-Image.")
        return f"data:image/png;base64,{base64.b64encode(raw).decode('ascii')}"

    def _parse_images(self, data: Dict[str, Any]) -> List[Image.Image]:
        items = data.get("data") or []
        if not items:
            raise RuntimeError(f"MiniMax H3-Image returned no images: {data}")

        images: List[Image.Image] = []
        errors: List[str] = []
        for index, item in enumerate(items):
            err = item.get("error")
            if err:
                msg = err.get("message") if isinstance(err, dict) else str(err)
                msg = msg or "unknown error"
                errors.append(msg)
                warnings.warn(
                    f"MiniMax H3-Image output {index + 1}: {msg}",
                    stacklevel=3,
                )
                continue
            if item.get("b64_json"):
                raw = base64.b64decode(item["b64_json"], validate=True)
                images.append(Image.open(io.BytesIO(raw)).convert("RGB"))
            elif item.get("url"):
                r = requests.get(item["url"], timeout=120)
                r.raise_for_status()
                images.append(Image.open(io.BytesIO(r.content)).convert("RGB"))
            else:
                errors.append(f"missing url/b64_json: {item}")

        if not images:
            detail = "; ".join(errors) if errors else "empty data"
            raise RuntimeError(f"MiniMax H3-Image: all outputs failed ({detail})")
        return images

    def _post(self, path: str, payload: Dict[str, Any]) -> List[Image.Image]:
        url = f"{self.base_url}{path}"
        # Non-idempotent billing; redirects must not trigger a second POST.
        resp = requests.post(
            url,
            headers=self.headers,
            json=payload,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=False,
        )
        if resp.status_code != 200:
            try:
                err_body = resp.json()
                err = err_body.get("error", {}) if isinstance(err_body, dict) else {}
            except ValueError:
                err = {}
            message = err.get("message") if isinstance(err, dict) else None
            message = message or resp.reason or resp.text
            raise RuntimeError(
                f"MiniMax H3-Image request failed ({resp.status_code}): {message}"
            )
        return self._parse_images(resp.json())

    def generate_text_to_image(
        self,
        prompt: str,
        size: str = "auto",
        aspect_ratio: Optional[str] = "auto",
        area: str = "4K",
        n: int = 1,
        response_format: str = "url",
        disable_prompt_enhanced: bool = False,
        model: Optional[str] = None,
        **kwargs: Any,
    ) -> List[Image.Image]:
        prompt = (prompt or "").strip()
        if not 1 <= len(prompt) <= 32000:
            raise ValueError("prompt must contain 1 to 32000 characters.")
        n_val = int(n)
        if not 1 <= n_val <= 10:
            raise ValueError("n must be between 1 and 10.")
        if response_format not in ("url", "b64_json"):
            raise ValueError("response_format must be url or b64_json.")
        payload: Dict[str, Any] = {
            "model": self._resolve_model(model) if model else self.model,
            "prompt": prompt,
            "size": size,
            "n": n_val,
            "response_format": response_format,
            "disable_prompt_enhanced": bool(disable_prompt_enhanced),
        }
        if aspect_ratio is not None and str(aspect_ratio).strip():
            payload["aspect_ratio"] = aspect_ratio
        if area:
            payload["area"] = area
        payload.update({k: v for k, v in kwargs.items() if v is not None})
        return self._post("/v1/images/generations", payload)

    def generate_image_edit(
        self,
        prompt: str,
        image: Union[str, io.BytesIO, Image.Image, bytes, List[Any]],
        size: str = "auto",
        aspect_ratio: Optional[str] = None,
        area: Optional[str] = None,
        n: int = 1,
        response_format: str = "url",
        model: Optional[str] = None,
        **kwargs: Any,
    ) -> List[Image.Image]:
        prompt = (prompt or "").strip()
        if not 1 <= len(prompt) <= 32000:
            raise ValueError("prompt must contain 1 to 32000 characters.")
        n_val = int(n)
        if not 1 <= n_val <= 10:
            raise ValueError("n must be between 1 and 10.")
        if isinstance(image, list):
            if not image:
                raise ValueError("At least one reference image is required.")
            if len(image) > 16:
                raise ValueError("MiniMax H3-Image edits support at most 16 reference images.")
            images_field = [{"image_url": self._prepare_image_url(img)} for img in image]
        else:
            images_field = [{"image_url": self._prepare_image_url(image)}]

        payload: Dict[str, Any] = {
            "model": self._resolve_model(model) if model else self.model,
            "prompt": prompt,
            "images": images_field,
            "size": size,
            "n": n_val,
            "response_format": response_format,
        }
        if aspect_ratio is not None:
            payload["aspect_ratio"] = aspect_ratio
        if area is not None:
            payload["area"] = area
        payload.update({k: v for k, v in kwargs.items() if v is not None})
        return self._post("/v1/images/edits", payload)