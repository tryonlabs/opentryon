import os
import base64
import json
import io
import requests
from typing import Optional, Union, List
from PIL import Image


class SegmindVTONAdapter:
    """
    Adapter for Segmind Try-On Diffusion API.
    
    Segmind provides virtual try-on capabilities that allow you to combine
    two images: a model image (person) and a cloth image (garment/product).
    The model generates realistic results showing the person wearing the garment.
    
    Reference: https://www.segmind.com/models/try-on-diffusion/api
    
    API endpoint: POST https://api.segmind.com/v1/try-on-diffusion
    
    Authentication:
        Requires API key for authentication via x-api-key header.
        Can be provided via constructor parameter or SEGMIND_API_KEY environment variable.
    
    The API accepts image URLs or base64-encoded images. This adapter automatically
    handles file paths by converting them to base64, and passes URLs as-is.
    
    Example:
        >>> import os
        >>> os.environ['SEGMIND_API_KEY'] = 'your_api_key'
        >>> adapter = SegmindVTONAdapter()
        >>> images = adapter.generate_and_decode(
        ...     model_image="person.jpg",
        ...     cloth_image="shirt.jpg",
        ...     category="Upper body"
        ... )
        >>> images[0].save("result.png")
        
        >>> # Using parameters directly
        >>> adapter = SegmindVTONAdapter(api_key="your_api_key")
        >>> images = adapter.generate_and_decode(
        ...     model_image="person.jpg",
        ...     cloth_image="shirt.jpg",
        ...     category="Upper body"
        ... )
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Segmind VTON client.
        
        Args:
            api_key: Segmind API key. Defaults to SEGMIND_API_KEY environment variable.
                    If not provided via parameter or environment variable, raises ValueError.
        
        Raises:
            ValueError: If API key is not provided.
        
        Example:
            >>> # Using environment variable
            >>> import os
            >>> os.environ['SEGMIND_API_KEY'] = 'your_api_key'
            >>> adapter = SegmindVTONAdapter()
            
            >>> # Using parameter
            >>> adapter = SegmindVTONAdapter(api_key="your_api_key")
        """
        self.api_key = api_key or os.getenv("SEGMIND_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Segmind API key is required. Set SEGMIND_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        self.endpoint = "https://api.segmind.com/v1/try-on-diffusion"
        
        # Default headers
        self.headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }
    
    def _prepare_image_input(self, image_input: Union[str, io.BytesIO]) -> str:
        """
        Prepare image input for API request.
        
        Handles file paths, file-like objects, URLs, and base64 strings.
        For local files and file-like objects, converts to base64.
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
            ValueError: If input format is invalid
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
            with open(image_input, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode("utf-8")
        
        # It's a file-like object
        if hasattr(image_input, 'read'):
            image_file = image_input
            image_file.seek(0)
            image_bytes = image_file.read()
            image_file.seek(0)
            
            return base64.b64encode(image_bytes).decode("utf-8")
        
        raise ValueError("Invalid image input: must be a file path, URL, file-like object, or base64 string")
    
    def create_virtual_try_on_payload(self,
                                     model_image: str,
                                     cloth_image: str,
                                     category: str = "Upper body",
                                     num_inference_steps: Optional[int] = None,
                                     guidance_scale: Optional[float] = None,
                                     seed: Optional[int] = None,
                                     base64: bool = False,
                                     **kwargs) -> dict:
        """
        Create the payload for virtual try-on request based on Segmind API format.
        
        The payload structure follows Segmind's API specification:
        - Uses `model_image` parameter for the person image (accepts URL or base64)
        - Uses `cloth_image` parameter for the garment image (accepts URL or base64)
        - Uses `category` parameter for garment type
        
        Args:
            model_image: URL (starts with http:// or https://) or base64 string of the model/person image.
            cloth_image: URL (starts with http:// or https://) or base64 string of the cloth/garment image.
            category: Garment category. Options: "Upper body", "Lower body", "Dress". Default: "Upper body".
            num_inference_steps: Number of denoising steps. Default: 25. Range: 20-100.
            guidance_scale: Scale for classifier-free guidance. Default: 2. Range: 1-25.
            seed: Seed for image generation. Default: -1. Range: -1 to 999999999999999.
            base64: Whether to return base64-encoded image. Default: False.
            **kwargs: Additional parameters as per Segmind API documentation.
        
        Returns:
            dict: Dictionary containing the request payload ready for API call.
        """
        # Base payload structure according to Segmind API
        payload = {
            "model_image": model_image,
            "cloth_image": cloth_image,
            "category": category,
            "base64": base64
        }
        
        # Add optional parameters if provided
        if num_inference_steps is not None:
            if not (20 <= num_inference_steps <= 100):
                raise ValueError("num_inference_steps must be between 20 and 100")
            payload["num_inference_steps"] = num_inference_steps
        
        if guidance_scale is not None:
            if not (1 <= guidance_scale <= 25):
                raise ValueError("guidance_scale must be between 1 and 25")
            payload["guidance_scale"] = guidance_scale
        
        if seed is not None:
            if seed != -1 and not (0 <= seed <= 999999999999999):
                raise ValueError("seed must be -1 or between 0 and 999999999999999")
            payload["seed"] = seed
        
        # Add any additional parameters
        payload.update(kwargs)
        
        return payload
    
    def generate(self,
                 model_image: Union[str, io.BytesIO],
                 cloth_image: Union[str, io.BytesIO],
                 category: str = "Upper body",
                 num_inference_steps: Optional[int] = None,
                 guidance_scale: Optional[float] = None,
                 seed: Optional[int] = None,
                 base64: bool = True,
                 **kwargs) -> Union[str, bytes]:
        """
        Generate virtual try-on image(s) using Segmind API.
        
        This method combines a model image (person) with a cloth image (garment/product)
        to create realistic virtual try-on results.
        
        The method handles multiple input formats:
        - File paths: Automatically converted to base64
        - URLs: Passed directly to API
        - File-like objects: Converted to base64
        - Base64 strings: Used directly
        
        Authentication:
            Uses the API key provided during adapter initialization
            via x-api-key header.
        
        Example:
            >>> import os
            >>> os.environ['SEGMIND_API_KEY'] = 'your_api_key'
            >>> adapter = SegmindVTONAdapter()
            >>> image_data = adapter.generate(
            ...     model_image="person.jpg",
            ...     cloth_image="hoodie.jpg",
            ...     category="Upper body"
            ... )
            
            >>> # Using URLs
            >>> adapter = SegmindVTONAdapter(api_key="your_api_key")
            >>> image_data = adapter.generate(
            ...     model_image="https://example.com/person.jpg",
            ...     cloth_image="https://example.com/garment.jpg",
            ...     category="Lower body"
            ... )
        
        Args:
            model_image: Model/person image in one of these formats:
                        - File path (str): Path to local image file
                        - URL (str): HTTP/HTTPS URL to image
                        - File-like object (io.BytesIO): BytesIO or similar
                        - Base64 string (str): Base64-encoded image
            cloth_image: Cloth/garment image in same formats as model_image.
            category: Garment category. Options: "Upper body", "Lower body", "Dress". Default: "Upper body".
            num_inference_steps: Number of denoising steps. Default: 25. Range: 20-100.
            guidance_scale: Scale for classifier-free guidance. Default: 2. Range: 1-25.
            seed: Seed for image generation. Default: -1. Range: -1 to 999999999999999.
            base64: Whether to return base64-encoded image. Default: True (for easier decoding).
            **kwargs: Additional parameters for Segmind API.
        
        Returns:
            Union[str, bytes]: Generated image data:
                              - If base64=True: Base64-encoded string
                              - If base64=False: Raw image bytes
        
        Raises:
            ValueError: If required parameters are missing, API returns an error,
                       or response format is unexpected.
        """
        try:
            # Validate category
            valid_categories = {"Upper body", "Lower body", "Dress"}
            if category not in valid_categories:
                raise ValueError(
                    f"Invalid category '{category}'. Must be one of: {valid_categories}"
                )
            
            # Prepare image inputs
            model_image_prepared = self._prepare_image_input(model_image)
            cloth_image_prepared = self._prepare_image_input(cloth_image)
            
            # Create payload
            payload = self.create_virtual_try_on_payload(
                model_image=model_image_prepared,
                cloth_image=cloth_image_prepared,
                category=category,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                seed=seed,
                base64=base64,
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
                
                # Handle response based on base64 flag
                if base64:
                    # Response should be JSON with base64 image
                    try:
                        response_data = response.json()
                        # Check for error in response
                        if "error" in response_data:
                            error_msg = response_data.get("error", {}).get("message", str(response_data.get("error")))
                            raise ValueError(f"Segmind API error: {error_msg}")
                        
                        # Extract base64 image from response
                        # Response format may vary, try common fields
                        image_base64 = (
                            response_data.get("image") or
                            response_data.get("data") or
                            response_data.get("result") or
                            response_data.get("output")
                        )
                        
                        if not image_base64:
                            raise ValueError(
                                f"Unexpected response format from Segmind API. "
                                f"Expected image data but got: {json.dumps(response_data, indent=2)}"
                            )
                        
                        return image_base64
                    except json.JSONDecodeError:
                        # Response might be plain text base64
                        return response.text
                else:
                    # Response should be raw image bytes
                    return response.content
                
            except requests.exceptions.HTTPError as e:
                error_msg = f"HTTP {e.response.status_code}"
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get("error", {}).get("message", str(error_data))
                except:
                    error_msg = e.response.text or str(e)
                
                # Map common HTTP errors to helpful messages
                if e.response.status_code == 401:
                    raise ValueError(
                        f"Segmind API authentication failed (401). "
                        f"Please check your API key."
                    )
                elif e.response.status_code == 403:
                    raise ValueError(
                        f"Segmind API access forbidden (403). "
                        f"Please check your API key permissions."
                    )
                elif e.response.status_code == 406:
                    raise ValueError(
                        f"Segmind API insufficient credits (406). "
                        f"Please add credits to your account."
                    )
                elif e.response.status_code == 429:
                    raise ValueError(
                        f"Segmind API rate limit exceeded (429). "
                        f"Please wait before making another request."
                    )
                else:
                    raise ValueError(
                        f"Segmind API HTTP error ({e.response.status_code}): {error_msg}. "
                        f"Please check your API key and request parameters."
                    )
            except requests.exceptions.RequestException as e:
                raise ValueError(
                    f"Failed to connect to Segmind API: {str(e)}. "
                    f"Please check your internet connection and API endpoint."
                )
            
        except ValueError:
            # Re-raise ValueError as-is (already formatted)
            raise
        except Exception as e:
            raise ValueError(f"Failed to generate virtual try-on: {str(e)}")
    
    def generate_and_decode(self,
                           model_image: Union[str, io.BytesIO],
                           cloth_image: Union[str, io.BytesIO],
                           category: str = "Upper body",
                           num_inference_steps: Optional[int] = None,
                           guidance_scale: Optional[float] = None,
                           seed: Optional[int] = None,
                           **kwargs) -> List[Image.Image]:
        """
        Generate virtual try-on images and decode them to PIL Image objects.
        
        Convenience method that combines generate() with image decoding. Automatically
        handles base64-encoded images returned by the API.
        
        Args:
            model_image: Model/person image in one of these formats:
                         - File path (str): Path to local image file
                         - URL (str): HTTP/HTTPS URL to image
                         - File-like object (io.BytesIO): BytesIO or similar
                         - Base64 string (str): Base64-encoded image
            cloth_image: Cloth/garment image in same formats as model_image.
            category: Garment category. Options: "Upper body", "Lower body", "Dress". Default: "Upper body".
            num_inference_steps: Number of denoising steps. Default: 25. Range: 20-100.
            guidance_scale: Scale for classifier-free guidance. Default: 2. Range: 1-25.
            seed: Seed for image generation. Default: -1. Range: -1 to 999999999999999.
            **kwargs: Additional parameters for Segmind API.
        
        Returns:
            List[Image.Image]: List of PIL Image objects ready for display or saving.
                             Each image can be saved, displayed, or further processed.
        
        Raises:
            ValueError: If required parameters are missing, API returns an error,
                       or image decoding fails.
        
        Example:
            >>> import os
            >>> os.environ['SEGMIND_API_KEY'] = 'your_api_key'
            >>> adapter = SegmindVTONAdapter()
            >>> images = adapter.generate_and_decode(
            ...     model_image="person.jpg",
            ...     cloth_image="shirt.jpg",
            ...     category="Upper body"
            ... )
            >>> images[0].save("result.png")
            
            >>> # Using parameters and URLs
            >>> adapter = SegmindVTONAdapter(api_key="your_api_key")
            >>> images = adapter.generate_and_decode(
            ...     model_image="https://example.com/person.jpg",
            ...     cloth_image="https://example.com/garment.jpg",
            ...     category="Dress"
            ... )
            >>> for idx, img in enumerate(images):
            ...     img.save(f"result_{idx}.png")
        """
        # Generate with base64=True for easier decoding
        image_data = self.generate(
            model_image=model_image,
            cloth_image=cloth_image,
            category=category,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
            seed=seed,
            base64=True,
            **kwargs
        )
        
        # Decode base64 to PIL Image
        if isinstance(image_data, str):
            # Decode base64 string
            image_bytes = base64.b64decode(image_data)
        else:
            # Already bytes
            image_bytes = image_data
        
        image_buffer = io.BytesIO(image_bytes)
        image = Image.open(image_buffer)
        
        # Return as list for consistency with other adapters
        return [image]
