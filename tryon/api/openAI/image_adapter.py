"""
GPT Image (OpenAI Image Generation) API Adapter

Adapter for OpenAI's GPT Image models (GPT-Image-1 and GPT-Image-1.5).

These models support high-quality image generation and image editing using
text prompts and reference images. This adapter provides a clean, unified
interface for the following workflows:

- Text-to-Image: Generate images from text descriptions
- Image + Text-to-Image (Editing): Modify existing images using prompts
- Multi-Image Editing / Composition: Use multiple input images for edits
- Mask-based editing: Apply changes to specific regions of an image
- Output control: Size, quality, background, and multiple image generation

The adapter returns raw image bytes, allowing callers to save, transform,
or convert outputs (e.g., to PIL Images) as needed.

Reference:
https://platform.openai.com/docs/guides/image-generation

Models:
- GPT-Image-1 (gpt-image-1): High-quality image generation and editing
- GPT-Image-1.5 (gpt-image-1.5): Enhanced quality, better prompt understanding, improved consistency (default)

Examples:
    Text-to-image with latest model:
        >>> from tryon.api.openAI.image_adapter import GPTImageAdapter
        >>> adapter = GPTImageAdapter()  # Uses gpt-image-1.5 by default
        >>> images = adapter.generate_text_to_image(
        ...     prompt="A cinematic portrait of a person wearing a futuristic jacket",
        ...     size="1024x1024",
        ...     quality="high"
        ... )
        >>> with open("result.png", "wb") as f:
        ...     f.write(images[0])

    Using GPT-Image-1 specifically:
        >>> adapter = GPTImageAdapter(model_version="gpt-image-1")
        >>> images = adapter.generate_text_to_image(
        ...     prompt="A fashion model in elegant attire",
        ...     size="1024x1024"
        ... )

    Image editing:
        >>> adapter = GPTImageAdapter()
        >>> images = adapter.generate_image_edit(
        ...     images="person.jpg",
        ...     prompt="Change the jacket color to black leather"
        ... )
        >>> with open("edited.png", "wb") as f:
        ...     f.write(images[0])

    Mask-based editing:
        >>> images = adapter.generate_image_edit(
        ...     images="scene.png",
        ...     mask="mask.png",
        ...     prompt="Replace the masked area with a swimming pool"
        ... )

    Multi-image composition:
        >>> images = adapter.generate_image_edit(
        ...     images=["shirt.png", "logo.png"],
        ...     prompt="Add the logo to the shirt fabric naturally"
        ... )
"""

import base64
import io
import os
from typing import Optional, Union, List
from PIL import Image

try:
    from openai import OpenAI
    OPENAI_API_KEY = True
except ImportError:
    OPENAI_API_KEY = False
    OpenAI = None

VALID_SIZES = {"1024x1024", "1536x1024", "1024x1536", "auto"}
VALID_QUALITY = {"low", "high", "medium", "auto"}
INPUT_FIDELITY = {"low", "high"}
VALID_MODELS = {"gpt-image-1", "gpt-image-1.5"}


