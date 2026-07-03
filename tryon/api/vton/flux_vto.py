import os
import base64
import io
import time
from typing import Optional, Union, List

import requests
from PIL import Image


class FluxVTONAdapter:
    """
    Adapter for Black Forest Labs FLUX Virtual Try-On (VTO) API.

    FLUX VTO generates virtual try-on results from a person image plus a garment
    reference. Unlike category-based VTON APIs, this endpoint requires a natural-
    language styling prompt describing what to try on.

    Reference: https://docs.bfl.ai/flux_tools/flux_vto

    API endpoint: POST https://api.bfl.ai/v1/flux-tools/vto-v1

    Regional endpoints (lower latency):
        - https://api.eu.bfl.ai/v1/flux-tools/vto-v1
        - https://api.us.bfl.ai/v1/flux-tools/vto-v1

    Authentication:
        Requires BFL API key via constructor or BFL_API_KEY environment variable.
        The API key is sent in the 'x-key' header.

    Example:
        >>> import os
        >>> os.environ['BFL_API_KEY'] = 'your_api_key'
        >>> adapter = FluxVTONAdapter()
        >>> images = adapter.generate_and_decode(
        ...     person="person.jpg",
        ...     garment="jacket.jpg",
        ...     garment_description="olive green bomber jacket with 'Black Forest Labs' branding"
        ... )
        >>> images[0].save("result.webp")
    """

    BASE_URL = "https://api.bfl.ai"
    ENDPOINT = "/v1/flux-tools/vto-v1"
    DEFAULT_PROMPT = (
        "The person of image 1, maintaining exactly their face and pose, "
        "wearing the garments of image 2."
    )
    VALID_OUTPUT_FORMATS = {"jpeg", "png", "webp"}
    FAILED_STATUSES = {
        "Error",
        "Failed",
        "Request Moderated",
        "Content Moderated",
        "Task not found",
    }

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize the FLUX VTO client.

        Args:
            api_key: BFL API key. Defaults to BFL_API_KEY environment variable.
            base_url: BFL API base URL. Defaults to BFL_BASE_URL or
                      'https://api.bfl.ai'. Use regional hosts such as
                      'https://api.eu.bfl.ai' or 'https://api.us.bfl.ai'
                      for lower latency.
        """
        self.api_key = api_key or os.getenv("BFL_API_KEY")
        if not self.api_key:
            raise ValueError(
                "BFL API key is required. Set BFL_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self.base_url = (base_url or os.getenv("BFL_BASE_URL") or self.BASE_URL).rstrip("/")
        self.endpoint = f"{self.base_url}{self.ENDPOINT}"
        self.headers = {
            "accept": "application/json",
            "x-key": self.api_key,
            "Content-Type": "application/json",
        }

    def build_prompt(
        self,
        prompt: Optional[str] = None,
        garment_description: Optional[str] = None,
    ) -> str:
        """
        Build the styling prompt for the VTO request.

        Args:
            prompt: Full prompt override. When provided, garment_description is ignored.
            garment_description: Concise garment description inserted into the
                                 recommended prompt template.

        Returns:
            str: Prompt sent to the FLUX VTO API.
        """
        if prompt:
            return prompt

        garment = garment_description or "garments"
        return (
            "The person of image 1, maintaining exactly their face and pose, "
            f"wearing the {garment} of image 2."
        )

    def _prepare_image_input(self, image_input: Union[str, io.BytesIO, Image.Image]) -> str:
        """Prepare image input as a URL or base64 string for the BFL API."""
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

    def _poll_task(self, task_id: str, polling_url: str, max_wait_time: int = 300) -> dict:
        """Poll task status until completion."""
        start_time = time.time()

        while True:
            elapsed_time = time.time() - start_time
            if elapsed_time > max_wait_time:
                raise ValueError(f"Task {task_id} timed out after {max_wait_time} seconds.")

            try:
                response = requests.get(
                    polling_url,
                    headers={"accept": "application/json", "x-key": self.api_key},
                    timeout=30,
                )
                response.raise_for_status()
                task_data = response.json()
            except requests.exceptions.RequestException as e:
                raise ValueError(f"Failed to poll task status: {str(e)}")

            status_raw = task_data.get("status", "")
            status = status_raw.lower()

            if status_raw in self.FAILED_STATUSES or status in {"failed", "fail", "error"}:
                error_msg = task_data.get("error", {}).get("message", status_raw)
                if not error_msg:
                    error_msg = task_data.get("message", str(task_data))
                raise ValueError(f"Task {task_id} failed: {error_msg}")

            if status_raw == "Ready" or status in {"completed", "succeed", "ready"}:
                return task_data

            if status in {"pending", "processing", "submitted"}:
                elapsed_minutes = int(elapsed_time / 60)
                elapsed_seconds = int(elapsed_time % 60)
                print(
                    f"Task {task_id} status: {status_raw} "
                    f"(elapsed: {elapsed_minutes}m {elapsed_seconds}s)..."
                )
                time.sleep(1)
                continue

            raise ValueError(
                f"Unknown task status: {status_raw}. Response data: {task_data}"
            )

    def _extract_result_sample(self, response_data: dict) -> str:
        """Extract the result image URL or base64 sample from a completed task."""
        result = response_data.get("result", {})
        if isinstance(result, dict) and "sample" in result:
            return result["sample"]

        if "sample" in response_data:
            return response_data["sample"]

        raise ValueError(
            "No result sample returned from FLUX VTO API. "
            f"Response data: {response_data}"
        )

    def _decode_sample(self, sample: str) -> Image.Image:
        """Decode a result sample URL or base64 string into a PIL Image."""
        if sample.startswith(("http://", "https://")):
            response = requests.get(sample, timeout=60)
            response.raise_for_status()
            image_bytes = response.content
        else:
            image_bytes = base64.b64decode(sample)

        return Image.open(io.BytesIO(image_bytes))

    def create_virtual_try_on_payload(
        self,
        person: str,
        garment: str,
        prompt: str,
        seed: Optional[int] = None,
        safety_tolerance: int = 2,
        output_format: str = "webp",
        **kwargs,
    ) -> dict:
        """
        Create the payload for a FLUX VTO request.

        Args:
            person: Person image as URL or base64.
            garment: Garment reference as URL or base64.
            prompt: Natural-language styling instruction.
            seed: Optional seed for reproducibility.
            safety_tolerance: Moderation strictness from 0 (strict) to 5 (permissive).
            output_format: Output format: 'jpeg', 'png', or 'webp'.
            **kwargs: Additional API parameters such as webhook_url or webhook_secret.
        """
        if output_format not in self.VALID_OUTPUT_FORMATS:
            raise ValueError(
                f"Invalid output_format '{output_format}'. "
                f"Must be one of: {sorted(self.VALID_OUTPUT_FORMATS)}"
            )

        if not (0 <= safety_tolerance <= 5):
            raise ValueError("safety_tolerance must be between 0 and 5")

        payload = {
            "prompt": prompt,
            "person": person,
            "garment": garment,
            "safety_tolerance": safety_tolerance,
            "output_format": output_format,
        }

        if seed is not None:
            payload["seed"] = seed

        payload.update(kwargs)
        return payload

    def generate(
        self,
        person: Optional[Union[str, io.BytesIO, Image.Image]] = None,
        garment: Optional[Union[str, io.BytesIO, Image.Image]] = None,
        *,
        source_image: Optional[Union[str, io.BytesIO, Image.Image]] = None,
        reference_image: Optional[Union[str, io.BytesIO, Image.Image]] = None,
        model_image: Optional[Union[str, io.BytesIO, Image.Image]] = None,
        cloth_image: Optional[Union[str, io.BytesIO, Image.Image]] = None,
        person_image: Optional[Union[str, io.BytesIO, Image.Image]] = None,
        garment_image: Optional[Union[str, io.BytesIO, Image.Image]] = None,
        prompt: Optional[str] = None,
        garment_description: Optional[str] = None,
        seed: Optional[int] = None,
        safety_tolerance: int = 2,
        output_format: str = "webp",
        max_wait_time: int = 300,
        **kwargs,
    ) -> str:
        """
        Generate a virtual try-on result using the FLUX VTO API.

        This method accepts person and garment images in multiple formats:
        file paths, URLs, PIL Images, file-like objects, or base64 strings.

        For compatibility with other VTON adapters, you may also pass:
        - source_image / person_image / model_image for the person image
        - reference_image / garment_image / cloth_image for the garment image

        Args:
            person: Person/model image.
            garment: Garment reference image.
            source_image: Alias for person.
            reference_image: Alias for garment.
            model_image: Alias for person.
            cloth_image: Alias for garment.
            person_image: Alias for person.
            garment_image: Alias for garment.
            prompt: Full styling prompt. Overrides garment_description when set.
            garment_description: Concise garment description used to build the prompt.
            seed: Optional seed for reproducibility.
            safety_tolerance: Moderation strictness from 0 to 5. Default: 2.
            output_format: Output format: 'jpeg', 'png', or 'webp'. Default: 'webp'.
            max_wait_time: Maximum polling time in seconds. Default: 300.
            **kwargs: Additional API parameters such as webhook_url or webhook_secret.

        Returns:
            str: Signed result URL from the FLUX VTO API. URLs are valid for about
                 10 minutes, so download promptly if you need to persist the output.
        """
        resolved_person = person or source_image or person_image or model_image
        resolved_garment = garment or reference_image or garment_image or cloth_image

        if resolved_person is None:
            raise ValueError(
                "Person image is required. Pass person, source_image, person_image, "
                "or model_image."
            )
        if resolved_garment is None:
            raise ValueError(
                "Garment image is required. Pass garment, reference_image, "
                "garment_image, or cloth_image."
            )

        person_prepared = self._prepare_image_input(resolved_person)
        garment_prepared = self._prepare_image_input(resolved_garment)
        styling_prompt = self.build_prompt(
            prompt=prompt,
            garment_description=garment_description,
        )

        payload = self.create_virtual_try_on_payload(
            person=person_prepared,
            garment=garment_prepared,
            prompt=styling_prompt,
            seed=seed,
            safety_tolerance=safety_tolerance,
            output_format=output_format,
            **kwargs,
        )

        try:
            response = requests.post(
                self.endpoint,
                headers=self.headers,
                json=payload,
                timeout=300,
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
            raise ValueError(
                f"BFL FLUX VTO API HTTP error ({e.response.status_code}): {error_msg}"
            )
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Failed to connect to BFL FLUX VTO API: {str(e)}")

        task_id = response_data.get("id", "unknown")
        polling_url = response_data.get(
            "polling_url",
            f"{self.base_url}/v1/get_result?id={task_id}",
        )
        completed_task = self._poll_task(task_id, polling_url, max_wait_time=max_wait_time)
        return self._extract_result_sample(completed_task)

    def generate_and_decode(
        self,
        person: Optional[Union[str, io.BytesIO, Image.Image]] = None,
        garment: Optional[Union[str, io.BytesIO, Image.Image]] = None,
        *,
        source_image: Optional[Union[str, io.BytesIO, Image.Image]] = None,
        reference_image: Optional[Union[str, io.BytesIO, Image.Image]] = None,
        model_image: Optional[Union[str, io.BytesIO, Image.Image]] = None,
        cloth_image: Optional[Union[str, io.BytesIO, Image.Image]] = None,
        person_image: Optional[Union[str, io.BytesIO, Image.Image]] = None,
        garment_image: Optional[Union[str, io.BytesIO, Image.Image]] = None,
        prompt: Optional[str] = None,
        garment_description: Optional[str] = None,
        seed: Optional[int] = None,
        safety_tolerance: int = 2,
        output_format: str = "webp",
        max_wait_time: int = 300,
        **kwargs,
    ) -> List[Image.Image]:
        """
        Generate virtual try-on images and decode them to PIL Image objects.

        Args:
            person: Person/model image.
            garment: Garment reference image.
            source_image: Alias for person.
            reference_image: Alias for garment.
            model_image: Alias for person.
            cloth_image: Alias for garment.
            person_image: Alias for person.
            garment_image: Alias for garment.
            prompt: Full styling prompt.
            garment_description: Concise garment description used to build the prompt.
            seed: Optional seed for reproducibility.
            safety_tolerance: Moderation strictness from 0 to 5. Default: 2.
            output_format: Output format: 'jpeg', 'png', or 'webp'. Default: 'webp'.
            max_wait_time: Maximum polling time in seconds. Default: 300.
            **kwargs: Additional API parameters such as webhook_url or webhook_secret.

        Returns:
            List[Image.Image]: Decoded try-on result images.
        """
        sample = self.generate(
            person=person,
            garment=garment,
            source_image=source_image,
            reference_image=reference_image,
            model_image=model_image,
            cloth_image=cloth_image,
            person_image=person_image,
            garment_image=garment_image,
            prompt=prompt,
            garment_description=garment_description,
            seed=seed,
            safety_tolerance=safety_tolerance,
            output_format=output_format,
            max_wait_time=max_wait_time,
            **kwargs,
        )
        return [self._decode_sample(sample)]
