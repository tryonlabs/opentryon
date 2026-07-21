"""
Pruna AI P-Image-Try-On API Adapter

Adapter for Pruna AI's P-Image-Try-On model: virtually fits one or more
garments onto a person's photo. Unlike single-garment VTON APIs (Nova Canvas,
Kling AI, Segmind), this endpoint accepts up to 11 garment reference images
in a single call (multi-garment try-on) and also doubles as a general
garment-composition/image-editing tool.

Reference: https://docs.api.pruna.ai/guides/models/p-image-try-on
API docs: https://docs.api.pruna.ai/guides/quickstart

API endpoints:
    POST https://api.pruna.ai/v1/files                     -- upload a local image, get a temp URL back
    POST https://api.pruna.ai/v1/predictions                -- create a prediction (Model: p-image-try-on)
    GET  https://api.pruna.ai/v1/predictions/status/{id}    -- poll an async prediction
    GET  <generation_url>                                    -- download the result image

Authentication:
    Requires a Pruna API key via constructor or PRUNA_API_KEY environment
    variable. The key is sent as the ``apikey`` header on every request.

Example:
    >>> import os
    >>> os.environ['PRUNA_API_KEY'] = 'your_api_key'
    >>> adapter = PImageTryOnAdapter()
    >>> images = adapter.generate_and_decode(
    ...     person_image="person.jpg",
    ...     garment_images=["shirt.jpg"],
    ... )
    >>> images[0].save("result.jpg")
"""

import io
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import requests
from PIL import Image