class GPTImageAdapter:
    """
    Adapter for OpenAI GPT Image API (supports both GPT-Image-1 and GPT-Image-1.5).
    
    Args:
        api_key (str, optional): OpenAI API key. If not provided, reads from OPENAI_API_KEY environment variable.
        model_version (str, optional): Model version to use. Options: "gpt-image-1", "gpt-image-1.5". 
                                       Defaults to "gpt-image-1.5" (latest and recommended).
    
    Examples:
        >>> # Use latest model (GPT-Image-1.5)
        >>> adapter = GPTImageAdapter()
        
        >>> # Use specific model version
        >>> adapter = GPTImageAdapter(model_version="gpt-image-1")
        
        >>> # With explicit API key
        >>> adapter = GPTImageAdapter(api_key="sk-...", model_version="gpt-image-1.5")
    """

    def __init__(self, api_key: Optional[str] = None, model_version: str = "gpt-image-1.5"):
        
        if not OPENAI_API_KEY:
            raise ImportError(
                "OpenAI SDK is not available. " \
                "Please install it with 'pip install openai'."
            )
        
        if model_version not in VALID_MODELS:
            raise ValueError(
                f"Invalid model_version: {model_version}. "
                f"Supported models: {VALID_MODELS}"
            )
        
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key must be provided either as a parameter or through the OPENAI_API_KEY environment variable.")
        
        self.model_version = model_version
        self.client = OpenAI(api_key=self.api_key)

    
    def prepare_image(self, image: Union[str, io.BytesIO, Image.Image]):

        if isinstance(image, str):
            return open(image, "rb")

        if isinstance(image, Image.Image):
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            buffer.seek(0)
            buffer.name = "image.png"   
            return buffer

        if isinstance(image, io.BytesIO):
            image.seek(0)
            image.name = "image.png"  
            return image

        raise TypeError(f"Unsupported image type: {type(image)}")

    
    def generate_text_to_image(
        self,
        prompt: str,
        size: str = "auto",
        quality: str = "auto",
        background: str = "auto",
        n: int = 1,
    ) -> List[bytes]:
        
        """
        Generate images from a text prompt using OpenAI's GPT Image 1 model.

        This method performs text-to-image generation and returns the generated
        images as raw byte data. The caller is responsible for saving or converting
        the returned bytes (e.g., into PIL Images).

        Args:
            prompt (str):
                Text description used to generate the image(s).
                Must be a non-empty string.

            size (str, optional):
                Output image resolution.
                Allowed values: {"1024x1024", "1536x1024", "1024x1536", "auto"}.
                Defaults to "auto".

            quality (str, optional):
                Image generation quality.
                Allowed values: {"low", "medium", "high", "auto"}.
                Defaults to "auto".

            background (str, optional):
                Background mode for the generated image.
                Common values include "auto" and "transparent".
                Defaults to "auto".

            n (int, optional):
                Number of images to generate.
                Must be >= 1.
                Defaults to 1.

        Returns:
            List[bytes]:
                A list of generated images as raw bytes.
                Each element represents a single image.

        Raises:
            ValueError:
                - If the prompt is empty
                - If `n` is less than 1
                - If `size` or `quality` is not a supported value

        Example:
            >>> adapter = GPTImageAdapter()
            >>> images = adapter.generate_text_to_image(
            ...     prompt="A cinematic portrait of a person wearing a leather jacket",
            ...     size="1024x1024",
            ...     quality="high",
            ...     n=2
            ... )
            >>> with open("image.png", "wb") as f:
            ...     f.write(images[0])
        """
        
        if not prompt:
            raise ValueError("Prompt is required for Text to Image generation.")
        
        if n < 1:
            raise ValueError("n must be >= 1.")
        
        if size not in VALID_SIZES:
            raise ValueError(f"Invalid Size: {size}, Available Options are: {VALID_SIZES}")
        
        if quality not in VALID_QUALITY:
            raise ValueError(f"Invalid quality: {quality}, Available Options are: {VALID_QUALITY}")

        response = self.client.images.generate(
            model=self.model_version,
            prompt=prompt,
            size=size,
            quality=quality,
            background=background,
            n=n,
        )

        output_images = []

        for item in response.data:
            image_bytes = base64.b64decode(item.b64_json)
            output_images.append(image_bytes)

        return output_images
    

    def generate_image_edit(
        self,
        images: List[Union[str, io.BytesIO, Image.Image]],
        prompt: Optional[str] = None,
        mask: Optional[Union[str, io.BytesIO, Image.Image]] = None,
        size: str = "auto",
        quality: str = "auto",
        background: str = "auto",
        input_fidelity: str = "low",
        n: int = 1,
    ) -> List[bytes]:
        
        """
        Edit or transform existing images using OpenAI's GPT Image 1 model.

        This method performs image-to-image generation by applying a text prompt
        to one or more input images. It supports multi-image editing, optional
        mask-based edits, and controlled output parameters such as size and quality.

        Input images may be provided as file paths, file-like objects, PIL Images,
        or base64-encoded strings. The method always returns raw image bytes.

        Args:
            images (Union[str, io.BytesIO, PIL.Image.Image, List[...]]):
                One or more input images to be edited.
                A single image may be passed directly or as a list.

            prompt (str, optional):
                Text instruction describing how the image(s) should be edited.
                If omitted, the model performs a minimal transformation.

            mask (Union[str, io.BytesIO, PIL.Image.Image], optional):
                Optional mask image defining the region to be edited.
                Masked areas will be modified while unmasked areas remain unchanged.

            size (str, optional):
                Output image resolution.
                Allowed values: {"1024x1024", "1536x1024", "1024x1536", "auto"}.
                Defaults to "auto".

            quality (str, optional):
                Image generation quality.
                Allowed values: {"low", "medium", "high", "auto"}.
                Defaults to "auto".

            background (str, optional):
                Background mode for the generated image.
                Common values include "auto" and "transparent".
                Defaults to "auto".

            input_fidelity (str, optional):
                Controls how strictly the model preserves the original image(s).
                Allowed values are defined in INPUT_FIDELITY.
                Defaults to "low".

            n (int, optional):
                Number of edited images to generate.
                Must be >= 1.
                Defaults to 1.

        Returns:
            List[bytes]:
                A list of edited images as raw byte data.

        Raises:
            ValueError:
                - If no images are provided
                - If `n` is less than 1
                - If `size`, `quality`, or `input_fidelity` is invalid

        Example:
            >>> adapter = GPTImageAdapter()
            >>> images = adapter.generate_image_edit(
            ...     images="person.jpg",
            ...     prompt="Change the jacket color to black leather",
            ...     quality="high"
            ... )
            >>> with open("edited.png", "wb") as f:
            ...     f.write(images[0])

            >>> images = adapter.generate_image_edit(
            ...     images=["scene.png"],
            ...     mask="mask.png",
            ...     prompt="Replace the masked area with a swimming pool"
            ... )
        """
        
        # If a single image is passed
        if not isinstance(images, list):
            images = [images]
        
        # Validation Check
        if len(images) == 0:
            raise ValueError("At least one image is required for Image Edit.")

        if n < 1:
            raise ValueError("n must be >= 1.")

        if size not in VALID_SIZES:
            raise ValueError(f"Invalid Size: {size}, Available Options are: {VALID_SIZES}")

        if quality not in VALID_QUALITY:
            raise ValueError(f"Invalid quality: {quality}, Available Options are: {VALID_QUALITY}")

        if input_fidelity not in INPUT_FIDELITY:
            raise ValueError(f"input_fidelity can only be {INPUT_FIDELITY}")


        # Prepare base images
        image_files = [self.prepare_image(img) for img in images]

        # Build request dynamically
        kwargs = {
            "model": self.model_version,
            "image": image_files,
            "prompt": prompt,
            "size": size,
            "quality": quality,
            "background": background,
            "input_fidelity": input_fidelity,
            "n": n,
        }

        # Attach mask only if it exists
        if mask:
            kwargs["mask"] = self.prepare_image(mask)

        response = self.client.images.edit(**kwargs)

        output_images = []

        for item in response.data:
            output_images.append(base64.b64decode(item.b64_json))

        return output_images