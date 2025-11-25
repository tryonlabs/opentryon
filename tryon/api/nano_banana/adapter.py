"""
Nano Banana (Gemini Image Generation) API Adapter

Adapter for Google's Gemini image generation models (Nano Banana and Nano Banana Pro).

Gemini can generate and process images conversationally. You can prompt Gemini with text,
images, or a combination of both, allowing you to create, edit, and iterate on visuals:

- Text-to-Image: Generate high-quality images from text descriptions
- Image + Text-to-Image (Editing): Provide an image and use text prompts to edit
- Multi-Image to Image (Composition & style transfer): Use multiple input images
- Iterative refinement: Progressively refine images over multiple turns
- High-Fidelity text rendering: Generate images with legible text

Reference: https://ai.google.dev/gemini-api/docs/image-generation

Models:
- Gemini 2.5 Flash Image (Nano Banana): Fast, efficient, 1024px resolution
- Gemini 3 Pro Image Preview (Nano Banana Pro): Advanced, 4K resolution, search-grounded

Example:
    Text-to-image:
        >>> from tryon.api.nano_banana import NanoBananaAdapter
        >>> adapter = NanoBananaAdapter()
        >>> images = adapter.generate_text_to_image(
        ...     prompt="A nano banana dish in a fancy restaurant with a Gemini theme"
        ... )
        >>> images[0].save("result.png")
    
    Image editing:
        >>> images = adapter.generate_image_edit(
        ...     image="cat.jpg",
        ...     prompt="Add a nano-banana to the scene"
        ... )
    
    Multi-image composition:
        >>> images = adapter.generate_multi_image(
        ...     images=["image1.jpg", "image2.jpg"],
        ...     prompt="Combine these images with a Gemini theme"
        ... )
"""

import os
import base64
import io
from typing import Optional, Union, List, Dict, Any
from PIL import Image

try:
    from google import genai
    from google.genai import types
    GOOGLE_GENAI_AVAILABLE = True
except ImportError:
    GOOGLE_GENAI_AVAILABLE = False
    genai = None
    types = None


# Supported aspect ratios for Gemini 2.5 Flash Image
GEMINI_25_FLASH_ASPECT_RATIOS = {
    "1:1": {"resolution": "1024x1024", "tokens": 1290},
    "2:3": {"resolution": "832x1248", "tokens": 1290},
    "3:2": {"resolution": "1248x832", "tokens": 1290},
    "3:4": {"resolution": "864x1184", "tokens": 1290},
    "4:3": {"resolution": "1184x864", "tokens": 1290},
    "4:5": {"resolution": "896x1152", "tokens": 1290},
    "5:4": {"resolution": "1152x896", "tokens": 1290},
    "9:16": {"resolution": "768x1344", "tokens": 1290},
    "16:9": {"resolution": "1344x768", "tokens": 1290},
    "21:9": {"resolution": "1536x672", "tokens": 1290},
}

# Supported aspect ratios for Gemini 3 Pro Image Preview
GEMINI_3_PRO_ASPECT_RATIOS = {
    "1:1": {"1K": "1024x1024", "2K": "2048x2048", "4K": "4096x4096"},
    "2:3": {"1K": "848x1264", "2K": "1696x2528", "4K": "3392x5056"},
    "3:2": {"1K": "1264x848", "2K": "2528x1696", "4K": "5056x3392"},
    "3:4": {"1K": "896x1200", "2K": "1792x2400", "4K": "3584x4800"},
    "4:3": {"1K": "1200x896", "2K": "2400x1792", "4K": "4800x3584"},
    "4:5": {"1K": "928x1152", "2K": "1856x2304", "4K": "3712x4608"},
    "5:4": {"1K": "1152x928", "2K": "2304x1856", "4K": "4608x3712"},
    "9:16": {"1K": "768x1376", "2K": "1536x2752", "4K": "3072x5504"},
    "16:9": {"1K": "1376x768", "2K": "2752x1536", "4K": "5504x3072"},
    "21:9": {"1K": "1584x672", "2K": "3168x1344", "4K": "6336x2688"},
}