class PImageTryOnAdapter:
    """
    Adapter for Pruna AI's P-Image-Try-On API.

    Fits one or more garment reference images onto a person's photo.
    Supports up to 11 garment reference images (up to 6 recommended) in a
    single call, an experimental ``prompt`` for disambiguating non-flatlay
    garment images, and an experimental ``reference_pose`` to repose the
    person before compositing.

    Reference: https://docs.api.pruna.ai/guides/models/p-image-try-on

    Authentication:
        Requires PRUNA_API_KEY via constructor or environment variable.

    Example:
        >>> adapter = PImageTryOnAdapter()
        >>> images = adapter.generate_and_decode(
        ...     person_image="person.jpg",
        ...     garment_images=["jacket.jpg", "trousers.jpg"],
        ... )
        >>> images[0].save("result.jpg")
    """

    BASE_URL = "https://api.pruna.ai"
    MODEL = "p-image-try-on"
    VALID_OUTPUT_FORMATS = {"jpg", "png", "webp"}
    TERMINAL_STATUSES = {"succeeded", "failed", "canceled"}

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize the P-Image-Try-On client.

        Args:
            api_key: Pruna API key. Defaults to PRUNA_API_KEY environment variable.
            base_url: Pruna API base URL. Defaults to PRUNA_BASE_URL or
                      'https://api.pruna.ai'.
        """
        self.api_key = api_key or os.getenv("PRUNA_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Pruna API key is required. Set PRUNA_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self.base_url = (base_url or os.getenv("PRUNA_BASE_URL") or self.BASE_URL).rstrip("/")
        self.headers = {"apikey": self.api_key}

    def _resolve_url(self, url: str) -> str:
        """Pruna sometimes returns a relative path for `generation_url`; make it absolute."""
        if url.startswith(("http://", "https://")):
            return url
        return f"{self.base_url}{url if url.startswith('/') else '/' + url}"

    def _upload_bytes(self, data: bytes, filename: str = "image.png") -> str:
        """Upload raw image bytes to Pruna's temporary file store and return its hosted URL."""
        response = requests.post(
            f"{self.base_url}/v1/files",
            headers=self.headers,
            files={"content": (filename, data)},
            timeout=60,
        )
        response.raise_for_status()
        data_json = response.json()
        try:
            return data_json["urls"]["get"]
        except (KeyError, TypeError):
            raise ValueError(f"Unexpected file upload response from Pruna: {data_json}")

    def _prepare_image_input(self, image_input: Union[str, io.BytesIO, Image.Image, bytes]) -> str:
        """
        Resolve any supported image input to a URL Pruna's API can fetch.

        Pruna's `/v1/predictions` endpoint only accepts image *URLs*, so
        anything that isn't already an http(s) URL gets uploaded via
        `/v1/files` first and its temporary hosted URL is used instead.
        """
        if isinstance(image_input, Image.Image):
            buffer = io.BytesIO()
            image_input.save(buffer, format="PNG")
            return self._upload_bytes(buffer.getvalue(), filename="image.png")

        if isinstance(image_input, (bytes, bytearray)):
            return self._upload_bytes(bytes(image_input), filename="image.png")

        if hasattr(image_input, "read"):
            image_input.seek(0)
            return self._upload_bytes(image_input.read(), filename="image.png")

        if isinstance(image_input, str):
            if image_input.startswith(("http://", "https://")):
                return image_input

            if os.path.exists(image_input):
                with open(image_input, "rb") as f:
                    return self._upload_bytes(f.read(), filename=Path(image_input).name)

            if len(image_input) > 100:
                try:
                    import base64
                    image_bytes = base64.b64decode(image_input)
                    return self._upload_bytes(image_bytes, filename="image.png")
                except Exception:
                    pass

            raise ValueError(f"Image path does not exist: {image_input}")

        raise ValueError(
            "Invalid image input: must be a file path, URL, PIL Image, bytes, "
            "file-like object, or base64 string"
        )

    def _poll_prediction(self, get_url: str, max_wait_time: int = 120, poll_interval: float = 1.0) -> Dict[str, Any]:
        """Poll an async prediction's status endpoint until it reaches a terminal state."""
        start_time = time.time()
        while True:
            elapsed = time.time() - start_time
            if elapsed > max_wait_time:
                raise ValueError(f"Prediction timed out after {max_wait_time} seconds.")

            response = requests.get(get_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            status = data.get("status")

            if status == "succeeded":
                return data
            if status in ("failed", "canceled"):
                raise ValueError(f"Prediction {status}: {data.get('error') or data.get('message') or data}")

            time.sleep(poll_interval)

    def generate(
        self,
        person_image: Optional[Union[str, io.BytesIO, Image.Image]] = None,
        garment_images: Optional[Union[str, io.BytesIO, Image.Image, List[Any]]] = None,
        *,
        person: Optional[Union[str, io.BytesIO, Image.Image]] = None,
        garments: Optional[Union[str, io.BytesIO, Image.Image, List[Any]]] = None,
        source_image: Optional[Union[str, io.BytesIO, Image.Image]] = None,
        model_image: Optional[Union[str, io.BytesIO, Image.Image]] = None,
        prompt: str = "",
        seed: Optional[int] = None,
        turbo: bool = False,
        output_format: str = "jpg",
        output_quality: int = 95,
        reference_pose: Optional[Union[str, io.BytesIO, Image.Image]] = None,
        preserve_input_size: bool = True,
        wait: bool = True,
        max_wait_time: int = 120,
        **kwargs,
    ) -> str:
        """
        Generate a virtual try-on result using the P-Image-Try-On API.

        Args:
            person_image: Person/model image.
            garment_images: One or more garment reference images (path, URL, PIL
                Image, or bytes/file-like), or a list of any of those. Up to 11
                supported (6 recommended).
            person: Alias for person_image.
            garments: Alias for garment_images.
            source_image: Alias for person_image.
            model_image: Alias for person_image.
            prompt: Experimental guidance for non-flatlay garment images, e.g.
                which garment from which image to use. Default: "".
            seed: Optional random seed. Leave unset for a random seed.
            turbo: Run faster with additional optimizations. Not recommended
                for more than 4 garments. Default: False.
            output_format: 'jpg', 'png', or 'webp'. Default: 'jpg'.
            output_quality: JPEG/WebP quality 0-100. Default: 95.
            reference_pose: EXPERIMENTAL optional reference pose image; when
                provided, the person is reposed to match it before try-on.
            preserve_input_size: Return the output at the original input
                resolution. Default: True.
            wait: If True (default), use Pruna's synchronous mode
                (`Try-Sync: true`) and poll automatically if it doesn't finish
                within 60s. If False, submit asynchronously and poll until
                `max_wait_time`.
            max_wait_time: Maximum polling time in seconds. Default: 120.
            **kwargs: Additional input fields passed through to the API.

        Returns:
            str: URL of the generated result image.
        """
        resolved_person = person_image or person or source_image or model_image
        resolved_garments = garment_images if garment_images is not None else garments

        if resolved_person is None:
            raise ValueError("Person image is required. Pass person_image (or person/source_image/model_image).")
        if not resolved_garments:
            raise ValueError("At least one garment image is required. Pass garment_images (or garments).")

        if isinstance(resolved_garments, (list, tuple)):
            garment_list = list(resolved_garments)
        else:
            garment_list = [resolved_garments]

        if output_format not in self.VALID_OUTPUT_FORMATS:
            raise ValueError(
                f"Invalid output_format '{output_format}'. Must be one of: {sorted(self.VALID_OUTPUT_FORMATS)}"
            )

        person_url = self._prepare_image_input(resolved_person)
        garment_urls = [self._prepare_image_input(g) for g in garment_list]

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
            input_payload["reference_pose"] = self._prepare_image_input(reference_pose)
        input_payload.update(kwargs)

        headers = {**self.headers, "Content-Type": "application/json", "Model": self.MODEL}
        if wait:
            headers["Try-Sync"] = "true"

        try:
            response = requests.post(
                f"{self.base_url}/v1/predictions",
                headers=headers,
                json={"input": input_payload},
                timeout=90,
            )
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.HTTPError as e:
            error_msg = e.response.text
            try:
                error_msg = e.response.json().get("error", error_msg)
            except Exception:
                pass
            raise ValueError(f"Pruna P-Image-Try-On API HTTP error ({e.response.status_code}): {error_msg}")
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Failed to connect to Pruna P-Image-Try-On API: {str(e)}")

        status = data.get("status")
        if status == "succeeded":
            return self._resolve_url(data["generation_url"])
        if status == "failed":
            raise ValueError(f"Prediction failed: {data.get('error') or data.get('message') or data}")

        get_url = data.get("get_url") or f"{self.base_url}/v1/predictions/status/{data.get('id')}"
        completed = self._poll_prediction(get_url, max_wait_time=max_wait_time)
        return self._resolve_url(completed["generation_url"])

    def generate_and_decode(
        self,
        person_image: Optional[Union[str, io.BytesIO, Image.Image]] = None,
        garment_images: Optional[Union[str, io.BytesIO, Image.Image, List[Any]]] = None,
        **kwargs,
    ) -> List[Image.Image]:
        """
        Generate a virtual try-on result and decode it to a PIL Image.

        Args, and Returns: same as `generate()`, but returns decoded images
        instead of a URL.

        Returns:
            List[Image.Image]: Decoded try-on result image(s) (currently
            always a single-element list; Pruna returns one composite image
            per prediction).
        """
        url = self.generate(person_image=person_image, garment_images=garment_images, **kwargs)
        response = requests.get(url, headers=self.headers, timeout=60)
        response.raise_for_status()
        return [Image.open(io.BytesIO(response.content))]
