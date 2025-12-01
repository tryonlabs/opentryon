"""
Luma AI API adapter
"""

import os
import io
from io import BytesIO
from typing import Optional, Union, Dict, Any, List
from PIL import Image
import requests


try:
    from lumaai import LumaAI
    LUMA_AI_AVAILABLE = True
except ImportError:
    LUMA_AI_AVAILABLE = False
    LumaAI = None

# Supported aspect ratios for Luma AI
LUMA_AI_ASPECT_RATIO = {
    "1:1": {"resolution": "1536x1536"},
    "3:4": {"resolution": "1344x1792"},
    "4:3": {"resolution": "1792x1344"},
    "9:16": {"resolution": "1152x2048"},
    "16:9": {"resolution": "2048x1152"},
    "9:21": {"resolution": "1024x2432"},
    "21:9": {"resolution": "2432x1024"},
}

class LumaAIAdapter:
    """
    Adapter for Luma AI API.
    """

    def __init__(self, auth_token: Optional[str] = None):
        """
        Initialize the Luma AI adapter.

        Args:
            api_key: Luma AI API key. Defaults to LUMA_AI_API_KEY environment variable.
                If not provided via parameter or environment variable, raises ValueError.
        
        Raises:
            ValueError: If API key is not provided.
            ImportError: If lumaai is not available.

        Example:
            >>> # Using environment variable
            >>> import os
            >>> os.environ['LUMA_AI_API_KEY'] = 'your_api_key'
            >>> adapter = LumaAIAdapter()
            
            >>> # Using parameter
            >>> adapter = LumaAIAdapter(api_key="your_api_key")    
        """

        if not LUMA_AI_AVAILABLE:
            raise ImportError(
                "Luma AI library is not available. " \
                "Please install it with 'pip install lumaai'."
            )
        
        self.auth_token = auth_token or os.getenv("LUMA_AI_API_KEY")
        if not self.auth_token:
            raise ValueError("Luma AI API key must be provided either as a parameter or through the LUMA_AI_API_KEY environment variable.")
        
        self.client = LumaAI(auth_token=self.auth_token)

    
    def _prepare_image_input(self, image_input: Union[str, io.BytesIO, Image.Image]) -> str:
        """
        LumaAI requires a CDN URL. No local files, no base64, no bytes, no PIL Images.
        This function normalizes input into a URL.

        Args:
            image_input: Image input in one of the following formats:
                       - File path (str): Path to local image file
                       - URL (str): HTTP/HTTPS URL to image
                       - Base64 string (str): Base64-encoded image data
                       - File-like object (io.BytesIO): BytesIO or similar object
                       - PIL Image: PIL Image object

        Returns:
            str: CDN URL pointing to the uploaded image
        """
        # Case 1: Already a URL
        if isinstance(image_input, str) and image_input.startswith(("http://", "https://")):
            return image_input

        # Case 2: Local file path
        if isinstance(image_input, str) and os.path.exists(image_input):
            return self._upload_to_cdn(open(image_input, "rb"))

        # Case 3: File-like object (BytesIO)
        if hasattr(image_input, "read"):
            image_file = image_input
            image_file.seek(0)
            return self._upload_to_cdn(image_file)

        # Case 4: PIL Image
        if isinstance(image_input, Image.Image):
            buffer = io.BytesIO()
            image_input.save(buffer, format="PNG")
            buffer.seek(0)
            return self._upload_to_cdn(buffer)

        raise ValueError(
            "Invalid image input: must be a file path, URL, PIL Image, file-like object, or base64 string."
        )

    def _upload_to_cdn(self, file_obj: io.BytesIO) -> str:
        """
        Uploads file_obj to your CDN and returns a public URL.
        """
        raise NotImplementedError("CDN upload must be implemented before using local images.")
    
    
    def generate_text_to_image(
            self,
            prompt: str,
            model: Optional[str] = 'photon-1',
            aspect_ratio: Optional[str] = None,
    ) -> List[Image.Image]:
        """
        Generate Image(s) from text prompt (text-to-image).
        
        Args:
            prompt: Text prompt to generate image(s).
            aspect_ratio: Optional aspect ratio. Options: 
                "1:1", "3:4", "4:3", "9:16", "16:9", "9:21", "21:9".
                Defaults to "1:1" if not provided.
        
        Returns:
            List of PIL Image objects.
        
        Example:
            >>> adapter = LumaAIAdapter()
            >>> images = adapter.generate_text_to_image(
            ...     prompt="A stylish fashion model wearing a modern casual outfit",
            ...     aspect_ratio="16:9"
            ... )
            >>> images[0].save("result.png")
        """

        if not prompt:
            raise ValueError("Prompt is required")
        
        if len(prompt) < 3 or len(prompt) > 5000:
            raise ValueError("Prompt should have a minimum of 3 characters and a maximum of 5000 characters.")

        if aspect_ratio:
            if aspect_ratio not in LUMA_AI_ASPECT_RATIO:
                raise ValueError(
                    f"Invalid aspect ratio '{aspect_ratio}'. "
                    f"Valid options are: {', '.join(LUMA_AI_ASPECT_RATIO.keys())}."
                )

        # Create Generation
        generation = self.client.generations.image.create(
            prompt=prompt,
            model=model,
            aspect_ratio=aspect_ratio
        )

        # --- Polling Loop ---
        while True:
            gen = self.client.generations.get(id=generation.id)

            if gen.state == "completed":
                break
            if gen.state == "failed":
                raise RuntimeError(f"Generation failed: {gen.failure_reason}")
        
        # Final Image URL
        image_url = gen.assets.image
        if not image_url:
            raise ValueError("No image returned by Luma AI.")
        
        images = []

        # Download the image
        response = requests.get(image_url, stream=True)
        img_bytes = response.content
        img = Image.open(BytesIO(img_bytes))
        images.append(img)

        return images
    
    
    def generate_with_image_reference(
            self,
            image_ref: List[Dict[str, Any]],
            prompt: str,
            model: Optional[str] = 'photon-1',
            aspect_ratio: Optional[str] = None,
    ) -> List[Image.Image]:
        """
        Generate Image(s) from text prompt with image reference. 
        This feature is very useful when you want to create variations 
        of an image or when you have a concept that is hard to describe, 
        but easy to visualize. You can use the weight key to tune the 
        influence of the images.
        
        Args:
            image_refs: List of dictionaries with "image" and "weight" keys.
                Example: [{"url": "http://example.com/image.jpg", "weight": 1.0}].
            prompt: Text prompt to generate image(s).
            aspect_ratio: Optional aspect ratio. Options: 
                "1:1", "3:4", "4:3", "9:16", "16:9", "9:21", "21:9".
                Defaults to "1:1" if not provided.
        
        Returns:
            List of PIL Image objects.
        
        Example:
            >>> adapter = LumaAIAdapter()
            >>> images = adapter.generate_with_image_reference(
            ...     image=[{"url": "http://example.com/image.jpg", "weight": 1.0}],
            ...     prompt="A stylish fashion model wearing a modern casual outfit",
            ...     aspect_ratio="16:9"
            ... )
            >>> images[0].save("result.png")
        """

        # Validation of input parameters
        if not prompt:
            raise ValueError("Prompt is required")
        
        if len(prompt) < 3 or len(prompt) > 5000:
            raise ValueError("Prompt should have a minimum of 3 characters and a maximum of 5000 characters.")  

        if aspect_ratio:
            if aspect_ratio not in LUMA_AI_ASPECT_RATIO:
                raise ValueError(
                    f"Invalid aspect ratio '{aspect_ratio}'. "
                    f"Valid options are: {', '.join(LUMA_AI_ASPECT_RATIO.keys())}."
                )
        
        if not isinstance(image_ref, list) or len(image_ref) == 0:
            raise ValueError("Image references must be a non-empty list of dictionaries with 'url' and 'weight' keys.")
        
        if len(image_ref) > 4:
            raise ValueError("Luma AI supports a maximum of 4 image references.")
        
        img_ref_list = []

        for ref in image_ref:
            if not isinstance(ref, dict):
                raise ValueError("Each image reference must be a dictionary with 'url' and Optional 'weight' keys.")
            
            url = ref.get("url")
            if url is None:
                raise ValueError("Image reference must contain a 'url' key.")
            
            cdn_url = self._prepare_image_input(url)
            
            weight = ref.get("weight", 0.85)
            if not isinstance(weight, (int, float)) or not (0 <= weight <= 1):
                raise ValueError("Weight must be a float between 0 and 1.")
            
            img_ref_list.append({"url": cdn_url, "weight": weight})
        
        generation = self.client.generations.image.create(
            prompt=prompt,
            model=model,
            aspect_ratio=aspect_ratio,
            image_ref=img_ref_list
        )

        # --- Polling Loop --- 
        while True:
            gen = self.client.generations.get(id=generation.id)

            if gen.state == "completed":
                break
            if gen.state == "failed":
                raise RuntimeError(f"Generation failed: {gen.failure_reason}")
        
        # Final Image URL
        image_url = gen.assets.image
        if not image_url:
            raise ValueError("No image returned by Luma AI.")
        
        images = []

        # Download the image
        response = requests.get(image_url, stream=True)
        img_bytes = response.content
        img = Image.open(BytesIO(img_bytes))
        images.append(img)

        return images
    
    
    def generate_with_style_reference(
            self,
            prompt: str,
            style_ref: List[Dict[str, float | str]],
            model: Optional[str] = 'photon-1',
            aspect_ratio: Optional[str] = None,
    ) -> List[Image.Image]:
        """
        Generate Image(s) from text prompt with style reference.
        This feature is used to apply a specific 
        style to the generation. You can use the weight key to 
        tune the influence of the style image reference.
        
        Args:
            prompt: Text prompt to generate image(s).
            style_ref: List of dictionaries with "url" and "weight" keys.
                Example: [{"url": "http://example.com/style.jpg", "weight": 1.0}].
            aspect_ratio: Optional aspect ratio. Options: 
                "1:1", "3:4", "4:3", "9:16", "16:9", "9:21", "21:9".
                Defaults to "1:1" if not provided.
        
        Returns:
            List of PIL Image objects.

        Example:
            >>> adapter = LumaAIAdapter()
            >>> images = adapter.generate_with_style_reference(
            ...     prompt="A stylish fashion model wearing a modern casual outfit",
            ...     style_ref=[{"url": "http://example.com/style.jpg", "weight": 1.0}],
            ...     aspect_ratio="16:9"
            ... )
            >>> images[0].save("result.png")
        """

        # Validation of input parameters
        if not prompt:
            raise ValueError("Prompt is required")
        
        if len(prompt) < 3 or len(prompt) > 5000:
            raise ValueError("Prompt should have a minimum of 3 characters and a maximum of 5000 characters.")  

        if aspect_ratio:
            if aspect_ratio not in LUMA_AI_ASPECT_RATIO:
                raise ValueError(
                    f"Invalid aspect ratio '{aspect_ratio}'. "
                    f"Valid options are: {', '.join(LUMA_AI_ASPECT_RATIO.keys())}."
                )
        
        if not isinstance(style_ref, list) or len(style_ref) == 0:
            raise ValueError("Image references must be a non-empty list of dictionaries with 'url' and 'weight' keys.")
        
        if len(style_ref) > 4:
            raise ValueError("Luma AI supports a maximum of 4 image references.")
        
        img_ref_list = []

        for ref in style_ref:
            if not isinstance(ref, dict):
                raise ValueError("Each image reference must be a dictionary with 'url' and Optional 'weight' keys.")
            
            url = ref.get("url")
            if url is None:
                raise ValueError("Image reference must contain a 'url' key.")
            
            cdn_url = self._prepare_image_input(url)
            
            weight = ref.get("weight", 0.85)
            if not isinstance(weight, (int, float)) or not (0 <= weight <= 1):
                raise ValueError("Weight must be a float between 0 and 1.")
            
            img_ref_list.append({"url": cdn_url, "weight": weight})
        
        generation = self.client.generations.image.create(
            prompt=prompt,
            model=model,
            aspect_ratio=aspect_ratio,
            image_ref=img_ref_list
        )

        # --- Polling Loop --- 
        while True:
            gen = self.client.generations.get(id=generation.id)

            if gen.state == "completed":
                break
            if gen.state == "failed":
                raise RuntimeError(f"Generation failed: {gen.failure_reason}")
        
        # Final Image URL
        image_url = gen.assets.image
        if not image_url:
            raise ValueError("No image returned by Luma AI.")
        
        images = []

        # Download the image
        response = requests.get(image_url, stream=True)
        img_bytes = response.content
        img = Image.open(BytesIO(img_bytes))
        images.append(img)

        return images
    

    def generate_with_character_reference(
    self,
    prompt: str,
    character_ref: dict[str, Any],
    model: Optional[str] = 'photon-1',
    aspect_ratio: Optional[str] = None,
) -> List[Image.Image]:
        """
        Generate an image using LumaAI character reference.

        Args:
            prompt: Text prompt to generate image(s).
            character_ref must follow:
            {
                "identity0": {
                    "images": [URL1, URL2, ...]
                },
                "identity1": {
                    "images": [...],
                }
            }
            aspect_ratio: Optional aspect ratio. Options: 
                "1:1", "3:4", "4:3", "9:16", "16:9", "9:21", "21:9".
                Defaults to "1:1" if not provided.
            
            Returns:
            List of PIL Image objects.

            Example:
            >>> adapter = LumaAIAdapter()
            >>> character_ref = {
            ...     "identity0": {
            ...         "images": ["http://example.com/image1.jpg", "http://example.com/image2.jpg"]
            ...     },
            ...     "identity1": {
            ...         "images": ["http://example.com/image3.jpg"]
            ...     }
            ... }
            >>> images = adapter.generate_with_character_reference(
            ...     prompt="A stylish fashion model wearing a modern casual outfit",
            ...     character_ref=character_ref,
            ...     aspect_ratio="16:9"
            ... )
            >>> images[0].save("result.png")
        """

        if not prompt:
            raise ValueError("Prompt is required")
        
        if len(prompt) < 3 or len(prompt) > 5000:
            raise ValueError("Prompt should have a minimum of 3 characters and a maximum of 5000 characters.")  

        if aspect_ratio:
            if aspect_ratio not in LUMA_AI_ASPECT_RATIO:
                raise ValueError(
                    f"Invalid aspect ratio '{aspect_ratio}'. "
                    f"Valid options are: {', '.join(LUMA_AI_ASPECT_RATIO.keys())}."
                )
            
        if not isinstance(character_ref, dict):
            raise ValueError("character_ref must be a dict mapping identity -> {images: [...]}")
        
        clean_character_ref = {}

        for identity, block in character_ref.items():
            if not isinstance(identity, str):
                raise ValueError("Identity keys must be strings, e.g., 'identity0'")

            if not isinstance(block, dict) or "images" not in block:
                raise ValueError(f"{identity} must map to a dict containing an 'images' list")

            urls = block["images"]
            if not isinstance(urls, list) or not urls:
                raise ValueError(f"{identity} -> 'images' must be a non-empty list")

            # Validate and clean all URLs
            clean_urls = []

            for img_input in urls:
                cdn_url = self._prepare_image_input(img_input)
                clean_urls.append(cdn_url)

            clean_character_ref[identity] = {"images": clean_urls}

        # --- Luma API call ---
        generation = self.client.generations.image.create(
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            character_ref=clean_character_ref,
            model=model,
        )

        # --- Polling ---
        while True:
            generation = self.client.generations.get(id=generation.id)

            if generation.state == "completed":
                break
            if generation.state == "failed":
                raise RuntimeError(f"Generation failed: {generation.failure_reason}")
            
        images = []

        # --- Download the final image ---
        image_url = generation.assets.image
        image_bytes = requests.get(image_url).content
        img = Image.open(BytesIO(image_bytes))
        images.append(img)

        return images
    

    def generate_with_modify_image(
    self,
    image: Union[str, io.BytesIO, Image.Image],
    prompt: str,
    weight: float,
    model: Optional[str] = 'photon-1',
    aspect_ratio: Optional[str] = None
) -> List[Image.Image]:
        """
        Modify an input image using LumaAI's modify_image_ref.
        Supports local paths, URLs, BytesIO, PIL images, etc.
        """

        # --- Prompt validation ---
        if not prompt:
            raise ValueError("Prompt is required")
        
        if len(prompt) < 3 or len(prompt) > 5000:
            raise ValueError("Prompt should have a minimum of 3 characters and a maximum of 5000 characters.")
        
        if aspect_ratio:
            if aspect_ratio not in LUMA_AI_ASPECT_RATIO:
                raise ValueError(
                    f"Invalid aspect ratio '{aspect_ratio}'. "
                    f"Valid options are: {', '.join(LUMA_AI_ASPECT_RATIO.keys())}."
                )

        # --- Weight validation ---
        if not isinstance(weight, (int, float)) or not (0 <= weight <= 1):
            raise ValueError("weight must be a float between 0 and 1")

        # --- Prepare image (convert any format to CDN URL) ---
        cdn_url = self._prepare_image_input(image)

        generation = self.client.generations.image.create(
            prompt=prompt,
            model=model,
            aspect_ratio=aspect_ratio,
            modify_image_ref={
                "url": cdn_url,
                "weight": float(weight),
            },
        )

        # --- Polling loop ---
        while True:
            gen = self.client.generations.get(id=generation.id)

            if gen.state == "completed":
                break
            if gen.state == "failed":
                raise RuntimeError(f"Generation failed: {gen.failure_reason}")
        
        images = []

        # --- Download final image ---
        image_url = gen.assets.image
        img_bytes = requests.get(image_url, stream=True)
        img = Image.open(BytesIO(img_bytes.content))
        images.append(img)

        return images
