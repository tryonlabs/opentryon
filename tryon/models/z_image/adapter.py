"""
Z-Image Model Adapter

Adapter for the Z-Image family of image generation models from Tongyi-MAI.

Z-Image is a powerful and highly efficient image generation model family with 6B parameters.
It supports photorealistic image generation, bilingual text rendering (English & Chinese),
and robust instruction adherence.

Model Variants:
    - Z-Image-Turbo: Distilled version with 8 NFEs, sub-second inference, fits in 16GB VRAM
    - Z-Image: Foundation model with high-quality generation, rich aesthetics, diversity
    - Z-Image-Omni-Base: Versatile foundation for both generation and editing tasks
    - Z-Image-Edit: Fine-tuned specifically for image editing tasks

Reference: https://github.com/Tongyi-MAI/Z-Image

Requirements:
    pip install torch diffusers
    pip install git+https://github.com/huggingface/diffusers  # For latest Z-Image support

Example:
    >>> from tryon.models.z_image import ZImageAdapter
    >>> 
    >>> # Text-to-image with Z-Image-Turbo (fastest)
    >>> adapter = ZImageAdapter(model_variant="turbo")
    >>> images = adapter.generate(
    ...     prompt="A cute baby polar bear in a snowy landscape"
    ... )
    >>> images[0].save("polar_bear.png")
    >>> 
    >>> # High-quality generation with Z-Image
    >>> adapter = ZImageAdapter(model_variant="base")
    >>> images = adapter.generate(
    ...     prompt="Young Chinese woman in red Hanfu",
    ...     negative_prompt="blurry, low quality",
    ...     num_inference_steps=50,
    ...     guidance_scale=4.0
    ... )
"""

import os
import io
from enum import Enum
from typing import Optional, Union, List, Dict, Any, Literal
from dataclasses import dataclass, field
from PIL import Image

import torch

try:
    from diffusers import ZImagePipeline
    DIFFUSERS_AVAILABLE = True
except ImportError:
    DIFFUSERS_AVAILABLE = False
    ZImagePipeline = None


class ZImageModelVariant(str, Enum):
    """Z-Image model variants."""
    TURBO = "turbo"
    BASE = "base"
    OMNI_BASE = "omni_base"
    EDIT = "edit"


@dataclass
class ZImageModelConfig:
    """Configuration for a Z-Image model variant."""
    model_id: str
    default_steps: int
    default_guidance_scale: float
    supports_negative_prompt: bool
    supports_cfg_normalization: bool
    supports_editing: bool
    min_steps: int = 1
    max_steps: int = 100
    min_guidance: float = 0.0
    max_guidance: float = 20.0
    description: str = ""


# Model configurations for each variant
MODEL_CONFIGS: Dict[ZImageModelVariant, ZImageModelConfig] = {
    ZImageModelVariant.TURBO: ZImageModelConfig(
        model_id="Tongyi-MAI/Z-Image-Turbo",
        default_steps=9,  # Results in 8 DiT forwards
        default_guidance_scale=0.0,  # Guidance should be 0 for Turbo
        supports_negative_prompt=False,
        supports_cfg_normalization=False,
        supports_editing=False,
        min_steps=1,
        max_steps=20,
        min_guidance=0.0,
        max_guidance=0.0,
        description="Distilled version with 8 NFEs, sub-second inference, 16GB VRAM"
    ),
    ZImageModelVariant.BASE: ZImageModelConfig(
        model_id="Tongyi-MAI/Z-Image",
        default_steps=50,
        default_guidance_scale=4.0,
        supports_negative_prompt=True,
        supports_cfg_normalization=True,
        supports_editing=False,
        min_steps=28,
        max_steps=100,
        min_guidance=3.0,
        max_guidance=5.0,
        description="Foundation model with high-quality generation, rich aesthetics"
    ),
    ZImageModelVariant.OMNI_BASE: ZImageModelConfig(
        model_id="Tongyi-MAI/Z-Image-Omni-Base",
        default_steps=50,
        default_guidance_scale=4.0,
        supports_negative_prompt=True,
        supports_cfg_normalization=True,
        supports_editing=True,
        min_steps=28,
        max_steps=100,
        min_guidance=3.0,
        max_guidance=5.0,
        description="Versatile foundation for both generation and editing tasks"
    ),
    ZImageModelVariant.EDIT: ZImageModelConfig(
        model_id="Tongyi-MAI/Z-Image-Edit",
        default_steps=50,
        default_guidance_scale=4.0,
        supports_negative_prompt=True,
        supports_cfg_normalization=True,
        supports_editing=True,
        min_steps=28,
        max_steps=100,
        min_guidance=3.0,
        max_guidance=5.0,
        description="Fine-tuned specifically for image editing tasks"
    ),
}