class NanoBananaAdapter:
    """
    Adapter for Gemini 2.5 Flash Image (Nano Banana) API.
    
    Gemini 2.5 Flash Image is designed for speed and efficiency, optimized for
    high-volume, low-latency tasks and generates images at 1024px resolution.
    
    Reference: https://ai.google.dev/gemini-api/docs/image-generation
    
    Authentication:
        Requires API key for authentication. Can be provided via constructor
        parameter or GEMINI_API_KEY environment variable.
    
    Example:
        >>> import os
        >>> os.environ['GEMINI_API_KEY'] = 'your_api_key'
        >>> adapter = NanoBananaAdapter()
        >>> images = adapter.generate_text_to_image(
        ...     prompt="A stylish fashion model wearing a modern casual outfit"
        ... )
        >>> images[0].save("result.png")
    """
    
    MODEL_NAME = "gemini-2.5-flash-image"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Nano Banana (Gemini 2.5 Flash Image) adapter.
        
        Args:
            api_key: Google Gemini API key. Defaults to GEMINI_API_KEY environment variable.
                   If not provided via parameter or environment variable, raises ValueError.
        
        Raises:
            ValueError: If API key is not provided or Google GenAI SDK is not installed.
            ImportError: If google.genai is not available.
        
        Example:
            >>> # Using environment variable
            >>> import os
            >>> os.environ['GEMINI_API_KEY'] = 'your_api_key'
            >>> adapter = NanoBananaAdapter()
            
            >>> # Using parameter
            >>> adapter = NanoBananaAdapter(api_key="your_api_key")
        """
        if not GOOGLE_GENAI_AVAILABLE:
            raise ImportError(
                "Google GenAI SDK is required for Nano Banana. "
                "Install it with: pip install google-genai"
            )
        
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Gemini API key is required. Set GEMINI_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        self.client = genai.Client(api_key=self.api_key)
    
    def _prepare_image_input(self, image_input: Union[str, io.BytesIO, Image.Image]) -> Image.Image:
        """
        Prepare image input for API request.
        
        Handles file paths, file-like objects, PIL Images, URLs, and base64 strings.
        
        Args:
            image_input: Image input in one of the following formats:
                       - File path (str): Path to local image file
                       - URL (str): HTTP/HTTPS URL to image
                       - Base64 string (str): Base64-encoded image data
                       - File-like object (io.BytesIO): BytesIO or similar object
                       - PIL Image: PIL Image object
        
        Returns:
            PIL Image object
            
        Raises:
            ValueError: If input format is invalid
        """
        # If it's already a PIL Image
        if isinstance(image_input, Image.Image):
            return image_input
        
        # If it's a file-like object
        if hasattr(image_input, 'read'):
            image_file = image_input
            image_file.seek(0)
            return Image.open(image_file)
        
        # If it's a string
        if isinstance(image_input, str):
            # Check if it's a URL
            if image_input.startswith(("http://", "https://")):
                import requests
                response = requests.get(image_input)
                response.raise_for_status()
                return Image.open(io.BytesIO(response.content))
            
            # Check if it's base64
            if len(image_input) > 100 and not os.path.exists(image_input):
                try:
                    image_bytes = base64.b64decode(image_input)
                    return Image.open(io.BytesIO(image_bytes))
                except:
                    pass
            
            # It's a file path
            return Image.open(image_input)
        
        raise ValueError("Invalid image input: must be a file path, URL, PIL Image, file-like object, or base64 string")
    
    def _image_to_part(self, image: Image.Image) -> types.Part:
        """Convert PIL Image to GenAI Part."""
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        buffer.seek(0)
        image_bytes = buffer.read()
        
        return types.Part.from_bytes(
            data=image_bytes,
            mime_type="image/png"
        )
    
    def generate_text_to_image(
        self,
        prompt: str,
        aspect_ratio: Optional[str] = None,
        **kwargs
    ) -> List[Image.Image]:
        """
        Generate image(s) from text prompt (text-to-image).
        
        Args:
            prompt: Text description of the image to generate
            aspect_ratio: Optional aspect ratio. Options: "1:1", "2:3", "3:2", "3:4", "4:3",
                         "4:5", "5:4", "9:16", "16:9", "21:9". Default: None (uses model default)
            **kwargs: Additional generation config parameters
        
        Returns:
            List of PIL Image objects
            
        Example:
            >>> adapter = NanoBananaAdapter()
            >>> images = adapter.generate_text_to_image(
            ...     prompt="A stylish fashion model wearing a modern casual outfit",
            ...     aspect_ratio="16:9"
            ... )
            >>> images[0].save("result.png")
        """
        # Build generation config
        config = {}
        if aspect_ratio:
            if aspect_ratio not in GEMINI_25_FLASH_ASPECT_RATIOS:
                raise ValueError(
                    f"Invalid aspect ratio '{aspect_ratio}'. "
                    f"Valid options: {list(GEMINI_25_FLASH_ASPECT_RATIOS.keys())}"
                )
            config['image_config'] = types.ImageConfig(aspect_ratio=aspect_ratio)
        
        # Add any additional config from kwargs
        config.update(kwargs)
        
        # Generate content
        response = self.client.models.generate_content(
            model=self.MODEL_NAME,
            contents=[prompt],
            config=types.GenerateContentConfig(**config) if config else None
        )
        
        # Extract images from response
        images = []
        for part in response.parts:
            if part.inline_data is not None:
                image = part.as_image()
                images.append(image)
        
        if not images:
            raise ValueError("No images generated in response")
        
        return images
    
    def generate_image_edit(
        self,
        image: Union[str, io.BytesIO, Image.Image],
        prompt: str,
        aspect_ratio: Optional[str] = None,
        **kwargs
    ) -> List[Image.Image]:
        """
        Generate edited image from image + text prompt (image editing).
        
        Provide an image and use text prompts to add, remove, or modify elements,
        change the style, or adjust the color grading.
        
        Args:
            image: Input image (file path, URL, PIL Image, file-like object, or base64)
            prompt: Text description of the edits to make
            aspect_ratio: Optional aspect ratio. Options: "1:1", "2:3", "3:2", "3:4", "4:3",
                         "4:5", "5:4", "9:16", "16:9", "21:9". Default: None
            **kwargs: Additional generation config parameters
        
        Returns:
            List of PIL Image objects
            
        Example:
            >>> adapter = NanoBananaAdapter()
            >>> images = adapter.generate_image_edit(
            ...     image="person.jpg",
            ...     prompt="Change the outfit to a formal business suit"
            ... )
        """
        # Prepare image
        pil_image = self._prepare_image_input(image)
        image_part = self._image_to_part(pil_image)
        
        # Build generation config
        config = {}
        if aspect_ratio:
            if aspect_ratio not in GEMINI_25_FLASH_ASPECT_RATIOS:
                raise ValueError(
                    f"Invalid aspect ratio '{aspect_ratio}'. "
                    f"Valid options: {list(GEMINI_25_FLASH_ASPECT_RATIOS.keys())}"
                )
            config['image_config'] = types.ImageConfig(aspect_ratio=aspect_ratio)
        
        config.update(kwargs)
        
        # Generate content
        response = self.client.models.generate_content(
            model=self.MODEL_NAME,
            contents=[image_part, prompt],
            config=types.GenerateContentConfig(**config) if config else None
        )
        
        # Extract images
        images = []
        for part in response.parts:
            if part.inline_data is not None:
                image = part.as_image()
                images.append(image)
        
        if not images:
            raise ValueError("No images generated in response")
        
        return images
    
    def generate_multi_image(
        self,
        images: List[Union[str, io.BytesIO, Image.Image]],
        prompt: str,
        aspect_ratio: Optional[str] = None,
        **kwargs
    ) -> List[Image.Image]:
        """
        Generate image from multiple input images (composition & style transfer).
        
        Use multiple input images to compose a new scene or transfer the style
        from one image to another.
        
        Args:
            images: List of input images (file paths, URLs, PIL Images, file-like objects, or base64)
            prompt: Text description of how to combine/transform the images
            aspect_ratio: Optional aspect ratio. Options: "1:1", "2:3", "3:2", "3:4", "4:3",
                         "4:5", "5:4", "9:16", "16:9", "21:9". Default: None
            **kwargs: Additional generation config parameters
        
        Returns:
            List of PIL Image objects
            
        Example:
            >>> adapter = NanoBananaAdapter()
            >>> images = adapter.generate_multi_image(
            ...     images=["outfit1.jpg", "outfit2.jpg"],
            ...     prompt="Create a fashion catalog layout combining these clothing styles"
            ... )
        """
        # Prepare images
        image_parts = []
        for img in images:
            pil_image = self._prepare_image_input(img)
            image_parts.append(self._image_to_part(pil_image))
        
        # Build contents: images + prompt
        contents = image_parts + [prompt]
        
        # Build generation config
        config = {}
        if aspect_ratio:
            if aspect_ratio not in GEMINI_25_FLASH_ASPECT_RATIOS:
                raise ValueError(
                    f"Invalid aspect ratio '{aspect_ratio}'. "
                    f"Valid options: {list(GEMINI_25_FLASH_ASPECT_RATIOS.keys())}"
                )
            config['image_config'] = types.ImageConfig(aspect_ratio=aspect_ratio)
        
        config.update(kwargs)
        
        # Generate content
        response = self.client.models.generate_content(
            model=self.MODEL_NAME,
            contents=contents,
            config=types.GenerateContentConfig(**config) if config else None
        )
        
        # Extract images
        images_result = []
        for part in response.parts:
            if part.inline_data is not None:
                image = part.as_image()
                images_result.append(image)
        
        if not images_result:
            raise ValueError("No images generated in response")
        
        return images_result
    
    def generate_batch(
        self,
        prompts: List[str],
        aspect_ratio: Optional[str] = None,
        **kwargs
    ) -> List[List[Image.Image]]:
        """
        Generate images in batch from multiple text prompts.
        
        Args:
            prompts: List of text prompts
            aspect_ratio: Optional aspect ratio for all images
            **kwargs: Additional generation config parameters
        
        Returns:
            List of lists, where each inner list contains PIL Images for that prompt
            
        Example:
            >>> adapter = NanoBananaAdapter()
            >>> results = adapter.generate_batch(
            ...     prompts=[
            ...         "A fashion model showcasing summer collection",
            ...         "Professional photography of formal wear",
            ...         "Casual street style outfit on a model"
            ...     ]
            ... )
            >>> for idx, images in enumerate(results):
            ...     images[0].save(f"result_{idx}.png")
        """
        results = []
        for prompt in prompts:
            images = self.generate_text_to_image(
                prompt=prompt,
                aspect_ratio=aspect_ratio,
                **kwargs
            )
            results.append(images)
        return results


class NanoBananaProAdapter:
    """
    Adapter for Gemini 3 Pro Image Preview (Nano Banana Pro) API.
    
    Gemini 3 Pro Image Preview is designed for professional asset production and
    complex instructions. This model features:
    - Real-world grounding using Google Search
    - Default "Thinking" process that refines composition prior to generation
    - Can generate images of up to 4K resolutions
    
    Reference: https://ai.google.dev/gemini-api/docs/image-generation
    
    Authentication:
        Requires API key for authentication. Can be provided via constructor
        parameter or GEMINI_API_KEY environment variable.
    
    Example:
        >>> import os
        >>> os.environ['GEMINI_API_KEY'] = 'your_api_key'
        >>> adapter = NanoBananaProAdapter()
        >>> images = adapter.generate_text_to_image(
        ...     prompt="Professional fashion photography of elegant evening wear on a runway",
        ...     resolution="4K",
        ...     aspect_ratio="16:9"
        ... )
        >>> images[0].save("result.png")
    """
    
    MODEL_NAME = "gemini-3-pro-image-preview"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Nano Banana Pro (Gemini 3 Pro Image Preview) adapter.
        
        Args:
            api_key: Google Gemini API key. Defaults to GEMINI_API_KEY environment variable.
                   If not provided via parameter or environment variable, raises ValueError.
        
        Raises:
            ValueError: If API key is not provided or Google GenAI SDK is not installed.
            ImportError: If google.genai is not available.
        
        Example:
            >>> # Using environment variable
            >>> import os
            >>> os.environ['GEMINI_API_KEY'] = 'your_api_key'
            >>> adapter = NanoBananaProAdapter()
            
            >>> # Using parameter
            >>> adapter = NanoBananaProAdapter(api_key="your_api_key")
        """
        if not GOOGLE_GENAI_AVAILABLE:
            raise ImportError(
                "Google GenAI SDK is required for Nano Banana Pro. "
                "Install it with: pip install google-genai"
            )
        
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Gemini API key is required. Set GEMINI_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        self.client = genai.Client(api_key=self.api_key)
    
    def _prepare_image_input(self, image_input: Union[str, io.BytesIO, Image.Image]) -> Image.Image:
        """
        Prepare image input for API request.
        
        Handles file paths, file-like objects, PIL Images, URLs, and base64 strings.
        
        Args:
            image_input: Image input in one of the following formats:
                       - File path (str): Path to local image file
                       - URL (str): HTTP/HTTPS URL to image
                       - Base64 string (str): Base64-encoded image data
                       - File-like object (io.BytesIO): BytesIO or similar object
                       - PIL Image: PIL Image object
        
        Returns:
            PIL Image object
            
        Raises:
            ValueError: If input format is invalid
        """
        # If it's already a PIL Image
        if isinstance(image_input, Image.Image):
            return image_input
        
        # If it's a file-like object
        if hasattr(image_input, 'read'):
            image_file = image_input
            image_file.seek(0)
            return Image.open(image_file)
        
        # If it's a string
        if isinstance(image_input, str):
            # Check if it's a URL
            if image_input.startswith(("http://", "https://")):
                import requests
                response = requests.get(image_input)
                response.raise_for_status()
                return Image.open(io.BytesIO(response.content))
            
            # Check if it's base64
            if len(image_input) > 100 and not os.path.exists(image_input):
                try:
                    image_bytes = base64.b64decode(image_input)
                    return Image.open(io.BytesIO(image_bytes))
                except:
                    pass
            
            # It's a file path
            return Image.open(image_input)
        
        raise ValueError("Invalid image input: must be a file path, URL, PIL Image, file-like object, or base64 string")
    
    def _image_to_part(self, image: Image.Image) -> types.Part:
        """Convert PIL Image to GenAI Part."""
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        buffer.seek(0)
        image_bytes = buffer.read()
        
        return types.Part.from_bytes(
            data=image_bytes,
            mime_type="image/png"
        )
    
    def generate_text_to_image(
        self,
        prompt: str,
        resolution: str = "1K",
        aspect_ratio: Optional[str] = None,
        use_search_grounding: bool = False,
        **kwargs
    ) -> List[Image.Image]:
        """
        Generate image(s) from text prompt (text-to-image).
        
        Args:
            prompt: Text description of the image to generate
            resolution: Resolution level. Options: "1K", "2K", "4K". Default: "1K"
                       This is passed as `image_size` to ImageConfig.
            aspect_ratio: Optional aspect ratio. Options: "1:1", "2:3", "3:2", "3:4", "4:3",
                         "4:5", "5:4", "9:16", "16:9", "21:9". Default: None
            use_search_grounding: If True, use Google Search for real-world grounding. Default: False
            **kwargs: Additional generation config parameters
        
        Returns:
            List of PIL Image objects
            
        Example:
            >>> adapter = NanoBananaProAdapter()
            >>> images = adapter.generate_text_to_image(
            ...     prompt="A professional fashion photography",
            ...     resolution="4K",
            ...     aspect_ratio="16:9",
            ...     use_search_grounding=True
            ... )
        """
        if resolution not in ["1K", "2K", "4K"]:
            raise ValueError(f"Invalid resolution '{resolution}'. Must be '1K', '2K', or '4K'")
        
        # Build generation config
        config = {}
        
        # Image config with aspect ratio and image_size (resolution)
        image_config_params = {}
        if aspect_ratio:
            if aspect_ratio not in GEMINI_3_PRO_ASPECT_RATIOS:
                raise ValueError(
                    f"Invalid aspect ratio '{aspect_ratio}'. "
                    f"Valid options: {list(GEMINI_3_PRO_ASPECT_RATIOS.keys())}"
                )
            image_config_params['aspect_ratio'] = aspect_ratio
        
        # Add image_size (resolution) for Nano Banana Pro
        image_config_params['image_size'] = resolution
        
        print(f"image_config_params: {image_config_params}")
        if image_config_params:
            config['image_config'] = types.ImageConfig(**image_config_params)
        
        # Search grounding (if supported by SDK)
        if use_search_grounding:
            try:
                # Try to add Google Search tool for grounding
                # Note: This may vary based on SDK version
                search_tool = types.Tool.from_google_search()
                config['tools'] = [search_tool]
            except (AttributeError, TypeError):
                # If not available, skip search grounding
                pass
        
        config.update(kwargs)
        
        # Generate content
        response = self.client.models.generate_content(
            model=self.MODEL_NAME,
            contents=[prompt],
            config=types.GenerateContentConfig(**config) if config else None
        )
        
        # Extract images
        images = []
        for part in response.parts:
            if part.inline_data is not None:
                image = part.as_image()
                images.append(image)
        
        if not images:
            raise ValueError("No images generated in response")
        
        return images
    
    def generate_image_edit(
        self,
        image: Union[str, io.BytesIO, Image.Image],
        prompt: str,
        resolution: str = "1K",
        aspect_ratio: Optional[str] = None,
        **kwargs
    ) -> List[Image.Image]:
        """
        Generate edited image from image + text prompt (image editing).
        
        Provide an image and use text prompts to add, remove, or modify elements,
        change the style, or adjust the color grading.
        
        Args:
            image: Input image (file path, URL, PIL Image, file-like object, or base64)
            prompt: Text description of the edits to make
            resolution: Resolution level. Options: "1K", "2K", "4K". Default: "1K"
                       This is passed as `image_size` to ImageConfig.
            aspect_ratio: Optional aspect ratio. Options: "1:1", "2:3", "3:2", "3:4", "4:3",
                         "4:5", "5:4", "9:16", "16:9", "21:9". Default: None
            **kwargs: Additional generation config parameters
        
        Returns:
            List of PIL Image objects
            
        Example:
            >>> adapter = NanoBananaProAdapter()
            >>> images = adapter.generate_image_edit(
            ...     image="person.jpg",
            ...     prompt="Change the outfit to a formal business suit",
            ...     resolution="2K"
            ... )
        """
        if resolution not in ["1K", "2K", "4K"]:
            raise ValueError(f"Invalid resolution '{resolution}'. Must be '1K', '2K', or '4K'")
        
        # Prepare image
        pil_image = self._prepare_image_input(image)
        image_part = self._image_to_part(pil_image)
        
        # Build generation config
        config = {}
        
        # Image config with aspect ratio and image_size (resolution)
        image_config_params = {}
        if aspect_ratio:
            if aspect_ratio not in GEMINI_3_PRO_ASPECT_RATIOS:
                raise ValueError(
                    f"Invalid aspect ratio '{aspect_ratio}'. "
                    f"Valid options: {list(GEMINI_3_PRO_ASPECT_RATIOS.keys())}"
                )
            image_config_params['aspect_ratio'] = aspect_ratio
        
        # Add image_size (resolution) for Nano Banana Pro
        image_config_params['image_size'] = resolution
        
        if image_config_params:
            config['image_config'] = types.ImageConfig(**image_config_params)
        
        config.update(kwargs)
        
        # Generate content
        response = self.client.models.generate_content(
            model=self.MODEL_NAME,
            contents=[image_part, prompt],
            config=types.GenerateContentConfig(**config) if config else None
        )
        
        # Extract images
        images = []
        for part in response.parts:
            if part.inline_data is not None:
                image = part.as_image()
                images.append(image)
        
        if not images:
            raise ValueError("No images generated in response")
        
        return images
    
    def generate_multi_image(
        self,
        images: List[Union[str, io.BytesIO, Image.Image]],
        prompt: str,
        resolution: str = "1K",
        aspect_ratio: Optional[str] = None,
        **kwargs
    ) -> List[Image.Image]:
        """
        Generate image from multiple input images (composition & style transfer).
        
        Use multiple input images to compose a new scene or transfer the style
        from one image to another.
        
        Args:
            images: List of input images (file paths, URLs, PIL Images, file-like objects, or base64)
            prompt: Text description of how to combine/transform the images
            resolution: Resolution level. Options: "1K", "2K", "4K". Default: "1K"
                       This is passed as `image_size` to ImageConfig.
            aspect_ratio: Optional aspect ratio. Options: "1:1", "2:3", "3:2", "3:4", "4:3",
                         "4:5", "5:4", "9:16", "16:9", "21:9". Default: None
            **kwargs: Additional generation config parameters
        
        Returns:
            List of PIL Image objects
            
        Example:
            >>> adapter = NanoBananaProAdapter()
            >>> images = adapter.generate_multi_image(
            ...     images=["outfit1.jpg", "outfit2.jpg"],
            ...     prompt="Create a fashion catalog layout combining these clothing styles",
            ...     resolution="2K"
            ... )
        """
        if resolution not in ["1K", "2K", "4K"]:
            raise ValueError(f"Invalid resolution '{resolution}'. Must be '1K', '2K', or '4K'")
        
        # Prepare images
        image_parts = []
        for img in images:
            pil_image = self._prepare_image_input(img)
            image_parts.append(self._image_to_part(pil_image))
        
        # Build contents: images + prompt
        contents = image_parts + [prompt]
        
        # Build generation config
        config = {}
        
        # Image config with aspect ratio and image_size (resolution)
        image_config_params = {}
        if aspect_ratio:
            if aspect_ratio not in GEMINI_3_PRO_ASPECT_RATIOS:
                raise ValueError(
                    f"Invalid aspect ratio '{aspect_ratio}'. "
                    f"Valid options: {list(GEMINI_3_PRO_ASPECT_RATIOS.keys())}"
                )
            image_config_params['aspect_ratio'] = aspect_ratio
        
        # Add image_size (resolution) for Nano Banana Pro
        image_config_params['image_size'] = resolution
        
        if image_config_params:
            config['image_config'] = types.ImageConfig(**image_config_params)
        
        config.update(kwargs)
        
        # Generate content
        response = self.client.models.generate_content(
            model=self.MODEL_NAME,
            contents=contents,
            config=types.GenerateContentConfig(**config) if config else None
        )
        
        # Extract images
        images_result = []
        for part in response.parts:
            if part.inline_data is not None:
                image = part.as_image()
                images_result.append(image)
        
        if not images_result:
            raise ValueError("No images generated in response")
        
        return images_result
    
    def generate_batch(
        self,
        prompts: List[str],
        resolution: str = "1K",
        aspect_ratio: Optional[str] = None,
        **kwargs
    ) -> List[List[Image.Image]]:
        """
        Generate images in batch from multiple text prompts.
        
        Args:
            prompts: List of text prompts
            resolution: Resolution level for all images. Options: "1K", "2K", "4K". Default: "1K"
                       Note: Resolution may not be directly controllable via the SDK.
                       The model determines resolution automatically.
            aspect_ratio: Optional aspect ratio for all images
            **kwargs: Additional generation config parameters
        
        Returns:
            List of lists, where each inner list contains PIL Images for that prompt
            
        Example:
            >>> adapter = NanoBananaProAdapter()
            >>> results = adapter.generate_batch(
            ...     prompts=[
            ...         "A fashion model showcasing summer collection",
            ...         "Professional photography of formal wear",
            ...         "Casual street style outfit on a model"
            ...     ],
            ...     resolution="2K"
            ... )
        """
        results = []
        for prompt in prompts:
            images = self.generate_text_to_image(
                prompt=prompt,
                resolution=resolution,
                aspect_ratio=aspect_ratio,
                **kwargs
            )
            results.append(images)
        return results

