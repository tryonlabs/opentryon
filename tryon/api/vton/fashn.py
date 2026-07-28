"""
FASHN AI Virtual Try-On API Adapter

Adapter for FASHN's fashion-focused virtual try-on endpoints:

- ``tryon-max`` -- recommended high-fidelity try-on (up to 4K, prompt-based
  customization; clothing, shoes, hats, jewelry, bags, etc.)
- ``tryon-v1.6`` -- fast, lightweight try-on optimized for real-time
  e-commerce (fixed ~864x1296 processing, 1 credit/image)

Both share FASHN's universal ``POST /v1/run`` + ``GET /v1/status/{id}``
pattern. This adapter uses ``requests`` directly (same as Segmind/Pruna)
rather than requiring the optional ``fashn`` Python SDK.

Reference:
    https://docs.fashn.ai/
    https://docs.fashn.ai/api-reference/tryon-max
    https://docs.fashn.ai/api-reference/tryon-v1-6
    https://docs.fashn.ai/sdk/python

Authentication:
    Requires a FASHN API key via constructor or ``FASHN_API_KEY`` environment
    variable. Sent as ``Authorization: Bearer <key>``.

Example:
    >>> adapter = FashnVTONAdapter()
    >>> images = adapter.generate_and_decode(
    ...     model_image="person.jpg",
    ...     product_image="jacket.jpg",
    ...     model_name="tryon-max",
    ... )
    >>> images[0].save("result.png")
"""

from __future__ import annotations

import base64
import io
import mimetypes
import os
import time
from typing import Any, Dict, List, Optional, Union

import requests
from PIL import Image


