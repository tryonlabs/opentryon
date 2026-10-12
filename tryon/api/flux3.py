import base64
import io
import os
import time
from typing import List, Optional, Union

import requests
from PIL import Image


class Flux3ImageAdapter:
    """
    Adapter for Black Forest Labs FLUX 3 Image API.

    One endpoint handles text-to-image, edits, and multi-reference composition (1–10
    reference images). There is no separate ``mode`` field; omit ``images`` to generate,
    or attach references and describe their use in ``prompt``.

    Reference: https://docs.bfl.ml/flux_3/flux3_image_overview
    API endpoint: POST https://api.bfl.ai/v1/flux-3-image
    Auth: ``BFL_API_KEY`` via the ``x-key`` header.
    """

    BASE_URL = "https://api.bfl.ai"
    ENDPOINT = "/v1/flux-3-image"
    MAX_REFERENCE_IMAGES = 10

    _IN_PROGRESS_STATUSES = frozenset(
        {
            "pending",
            "processing",
            "submitted",
            "reasoning",
            "generating",
            "request moderated",
            "content moderated",
        }
    )

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or os.getenv("BFL_API_KEY")
        if not self.api_key:
            raise ValueError(
                "BFL API key is required. Set BFL_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self.base_url = base_url or self.BASE_URL
        self.endpoint = f"{self.base_url}{self.ENDPOINT}"
        self.headers = {
            "x-key": self.api_key,
            "Content-Type": "application/json",
        }

    def _prepare_image_input(self, image_input: Union[str, io.BytesIO, Image.Image]) -> str:
        if isinstance(image_input, Image.Image):
            buffer = io.BytesIO()
            image_input.save(buffer, format="PNG")
            buffer.seek(0)
            return base64.b64encode(buffer.read()).decode("utf-8")

        if hasattr(image_input, "read"):
            image_file = image_input
            image_file.seek(0)
            image_bytes = image_file.read()
            image_file.seek(0)
            return base64.b64encode(image_bytes).decode("utf-8")

        if isinstance(image_input, str):
            if image_input.startswith(("http://", "https://")):
                return image_input

            if len(image_input) > 100 and not os.path.exists(image_input):
                try:
                    base64.b64decode(image_input[:100])
                    return image_input
                except Exception:
                    pass

            with open(image_input, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode("utf-8")

        raise ValueError(
            "Invalid image input: must be a file path, URL, file-like object, "
            "PIL Image, or base64 string"
        )

    def _poll_task(self, task_id: str, polling_url: str, max_wait_time: int = 600) -> dict:
        start_time = time.time()

        while True:
            elapsed_time = time.time() - start_time
            if elapsed_time > max_wait_time:
                raise ValueError(f"Task {task_id} timed out after {max_wait_time} seconds.")

            try:
                response = requests.get(
                    polling_url,
                    headers={"accept": "application/json", "x-key": self.api_key},
                    timeout=60,
                )
                if response.status_code in (502, 503):
                    try:
                        task_data = response.json()
                    except Exception:
                        time.sleep(1.5)
                        continue
                else:
                    response.raise_for_status()
                    task_data = response.json()
            except requests.exceptions.RequestException as e:
                raise ValueError(f"Failed to poll task status: {str(e)}")

            status_raw = task_data.get("status", "")
            status = status_raw.lower()

            if status_raw == "Ready" or status in {"completed", "succeed", "ready"}:
                return task_data

            if status_raw in {"Error", "Failed"} or status in {"failed", "fail", "error"}:
                error_msg = task_data.get("error", {})
                if isinstance(error_msg, dict):
                    error_msg = error_msg.get("message", status_raw)
                if not error_msg:
                    error_msg = task_data.get("message", str(task_data))
                raise ValueError(f"Task {task_id} failed: {error_msg}")

            if status in self._IN_PROGRESS_STATUSES:
                time.sleep(1.5)
                continue

            if status == "task not found":
                raise ValueError(f"Task {task_id} not found. It may have expired or been deleted.")

            raise ValueError(f"Unknown task status: {status_raw}. Response data: {task_data}")

    def _extract_sample(self, response_data: dict) -> str:
        result = response_data.get("result", {})
        if isinstance(result, dict) and "sample" in result:
            return result["sample"]
        if "sample" in response_data:
            return response_data["sample"]
        raise ValueError(f"No result sample in FLUX 3 Image response: {response_data}")

    def _decode_sample(self, sample: str) -> Image.Image:
        if sample.startswith(("http://", "https://")):
            response = requests.get(sample, timeout=120)
            response.raise_for_status()
            image_bytes = response.content
        else:
            image_bytes = base64.b64decode(sample)
        return Image.open(io.BytesIO(image_bytes))

    def _images_payload(
        self, images: Optional[Union[str, List[Union[str, io.BytesIO, Image.Image]]]]
    ) -> Optional[Union[str, List[str]]]:
        if images is None:
            return None
        if isinstance(images, list):
            prepared = [self._prepare_image_input(img) for img in images]
            if len(prepared) > self.MAX_REFERENCE_IMAGES:
                raise ValueError(f"Maximum {self.MAX_REFERENCE_IMAGES} reference images supported")
            return prepared if len(prepared) != 1 else prepared[0]
        return self._prepare_image_input(images)

    def _run(
        self,
        prompt: str,
        *,
        images: Optional[Union[str, List[Union[str, io.BytesIO, Image.Image]]]] = None,
        aspect_ratio: str = "auto",
        resolution: str = "1k",
        safety_tolerance: int = 2,
        grounding: bool = True,
        **kwargs,
    ) -> List[Image.Image]:
        if safety_tolerance < 0 or safety_tolerance > 4:
            raise ValueError("safety_tolerance must be between 0 and 4")

        payload = {
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
            "safety_tolerance": safety_tolerance,
            "grounding": grounding,
        }
        images_field = self._images_payload(images)
        if images_field is not None:
            payload["images"] = images_field
        payload.update(kwargs)

        try:
            response = requests.post(
                self.endpoint,
                headers=self.headers,
                json=payload,
                timeout=120,
            )
            response.raise_for_status()
            response_data = response.json()
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP {e.response.status_code}"
            try:
                error_data = e.response.json()
                error_msg = error_data.get("detail", str(error_data))
            except Exception:
                error_msg = e.response.text or str(e)
            raise ValueError(f"BFL FLUX 3 Image API HTTP error ({e.response.status_code}): {error_msg}")
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Failed to connect to BFL FLUX 3 Image API: {str(e)}")

        if "polling_url" in response_data:
            task_id = response_data.get("id", "unknown")
            response_data = self._poll_task(task_id, response_data["polling_url"])

        sample = self._extract_sample(response_data)
        return [self._decode_sample(sample)]

    def generate_text_to_image(
        self,
        prompt: str,
        aspect_ratio: str = "auto",
        resolution: str = "1k",
        safety_tolerance: int = 2,
        grounding: bool = True,
        **kwargs,
    ) -> List[Image.Image]:
        return self._run(
            prompt,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            safety_tolerance=safety_tolerance,
            grounding=grounding,
            **kwargs,
        )

    def generate_image_edit(
        self,
        prompt: str,
        input_image: Union[str, io.BytesIO, Image.Image],
        reference_images: Optional[List[Union[str, io.BytesIO, Image.Image]]] = None,
        aspect_ratio: str = "auto",
        resolution: str = "1k",
        safety_tolerance: int = 2,
        grounding: bool = True,
        **kwargs,
    ) -> List[Image.Image]:
        images: List[Union[str, io.BytesIO, Image.Image]] = [input_image]
        if reference_images:
            images.extend(reference_images)
        return self._run(
            prompt,
            images=images,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            safety_tolerance=safety_tolerance,
            grounding=grounding,
            **kwargs,
        )

    def generate_multi_image(
        self,
        prompt: str,
        images: List[Union[str, io.BytesIO, Image.Image]],
        aspect_ratio: str = "auto",
        resolution: str = "1k",
        safety_tolerance: int = 2,
        grounding: bool = True,
        **kwargs,
    ) -> List[Image.Image]:
        if not images:
            raise ValueError("At least one reference image is required")
        return self._run(
            prompt,
            images=images,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            safety_tolerance=safety_tolerance,
            grounding=grounding,
            **kwargs,
        )
