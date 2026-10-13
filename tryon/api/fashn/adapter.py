"""
FASHN AI catalogue-workflow API Adapter

Wraps the non-try-on FASHN endpoints that cover the e-commerce photo workflow.
All share FASHN's universal ``POST /v1/run`` + ``GET /v1/status/{id}`` protocol
and the same ``FASHN_API_KEY`` as the try-on adapter
(:class:`tryon.api.vton.fashn.FashnVTONAdapter`, which this class extends so
the image handling, auth and polling are shared).

Endpoints (lifecycle as published by FASHN):

- ``product-to-model``  (Preview)      product photo -> person wearing it; optional
  inspiration image, background reference and face reference
- ``model-create``      (Experimental) text / reference image -> new fashion model photo
- ``model-swap``        (Experimental) change the model's identity, keep outfit and pose
- ``face-to-model``     (Experimental) headshot / selfie -> try-on-ready upper-body avatar
- ``reframe``           (Experimental) expand or crop to a target aspect ratio
- ``edit``                             prompt-driven edit with optional mask / context image
- ``image-to-video``                   animate a still into a 5 or 10 s clip
- ``background-remove``                1-credit cut-out with transparent background

Credits for the image endpoints are ``generation_mode`` x ``resolution``
(fast/balanced/quality x 1k/2k/4k = 1..5, ``face_reference`` adds +3 per image,
``num_images`` multiplies). Video is 1-12 credits (duration x resolution);
background-remove is 1.

Reference:
    https://docs.fashn.ai/
    https://docs.fashn.ai/api-reference/product-to-model

Env:
    FASHN_API_KEY (required), FASHN_BASE_URL (optional)

Examples:
    >>> adapter = FashnAdapter()
    >>> images = adapter.generate_product_to_model("jacket.jpg", prompt="studio background")
    >>> images = adapter.generate_model_swap("look.jpg", prompt="woman with red hair")
    >>> video = adapter.generate_image_to_video("look.jpg", duration=5, resolution="720p")
"""

from __future__ import annotations

import base64
import io
from typing import Any, Dict, List, Optional, Union

import requests
from PIL import Image

from tryon.api.vton.fashn import FashnVTONAdapter

ImageInput = Union[str, io.BytesIO, Image.Image, bytes]

RESOLUTIONS = ("1k", "2k", "4k")
GENERATION_MODES = ("fast", "balanced", "quality")
FACE_REFERENCE_MODES = ("match_base", "match_reference")
OUTPUT_FORMATS = ("png", "jpeg")
MAX_IMAGES = 4

