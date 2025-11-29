import os
import base64
import json
import io
import requests
import time
from typing import Optional, Union, List
from PIL import Image


class Flux2ProAdapter:
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
    
    BASE_URL = "https://api.bfl.ai"
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
        self.api_key = api_key or os.getenv("BFL_API_KEY")
        if not self.api_key:
            raise ValueError(
                "BFL API key is required. Set BFL_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        self.base_url = base_url or self.BASE_URL
        self.endpoint = f"{self.base_url}{self.ENDPOINT}"
        
        # Default headers
        self.headers = {
            "x-key": self.api_key,
            "Content-Type": "application/json"
        }
    
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
                except:
                    pass
            
            # It's a file path
            with open(image_input, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode("utf-8")
        
        raise ValueError("Invalid image input: must be a file path, URL, file-like object, PIL Image, or base64 string")
    
    def _poll_task(self, task_id: str, polling_url: str, max_wait_time: int = 300) -> dict:
        """
        Poll task status until completion.
        
        Args:
            task_id: Task ID returned from API
            polling_url: URL to poll for task status
            max_wait_time: Maximum time to wait in seconds. Default: 300 (5 minutes)
        
        Returns:
            dict: Task result containing image data
        
        Raises:
            ValueError: If task fails or times out
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
                    timeout=30
                )
                response.raise_for_status()
                task_data = response.json()
            except requests.exceptions.RequestException as e:
                raise ValueError(f"Failed to poll task status: {str(e)}")
            
            # Check task status (BFL API uses capitalized status values)
            status_raw = task_data.get("status", "")
            status = status_raw.lower()
            
            # BFL API uses "Ready" (capitalized) to indicate task completion
            # Also check for common variations
            if status_raw == "Ready" or status == "completed" or status == "succeed" or status == "ready":
                # Task completed successfully
                return task_data
            elif status_raw == "Error" or status_raw == "Failed" or status == "failed" or status == "fail" or status == "error":
                error_msg = task_data.get("error", {}).get("message", "Unknown error")
                if not error_msg or error_msg == "Unknown error":
                    # Try alternative error message locations
                    error_msg = task_data.get("message", str(task_data.get("error", "Unknown error")))
                raise ValueError(f"Task {task_id} failed: {error_msg}")
            elif status in ["pending", "processing", "submitted", "request moderated", "content moderated"]:
                # Task still in progress
                elapsed_minutes = int(elapsed_time / 60)
                elapsed_seconds = int(elapsed_time % 60)
                print(
                    f"Task {task_id} status: {status_raw} "
                    f"(elapsed: {elapsed_minutes}m {elapsed_seconds}s)..."
                )
                time.sleep(0.5)  # Wait 0.5 seconds before next poll (as per BFL API polling example)
            elif status == "task not found":
                raise ValueError(f"Task {task_id} not found. It may have expired or been deleted.")
            else:
                raise ValueError(f"Unknown task status: {status_raw}. Response data: {task_data}")
    
    def _extract_images_from_response(self, response_data: dict) -> List[str]:
        """
        Extract image data from API response.
        
        BFL API returns images in result.sample when status is "Ready":
        - {"status": "Ready", "result": {"sample": "base64_string_or_url"}}
        - Also supports other formats for compatibility
        
        Args:
            response_data: Response data from API
        
        Returns:
            List[str]: List of base64-encoded image strings or URLs
        """
        images = []
        
        # BFL API uses result.sample for image data when status is "Ready"
        if "result" in response_data and isinstance(response_data["result"], dict):
            result = response_data["result"]
            # Check for result.sample first (BFL API standard)
            if "sample" in result:
                sample_data = result["sample"]
                if isinstance(sample_data, list):
                    images.extend(sample_data)
                else:
                    images.append(sample_data)
            # Also check for other common formats
            if "image" in result:
                images.append(result["image"])
            elif "images" in result:
                if isinstance(result["images"], list):
                    images.extend(result["images"])
                else:
                    images.append(result["images"])
            if "image_url" in result:
                images.append(result["image_url"])
            elif "image_urls" in result:
                if isinstance(result["image_urls"], list):
                    images.extend(result["image_urls"])
                else:
                    images.append(result["image_urls"])
        
        if "data" in response_data and isinstance(response_data["data"], dict):
            data = response_data["data"]
            if "image" in data:
                images.append(data["image"])
            elif "images" in data:
                if isinstance(data["images"], list):
                    images.extend(data["images"])
                else:
                    images.append(data["images"])
            if "image_url" in data:
                images.append(data["image_url"])
            elif "image_urls" in data:
                if isinstance(data["image_urls"], list):
                    images.extend(data["image_urls"])
                else:
                    images.append(data["image_urls"])
        
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
    
    def generate_text_to_image(
        self,
        prompt: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        seed: Optional[int] = None,
        safety_tolerance: int = 2,
        output_format: str = "png",
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
        # Build payload
        payload = {
            "prompt": prompt,
            "safety_tolerance": safety_tolerance,
            "output_format": output_format
        }
        
        if width is not None:
            payload["width"] = width
        if height is not None:
            payload["height"] = height
        if seed is not None:
            payload["seed"] = seed
        
        payload.update(kwargs)
        
        # Make API request
        try:
            response = requests.post(
                self.endpoint,
                headers=self.headers,
                json=payload,
                timeout=300
            )
            response.raise_for_status()
            response_data = response.json()
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP {e.response.status_code}"
            try:
                error_data = e.response.json()
                error_msg = error_data.get("detail", str(error_data))
            except:
                error_msg = e.response.text or str(e)
            raise ValueError(f"BFL API HTTP error ({e.response.status_code}): {error_msg}")
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Failed to connect to BFL API: {str(e)}")
        
        # Handle async response
        if "polling_url" in response_data:
            task_id = response_data.get("id", "unknown")
            polling_url = response_data["polling_url"]
            response_data = self._poll_task(task_id, polling_url)
        
        # Extract images
        image_data_list = self._extract_images_from_response(response_data)
        
        if not image_data_list:
            raise ValueError("No images returned from API")
        
        # Decode images
        decoded_images = []
        for image_data in image_data_list:
            if isinstance(image_data, str) and image_data.startswith(("http://", "https://")):
                # Fetch image from URL
                img_response = requests.get(image_data)
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
        
        return decoded_images
    
    def generate_image_edit(
        self,
        prompt: str,
        input_image: Union[str, io.BytesIO, Image.Image],
        width: Optional[int] = None,
        height: Optional[int] = None,
        seed: Optional[int] = None,
        safety_tolerance: int = 2,
        output_format: str = "png",
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
        
        Example:
            >>> adapter = Flux2ProAdapter()
            >>> images = adapter.generate_image_edit(
            ...     prompt="Change the outfit to casual streetwear style",
            ...     input_image="model.jpg"
            ... )
        """
        # Prepare image input
        image_input = self._prepare_image_input(input_image)
        
        # Build payload
        payload = {
            "prompt": prompt,
            "input_image": image_input,
            "safety_tolerance": safety_tolerance,
            "output_format": output_format
        }
        
        if width is not None:
            payload["width"] = width
        if height is not None:
            payload["height"] = height
        if seed is not None:
            payload["seed"] = seed
        
        payload.update(kwargs)
        
        # Make API request
        try:
            response = requests.post(
                self.endpoint,
                headers=self.headers,
                json=payload,
                timeout=300
            )
            response.raise_for_status()
            response_data = response.json()
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP {e.response.status_code}"
            try:
                error_data = e.response.json()
                error_msg = error_data.get("detail", str(error_data))
            except:
                error_msg = e.response.text or str(e)
            raise ValueError(f"BFL API HTTP error ({e.response.status_code}): {error_msg}")
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Failed to connect to BFL API: {str(e)}")
        
        # Handle async response
        if "polling_url" in response_data:
            task_id = response_data.get("id", "unknown")
            polling_url = response_data["polling_url"]
            response_data = self._poll_task(task_id, polling_url)
        
        # Extract images
        image_data_list = self._extract_images_from_response(response_data)
        
        if not image_data_list:
            raise ValueError("No images returned from API")
        
        # Decode images
        decoded_images = []
        for image_data in image_data_list:
            if isinstance(image_data, str) and image_data.startswith(("http://", "https://")):
                img_response = requests.get(image_data)
                img_response.raise_for_status()
                image_bytes = img_response.content
            elif isinstance(image_data, str):
                image_bytes = base64.b64decode(image_data)
            else:
                image_bytes = image_data if isinstance(image_data, bytes) else str(image_data).encode()
            
            image_buffer = io.BytesIO(image_bytes)
            image = Image.open(image_buffer)
            decoded_images.append(image)
        
        return decoded_images
    
    def generate_multi_image(
        self,
        prompt: str,
        images: List[Union[str, io.BytesIO, Image.Image]],
        width: Optional[int] = None,
        height: Optional[int] = None,
        seed: Optional[int] = None,
        safety_tolerance: int = 2,
        output_format: str = "png",
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
        
        Example:
            >>> adapter = Flux2ProAdapter()
            >>> images = adapter.generate_multi_image(
            ...     prompt="Create a fashion catalog layout combining these clothing styles",
            ...     images=["outfit1.jpg", "outfit2.jpg", "accessories.jpg"]
            ... )
        """
        if len(images) > 8:
            raise ValueError("Maximum 8 input images supported")
        
        # Prepare image inputs
        image_inputs = [self._prepare_image_input(img) for img in images]
        
        # Build payload
        payload = {
            "prompt": prompt,
            "safety_tolerance": safety_tolerance,
            "output_format": output_format
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
        try:
            response = requests.post(
                self.endpoint,
                headers=self.headers,
                json=payload,
                timeout=300
            )
            response.raise_for_status()
            response_data = response.json()
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP {e.response.status_code}"
            try:
                error_data = e.response.json()
                error_msg = error_data.get("detail", str(error_data))
            except:
                error_msg = e.response.text or str(e)
            raise ValueError(f"BFL API HTTP error ({e.response.status_code}): {error_msg}")
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Failed to connect to BFL API: {str(e)}")
        
        # Handle async response
        if "polling_url" in response_data:
            task_id = response_data.get("id", "unknown")
            polling_url = response_data["polling_url"]
            response_data = self._poll_task(task_id, polling_url)
        
        # Extract images
        image_data_list = self._extract_images_from_response(response_data)
        
        if not image_data_list:
            raise ValueError("No images returned from API")
        
        # Decode images
        decoded_images = []
        for image_data in image_data_list:
            if isinstance(image_data, str) and image_data.startswith(("http://", "https://")):
                img_response = requests.get(image_data)
                img_response.raise_for_status()
                image_bytes = img_response.content
            elif isinstance(image_data, str):
                image_bytes = base64.b64decode(image_data)
            else:
                image_bytes = image_data if isinstance(image_data, bytes) else str(image_data).encode()
            
            image_buffer = io.BytesIO(image_bytes)
            image = Image.open(image_buffer)
            decoded_images.append(image)
        
        return decoded_images


class Flux2FlexAdapter:
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
    
    BASE_URL = "https://api.bfl.ai"
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
        self.api_key = api_key or os.getenv("BFL_API_KEY")
        if not self.api_key:
            raise ValueError(
                "BFL API key is required. Set BFL_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        self.base_url = base_url or self.BASE_URL
        self.endpoint = f"{self.base_url}{self.ENDPOINT}"
        
        # Default headers
        self.headers = {
            "x-key": self.api_key,
            "Content-Type": "application/json"
        }
    
    def _prepare_image_input(self, image_input: Union[str, io.BytesIO, Image.Image]) -> str:
        """Prepare image input for API request (same as Flux2ProAdapter)."""
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
                try:
                    base64.b64decode(image_input[:100])
                    return image_input
                except:
                    pass
            
            # It's a file path
            with open(image_input, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode("utf-8")
        
        raise ValueError("Invalid image input: must be a file path, URL, file-like object, PIL Image, or base64 string")
    
    def _poll_task(self, task_id: str, polling_url: str, max_wait_time: int = 300) -> dict:
        """Poll task status until completion (same as Flux2ProAdapter)."""
        start_time = time.time()
        
        while True:
            elapsed_time = time.time() - start_time
            if elapsed_time > max_wait_time:
                raise ValueError(
                    f"Task {task_id} timed out after {max_wait_time} seconds."
                )
            
            try:
                response = requests.get(
                    polling_url,
                    headers={"x-key": self.api_key},
                    timeout=30
                )
                response.raise_for_status()
                task_data = response.json()
            except requests.exceptions.RequestException as e:
                raise ValueError(f"Failed to poll task status: {str(e)}")
            
            # Check task status (BFL API uses capitalized status values)
            status_raw = task_data.get("status", "")
            status = status_raw.lower()
            
            # BFL API uses "Ready" (capitalized) to indicate task completion
            # Also check for common variations
            if status_raw == "Ready" or status == "completed" or status == "succeed" or status == "ready":
                return task_data
            elif status_raw == "Error" or status_raw == "Failed" or status == "failed" or status == "fail" or status == "error":
                error_msg = task_data.get("error", {}).get("message", "Unknown error")
                if not error_msg or error_msg == "Unknown error":
                    # Try alternative error message locations
                    error_msg = task_data.get("message", str(task_data.get("error", "Unknown error")))
                raise ValueError(f"Task {task_id} failed: {error_msg}")
            elif status in ["pending", "processing", "submitted", "request moderated", "content moderated"]:
                elapsed_minutes = int(elapsed_time / 60)
                elapsed_seconds = int(elapsed_time % 60)
                print(
                    f"Task {task_id} status: {status_raw} "
                    f"(elapsed: {elapsed_minutes}m {elapsed_seconds}s)..."
                )
                time.sleep(0.5)  # Wait 0.5 seconds before next poll (as per BFL API polling example)
            elif status == "task not found":
                raise ValueError(f"Task {task_id} not found. It may have expired or been deleted.")
            else:
                raise ValueError(f"Unknown task status: {status_raw}. Response data: {task_data}")
    
    def _extract_images_from_response(self, response_data: dict) -> List[str]:
        """
        Extract image data from API response.
        
        BFL API returns images in result.sample when status is "Ready":
        - {"status": "Ready", "result": {"sample": "base64_string_or_url"}}
        - Also supports other formats for compatibility
        
        Args:
            response_data: Response data from API
        
        Returns:
            List[str]: List of base64-encoded image strings or URLs
        """
        images = []
        
        # BFL API uses result.sample for image data when status is "Ready"
        if "result" in response_data and isinstance(response_data["result"], dict):
            result = response_data["result"]
            # Check for result.sample first (BFL API standard)
            if "sample" in result:
                sample_data = result["sample"]
                if isinstance(sample_data, list):
                    images.extend(sample_data)
                else:
                    images.append(sample_data)
            # Also check for other common formats
            if "image" in result:
                images.append(result["image"])
            elif "images" in result:
                if isinstance(result["images"], list):
                    images.extend(result["images"])
                else:
                    images.append(result["images"])
            if "image_url" in result:
                images.append(result["image_url"])
            elif "image_urls" in result:
                if isinstance(result["image_urls"], list):
                    images.extend(result["image_urls"])
                else:
                    images.append(result["image_urls"])
        
        if "data" in response_data and isinstance(response_data["data"], dict):
            data = response_data["data"]
            if "image" in data:
                images.append(data["image"])
            elif "images" in data:
                if isinstance(data["images"], list):
                    images.extend(data["images"])
                else:
                    images.append(data["images"])
            if "image_url" in data:
                images.append(data["image_url"])
            elif "image_urls" in data:
                if isinstance(data["image_urls"], list):
                    images.extend(data["image_urls"])
                else:
                    images.append(data["image_urls"])
        
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
        output_format: str = "png",
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
        # Validate guidance
        if guidance < 1.5 or guidance > 10:
            raise ValueError("guidance must be between 1.5 and 10")
        
        # Build payload
        payload = {
            "prompt": prompt,
            "prompt_upsampling": prompt_upsampling,
            "guidance": guidance,
            "steps": steps,
            "safety_tolerance": safety_tolerance,
            "output_format": output_format
        }
        
        if width is not None:
            payload["width"] = width
        if height is not None:
            payload["height"] = height
        if seed is not None:
            payload["seed"] = seed
        
        payload.update(kwargs)
        
        # Make API request
        try:
            response = requests.post(
                self.endpoint,
                headers=self.headers,
                json=payload,
                timeout=300
            )
            response.raise_for_status()
            response_data = response.json()
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP {e.response.status_code}"
            try:
                error_data = e.response.json()
                error_msg = error_data.get("detail", str(error_data))
            except:
                error_msg = e.response.text or str(e)
            raise ValueError(f"BFL API HTTP error ({e.response.status_code}): {error_msg}")
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Failed to connect to BFL API: {str(e)}")
        
        # Handle async response
        if "polling_url" in response_data:
            task_id = response_data.get("id", "unknown")
            polling_url = response_data["polling_url"]
            response_data = self._poll_task(task_id, polling_url)
        
        # Extract images
        image_data_list = self._extract_images_from_response(response_data)
        
        if not image_data_list:
            raise ValueError("No images returned from API")
        
        # Decode images
        decoded_images = []
        for image_data in image_data_list:
            if isinstance(image_data, str) and image_data.startswith(("http://", "https://")):
                img_response = requests.get(image_data)
                img_response.raise_for_status()
                image_bytes = img_response.content
            elif isinstance(image_data, str):
                image_bytes = base64.b64decode(image_data)
            else:
                image_bytes = image_data if isinstance(image_data, bytes) else str(image_data).encode()
            
            image_buffer = io.BytesIO(image_bytes)
            image = Image.open(image_buffer)
            decoded_images.append(image)
        
        return decoded_images
    
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
        output_format: str = "png",
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
        """
        # Validate guidance
        if guidance < 1.5 or guidance > 10:
            raise ValueError("guidance must be between 1.5 and 10")
        
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
            "output_format": output_format
        }
        
        if width is not None:
            payload["width"] = width
        if height is not None:
            payload["height"] = height
        if seed is not None:
            payload["seed"] = seed
        
        payload.update(kwargs)
        
        # Make API request
        try:
            response = requests.post(
                self.endpoint,
                headers=self.headers,
                json=payload,
                timeout=300
            )
            response.raise_for_status()
            response_data = response.json()
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP {e.response.status_code}"
            try:
                error_data = e.response.json()
                error_msg = error_data.get("detail", str(error_data))
            except:
                error_msg = e.response.text or str(e)
            raise ValueError(f"BFL API HTTP error ({e.response.status_code}): {error_msg}")
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Failed to connect to BFL API: {str(e)}")
        
        # Handle async response
        if "polling_url" in response_data:
            task_id = response_data.get("id", "unknown")
            polling_url = response_data["polling_url"]
            response_data = self._poll_task(task_id, polling_url)
        
        # Extract images
        image_data_list = self._extract_images_from_response(response_data)
        
        if not image_data_list:
            raise ValueError("No images returned from API")
        
        # Decode images
        decoded_images = []
        for image_data in image_data_list:
            if isinstance(image_data, str) and image_data.startswith(("http://", "https://")):
                img_response = requests.get(image_data)
                img_response.raise_for_status()
                image_bytes = img_response.content
            elif isinstance(image_data, str):
                image_bytes = base64.b64decode(image_data)
            else:
                image_bytes = image_data if isinstance(image_data, bytes) else str(image_data).encode()
            
            image_buffer = io.BytesIO(image_bytes)
            image = Image.open(image_buffer)
            decoded_images.append(image)
        
        return decoded_images
    
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
        output_format: str = "png",
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
        """
        if len(images) > 8:
            raise ValueError("Maximum 8 input images supported")
        
        # Validate guidance
        if guidance < 1.5 or guidance > 10:
            raise ValueError("guidance must be between 1.5 and 10")
        
        # Prepare image inputs
        image_inputs = [self._prepare_image_input(img) for img in images]
        
        # Build payload
        payload = {
            "prompt": prompt,
            "prompt_upsampling": prompt_upsampling,
            "guidance": guidance,
            "steps": steps,
            "safety_tolerance": safety_tolerance,
            "output_format": output_format
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
        try:
            response = requests.post(
                self.endpoint,
                headers=self.headers,
                json=payload,
                timeout=300
            )
            response.raise_for_status()
            response_data = response.json()
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP {e.response.status_code}"
            try:
                error_data = e.response.json()
                error_msg = error_data.get("detail", str(error_data))
            except:
                error_msg = e.response.text or str(e)
            raise ValueError(f"BFL API HTTP error ({e.response.status_code}): {error_msg}")
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Failed to connect to BFL API: {str(e)}")
        
        # Handle async response
        if "polling_url" in response_data:
            task_id = response_data.get("id", "unknown")
            polling_url = response_data["polling_url"]
            response_data = self._poll_task(task_id, polling_url)
        
        # Extract images
        image_data_list = self._extract_images_from_response(response_data)
        
        if not image_data_list:
            raise ValueError("No images returned from API")
        
        # Decode images
        decoded_images = []
        for image_data in image_data_list:
            if isinstance(image_data, str) and image_data.startswith(("http://", "https://")):
                img_response = requests.get(image_data)
                img_response.raise_for_status()
                image_bytes = img_response.content
            elif isinstance(image_data, str):
                image_bytes = base64.b64decode(image_data)
            else:
                image_bytes = image_data if isinstance(image_data, bytes) else str(image_data).encode()
            
            image_buffer = io.BytesIO(image_bytes)
            image = Image.open(image_buffer)
            decoded_images.append(image)
        
        return decoded_images

