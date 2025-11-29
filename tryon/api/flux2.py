import os
import base64
import binascii
import json
import io
import logging
import requests
import time
from typing import Optional, Union, List, Literal, Dict, Any
from PIL import Image

# Configure logger
logger = logging.getLogger(__name__)


class _Flux2BaseAdapter:
    """
    Base class for FLUX.2 adapters with shared functionality.
    
    This class contains all common methods and constants used by both
    Flux2ProAdapter and Flux2FlexAdapter to eliminate code duplication.
    """
    
    # Constants
    BASE_URL = "https://api.bfl.ai"
    MIN_DIMENSION = 64
    MAX_IMAGES = 8
    DEFAULT_TIMEOUT = 300  # 5 minutes
    POLL_INTERVAL = 2  # seconds
    POLL_TIMEOUT = 30  # seconds for individual poll requests
    MIN_GUIDANCE = 1.5
    MAX_GUIDANCE = 10.0
    MIN_SAFETY_TOLERANCE = 0
    MAX_SAFETY_TOLERANCE = 5
    VALID_OUTPUT_FORMATS = ("jpeg", "png")
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, endpoint: str = ""):
        """
        Initialize the FLUX.2 client base.
        
        Args:
            api_key: BFL API key. Defaults to BFL_API_KEY environment variable.
            base_url: Base URL for BFL API. Defaults to BASE_URL constant if not set.
            endpoint: API endpoint path (e.g., "/v1/flux-2-pro").
        
        Raises:
            ValueError: If API key is not provided.
        """
        self.api_key = api_key or os.getenv("BFL_API_KEY")
        if not self.api_key:
            raise ValueError(
                "BFL API key is required. Set BFL_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        self.base_url = base_url or self.BASE_URL
        self.endpoint = f"{self.base_url}{endpoint}"
        
        # Default headers
        self.headers = {
            "x-key": self.api_key,
            "Content-Type": "application/json"
        }
    
    def _validate_dimensions(self, width: Optional[int], height: Optional[int]) -> None:
        """
        Validate image dimensions.
        
        Args:
            width: Image width (optional)
            height: Image height (optional)
        
        Raises:
            ValueError: If dimensions are invalid.
        """
        if width is not None and width < self.MIN_DIMENSION:
            raise ValueError(f"Width must be at least {self.MIN_DIMENSION} pixels, got {width}")
        if height is not None and height < self.MIN_DIMENSION:
            raise ValueError(f"Height must be at least {self.MIN_DIMENSION} pixels, got {height}")
    
    def _validate_safety_tolerance(self, tolerance: int) -> None:
        """
        Validate safety tolerance value.
        
        Args:
            tolerance: Safety tolerance level (0-5)
        
        Raises:
            ValueError: If tolerance is out of range.
        """
        if not isinstance(tolerance, int) or tolerance < self.MIN_SAFETY_TOLERANCE or tolerance > self.MAX_SAFETY_TOLERANCE:
            raise ValueError(
                f"Safety tolerance must be an integer between {self.MIN_SAFETY_TOLERANCE} "
                f"and {self.MAX_SAFETY_TOLERANCE}, got {tolerance}"
            )
    
    def _validate_output_format(self, output_format: str) -> None:
        """
        Validate output format.
        
        Args:
            output_format: Output format string
        
        Raises:
            ValueError: If format is invalid.
        """
        if output_format.lower() not in self.VALID_OUTPUT_FORMATS:
            raise ValueError(
                f"Output format must be one of {self.VALID_OUTPUT_FORMATS}, got '{output_format}'"
            )
    
    def _validate_prompt(self, prompt: str) -> None:
        """
        Validate prompt string.
        
        Args:
            prompt: Prompt text
        
        Raises:
            ValueError: If prompt is empty or invalid.
        """
        if not prompt or not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("Prompt cannot be empty")
    
    def _validate_images_list(self, images: List[Any]) -> None:
        """
        Validate images list.
        
        Args:
            images: List of images
        
        Raises:
            ValueError: If images list is invalid.
        """
        if not images:
            raise ValueError("At least one image is required")
        if len(images) > self.MAX_IMAGES:
            raise ValueError(f"Maximum {self.MAX_IMAGES} input images supported, got {len(images)}")
    
    def _prepare_image_input(self, image_input: Union[str, io.BytesIO, Image.Image]) -> str:
        """
        Prepare image input for API request.
        
        Handles file paths, file-like objects, PIL Images, URLs, and base64 strings.
        For local files and file-like objects, converts to base64.
        URLs and base64 strings are passed as-is.
        
        Args:
            image_input: Image input in one of the following formats:
                       - File path (str): Path to local image file
                       - URL (str): HTTP/HTTPS URL to image (starts with http:// or https://)
                       - Base64 string (str): Base64-encoded image data
                       - File-like object (io.BytesIO): BytesIO or similar object
                       - PIL Image (Image.Image): PIL Image object
        
        Returns:
            str: URL string (if input is URL) or base64-encoded string (if input is file/base64)
        
        Raises:
            ValueError: If image input format is invalid.
            FileNotFoundError: If file path doesn't exist.
        """
        # Handle PIL Image
        if isinstance(image_input, Image.Image):
            buffer = io.BytesIO()
            image_input.save(buffer, format='PNG')
            buffer.seek(0)
            return base64.b64encode(buffer.read()).decode('utf-8')
        
        # Handle file-like object
        if hasattr(image_input, 'read'):
            image_file = image_input
            image_file.seek(0)
            image_bytes = image_file.read()
            image_file.seek(0)
            return base64.b64encode(image_bytes).decode('utf-8')
        
        # Handle string (file path, URL, or base64)
        if isinstance(image_input, str):
            # Check if it's a URL
            if image_input.startswith(("http://", "https://")):
                return image_input
            
            # Check if it's already base64
            if len(image_input) > 100 and not os.path.exists(image_input):
                # Likely base64 string
                try:
                    # Try to decode to verify
                    base64.b64decode(image_input[:100])
                    return image_input
                except (ValueError, binascii.Error):
                    pass
            
            # It's a file path
            if not os.path.exists(image_input):
                raise FileNotFoundError(f"Image file not found: {image_input}")
            with open(image_input, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode("utf-8")
        
        raise ValueError(
            "Invalid image input: must be a file path, URL, file-like object, PIL Image, or base64 string"
        )
    
    def _poll_task(self, task_id: str, polling_url: str, max_wait_time: int = DEFAULT_TIMEOUT) -> Dict[str, Any]:
        """
        Poll task status until completion.
        
        Args:
            task_id: Task ID returned from API
            polling_url: URL to poll for task status
            max_wait_time: Maximum time to wait in seconds. Default: DEFAULT_TIMEOUT (5 minutes)
        
        Returns:
            dict: Task result containing image data
        
        Raises:
            ValueError: If task fails or times out.
            requests.exceptions.RequestException: If polling request fails.
        """
        start_time = time.time()
        
        while True:
            # Check timeout
            elapsed_time = time.time() - start_time
            if elapsed_time > max_wait_time:
                raise ValueError(
                    f"Task {task_id} timed out after {max_wait_time} seconds."
                )
            
            # Poll task status
            try:
                response = requests.get(
                    polling_url,
                    headers={"x-key": self.api_key},
                    timeout=self.POLL_TIMEOUT
                )
                response.raise_for_status()
                task_data = response.json()
            except requests.exceptions.HTTPError as e:
                raise ValueError(
                    f"Failed to poll task status: HTTP {e.response.status_code} - {e.response.text}"
                )
            except requests.exceptions.RequestException as e:
                raise ValueError(f"Failed to poll task status: {str(e)}")
            
            # Check task status
            status = task_data.get("status", "").lower()
            
            if status == "completed" or status == "succeed":
                # Task completed successfully
                logger.info(f"Task {task_id} completed successfully")
                return task_data
            elif status == "failed" or status == "fail":
                error_msg = task_data.get("error", {}).get("message", "Unknown error")
                raise ValueError(f"Task {task_id} failed: {error_msg}")
            elif status in ["pending", "processing", "submitted"]:
                # Task still in progress
                elapsed_minutes = int(elapsed_time / 60)
                elapsed_seconds = int(elapsed_time % 60)
                logger.info(
                    f"Task {task_id} status: {status} "
                    f"(elapsed: {elapsed_minutes}m {elapsed_seconds}s)..."
                )
                time.sleep(self.POLL_INTERVAL)
            else:
                raise ValueError(f"Unknown task status: {status}")
    
    def _extract_images_from_response(self, response_data: Dict[str, Any]) -> List[str]:
        """
        Extract image data from API response.
        
        Args:
            response_data: Response data from API
        
        Returns:
            List[str]: List of image data (base64 strings or URLs)
        """
        images = []
        
        # Check for direct image data
        if "image" in response_data:
            images.append(response_data["image"])
        elif "images" in response_data:
            if isinstance(response_data["images"], list):
                images.extend(response_data["images"])
            else:
                images.append(response_data["images"])
        
        # Check for image URL
        if "image_url" in response_data:
            images.append(response_data["image_url"])
        elif "image_urls" in response_data:
            if isinstance(response_data["image_urls"], list):
                images.extend(response_data["image_urls"])
            else:
                images.append(response_data["image_urls"])
        
        return images
    
    def _decode_images(self, image_data_list: List[str]) -> List[Image.Image]:
        """
        Decode image data to PIL Image objects.
        
        Handles both base64-encoded images and image URLs.
        
        Args:
            image_data_list: List of image data (base64 strings or URLs)
        
        Returns:
            List[Image.Image]: List of PIL Image objects
        
        Raises:
            ValueError: If image decoding fails.
            requests.exceptions.RequestException: If fetching image from URL fails.
        """
        decoded_images = []
        for image_data in image_data_list:
            try:
                if isinstance(image_data, str) and image_data.startswith(("http://", "https://")):
                    # Fetch image from URL
                    img_response = requests.get(image_data, timeout=self.POLL_TIMEOUT)
                    img_response.raise_for_status()
                    image_bytes = img_response.content
                elif isinstance(image_data, str):
                    # Decode base64
                    image_bytes = base64.b64decode(image_data)
                else:
                    image_bytes = image_data if isinstance(image_data, bytes) else str(image_data).encode()
                
                image_buffer = io.BytesIO(image_bytes)
                image = Image.open(image_buffer)
                decoded_images.append(image)
            except (ValueError, binascii.Error) as e:
                raise ValueError(f"Failed to decode image data: {str(e)}")
            except requests.exceptions.RequestException as e:
                raise ValueError(f"Failed to fetch image from URL: {str(e)}")
            except Exception as e:
                raise ValueError(f"Failed to process image: {str(e)}")
        
        return decoded_images
    
    def _make_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make API request and handle response.
        
        Args:
            payload: Request payload dictionary
        
        Returns:
            dict: Response data from API
        
        Raises:
            ValueError: If API request fails or returns an error.
        """
        try:
            response = requests.post(
                self.endpoint,
                headers=self.headers,
                json=payload,
                timeout=self.DEFAULT_TIMEOUT
            )
            response.raise_for_status()
            response_data = response.json()
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP {e.response.status_code}"
            try:
                error_data = e.response.json()
                error_msg = error_data.get("detail", str(error_data))
            except (ValueError, json.JSONDecodeError):
                error_msg = e.response.text or str(e)
            raise ValueError(f"BFL API HTTP error ({e.response.status_code}): {error_msg}")
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Failed to connect to BFL API: {str(e)}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response from API: {str(e)}")
        
        return response_data
    
    def _handle_async_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle async API response by polling if necessary.
        
        Args:
            response_data: Initial response data from API
        
        Returns:
            dict: Final response data (after polling if needed)
        """
        if "polling_url" in response_data:
            task_id = response_data.get("id", "unknown")
            polling_url = response_data["polling_url"]
            response_data = self._poll_task(task_id, polling_url)
        return response_data


class Flux2ProAdapter(_Flux2BaseAdapter):
    """
    Adapter for FLUX.2 [PRO] image generation API.
    
    FLUX.2 [PRO] is a high-quality image generation model that supports:
    - Text-to-image generation
    - Image editing (prompt + input image)
    - Multi-image composition (up to 8 reference images)
    - Custom width/height control
    - Seed for reproducibility
    - Safety tolerance control
    
    Reference: https://docs.bfl.ai/api-reference/models/generate-or-edit-an-image-with-flux2-[pro]
    
    API endpoint: POST https://api.bfl.ai/v1/flux-2-pro
    
    Authentication:
        Requires API key provided via constructor parameter or environment variable:
        - BFL_API_KEY: Your BFL API key
        The API key is sent in the 'x-key' header.
    
    The API accepts base64-encoded images or URLs. This adapter automatically
    handles file paths by converting them to base64.
    
    Example:
        >>> import os
        >>> os.environ['BFL_API_KEY'] = 'your_api_key'
        >>> adapter = Flux2ProAdapter()
        >>> images = adapter.generate_text_to_image(
        ...     prompt="A stylish fashion model wearing elegant evening wear"
        ... )
        >>> images[0].save("result.png")
        
        >>> # Image editing
        >>> images = adapter.generate_image_edit(
        ...     prompt="Change the outfit to casual streetwear",
        ...     input_image="model.jpg"
        ... )
        
        >>> # Multi-image composition
        >>> images = adapter.generate_multi_image(
        ...     prompt="Combine these clothing styles into a cohesive outfit",
        ...     images=["outfit1.jpg", "outfit2.jpg", "accessories.jpg"]
        ... )
    """
    
    ENDPOINT = "/v1/flux-2-pro"
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize the FLUX.2 [PRO] client.
        
        Args:
            api_key: BFL API key. Defaults to BFL_API_KEY environment variable.
                    If not provided via parameter or environment variable, raises ValueError.
            base_url: Base URL for BFL API. Defaults to 'https://api.bfl.ai' if not set.
        
        Raises:
            ValueError: If API key is not provided.
        
        Example:
            >>> # Using environment variable
            >>> import os
            >>> os.environ['BFL_API_KEY'] = 'your_api_key'
            >>> adapter = Flux2ProAdapter()
            
            >>> # Using parameter
            >>> adapter = Flux2ProAdapter(api_key="your_api_key")
        """
        super().__init__(api_key=api_key, base_url=base_url, endpoint=self.ENDPOINT)
    
    def generate_text_to_image(
        self,
        prompt: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        seed: Optional[int] = None,
        safety_tolerance: int = 2,
        output_format: Literal["jpeg", "png"] = "png",
        **kwargs
    ) -> List[Image.Image]:
        """
        Generate image from text prompt.
        
        Args:
            prompt: Text description of the image to generate
            width: Width of the output image. Minimum: 64. Default: Model default
            height: Height of the output image. Minimum: 64. Default: Model default
            seed: Optional seed for reproducibility
            safety_tolerance: Tolerance level for moderation (0-5). 0 = most strict, 5 = least strict. Default: 2
            output_format: Output format. Options: "jpeg", "png". Default: "png"
            **kwargs: Additional parameters (webhook_url, webhook_secret, etc.)
        
        Returns:
            List[Image.Image]: List of PIL Image objects
        
        Raises:
            ValueError: If parameters are invalid or API request fails.
        
        Example:
            >>> adapter = Flux2ProAdapter()
            >>> images = adapter.generate_text_to_image(
            ...     prompt="A professional fashion model wearing elegant evening wear",
            ...     width=1024,
            ...     height=1024,
            ...     seed=42
            ... )
            >>> images[0].save("result.png")
        """
        # Validate inputs
        self._validate_prompt(prompt)
        self._validate_dimensions(width, height)
        self._validate_safety_tolerance(safety_tolerance)
        self._validate_output_format(output_format)
        
        # Build payload
        payload = {
            "prompt": prompt,
            "safety_tolerance": safety_tolerance,
            "output_format": output_format.lower()
        }
        
        if width is not None:
            payload["width"] = width
        if height is not None:
            payload["height"] = height
        if seed is not None:
            payload["seed"] = seed
        
        payload.update(kwargs)
        
        # Make API request
        response_data = self._make_request(payload)
        
        # Handle async response
        response_data = self._handle_async_response(response_data)
        
        # Extract and decode images
        image_data_list = self._extract_images_from_response(response_data)
        
        if not image_data_list:
            raise ValueError("No images returned from API")
        
        return self._decode_images(image_data_list)
    
    def generate_image_edit(
        self,
        prompt: str,
        input_image: Union[str, io.BytesIO, Image.Image],
        width: Optional[int] = None,
        height: Optional[int] = None,
        seed: Optional[int] = None,
        safety_tolerance: int = 2,
        output_format: Literal["jpeg", "png"] = "png",
        **kwargs
    ) -> List[Image.Image]:
        """
        Generate edited image from prompt and input image.
        
        Args:
            prompt: Text description of how to edit the image
            input_image: Input image (file path, URL, PIL Image, file-like object, or base64)
            width: Width of the output image. Minimum: 64. Default: Model default
            height: Height of the output image. Minimum: 64. Default: Model default
            seed: Optional seed for reproducibility
            safety_tolerance: Tolerance level for moderation (0-5). Default: 2
            output_format: Output format. Options: "jpeg", "png". Default: "png"
            **kwargs: Additional parameters
        
        Returns:
            List[Image.Image]: List of PIL Image objects
        
        Raises:
            ValueError: If parameters are invalid or API request fails.
            FileNotFoundError: If input image file doesn't exist.
        
        Example:
            >>> adapter = Flux2ProAdapter()
            >>> images = adapter.generate_image_edit(
            ...     prompt="Change the outfit to casual streetwear style",
            ...     input_image="model.jpg"
            ... )
        """
        # Validate inputs
        self._validate_prompt(prompt)
        self._validate_dimensions(width, height)
        self._validate_safety_tolerance(safety_tolerance)
        self._validate_output_format(output_format)
        
        # Prepare image input
        image_input = self._prepare_image_input(input_image)
        
        # Build payload
        payload = {
            "prompt": prompt,
            "input_image": image_input,
            "safety_tolerance": safety_tolerance,
            "output_format": output_format.lower()
        }
        
        if width is not None:
            payload["width"] = width
        if height is not None:
            payload["height"] = height
        if seed is not None:
            payload["seed"] = seed
        
        payload.update(kwargs)
        
        # Make API request
        response_data = self._make_request(payload)
        
        # Handle async response
        response_data = self._handle_async_response(response_data)
        
        # Extract and decode images
        image_data_list = self._extract_images_from_response(response_data)
        
        if not image_data_list:
            raise ValueError("No images returned from API")
        
        return self._decode_images(image_data_list)
    
    def generate_multi_image(
        self,
        prompt: str,
        images: List[Union[str, io.BytesIO, Image.Image]],
        width: Optional[int] = None,
        height: Optional[int] = None,
        seed: Optional[int] = None,
        safety_tolerance: int = 2,
        output_format: Literal["jpeg", "png"] = "png",
        **kwargs
    ) -> List[Image.Image]:
        """
        Generate image from multiple input images (composition & style transfer).
        
        Supports up to 8 input images. Use multiple input images to compose
        a new scene or transfer styles from reference images.
        
        Args:
            prompt: Text description of how to combine/transform the images
            images: List of input images (file paths, URLs, PIL Images, file-like objects, or base64)
                   Maximum 8 images supported
            width: Width of the output image. Minimum: 64. Default: Model default
            height: Height of the output image. Minimum: 64. Default: Model default
            seed: Optional seed for reproducibility
            safety_tolerance: Tolerance level for moderation (0-5). Default: 2
            output_format: Output format. Options: "jpeg", "png". Default: "png"
            **kwargs: Additional parameters
        
        Returns:
            List[Image.Image]: List of PIL Image objects
        
        Raises:
            ValueError: If parameters are invalid or API request fails.
        
        Example:
            >>> adapter = Flux2ProAdapter()
            >>> images = adapter.generate_multi_image(
            ...     prompt="Create a fashion catalog layout combining these clothing styles",
            ...     images=["outfit1.jpg", "outfit2.jpg", "accessories.jpg"]
            ... )
        """
        # Validate inputs
        self._validate_prompt(prompt)
        self._validate_images_list(images)
        self._validate_dimensions(width, height)
        self._validate_safety_tolerance(safety_tolerance)
        self._validate_output_format(output_format)
        
        # Prepare image inputs
        image_inputs = [self._prepare_image_input(img) for img in images]
        
        # Build payload
        payload = {
            "prompt": prompt,
            "safety_tolerance": safety_tolerance,
            "output_format": output_format.lower()
        }
        
        # Add images to payload (input_image, input_image_2, ..., input_image_8)
        for idx, img_input in enumerate(image_inputs):
            if idx == 0:
                payload["input_image"] = img_input
            else:
                payload[f"input_image_{idx + 1}"] = img_input
        
        if width is not None:
            payload["width"] = width
        if height is not None:
            payload["height"] = height
        if seed is not None:
            payload["seed"] = seed
        
        payload.update(kwargs)
        
        # Make API request
        response_data = self._make_request(payload)
        
        # Handle async response
        response_data = self._handle_async_response(response_data)
        
        # Extract and decode images
        image_data_list = self._extract_images_from_response(response_data)
        
        if not image_data_list:
            raise ValueError("No images returned from API")
        
        return self._decode_images(image_data_list)


class Flux2FlexAdapter(_Flux2BaseAdapter):
    """
    Adapter for FLUX.2 [FLEX] image generation API.
    
    FLUX.2 [FLEX] is a flexible image generation model with additional controls:
    - Text-to-image generation with prompt upsampling
    - Image editing (prompt + input image)
    - Multi-image composition (up to 8 reference images)
    - Custom width/height control
    - Guidance scale control (1.5-10)
    - Steps control for generation
    - Seed for reproducibility
    - Safety tolerance control
    
    Reference: https://docs.bfl.ai/api-reference/models/generate-or-edit-an-image-with-flux2-[flex]
    
    API endpoint: POST https://api.bfl.ai/v1/flux-2-flex
    
    Authentication:
        Requires API key provided via constructor parameter or environment variable:
        - BFL_API_KEY: Your BFL API key
        The API key is sent in the 'x-key' header.
    
    Example:
        >>> import os
        >>> os.environ['BFL_API_KEY'] = 'your_api_key'
        >>> adapter = Flux2FlexAdapter()
        >>> images = adapter.generate_text_to_image(
        ...     prompt="A stylish fashion model wearing elegant evening wear",
        ...     guidance=7.5,
        ...     steps=50
        ... )
    """
    
    ENDPOINT = "/v1/flux-2-flex"
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize the FLUX.2 [FLEX] client.
        
        Args:
            api_key: BFL API key. Defaults to BFL_API_KEY environment variable.
            base_url: Base URL for BFL API. Defaults to 'https://api.bfl.ai' if not set.
        
        Raises:
            ValueError: If API key is not provided.
        """
        super().__init__(api_key=api_key, base_url=base_url, endpoint=self.ENDPOINT)
    
    def _validate_guidance(self, guidance: float) -> None:
        """
        Validate guidance scale value.
        
        Args:
            guidance: Guidance scale (1.5-10)
        
        Raises:
            ValueError: If guidance is out of range.
        """
        if guidance < self.MIN_GUIDANCE or guidance > self.MAX_GUIDANCE:
            raise ValueError(
                f"Guidance must be between {self.MIN_GUIDANCE} and {self.MAX_GUIDANCE}, got {guidance}"
            )
    
    def generate_text_to_image(
        self,
        prompt: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        seed: Optional[int] = None,
        guidance: float = 3.5,
        steps: int = 28,
        prompt_upsampling: bool = True,
        safety_tolerance: int = 2,
        output_format: Literal["jpeg", "png"] = "png",
        **kwargs
    ) -> List[Image.Image]:
        """
        Generate image from text prompt with advanced controls.
        
        Args:
            prompt: Text description of the image to generate
            width: Width of the output image. Minimum: 64. Default: Model default
            height: Height of the output image. Minimum: 64. Default: Model default
            seed: Optional seed for reproducibility
            guidance: Guidance scale (1.5-10). Higher values = more adherence to prompt. Default: 3.5
            steps: Number of generation steps. Default: 28
            prompt_upsampling: Whether to use prompt upsampling. Default: True
            safety_tolerance: Tolerance level for moderation (0-5). Default: 2
            output_format: Output format. Options: "jpeg", "png". Default: "png"
            **kwargs: Additional parameters (webhook_url, webhook_secret, input_image_blob_path, etc.)
        
        Returns:
            List[Image.Image]: List of PIL Image objects
        
        Raises:
            ValueError: If parameters are invalid or API request fails.
        
        Example:
            >>> adapter = Flux2FlexAdapter()
            >>> images = adapter.generate_text_to_image(
            ...     prompt="A professional fashion model wearing elegant evening wear",
            ...     width=1024,
            ...     height=1024,
            ...     guidance=7.5,
            ...     steps=50,
            ...     seed=42
            ... )
        """
        # Validate inputs
        self._validate_prompt(prompt)
        self._validate_dimensions(width, height)
        self._validate_guidance(guidance)
        self._validate_safety_tolerance(safety_tolerance)
        self._validate_output_format(output_format)
        
        # Build payload
        payload = {
            "prompt": prompt,
            "prompt_upsampling": prompt_upsampling,
            "guidance": guidance,
            "steps": steps,
            "safety_tolerance": safety_tolerance,
            "output_format": output_format.lower()
        }
        
        if width is not None:
            payload["width"] = width
        if height is not None:
            payload["height"] = height
        if seed is not None:
            payload["seed"] = seed
        
        payload.update(kwargs)
        
        # Make API request
        response_data = self._make_request(payload)
        
        # Handle async response
        response_data = self._handle_async_response(response_data)
        
        # Extract and decode images
        image_data_list = self._extract_images_from_response(response_data)
        
        if not image_data_list:
            raise ValueError("No images returned from API")
        
        return self._decode_images(image_data_list)
    
    def generate_image_edit(
        self,
        prompt: str,
        input_image: Union[str, io.BytesIO, Image.Image],
        width: Optional[int] = None,
        height: Optional[int] = None,
        seed: Optional[int] = None,
        guidance: float = 3.5,
        steps: int = 28,
        prompt_upsampling: bool = True,
        safety_tolerance: int = 2,
        output_format: Literal["jpeg", "png"] = "png",
        **kwargs
    ) -> List[Image.Image]:
        """
        Generate edited image from prompt and input image with advanced controls.
        
        Args:
            prompt: Text description of how to edit the image
            input_image: Input image (file path, URL, PIL Image, file-like object, or base64)
            width: Width of the output image. Minimum: 64. Default: Model default
            height: Height of the output image. Minimum: 64. Default: Model default
            seed: Optional seed for reproducibility
            guidance: Guidance scale (1.5-10). Default: 3.5
            steps: Number of generation steps. Default: 28
            prompt_upsampling: Whether to use prompt upsampling. Default: True
            safety_tolerance: Tolerance level for moderation (0-5). Default: 2
            output_format: Output format. Options: "jpeg", "png". Default: "png"
            **kwargs: Additional parameters
        
        Returns:
            List[Image.Image]: List of PIL Image objects
        
        Raises:
            ValueError: If parameters are invalid or API request fails.
            FileNotFoundError: If input image file doesn't exist.
        """
        # Validate inputs
        self._validate_prompt(prompt)
        self._validate_dimensions(width, height)
        self._validate_guidance(guidance)
        self._validate_safety_tolerance(safety_tolerance)
        self._validate_output_format(output_format)
        
        # Prepare image input
        image_input = self._prepare_image_input(input_image)
        
        # Build payload
        payload = {
            "prompt": prompt,
            "input_image": image_input,
            "prompt_upsampling": prompt_upsampling,
            "guidance": guidance,
            "steps": steps,
            "safety_tolerance": safety_tolerance,
            "output_format": output_format.lower()
        }
        
        if width is not None:
            payload["width"] = width
        if height is not None:
            payload["height"] = height
        if seed is not None:
            payload["seed"] = seed
        
        payload.update(kwargs)
        
        # Make API request
        response_data = self._make_request(payload)
        
        # Handle async response
        response_data = self._handle_async_response(response_data)
        
        # Extract and decode images
        image_data_list = self._extract_images_from_response(response_data)
        
        if not image_data_list:
            raise ValueError("No images returned from API")
        
        return self._decode_images(image_data_list)
    
    def generate_multi_image(
        self,
        prompt: str,
        images: List[Union[str, io.BytesIO, Image.Image]],
        width: Optional[int] = None,
        height: Optional[int] = None,
        seed: Optional[int] = None,
        guidance: float = 3.5,
        steps: int = 28,
        prompt_upsampling: bool = True,
        safety_tolerance: int = 2,
        output_format: Literal["jpeg", "png"] = "png",
        **kwargs
    ) -> List[Image.Image]:
        """
        Generate image from multiple input images with advanced controls.
        
        Supports up to 8 input images for composition and style transfer.
        
        Args:
            prompt: Text description of how to combine/transform the images
            images: List of input images (file paths, URLs, PIL Images, file-like objects, or base64)
                   Maximum 8 images supported
            width: Width of the output image. Minimum: 64. Default: Model default
            height: Height of the output image. Minimum: 64. Default: Model default
            seed: Optional seed for reproducibility
            guidance: Guidance scale (1.5-10). Default: 3.5
            steps: Number of generation steps. Default: 28
            prompt_upsampling: Whether to use prompt upsampling. Default: True
            safety_tolerance: Tolerance level for moderation (0-5). Default: 2
            output_format: Output format. Options: "jpeg", "png". Default: "png"
            **kwargs: Additional parameters
        
        Returns:
            List[Image.Image]: List of PIL Image objects
        
        Raises:
            ValueError: If parameters are invalid or API request fails.
        
        Example:
            >>> adapter = Flux2FlexAdapter()
            >>> images = adapter.generate_multi_image(
            ...     prompt="Combine these fashion styles into a cohesive outfit",
            ...     images=["outfit1.jpg", "outfit2.jpg"],
            ...     guidance=7.5,
            ...     steps=50
            ... )
        """
        # Validate inputs
        self._validate_prompt(prompt)
        self._validate_images_list(images)
        self._validate_dimensions(width, height)
        self._validate_guidance(guidance)
        self._validate_safety_tolerance(safety_tolerance)
        self._validate_output_format(output_format)
        
        # Prepare image inputs
        image_inputs = [self._prepare_image_input(img) for img in images]
        
        # Build payload
        payload = {
            "prompt": prompt,
            "prompt_upsampling": prompt_upsampling,
            "guidance": guidance,
            "steps": steps,
            "safety_tolerance": safety_tolerance,
            "output_format": output_format.lower()
        }
        
        # Add images to payload
        for idx, img_input in enumerate(image_inputs):
            if idx == 0:
                payload["input_image"] = img_input
            else:
                payload[f"input_image_{idx + 1}"] = img_input
        
        if width is not None:
            payload["width"] = width
        if height is not None:
            payload["height"] = height
        if seed is not None:
            payload["seed"] = seed
        
        payload.update(kwargs)
        
        # Make API request
        response_data = self._make_request(payload)
        
        # Handle async response
        response_data = self._handle_async_response(response_data)
        
        # Extract and decode images
        image_data_list = self._extract_images_from_response(response_data)
        
        if not image_data_list:
            raise ValueError("No images returned from API")
        
        return self._decode_images(image_data_list)
