"""Generate still images with MiniMax-H3-Image or MiniMax-H3-Image-Highspeed.

https://platform.minimax.io/docs/api-reference/image-generation-h3-generations

    >>> from tryon.api.minimax import MiniMaxH3ImageAdapter
    >>> images = MiniMaxH3ImageAdapter().generate_text_to_image("A linen jacket")
    >>> images[0].save("jacket.png")
"""

import base64
import io
import os
import warnings

import requests
from PIL import Image

from .adapter import DEFAULT_BASE_URL


class MiniMaxH3ImageAdapter:
    """Synchronous text-to-image generation using the regional MiniMax API."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.api_key = api_key or os.getenv("MINIMAX_API_KEY")
        if not self.api_key:
            raise ValueError("Set MINIMAX_API_KEY to generate MiniMax H3 images.")
        self.base_url = (base_url or os.getenv("MINIMAX_API_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")

    def generate_text_to_image(
        self,
        prompt: str,
        model: str = "MiniMax-H3-Image",
        size: str = "auto",
        n: int = 1,
        response_format: str = "url",
    ) -> list[Image.Image]:
        """Return successful images in order and report any per-image failures."""
        prompt = prompt.strip()
        if not 1 <= len(prompt) <= 32000:
            raise ValueError("prompt must contain 1 to 32000 characters.")
        if model not in ("MiniMax-H3-Image", "MiniMax-H3-Image-Highspeed"):
            raise ValueError(f"Unsupported MiniMax H3 image model: {model}")
        if not 1 <= n <= 10:
            raise ValueError("n must be between 1 and 10.")
        if response_format not in ("url", "b64_json"):
            raise ValueError("response_format must be url or b64_json.")

        # A repeated POST generates and bills again, including on a 307/308 redirect.
        response = requests.post(
            f"{self.base_url}/v1/images/generations",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"prompt": prompt, "model": model, "size": size, "n": n, "response_format": response_format},
            timeout=600,
            allow_redirects=False,
        )
        if response.status_code != 200:
            try:
                error = response.json().get("error", {})
            except ValueError:
                error = {}
            message = error.get("message") or response.reason
            raise RuntimeError(f"MiniMax H3 image generation failed ({response.status_code}): {message}")

        images = []
        for index, item in enumerate(response.json().get("data", [])):
            if "error" in item:
                message = item["error"].get("message", "generation failed")
                warnings.warn(f"MiniMax H3 image {index + 1}: {message}", stacklevel=2)
                continue
            if response_format == "b64_json":
                raw = base64.b64decode(item["b64_json"], validate=True)
            else:
                download = requests.get(item["url"], timeout=60)
                download.raise_for_status()
                raw = download.content
            with Image.open(io.BytesIO(raw)) as image:
                images.append(image.copy())
        if not images:
            raise RuntimeError("MiniMax H3 returned no images.")
        return images