@dataclass
class GenerationParams:
    """Parameters for image generation."""
    prompt: str
    negative_prompt: Optional[str] = None
    width: int = 1024
    height: int = 1024
    num_inference_steps: Optional[int] = None
    guidance_scale: Optional[float] = None
    seed: Optional[int] = None
    cfg_normalization: Optional[bool] = None
    # Additional parameters for future extensibility
    extra_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EditingParams:
    """Parameters for image editing."""
    prompt: str
    image: Union[str, Image.Image, io.BytesIO]
    negative_prompt: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    num_inference_steps: Optional[int] = None
    guidance_scale: Optional[float] = None
    seed: Optional[int] = None
    cfg_normalization: Optional[bool] = None
    # Editing-specific parameters
    strength: float = 0.8  # How much to transform the image
    # Additional parameters for future extensibility
    extra_params: Dict[str, Any] = field(default_factory=dict)


class ZImageAdapter:
    """
    Adapter for Z-Image family of image generation models.
    
    This adapter provides a unified interface for all Z-Image model variants,
    handling the different parameter requirements and capabilities of each variant.
    
    Args:
        model_variant: Which Z-Image variant to use. Options:
            - "turbo": Z-Image-Turbo (fastest, 8 steps)
            - "base": Z-Image (highest quality, 50 steps)
            - "omni_base": Z-Image-Omni-Base (generation + editing)
            - "edit": Z-Image-Edit (image editing)
        device: Device to run the model on ("cuda", "cpu", "mps"). Defaults to "cuda".
        torch_dtype: Torch dtype for model weights. Defaults to torch.bfloat16.
        enable_cpu_offload: Enable CPU offloading for memory-constrained devices.
        enable_attention_slicing: Enable attention slicing to reduce memory usage.
        enable_flash_attention: Enable Flash Attention for better efficiency.
        compile_model: Compile the model for faster inference (first run slower).
        custom_model_id: Override the default model ID for the variant.
    
    Raises:
        ImportError: If diffusers is not installed or doesn't support ZImagePipeline.
        ValueError: If an invalid model variant is specified.
    
    Example:
        >>> adapter = ZImageAdapter(model_variant="turbo")
        >>> images = adapter.generate(prompt="A cute baby polar bear")
        >>> images[0].save("output.png")
    """
    
    def __init__(
        self,
        model_variant: Union[str, ZImageModelVariant] = "turbo",
        device: str = "cuda",
        torch_dtype: torch.dtype = torch.bfloat16,
        enable_cpu_offload: bool = False,
        enable_attention_slicing: bool = False,
        enable_flash_attention: bool = False,
        compile_model: bool = False,
        custom_model_id: Optional[str] = None,
    ):
        if not DIFFUSERS_AVAILABLE:
            raise ImportError(
                "diffusers library is not available or doesn't support ZImagePipeline. "
                "Please install the latest version: pip install git+https://github.com/huggingface/diffusers"
            )
        
        # Parse model variant
        if isinstance(model_variant, str):
            try:
                self.model_variant = ZImageModelVariant(model_variant.lower())
            except ValueError:
                valid_variants = [v.value for v in ZImageModelVariant]
                raise ValueError(
                    f"Invalid model variant: {model_variant}. "
                    f"Valid options: {valid_variants}"
                )
        else:
            self.model_variant = model_variant
        
        # Get model configuration
        self.config = MODEL_CONFIGS[self.model_variant]
        
        # Override model ID if custom one provided
        self.model_id = custom_model_id or self.config.model_id
        
        # Store settings
        self.device = device
        self.torch_dtype = torch_dtype
        self.enable_cpu_offload = enable_cpu_offload
        self.enable_attention_slicing = enable_attention_slicing
        self.enable_flash_attention = enable_flash_attention
        self.compile_model = compile_model
        
        # Pipeline will be loaded lazily
        self._pipeline = None
    
    @property
    def pipeline(self):
        """Lazy-load the pipeline when first accessed."""
        if self._pipeline is None:
            self._load_pipeline()
        return self._pipeline
    
    def _load_pipeline(self) -> None:
        """Load the Z-Image pipeline."""
        print(f"Loading Z-Image model: {self.model_id}...")
        
        self._pipeline = ZImagePipeline.from_pretrained(
            self.model_id,
            torch_dtype=self.torch_dtype,
            low_cpu_mem_usage=False,
        )
        
        # Move to device
        if self.enable_cpu_offload:
            self._pipeline.enable_model_cpu_offload()
        else:
            self._pipeline.to(self.device)
        
        # Apply optimizations
        if self.enable_attention_slicing:
            self._pipeline.enable_attention_slicing()
        
        if self.enable_flash_attention:
            try:
                self._pipeline.transformer.set_attention_backend("flash")
            except Exception as e:
                print(f"Warning: Could not enable Flash Attention: {e}")
        
        if self.compile_model:
            try:
                self._pipeline.transformer.compile()
                print("Model compiled successfully (first inference will be slower)")
            except Exception as e:
                print(f"Warning: Could not compile model: {e}")
        
        print(f"Model loaded successfully on {self.device}")
    
    def _prepare_image_input(
        self,
        image_input: Union[str, Image.Image, io.BytesIO]
    ) -> Image.Image:
        """
        Prepare image input for editing operations.
        
        Args:
            image_input: Image as file path, PIL Image, or BytesIO
        
        Returns:
            PIL.Image.Image: Loaded image
        """
        if isinstance(image_input, Image.Image):
            return image_input
        
        if isinstance(image_input, io.BytesIO):
            image_input.seek(0)
            return Image.open(image_input)
        
        if isinstance(image_input, str):
            if image_input.startswith(("http://", "https://")):
                import requests
                response = requests.get(image_input, timeout=60)
                response.raise_for_status()
                return Image.open(io.BytesIO(response.content))
            else:
                return Image.open(image_input)
        
        raise ValueError(
            f"Invalid image input type: {type(image_input)}. "
            "Expected file path, URL, PIL Image, or BytesIO."
        )
    
    def _get_generator(self, seed: Optional[int]) -> Optional[torch.Generator]:
        """Create a generator with the given seed."""
        if seed is not None:
            return torch.Generator(self.device).manual_seed(seed)
        return None
    
    def generate(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        width: int = 1024,
        height: int = 1024,
        num_inference_steps: Optional[int] = None,
        guidance_scale: Optional[float] = None,
        seed: Optional[int] = None,
        cfg_normalization: Optional[bool] = None,
        **kwargs
    ) -> List[Image.Image]:
        """
        Generate images from a text prompt.
        
        Args:
            prompt: Text description of the image to generate.
            negative_prompt: Text describing what to avoid in the image.
                           Only supported by base, omni_base, and edit variants.
            width: Width of the output image. Defaults to 1024.
            height: Height of the output image. Defaults to 1024.
            num_inference_steps: Number of denoising steps. If None, uses model default.
            guidance_scale: Classifier-free guidance scale. If None, uses model default.
            seed: Random seed for reproducibility. Defaults to None (random).
                 Uses torch.Generator internally as per Z-Image documentation.
            cfg_normalization: Whether to use CFG normalization.
                             False for stylism, True for realism.
                             Only supported by base, omni_base, and edit variants.
            **kwargs: Additional parameters passed to the pipeline.
        
        Returns:
            List[Image.Image]: List of generated PIL Image objects.
        
        Raises:
            ValueError: If unsupported parameters are used for the model variant.
        
        Example:
            >>> adapter = ZImageAdapter(model_variant="turbo")
            >>> images = adapter.generate(
            ...     prompt="A photograph of a red fox in an autumn forest",
            ...     width=1024,
            ...     height=1024,
            ...     seed=42
            ... )
            >>> images[0].save("fox.png")
        """
        # Validate parameters for model variant
        if negative_prompt and not self.config.supports_negative_prompt:
            print(
                f"Warning: negative_prompt is not supported by {self.model_variant.value}. "
                "It will be ignored."
            )
            negative_prompt = None
        
        if cfg_normalization is not None and not self.config.supports_cfg_normalization:
            print(
                f"Warning: cfg_normalization is not supported by {self.model_variant.value}. "
                "It will be ignored."
            )
            cfg_normalization = None
        
        # Use defaults if not specified
        if num_inference_steps is None:
            num_inference_steps = self.config.default_steps
        
        if guidance_scale is None:
            guidance_scale = self.config.default_guidance_scale
        
        # Build pipeline arguments (matching Z-Image documentation)
        pipe_kwargs = {
            "prompt": prompt,
            "height": height,
            "width": width,
            "num_inference_steps": num_inference_steps,
            "guidance_scale": guidance_scale,
        }
        
        # Add optional parameters
        if negative_prompt and self.config.supports_negative_prompt:
            pipe_kwargs["negative_prompt"] = negative_prompt
        
        if cfg_normalization is not None and self.config.supports_cfg_normalization:
            pipe_kwargs["cfg_normalization"] = cfg_normalization
        
        # Add generator for reproducibility (Z-Image uses generator, not seed directly)
        generator = self._get_generator(seed)
        if generator:
            pipe_kwargs["generator"] = generator
        
        # Add any extra kwargs
        pipe_kwargs.update(kwargs)
        
        # Generate images
        output = self.pipeline(**pipe_kwargs)
        
        return output.images
    
    def edit(
        self,
        prompt: str,
        image: Union[str, Image.Image, io.BytesIO],
        negative_prompt: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        num_inference_steps: Optional[int] = None,
        guidance_scale: Optional[float] = None,
        strength: float = 0.8,
        seed: Optional[int] = None,
        cfg_normalization: Optional[bool] = None,
        **kwargs
    ) -> List[Image.Image]:
        """
        Edit an existing image using a text prompt.
        
        This method is only available for model variants that support editing
        (omni_base and edit).
        
        Note: Z-Image-Edit and Z-Image-Omni-Base are not yet released.
        This method is prepared for when they become available.
        
        Args:
            prompt: Text description of the desired edit.
            image: Input image to edit (file path, URL, PIL Image, or BytesIO).
            negative_prompt: Text describing what to avoid.
            width: Output width. If None, uses input image width.
            height: Output height. If None, uses input image height.
            num_inference_steps: Number of denoising steps. If None, uses model default.
            guidance_scale: Classifier-free guidance scale. If None, uses model default.
            strength: How much to transform the image (0.0-1.0). Defaults to 0.8.
            seed: Random seed for reproducibility.
                 Uses torch.Generator internally as per Z-Image documentation.
            cfg_normalization: Whether to use CFG normalization.
            **kwargs: Additional parameters passed to the pipeline.
        
        Returns:
            List[Image.Image]: List of edited PIL Image objects.
        
        Raises:
            ValueError: If the model variant doesn't support editing.
        
        Example:
            >>> adapter = ZImageAdapter(model_variant="edit")
            >>> images = adapter.edit(
            ...     prompt="Add sunglasses to the person",
            ...     image="portrait.png",
            ...     strength=0.7,
            ...     seed=42
            ... )
            >>> images[0].save("edited.png")
        """
        if not self.config.supports_editing:
            raise ValueError(
                f"Image editing is not supported by {self.model_variant.value}. "
                f"Use 'omni_base' or 'edit' variant for editing tasks."
            )
        
        # Load and prepare the input image
        input_image = self._prepare_image_input(image)
        
        # Use image dimensions if not specified
        if width is None:
            width = input_image.width
        if height is None:
            height = input_image.height
        
        # Use defaults if not specified
        if num_inference_steps is None:
            num_inference_steps = self.config.default_steps
        
        if guidance_scale is None:
            guidance_scale = self.config.default_guidance_scale
        
        # Build pipeline arguments (matching Z-Image documentation)
        pipe_kwargs = {
            "prompt": prompt,
            "image": input_image,
            "height": height,
            "width": width,
            "num_inference_steps": num_inference_steps,
            "guidance_scale": guidance_scale,
            "strength": strength,
        }
        
        # Add optional parameters
        if negative_prompt:
            pipe_kwargs["negative_prompt"] = negative_prompt
        
        if cfg_normalization is not None:
            pipe_kwargs["cfg_normalization"] = cfg_normalization
        
        # Add generator for reproducibility (Z-Image uses generator, not seed directly)
        generator = self._get_generator(seed)
        if generator:
            pipe_kwargs["generator"] = generator
        
        # Add any extra kwargs
        pipe_kwargs.update(kwargs)
        
        # Generate edited images
        output = self.pipeline(**pipe_kwargs)
        
        return output.images
    
    def generate_from_params(self, params: GenerationParams) -> List[Image.Image]:
        """
        Generate images using a GenerationParams object.
        
        This method is useful for structured parameter passing and future extensibility.
        
        Args:
            params: GenerationParams object containing all generation parameters.
        
        Returns:
            List[Image.Image]: List of generated PIL Image objects.
        
        Example:
            >>> params = GenerationParams(
            ...     prompt="A beautiful landscape",
            ...     width=1024,
            ...     height=768,
            ...     seed=42
            ... )
            >>> images = adapter.generate_from_params(params)
        """
        return self.generate(
            prompt=params.prompt,
            negative_prompt=params.negative_prompt,
            width=params.width,
            height=params.height,
            num_inference_steps=params.num_inference_steps,
            guidance_scale=params.guidance_scale,
            seed=params.seed,
            cfg_normalization=params.cfg_normalization,
            **params.extra_params
        )
    
    def edit_from_params(self, params: EditingParams) -> List[Image.Image]:
        """
        Edit an image using an EditingParams object.
        
        This method is useful for structured parameter passing and future extensibility.
        
        Args:
            params: EditingParams object containing all editing parameters.
        
        Returns:
            List[Image.Image]: List of edited PIL Image objects.
        
        Example:
            >>> params = EditingParams(
            ...     prompt="Add a hat to the person",
            ...     image="portrait.png",
            ...     strength=0.7
            ... )
            >>> images = adapter.edit_from_params(params)
        """
        return self.edit(
            prompt=params.prompt,
            image=params.image,
            negative_prompt=params.negative_prompt,
            width=params.width,
            height=params.height,
            num_inference_steps=params.num_inference_steps,
            guidance_scale=params.guidance_scale,
            strength=params.strength,
            seed=params.seed,
            cfg_normalization=params.cfg_normalization,
            **params.extra_params
        )
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model variant.
        
        Returns:
            Dict containing model information and capabilities.
        """
        return {
            "variant": self.model_variant.value,
            "model_id": self.model_id,
            "description": self.config.description,
            "default_steps": self.config.default_steps,
            "default_guidance_scale": self.config.default_guidance_scale,
            "supports_negative_prompt": self.config.supports_negative_prompt,
            "supports_cfg_normalization": self.config.supports_cfg_normalization,
            "supports_editing": self.config.supports_editing,
            "device": self.device,
            "torch_dtype": str(self.torch_dtype),
        }
    
    def unload(self) -> None:
        """
        Unload the model from memory.
        
        Useful for freeing GPU memory when the model is no longer needed.
        """
        if self._pipeline is not None:
            del self._pipeline
            self._pipeline = None
            
            # Clear CUDA cache if using GPU
            if self.device == "cuda" and torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            print("Model unloaded from memory")
    
    def __repr__(self) -> str:
        return (
            f"ZImageAdapter(model_variant='{self.model_variant.value}', "
            f"model_id='{self.model_id}', device='{self.device}')"
        )


# Convenience factory functions
def create_turbo_adapter(**kwargs) -> ZImageAdapter:
    """Create a Z-Image-Turbo adapter (fastest inference)."""
    return ZImageAdapter(model_variant="turbo", **kwargs)


def create_base_adapter(**kwargs) -> ZImageAdapter:
    """Create a Z-Image adapter (highest quality)."""
    return ZImageAdapter(model_variant="base", **kwargs)


def create_omni_adapter(**kwargs) -> ZImageAdapter:
    """Create a Z-Image-Omni-Base adapter (generation + editing)."""
    return ZImageAdapter(model_variant="omni_base", **kwargs)


def create_edit_adapter(**kwargs) -> ZImageAdapter:
    """Create a Z-Image-Edit adapter (image editing)."""
    return ZImageAdapter(model_variant="edit", **kwargs)