class FashnVTONAdapter:
    """
    Adapter for FASHN AI virtual try-on (``tryon-max`` and ``tryon-v1.6``).

    Lives under ``tryon.api.vton`` (use-case directory) rather than a dedicated
    ``tryon.api.fashn`` package -- single-file, VTON-primary adapter.
    """

    BASE_URL = "https://api.fashn.ai"
    VALID_MODELS = {"tryon-max", "tryon-v1.6"}
    TERMINAL_STATUSES = {"completed", "failed", "canceled", "cancelled", "time_out"}

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize the FASHN VTON client.

        Args:
            api_key: FASHN API key. Defaults to ``FASHN_API_KEY``.
            base_url: API base URL. Defaults to ``FASHN_BASE_URL`` or
                      ``https://api.fashn.ai``.
        """
        self.api_key = api_key or os.getenv("FASHN_API_KEY")
        if not self.api_key:
            raise ValueError(
                "FASHN API key is required. Set FASHN_API_KEY environment variable "
                "or pass api_key parameter. Get a key at https://app.fashn.ai/api"
            )

        self.base_url = (base_url or os.getenv("FASHN_BASE_URL") or self.BASE_URL).rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        self.last_prediction_id: Optional[str] = None
        self.last_credits_used: Optional[str] = None

    def _guess_mime(self, path_or_name: str) -> str:
        mime, _ = mimetypes.guess_type(path_or_name)
        if mime and mime.startswith("image/"):
            return mime
        return "image/png"

    def _bytes_to_data_uri(self, data: bytes, mime: str = "image/png") -> str:
        encoded = base64.b64encode(data).decode("utf-8")
        return f"data:{mime};base64,{encoded}"

    def _prepare_image_input(self, image_input: Union[str, io.BytesIO, Image.Image, bytes]) -> str:
        """
        Resolve image input to a URL or ``data:`` URI FASHN accepts.

        URLs are passed through. Local files / PIL / bytes become data URIs
        with the required ``data:image/...;base64,`` prefix.
        """
        if isinstance(image_input, Image.Image):
            buffer = io.BytesIO()
            fmt = "PNG" if image_input.mode in ("RGBA", "LA", "P") else "JPEG"
            image_input.save(buffer, format=fmt)
            mime = "image/png" if fmt == "PNG" else "image/jpeg"
            return self._bytes_to_data_uri(buffer.getvalue(), mime=mime)

        if isinstance(image_input, (bytes, bytearray)):
            return self._bytes_to_data_uri(bytes(image_input))

        if hasattr(image_input, "read"):
            image_input.seek(0)
            return self._bytes_to_data_uri(image_input.read())

        if isinstance(image_input, str):
            if image_input.startswith(("http://", "https://", "data:")):
                return image_input

            if os.path.exists(image_input):
                with open(image_input, "rb") as f:
                    return self._bytes_to_data_uri(f.read(), mime=self._guess_mime(image_input))

            if len(image_input) > 100:
                try:
                    raw = base64.b64decode(image_input, validate=True)
                    return self._bytes_to_data_uri(raw)
                except Exception:
                    pass

            raise ValueError(f"Image path does not exist: {image_input}")

        raise ValueError(
            "Invalid image input: must be a file path, URL, data URI, PIL Image, "
            "bytes, file-like object, or base64 string"
        )

    def _poll_status(self, prediction_id: str, max_wait_time: int = 180, poll_interval: float = 1.5) -> Dict[str, Any]:
        """Poll ``GET /v1/status/{id}`` until a terminal status is reached."""
        start = time.time()
        url = f"{self.base_url}/v1/status/{prediction_id}"
        while True:
            if time.time() - start > max_wait_time:
                raise ValueError(f"FASHN prediction timed out after {max_wait_time} seconds.")

            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            status = data.get("status")
            self.last_credits_used = response.headers.get("x-fashn-credits-used")

            if status == "completed":
                return data
            if status in ("failed", "canceled", "cancelled", "time_out"):
                err = data.get("error") or {}
                if isinstance(err, dict):
                    message = err.get("message") or err.get("name") or str(err)
                else:
                    message = str(err)
                raise ValueError(f"FASHN prediction {status}: {message}")

            time.sleep(poll_interval)

    def generate(
        self,
        model_image: Optional[Union[str, io.BytesIO, Image.Image]] = None,
        product_image: Optional[Union[str, io.BytesIO, Image.Image]] = None,
        *,
        person: Optional[Union[str, io.BytesIO, Image.Image]] = None,
        garment: Optional[Union[str, io.BytesIO, Image.Image]] = None,
        garment_image: Optional[Union[str, io.BytesIO, Image.Image]] = None,
        source_image: Optional[Union[str, io.BytesIO, Image.Image]] = None,
        model_name: str = "tryon-max",
        prompt: Optional[str] = None,
        resolution: Optional[str] = None,
        generation_mode: Optional[str] = None,
        seed: Optional[int] = None,
        num_images: Optional[int] = None,
        output_format: str = "png",
        return_base64: bool = False,
        # tryon-v1.6-specific
        category: Optional[str] = None,
        segmentation_free: Optional[bool] = None,
        moderation_level: Optional[str] = None,
        garment_photo_type: Optional[str] = None,
        mode: Optional[str] = None,
        num_samples: Optional[int] = None,
        max_wait_time: int = 180,
        **kwargs,
    ) -> List[str]:
        """
        Run a FASHN virtual try-on and return output URL(s) or base64 data URIs.

        Args:
            model_image / person / source_image: Person/model photo.
            product_image / garment / garment_image: Garment/product photo.
                Mapped to ``product_image`` for ``tryon-max`` and
                ``garment_image`` for ``tryon-v1.6``.
            model_name: ``tryon-max`` (default) or ``tryon-v1.6``.
            prompt: Optional styling instruction (``tryon-max`` only), e.g.
                ``"roll up sleeves"``, ``"tuck in shirt"``.
            resolution: ``1k`` / ``2k`` / ``4k`` (``tryon-max`` only).
            generation_mode: ``fast`` / ``balanced`` / ``quality`` (``tryon-max``).
            seed: Optional seed.
            num_images: 1-4 outputs (``tryon-max``).
            output_format: ``png`` or ``jpeg``.
            return_base64: Return base64 data URIs instead of CDN URLs.
            category / segmentation_free / moderation_level /
            garment_photo_type / mode / num_samples: ``tryon-v1.6`` options.
            max_wait_time: Polling timeout in seconds.
            **kwargs: Extra fields forwarded into ``inputs``.

        Returns:
            List of output URLs (or data URIs when ``return_base64=True``).
        """
        if model_name not in self.VALID_MODELS:
            raise ValueError(
                f"Invalid model_name '{model_name}'. Must be one of: {sorted(self.VALID_MODELS)}"
            )

        resolved_person = model_image or person or source_image
        resolved_garment = product_image or garment or garment_image

        if resolved_person is None:
            raise ValueError(
                "Person/model image is required. Pass model_image (or person/source_image)."
            )
        if resolved_garment is None:
            raise ValueError(
                "Garment/product image is required. Pass product_image "
                "(or garment/garment_image)."
            )

        person_payload = self._prepare_image_input(resolved_person)
        garment_payload = self._prepare_image_input(resolved_garment)

        inputs: Dict[str, Any] = {
            "model_image": person_payload,
            "output_format": output_format,
            "return_base64": return_base64,
        }

        if model_name == "tryon-max":
            inputs["product_image"] = garment_payload
            if prompt is not None:
                inputs["prompt"] = prompt
            if resolution is not None:
                inputs["resolution"] = resolution
            if generation_mode is not None:
                inputs["generation_mode"] = generation_mode
            if num_images is not None:
                inputs["num_images"] = num_images
        else:
            # tryon-v1.6
            inputs["garment_image"] = garment_payload
            if category is not None:
                inputs["category"] = category
            if segmentation_free is not None:
                inputs["segmentation_free"] = segmentation_free
            if moderation_level is not None:
                inputs["moderation_level"] = moderation_level
            if garment_photo_type is not None:
                inputs["garment_photo_type"] = garment_photo_type
            if mode is not None:
                inputs["mode"] = mode
            if num_samples is not None:
                inputs["num_samples"] = num_samples

        if seed is not None:
            inputs["seed"] = seed
        inputs.update(kwargs)

        try:
            response = requests.post(
                f"{self.base_url}/v1/run",
                headers=self.headers,
                json={"model_name": model_name, "inputs": inputs},
                timeout=60,
            )
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.HTTPError as e:
            error_msg = e.response.text
            try:
                body = e.response.json()
                error_msg = body.get("message") or body.get("error") or error_msg
            except Exception:
                pass
            raise ValueError(f"FASHN API HTTP error ({e.response.status_code}): {error_msg}")
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Failed to connect to FASHN API: {str(e)}")

        if data.get("error") and not data.get("id"):
            raise ValueError(f"FASHN API error: {data.get('error')}")

        prediction_id = data.get("id")
        if not prediction_id:
            raise ValueError(f"Unexpected FASHN /v1/run response: {data}")

        self.last_prediction_id = prediction_id
        completed = self._poll_status(prediction_id, max_wait_time=max_wait_time)
        outputs = completed.get("output") or []
        if not outputs:
            raise ValueError(f"FASHN prediction completed with no output: {completed}")
        return list(outputs)

    def generate_and_decode(
        self,
        model_image: Optional[Union[str, io.BytesIO, Image.Image]] = None,
        product_image: Optional[Union[str, io.BytesIO, Image.Image]] = None,
        **kwargs,
    ) -> List[Image.Image]:
        """
        Run try-on and decode outputs to PIL Images.

        Same parameters as :meth:`generate`. Forces ``return_base64=True``
        when downloading is inconvenient; still accepts CDN URLs and fetches them.
        """
        # Prefer base64 to avoid CDN expiry / auth issues when decoding.
        kwargs.setdefault("return_base64", True)
        outputs = self.generate(
            model_image=model_image,
            product_image=product_image,
            **kwargs,
        )

        images: List[Image.Image] = []
        for item in outputs:
            if isinstance(item, str) and item.startswith("data:"):
                # data:image/png;base64,<payload>
                try:
                    b64 = item.split(",", 1)[1]
                except IndexError:
                    raise ValueError(f"Malformed data URI in FASHN output: {item[:64]}...")
                images.append(Image.open(io.BytesIO(base64.b64decode(b64))))
            elif isinstance(item, str) and item.startswith(("http://", "https://")):
                resp = requests.get(item, timeout=60)
                resp.raise_for_status()
                images.append(Image.open(io.BytesIO(resp.content)))
            else:
                # Assume raw base64 without prefix
                images.append(Image.open(io.BytesIO(base64.b64decode(item))))
        return images