PRODUCT_TO_MODEL_RATIOS = ("1:1", "3:4", "4:3", "9:16", "16:9", "2:3", "3:2", "4:5", "5:4")
MODEL_CREATE_RATIOS = ("21:9", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3", "4:5", "5:4", "1:1")
FACE_TO_MODEL_RATIOS = ("1:1", "4:5", "3:4", "2:3", "9:16")  # vertical only
REFRAME_RATIOS = ("21:9", "1:1", "4:3", "3:2", "2:3", "5:4", "4:5", "3:4", "16:9", "9:16")
VIDEO_DURATIONS = (5, 10)
VIDEO_RESOLUTIONS = ("480p", "720p", "1080p")


def _check(name: str, value: Any, allowed) -> None:
    if value is not None and value not in allowed:
        raise ValueError(f"{name} must be one of {list(allowed)} (got {value!r}).")


class FashnAdapter(FashnVTONAdapter):
    """FASHN catalogue-workflow endpoints (extends the try-on adapter)."""

    VALID_MODELS = {
        "product-to-model", "model-create", "model-swap", "face-to-model",
        "reframe", "edit", "image-to-video", "background-remove",
    }

    def generate(self, *args, **kwargs):  # pragma: no cover - guard against inherited try-on entry point
        raise NotImplementedError(
            "FashnAdapter covers the catalogue endpoints (generate_product_to_model, generate_model_create, ...). "
            "For try-on use tryon.api.vton.fashn.FashnVTONAdapter."
        )

    generate_and_decode = generate

    # -- shared plumbing --------------------------------------------------

    def _run(self, model_name: str, inputs: Dict[str, Any], max_wait_time: int = 300) -> List[str]:
        """Submit ``inputs`` to ``model_name`` and poll to completion; returns output URLs / data URIs."""
        try:
            response = requests.post(
                f"{self.base_url}/v1/run",
                headers=self.headers,
                json={"model_name": model_name, "inputs": inputs},
                timeout=60,
            )
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.HTTPError as exc:
            msg = exc.response.text
            try:
                body = exc.response.json()
                msg = body.get("message") or body.get("error") or msg
            except Exception:
                pass
            raise ValueError(f"FASHN API HTTP error ({exc.response.status_code}): {msg}")
        except requests.exceptions.RequestException as exc:
            raise ValueError(f"Failed to connect to FASHN API: {exc}")

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

    @staticmethod
    def _decode(outputs: List[str]) -> List[Image.Image]:
        images: List[Image.Image] = []
        for item in outputs:
            if item.startswith("data:"):
                images.append(Image.open(io.BytesIO(base64.b64decode(item.split(",", 1)[1]))))
            elif item.startswith(("http://", "https://")):
                resp = requests.get(item, timeout=120)
                resp.raise_for_status()
                images.append(Image.open(io.BytesIO(resp.content)))
            else:
                images.append(Image.open(io.BytesIO(base64.b64decode(item))))
        return images

    def _image_endpoint(
        self,
        model_name: str,
        inputs: Dict[str, Any],
        *,
        resolution: Optional[str],
        generation_mode: Optional[str],
        seed: Optional[int],
        num_images: Optional[int],
        output_format: str,
        max_wait_time: int,
    ) -> List[Image.Image]:
        _check("resolution", resolution, RESOLUTIONS)
        _check("generation_mode", generation_mode, GENERATION_MODES)
        _check("output_format", output_format, OUTPUT_FORMATS)
        if num_images is not None and not 1 <= int(num_images) <= MAX_IMAGES:
            raise ValueError(f"num_images must be between 1 and {MAX_IMAGES} (got {num_images}).")
        if resolution is not None:
            inputs["resolution"] = resolution
        if generation_mode is not None:
            inputs["generation_mode"] = generation_mode
        if seed is not None:
            inputs["seed"] = int(seed)
        if num_images is not None:
            inputs["num_images"] = int(num_images)
        inputs["output_format"] = output_format
        inputs["return_base64"] = True  # avoid CDN expiry; outputs live <= 60 min server-side
        return self._decode(self._run(model_name, inputs, max_wait_time))

    def _img(self, value: Optional[ImageInput]) -> Optional[str]:
        return None if value is None else self._prepare_image_input(value)

    def _identity(self, inputs: Dict[str, Any], face_reference: Optional[ImageInput], mode: Optional[str]) -> None:
        _check("face_reference_mode", mode, FACE_REFERENCE_MODES)
        if mode is not None and face_reference is None:
            raise ValueError("face_reference_mode requires face_reference.")
        if face_reference is not None:
            inputs["face_reference"] = self._img(face_reference)
        if mode is not None:
            inputs["face_reference_mode"] = mode

    # -- endpoints --------------------------------------------------------

    def generate_product_to_model(
        self,
        product_image: ImageInput,
        prompt: Optional[str] = None,
        image_prompt: Optional[ImageInput] = None,
        background_reference: Optional[ImageInput] = None,
        face_reference: Optional[ImageInput] = None,
        face_reference_mode: Optional[str] = None,
        aspect_ratio: Optional[str] = None,
        resolution: Optional[str] = None,
        generation_mode: Optional[str] = None,
        seed: Optional[int] = None,
        num_images: Optional[int] = None,
        output_format: str = "png",
        max_wait_time: int = 300,
    ) -> List[Image.Image]:
        """Product photo -> a person wearing the product (clothing, shoes, hats, jewellery, bags).

        ``image_prompt`` guides pose / environment / lighting; ``background_reference``
        anchors the scene; ``face_reference`` fixes identity (+3 credits, ~+20 s). This does
        **not** keep an existing person's pose or background -- use ``tryon-max`` for that.
        """
        if product_image is None:
            raise ValueError("product_image is required.")
        _check("aspect_ratio", aspect_ratio, PRODUCT_TO_MODEL_RATIOS)
        inputs: Dict[str, Any] = {"product_image": self._img(product_image)}
        for key, value in (("image_prompt", image_prompt), ("background_reference", background_reference)):
            if value is not None:
                inputs[key] = self._img(value)
        if prompt:
            inputs["prompt"] = prompt
        if aspect_ratio:
            inputs["aspect_ratio"] = aspect_ratio
        self._identity(inputs, face_reference, face_reference_mode)
        return self._image_endpoint("product-to-model", inputs, resolution=resolution, generation_mode=generation_mode,
                                    seed=seed, num_images=num_images, output_format=output_format,
                                    max_wait_time=max_wait_time)

    def generate_model_create(
        self,
        prompt: str,
        image_reference: Optional[ImageInput] = None,
        face_reference: Optional[ImageInput] = None,
        face_reference_mode: Optional[str] = None,
        aspect_ratio: Optional[str] = None,
        resolution: Optional[str] = None,
        generation_mode: Optional[str] = None,
        seed: Optional[int] = None,
        num_images: Optional[int] = None,
        output_format: str = "png",
        max_wait_time: int = 300,
    ) -> List[Image.Image]:
        """Text (and optional reference image) -> a new fashion model photo.

        ``face_reference`` keeps one identity across generations (caps output at 2K, +3 credits).
        """
        if not prompt or not prompt.strip():
            raise ValueError("prompt is required for model-create.")
        _check("aspect_ratio", aspect_ratio, MODEL_CREATE_RATIOS)
        inputs: Dict[str, Any] = {"prompt": prompt}
        if image_reference is not None:
            inputs["image_reference"] = self._img(image_reference)
        if aspect_ratio:
            inputs["aspect_ratio"] = aspect_ratio
        self._identity(inputs, face_reference, face_reference_mode)
        return self._image_endpoint("model-create", inputs, resolution=resolution, generation_mode=generation_mode,
                                    seed=seed, num_images=num_images, output_format=output_format,
                                    max_wait_time=max_wait_time)

    def generate_model_swap(
        self,
        model_image: ImageInput,
        prompt: Optional[str] = None,
        face_reference: Optional[ImageInput] = None,
        face_reference_mode: Optional[str] = None,
        resolution: Optional[str] = None,
        generation_mode: Optional[str] = None,
        seed: Optional[int] = None,
        num_images: Optional[int] = None,
        output_format: str = "png",
        max_wait_time: int = 300,
    ) -> List[Image.Image]:
        """Change the model's identity (face, skin tone, hair) while keeping outfit and pose."""
        if model_image is None:
            raise ValueError("model_image is required.")
        inputs: Dict[str, Any] = {"model_image": self._img(model_image)}
        if prompt:
            inputs["prompt"] = prompt
        self._identity(inputs, face_reference, face_reference_mode)
        return self._image_endpoint("model-swap", inputs, resolution=resolution, generation_mode=generation_mode,
                                    seed=seed, num_images=num_images, output_format=output_format,
                                    max_wait_time=max_wait_time)

    def generate_face_to_model(
        self,
        face_image: ImageInput,
        prompt: Optional[str] = None,
        aspect_ratio: Optional[str] = None,
        resolution: Optional[str] = None,
        generation_mode: Optional[str] = None,
        seed: Optional[int] = None,
        num_images: Optional[int] = None,
        output_format: str = "jpeg",
        max_wait_time: int = 300,
    ) -> List[Image.Image]:
        """Headshot / selfie -> try-on-ready upper-body avatar (vertical aspect ratios only)."""
        if face_image is None:
            raise ValueError("face_image is required.")
        _check("aspect_ratio", aspect_ratio, FACE_TO_MODEL_RATIOS)
        inputs: Dict[str, Any] = {"face_image": self._img(face_image)}
        if prompt:
            inputs["prompt"] = prompt
        if aspect_ratio:
            inputs["aspect_ratio"] = aspect_ratio
        return self._image_endpoint("face-to-model", inputs, resolution=resolution, generation_mode=generation_mode,
                                    seed=seed, num_images=num_images, output_format=output_format,
                                    max_wait_time=max_wait_time)

    def generate_reframe(
        self,
        image: ImageInput,
        aspect_ratio: str,
        resolution: Optional[str] = None,
        generation_mode: Optional[str] = None,
        seed: Optional[int] = None,
        num_images: Optional[int] = None,
        output_format: str = "png",
        max_wait_time: int = 300,
    ) -> List[Image.Image]:
        """Expand (outpaint) or crop to ``aspect_ratio``; errors if the image already matches it."""
        if image is None:
            raise ValueError("image is required.")
        if aspect_ratio not in REFRAME_RATIOS:
            raise ValueError(f"aspect_ratio must be one of {list(REFRAME_RATIOS)} (got {aspect_ratio!r}).")
        inputs: Dict[str, Any] = {"image": self._img(image), "aspect_ratio": aspect_ratio}
        return self._image_endpoint("reframe", inputs, resolution=resolution, generation_mode=generation_mode,
                                    seed=seed, num_images=num_images, output_format=output_format,
                                    max_wait_time=max_wait_time)

    def generate_image_edit(
        self,
        image: ImageInput,
        prompt: str,
        mask: Optional[ImageInput] = None,
        image_context: Optional[ImageInput] = None,
        resolution: Optional[str] = None,
        generation_mode: Optional[str] = None,
        seed: Optional[int] = None,
        num_images: Optional[int] = None,
        output_format: str = "png",
        max_wait_time: int = 300,
    ) -> List[Image.Image]:
        """Prompt-driven edit preserving subject and product fidelity.

        ``mask``: white = prioritise, black = preserve (same size as ``image``).
        ``image_context``: extra visual reference (a background, pose or texture).
        """
        if image is None:
            raise ValueError("image is required.")
        if not prompt or not prompt.strip():
            raise ValueError("prompt is required for edit.")
        inputs: Dict[str, Any] = {"image": self._img(image), "prompt": prompt}
        for key, value in (("mask", mask), ("image_context", image_context)):
            if value is not None:
                inputs[key] = self._img(value)
        return self._image_endpoint("edit", inputs, resolution=resolution, generation_mode=generation_mode,
                                    seed=seed, num_images=num_images, output_format=output_format,
                                    max_wait_time=max_wait_time)

    def generate_image_to_video(
        self,
        image: ImageInput,
        prompt: Optional[str] = None,
        duration: int = 5,
        resolution: str = "1080p",
        end_image: Optional[ImageInput] = None,
        max_wait_time: int = 600,
    ) -> bytes:
        """Animate a still into a 5 or 10 s MP4 (returned as bytes).

        Leave ``prompt`` empty for automatic motion planning (FASHN recommends short guidance only).
        Credits: 5 s = 1 / 3 / 6, 10 s = 2 / 6 / 12 at 480p / 720p / 1080p.
        """
        if image is None:
            raise ValueError("image is required.")
        if int(duration) not in VIDEO_DURATIONS:
            raise ValueError(f"duration must be one of {list(VIDEO_DURATIONS)} (got {duration}).")
        _check("resolution", resolution, VIDEO_RESOLUTIONS)
        inputs: Dict[str, Any] = {"image": self._img(image), "duration": int(duration), "resolution": resolution}
        if prompt:
            inputs["prompt"] = prompt
        if end_image is not None:
            inputs["end_image"] = self._img(end_image)
        url = self._run("image-to-video", inputs, max_wait_time)[0]
        if url.startswith("data:"):
            return base64.b64decode(url.split(",", 1)[1])
        resp = requests.get(url, timeout=300)
        resp.raise_for_status()
        return resp.content

    def remove_background(self, image: ImageInput, max_wait_time: int = 120) -> List[Image.Image]:
        """Cut out the main subject (transparent PNG); 1 credit, typically 1-3 s."""
        if image is None:
            raise ValueError("image is required.")
        inputs: Dict[str, Any] = {"image": self._img(image), "return_base64": True}
        return self._decode(self._run("background-remove", inputs, max_wait_time))
