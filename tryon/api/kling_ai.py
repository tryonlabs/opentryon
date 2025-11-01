import os
import base64
import json
import io
import requests
import time
import jwt
from typing import Optional, Union, List
from PIL import Image


class KlingAIVTONAdapter:
    """
    Adapter for Kling AI Virtual Try-On (VTON) API.
    
    Kling AI supports virtual try-on capabilities that allow you to combine
    two images: a human image (person) and a cloth image (garment/product).
    The model generates realistic results showing the person wearing the garment.
    
    Reference: https://app.klingai.com/global/dev/document-api/apiReference/model/functionalityTry
    
    API endpoint: POST /v1/images/kolors-virtual-try-on
    
    Authentication:
        Requires both API key (access key) and secret key for authentication.
        These can be provided via constructor parameters or environment variables:
        - KLING_AI_API_KEY: Your Kling AI API key (access key)
        - KLING_AI_SECRET_KEY: Your Kling AI secret key
        The adapter automatically generates a JWT token using these credentials
        for API authentication.
    
    The API accepts image URLs or base64-encoded images. This adapter automatically
    handles file paths by converting them to base64, and passes URLs as-is.
    
    Example:
        >>> import os
        >>> os.environ['KLING_AI_API_KEY'] = 'your_api_key'
        >>> os.environ['KLING_AI_SECRET_KEY'] = 'your_secret_key'
        >>> adapter = KlingAIVTONAdapter()
        >>> images = adapter.generate_and_decode(
        ...     source_image="person.jpg",
        ...     reference_image="shirt.jpg"
        ... )
        >>> images[0].save("result.png")
        
        >>> # Using parameters directly
        >>> adapter = KlingAIVTONAdapter(
        ...     api_key="your_api_key",
        ...     secret_key="your_secret_key"
        ... )
        >>> images = adapter.generate_and_decode(
        ...     source_image="person.jpg",
        ...     reference_image="shirt.jpg"
        ... )
    """
    
    MAX_IMAGE_PIXELS = 16_000_000  # Reasonable default, adjust based on Kling AI limits
    MAX_IMAGE_DIMENSION = 4096  # Reasonable default, adjust based on Kling AI limits
    
    def __init__(self, api_key: Optional[str] = None, secret_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize the Kling AI VTON client.
        
        Args:
            api_key: Kling AI API key. Defaults to KLING_AI_API_KEY environment variable.
                    If not provided via parameter or environment variable, raises ValueError.
            secret_key: Kling AI secret key. Defaults to KLING_AI_SECRET_KEY environment variable.
                    If not provided via parameter or environment variable, raises ValueError.
            base_url: Base URL for Kling AI API. Defaults to KLING_AI_BASE_URL environment variable
                     or 'https://api-singapore.klingai.com' if not set.
                     The endpoint path '/v1/images/kolors-virtual-try-on' is automatically appended.
        
        Raises:
            ValueError: If API key or secret key is not provided.
        
        Example:
            >>> # Using environment variable
            >>> import os
            >>> os.environ['KLING_AI_API_KEY'] = 'your_api_key'
            >>> os.environ['KLING_AI_SECRET_KEY'] = 'your_secret_key'
            >>> adapter = KlingAIVTONAdapter()
            
            >>> # Using parameter
            >>> adapter = KlingAIVTONAdapter(api_key="your_api_key", secret_key="your_secret_key")
            
        """
        self.api_key = api_key or os.getenv("KLING_AI_API_KEY")
        self.secret_key = secret_key or os.getenv("KLING_AI_SECRET_KEY")
        if not self.api_key or not self.secret_key:
            raise ValueError(
                "Kling AI API key and secret key are required. Set KLING_AI_API_KEY and KLING_AI_SECRET_KEY environment variables "
                "or pass api_key and secret_key parameters."
            )
        
        self.base_url = base_url or os.getenv("KLING_AI_BASE_URL", "https://api-singapore.klingai.com")
        
        # Based on Kling AI API documentation
        self.endpoint = f"{self.base_url}/v1/images/kolors-virtual-try-on"
        
        # Default headers
        self.headers = {
            "Authorization": f"Bearer {generate_api_token(self.api_key, self.secret_key)}",
            "Content-Type": "application/json"
        }
    
    def validate_image_size(self, image: Image.Image) -> None:
        """
        Validate that image dimensions meet Kling AI requirements.
        
        Args:
            image: PIL Image object to validate
            
        Raises:
            ValueError: If image exceeds size limits
        """
        width, height = image.size
        total_pixels = width * height
        
        if total_pixels > self.MAX_IMAGE_PIXELS:
            raise ValueError(
                f"Image size ({width}x{height} = {total_pixels:,} pixels) exceeds "
                f"maximum allowed ({self.MAX_IMAGE_PIXELS:,} pixels / {self.MAX_IMAGE_DIMENSION}x{self.MAX_IMAGE_DIMENSION}). "
                f"Please resize your image."
            )
        
        if width > self.MAX_IMAGE_DIMENSION or height > self.MAX_IMAGE_DIMENSION:
            raise ValueError(
                f"Image dimensions ({width}x{height}) exceed maximum allowed "
                f"({self.MAX_IMAGE_DIMENSION}x{self.MAX_IMAGE_DIMENSION}). Please resize your image."
            )
    
    def _prepare_image_input(self, image_input: Union[str, io.BytesIO]) -> str:
        """
        Prepare image input for API request.
        
        Handles file paths, file-like objects, URLs, and base64 strings.
        For local files and file-like objects, converts to base64 with validation.
        URLs are passed as-is without modification.
        
        Args:
            image_input: Image input in one of the following formats:
                       - File path (str): Path to local image file
                       - URL (str): HTTP/HTTPS URL to image (starts with http:// or https://)
                       - Base64 string (str): Base64-encoded image data
                       - File-like object (io.BytesIO): BytesIO or similar object
            
        Returns:
            str: URL string (if input is URL) or base64-encoded string (if input is file/base64)
            
        Raises:
            ValueError: If image exceeds size limits or input format is invalid
        """
        # If it's already a URL or base64 string
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
            image = Image.open(image_input)
            self.validate_image_size(image)
            with open(image_input, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode("utf-8")
        
        # It's a file-like object
        if hasattr(image_input, 'read'):
            image_file = image_input
            image_file.seek(0)
            image_bytes = image_file.read()
            image_file.seek(0)
            
            # Validate image size
            image_buffer = io.BytesIO(image_bytes)
            image = Image.open(image_buffer)
            self.validate_image_size(image)
            
            return base64.b64encode(image_bytes).decode("utf-8")
        
        raise ValueError("Invalid image input: must be a file path, URL, file-like object, or base64 string")
    
    def create_virtual_try_on_payload(self, 
                                     human_image: str,
                                     cloth_image: str,
                                     model: Optional[str] = None,
                                     **kwargs) -> dict:
        """
        Create the payload for virtual try-on request based on Kling AI API format.
        
        The payload structure follows Kling AI's API specification:
        - Uses `human_image` parameter for the person image (accepts URL or base64)
        - Uses `cloth_image` parameter for the garment image (accepts URL or base64)
        
        Args:
            human_image: URL (starts with http:// or https://) or base64 string of the human/person image.
            cloth_image: URL (starts with http:// or https://) or base64 string of the cloth/garment image.
                        This will be mapped to 'cloth_image' in the API payload.
            model: Optional model version to use (e.g., 'kolors-virtual-try-on-v1', 'kolors-virtual-try-on-v1-5').
                   If not specified, uses the API default model.
            **kwargs: Additional parameters for Kling AI API:
                     - webhook_url (str, optional): URL to receive async results when task completes
                     - webhook_secret (str, optional): Secret key for webhook authentication
                     - Other parameters as per Kling AI API documentation
            
        Returns:
            dict: Dictionary containing the request payload ready for API call.
                 Structure: {
                     "human_image": ... (URL or base64),
                     "cloth_image": ... (URL or base64),
                     "model": ... (if provided),
                     ...other kwargs
                 }
        """
        # Base payload structure according to Kling AI API
        payload = {}
        
        # Kling AI API uses 'human_image' and 'cloth_image' parameters
        # Both accept URLs or base64 strings
        payload["human_image"] = human_image
        payload["cloth_image"] = cloth_image
        
        # Add optional model parameter
        if model:
            payload["model"] = model
        
        # Add any additional parameters
        payload.update(kwargs)
        
        return payload
    
    def generate(self, 
                 source_image: Union[str, io.BytesIO],
                 reference_image: Union[str, io.BytesIO],
                 model: Optional[str] = None,
                 **kwargs) -> List[str]:
        """
        Generate virtual try-on image(s) using Kling AI API.
        
        This method combines a human image (person/model) with a cloth image (garment/product)
        to create realistic virtual try-on results. Images are automatically validated for size limits.
        
        The method handles multiple input formats:
        - File paths: Automatically converted to base64
        - URLs: Passed directly to API
        - File-like objects: Converted to base64
        - Base64 strings: Used directly
        
        Authentication:
            Uses the API key and secret key provided during adapter initialization
            to generate a JWT token for authentication. The token is automatically
            included in the request headers.
        
        Example:
            >>> import os
            >>> os.environ['KLING_AI_API_KEY'] = 'your_api_key'
            >>> os.environ['KLING_AI_SECRET_KEY'] = 'your_secret_key'
            >>> adapter = KlingAIVTONAdapter()
            >>> images = adapter.generate(
            ...     source_image="person.jpg",
            ...     reference_image="hoodie.jpg"
            ... )
            
            >>> # Using URLs
            >>> adapter = KlingAIVTONAdapter(
            ...     api_key="your_api_key",
            ...     secret_key="your_secret_key"
            ... )
            >>> images = adapter.generate(
            ...     source_image="https://example.com/person.jpg",
            ...     reference_image="https://example.com/garment.jpg",
            ...     model="kolors-virtual-try-on-v1-5"
            ... )
        
        Args:
            source_image: Human/person image in one of these formats:
                         - File path (str): Path to local image file
                         - URL (str): HTTP/HTTPS URL to image
                         - File-like object (io.BytesIO): BytesIO or similar
                         - Base64 string (str): Base64-encoded image
            reference_image: Cloth/garment image in same formats as source_image.
            model: Optional model version to use. Examples:
                   - 'kolors-virtual-try-on-v1'
                   - 'kolors-virtual-try-on-v1-5'
                   If not specified, uses API default.
            **kwargs: Additional parameters for Kling AI API:
                     - webhook_url (str, optional): URL to receive async results when task completes
                     - webhook_secret (str, optional): Secret key for webhook authentication header
                     - Other parameters as per Kling AI API documentation
            
        Returns:
            List[str]: List of generated images. Each item can be:
                      - Base64-encoded string
                      - Image URL (if API returns URLs)
                      The exact format depends on Kling AI API response structure.
            
        Raises:
            ValueError: If images exceed size limits, required parameters are missing,
                       API returns an error, or response format is unexpected.
                       
        Note:
            If the API returns a task_id (async processing), this method will automatically
            poll for task completion until images are available. The polling will continue
            until the task succeeds, fails, or times out (default: 5 minutes).
            
            Authentication is handled automatically using the API key and secret key
            provided during adapter initialization. No additional authentication
            parameters are required for this method.
        """
        try:
            # Prepare image inputs
            human_image = self._prepare_image_input(source_image)
            cloth_image = self._prepare_image_input(reference_image)
            
            # Create payload
            payload = self.create_virtual_try_on_payload(
                human_image=human_image,
                cloth_image=cloth_image,
                model=model,
                **kwargs
            )
            
            # Make API request
            try:
                response = requests.post(
                    self.endpoint,
                    headers=self.headers,
                    json=payload,
                    timeout=300  # 5 minutes timeout for image generation
                )
                
                # Check HTTP status
                response.raise_for_status()
                
                # Parse response
                response_data = response.json()
                
                print("response_data", response_data)
                
                # Handle errors
                if "error" in response_data:
                    error_msg = response_data.get("error", {}).get("message", str(response_data.get("error")))
                    raise ValueError(f"Kling AI API error: {error_msg}")
                
                # Handle async task response (if API returns task_id)
                if "task_id" in response_data:
                    task_id = response_data["task_id"]
                    # Poll for task completion
                    print(f"Task submitted with ID: {task_id}. Polling for completion...")
                    return self.poll_task_until_complete(task_id)
                
                # Also check for task_id in nested data structure
                if "data" in response_data and isinstance(response_data["data"], dict):
                    if "task_id" in response_data["data"]:
                        task_id = response_data["data"]["task_id"]
                        print(f"Task submitted with ID: {task_id}. Polling for completion...")
                        return self.poll_task_until_complete(task_id)
                
                # If no task_id, assume synchronous response (shouldn't happen based on API docs)
                # But handle it gracefully just in case
                raise ValueError(
                    f"Unexpected response format from Kling AI API. "
                    f"Expected task_id but got: {json.dumps(response_data, indent=2)}"
                )
                
            except requests.exceptions.HTTPError as e:
                error_msg = f"HTTP {e.response.status_code}"
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get("error", {}).get("message", str(error_data))
                except:
                    error_msg = e.response.text or str(e)
                
                raise ValueError(
                    f"Kling AI API HTTP error ({e.response.status_code}): {error_msg}. "
                    f"Please check your API key and request parameters."
                )
            except requests.exceptions.RequestException as e:
                raise ValueError(
                    f"Failed to connect to Kling AI API: {str(e)}. "
                    f"Please check your internet connection and API endpoint."
                )
            
        except ValueError:
            # Re-raise ValueError as-is (already formatted)
            raise
        except Exception as e:
            raise ValueError(f"Failed to generate virtual try-on: {str(e)}")
    
    def generate_and_decode(self,
                           source_image: Union[str, io.BytesIO],
                           reference_image: Union[str, io.BytesIO],
                           model: Optional[str] = None,
                           **kwargs) -> List[Image.Image]:
        """
        Generate virtual try-on images and decode them to PIL Image objects.
        
        Convenience method that combines generate() with image decoding. Automatically
        handles both base64-encoded images and image URLs returned by the API.
        
        Authentication:
            Uses the API key and secret key provided during adapter initialization
            to generate a JWT token for authentication. The token is automatically
            included in the request headers.
        
        Args:
            source_image: Human/person image in one of these formats:
                         - File path (str): Path to local image file
                         - URL (str): HTTP/HTTPS URL to image
                         - File-like object (io.BytesIO): BytesIO or similar
                         - Base64 string (str): Base64-encoded image
            reference_image: Cloth/garment image in same formats as source_image.
            model: Optional model version to use (e.g., 'kolors-virtual-try-on-v1-5').
            **kwargs: Additional parameters for Kling AI API:
                     - webhook_url (str, optional): URL for async result delivery
                     - webhook_secret (str, optional): Secret for webhook authentication
                     - Other parameters as per Kling AI API documentation
            
        Returns:
            List[Image.Image]: List of PIL Image objects ready for display or saving.
                             Each image can be saved, displayed, or further processed.
            
        Raises:
            ValueError: If images exceed size limits, required parameters are missing,
                       API returns an error, or image decoding fails.
            
        Example:
            >>> import os
            >>> os.environ['KLING_AI_API_KEY'] = 'your_api_key'
            >>> os.environ['KLING_AI_SECRET_KEY'] = 'your_secret_key'
            >>> adapter = KlingAIVTONAdapter()
            >>> images = adapter.generate_and_decode(
            ...     source_image="person.jpg",
            ...     reference_image="shirt.jpg"
            ... )
            >>> images[0].save("result.png")
            
            >>> # Using parameters and URLs
            >>> adapter = KlingAIVTONAdapter(
            ...     api_key="your_api_key",
            ...     secret_key="your_secret_key"
            ... )
            >>> images = adapter.generate_and_decode(
            ...     source_image="https://example.com/person.jpg",
            ...     reference_image="https://example.com/garment.jpg"
            ... )
            >>> for idx, img in enumerate(images):
            ...     img.save(f"result_{idx}.png")
        """
        images = self.generate(
            source_image=source_image,
            reference_image=reference_image,
            model=model,
            **kwargs
        )
        
        decoded_images = []
        for image_data in images:
            # Handle both URLs and base64 strings
            if isinstance(image_data, str) and image_data.startswith(("http://", "https://")):
                # Fetch image from URL
                img_response = requests.get(image_data)
                img_response.raise_for_status()
                image_bytes = img_response.content
            elif isinstance(image_data, str):
                # Decode base64 string
                image_bytes = base64.b64decode(image_data)
            else:
                # Already bytes or other format
                image_bytes = image_data if isinstance(image_data, bytes) else str(image_data).encode()
            
            image_buffer = io.BytesIO(image_bytes)
            image = Image.open(image_buffer)
            decoded_images.append(image)
        
        return decoded_images
    
    def query_task_status(self, task_id: str) -> dict:
        """
        Query the status of a virtual try-on task by task ID.
        
        Fetches the current status of a task using the Kling AI task status endpoint.
        
        Args:
            task_id: The task ID returned from the initial API request.
        
        Returns:
            dict: Task status response containing:
                  - code: Error code (0 = success)
                  - message: Status message
                  - request_id: System-generated request ID
                  - data: Task data containing:
                      - task_id: Task identifier
                      - task_status: Current status ("submitted", "processing", "succeed", "fail")
                      - task_status_msg: Additional status information
                      - created_at: Task creation timestamp (milliseconds)
                      - updated_at: Task update timestamp (milliseconds)
                      - task_result: Result data (when status is "succeed")
                          - images: List of image objects with index and url
        
        Raises:
            ValueError: If the API request fails or returns an error.
        """
        # Task status endpoint: GET /v1/images/kolors-virtual-try-on/{id}
        status_endpoint = f"{self.base_url}/v1/images/kolors-virtual-try-on/{task_id}"
        
        try:
            response = requests.get(
                status_endpoint,
                headers=self.headers,
                timeout=30
            )
            
            # Check HTTP status
            response.raise_for_status()
            
            # Parse response
            response_data = response.json()
            
            # Check for errors in response
            if response_data.get("code") != 0:
                error_msg = response_data.get("message", "Unknown error")
                raise ValueError(f"Kling AI API error (code {response_data.get('code')}): {error_msg}")
            
            return response_data
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP {e.response.status_code}"
            try:
                error_data = e.response.json()
                error_msg = error_data.get("message", str(error_data))
            except:
                error_msg = e.response.text or str(e)
            
            raise ValueError(
                f"Failed to query task status. HTTP error ({e.response.status_code}): {error_msg}"
            )
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Failed to connect to Kling AI API: {str(e)}")
    
    def poll_task_until_complete(self, task_id: str, 
                                 poll_interval: int = 2,
                                 max_wait_time: int = 300) -> List[str]:
        """
        Poll task status until completion and return image URLs.
        
        Continuously queries the task status endpoint until the task is completed
        (succeeds or fails). Returns image URLs when the task succeeds.
        
        Args:
            task_id: The task ID returned from the initial API request.
            poll_interval: Number of seconds to wait between status checks. Default: 2 seconds.
            max_wait_time: Maximum time to wait for task completion in seconds. Default: 300 (5 minutes).
        
        Returns:
            List[str]: List of image URLs when task succeeds.
        
        Raises:
            ValueError: If the task fails, times out, or encounters an error.
        """
        import time
        
        start_time = time.time()
        last_status = None
        
        while True:
            # Check timeout
            elapsed_time = time.time() - start_time
            if elapsed_time > max_wait_time:
                raise ValueError(
                    f"Task {task_id} timed out after {max_wait_time} seconds. "
                    f"Last status: {last_status}"
                )
            
            # Query task status
            status_response = self.query_task_status(task_id)
            
            print("current status response:", status_response)
            
            # Extract task data
            task_data = status_response.get("data", {})
            task_status = task_data.get("task_status", "").lower()
            task_status_msg = task_data.get("task_status_msg", "")
            
            last_status = task_status
            
            # Handle different task statuses
            if task_status == "succeed":
                # Task completed successfully - extract image URLs
                task_result = task_data.get("task_result", {})
                images = task_result.get("images", [])
                
                if not images:
                    raise ValueError(
                        f"Task {task_id} completed successfully but no images found in response."
                    )
                
                # Extract URLs from images array
                image_urls = []
                for img in images:
                    if isinstance(img, dict):
                        url = img.get("url")
                        if url:
                            image_urls.append(url)
                    elif isinstance(img, str):
                        image_urls.append(img)
                
                if not image_urls:
                    raise ValueError(
                        f"Task {task_id} completed successfully but no valid image URLs found."
                    )
                
                print(f"✓ Task {task_id} completed successfully. Found {len(image_urls)} image(s).")
                return image_urls
                
            elif task_status == "fail":
                # Task failed
                raise ValueError(
                    f"Task {task_id} failed. Status message: {task_status_msg}"
                )
                
            elif task_status in ["submitted", "processing"]:
                # Task is still in progress
                elapsed_minutes = int(elapsed_time / 60)
                elapsed_seconds = int(elapsed_time % 60)
                print(
                    f"Task {task_id} status: {task_status} "
                    f"(elapsed: {elapsed_minutes}m {elapsed_seconds}s)..."
                )
                
                # Wait before next poll
                time.sleep(poll_interval)
                
            else:
                # Unknown status
                raise ValueError(
                    f"Task {task_id} returned unknown status: {task_status}. "
                    f"Message: {task_status_msg}"
                )

def generate_api_token(api_key: Optional[str] = None, secret_key: Optional[str] = None, 
                       expiration_seconds: int = 1800) -> str:
    """
    Generate a JWT API token for Kling AI authentication.
    
    Creates a JWT token using HS256 algorithm with API key and secret key.
    The token can be used for authenticating requests to Kling AI API endpoints.
    
    Reference: https://app.klingai.com/global/dev/document-api/apiReference/commonInfo
    
    Args:
        api_key: Kling AI API key. Defaults to KLING_AI_API_KEY environment variable.
                If not provided via parameter or environment variable, raises ValueError.
        secret_key: Kling AI secret key. Defaults to KLING_AI_SECRET_KEY environment variable.
                   If not provided via parameter or environment variable, raises ValueError.
        expiration_seconds: Token expiration time in seconds from now. Default: 1800 (30 minutes).
                          The token will be valid until current_time + expiration_seconds.
    
    Returns:
        str: JWT token string that can be used for API authentication.
    
    Raises:
        ValueError: If API key or secret key is not provided.
        ImportError: If PyJWT library is not installed.
        
    Environment Variables:
        KLING_AI_API_KEY: Your Kling AI API key (required if not passed as parameter)
        KLING_AI_SECRET_KEY: Your Kling AI secret key (required if not passed as parameter)
    
    Example:
        >>> import os
        >>> os.environ['KLING_AI_API_KEY'] = 'your_api_key'
        >>> os.environ['KLING_AI_SECRET_KEY'] = 'your_secret_key'
        >>> token = generate_api_token()
        >>> print(token)
        
        >>> # Using parameters directly
        >>> token = generate_api_token(
        ...     api_key="your_api_key",
        ...     secret_key="your_secret_key",
        ...     expiration_seconds=3600  # 1 hour
        ... )
    """
    # Get API key and secret from parameters or environment variables
    api_key = api_key or os.getenv("KLING_AI_API_KEY")
    secret_key = secret_key or os.getenv("KLING_AI_SECRET_KEY")
    
    if not api_key:
        raise ValueError(
            "API key is required. Provide it as parameter or set KLING_AI_API_KEY "
            "environment variable."
        )
    
    if not secret_key:
        raise ValueError(
            "Secret key is required. Provide it as parameter or set KLING_AI_SECRET_KEY "
            "environment variable."
        )
    
    # Validate expiration_seconds
    if expiration_seconds <= 0:
        raise ValueError("expiration_seconds must be a positive integer.")
    
    # JWT headers
    headers = {
        "alg": "HS256",
        "typ": "JWT"
    }
    
    # Current timestamp
    current_time = int(time.time())
    
    # JWT payload
    payload = {
        "iss": api_key,  # Issuer: API key
        "exp": current_time + expiration_seconds,  # Expiration time: current time + expiration_seconds
        "nbf": current_time - 5  # Not before: current time minus 5 seconds (leeway for clock skew)
    }
    
    try:
        # Encode JWT token using secret key
        token = jwt.encode(payload, secret_key, algorithm="HS256", headers=headers)
        return token
    except Exception as e:
        raise ValueError(f"Failed to generate JWT token: {str(e)}")