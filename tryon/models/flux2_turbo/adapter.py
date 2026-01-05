"""
FLUX.2-dev Turbo Adapter

A local inference adapter for FLUX.2-dev Turbo, a distilled LoRA adapter that enables
high-quality image generation in just 8 inference steps (6x faster than the base model).

Model: https://huggingface.co/fal/FLUX.2-dev-Turbo
Base Model: https://huggingface.co/black-forest-labs/FLUX.2-dev
License: FLUX [dev] Non-Commercial License

Key Features:
    - 8-step inference (6x faster than base model's typical 50 steps)
    - Quality preserved or surpasses original FLUX.2 [dev]
    - Supports text-to-image and image-to-image generation
    - LoRA adapter - lightweight and easy to integrate
    - Caption upsampling for improved outputs (recommended: 0.15)

Requirements:
    - CUDA-capable GPU (recommended: 12GB+ VRAM for 1024x1024)
    - PyTorch 2.1+
    - diffusers >= 0.29.0
    - transformers
    - accelerate
"""

import torch
from typing import List, Optional, Union
from PIL import Image
import warnings
import os


# Pre-shifted custom sigmas for 8-step turbo inference
# These are optimized for the distilled LoRA
TURBO_SIGMAS = [1.0, 0.6509, 0.4374, 0.2932, 0.1893, 0.1108, 0.0495, 0.00031]

# Model identifiers
BASE_MODEL_ID = "black-forest-labs/FLUX.2-dev"
LORA_MODEL_ID = "fal/FLUX.2-dev-Turbo"
LORA_WEIGHT_NAME = "flux.2-turbo-lora.safetensors"


def check_gpu_availability():
    """Check if CUDA is available and return device info."""
    if not torch.cuda.is_available():
        warnings.warn(
            "CUDA is not available. FLUX.2-dev Turbo requires a GPU for efficient inference. "
            "Running on CPU will be extremely slow."
        )
        return "cpu"
    
    # Get GPU memory info
    device_name = torch.cuda.get_device_name(0)
    total_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)  # GB
    
    if total_memory < 10:
        warnings.warn(
            f"GPU memory ({total_memory:.1f}GB) may be insufficient for FLUX.2-dev Turbo. "
            "Recommended: 12GB+ VRAM. Consider using lower resolution or enable CPU offloading."
        )
    
    return "cuda"


class Flux2TurboAdapter:
    """
    Local inference adapter for FLUX.2-dev Turbo.
    
    FLUX.2-dev Turbo is a distilled LoRA adapter that enables high-quality 
    image generation in just 8 inference steps, making it 6x faster than 
    the base FLUX.2 [dev] model.
    
    Attributes:
        device (str): Device to run inference on ("cuda" or "cpu")
        pipe: The Flux2Pipeline with loaded LoRA weights
        
    Example:
        >>> from tryon.models.flux2_turbo import Flux2TurboAdapter
        >>> 
        >>> # Initialize adapter (downloads model on first use)
        >>> adapter = Flux2TurboAdapter()
        >>> 
        >>> # Generate image
        >>> images = adapter.generate_text_to_image(
        ...     prompt="A professional fashion model wearing an elegant dress",
        ...     width=1024,
        ...     height=1024
        ... )
        >>> images[0].save("output.png")
        
        >>> # Image-to-image generation
        >>> output = adapter.generate_image_to_image(
        ...     image="input.jpg",
        ...     prompt="A fashion model in an elegant blue dress"
        ... )
        >>> output[0].save("output.png")
    """
    
    def __init__(
        self,
        device: Optional[str] = None,
        torch_dtype: torch.dtype = torch.bfloat16,
        load_lora: bool = True,
        enable_cpu_offload: bool = False,
        enable_attention_slicing: bool = False,
        cache_dir: Optional[str] = None
    ):
        """
        Initialize the FLUX.2-dev Turbo adapter.
        
        Args:
            device: Device to run inference on. Auto-detected if None.
                   Options: "cuda", "cpu"
            torch_dtype: Data type for model weights. 
                        Default: torch.bfloat16 (recommended for FLUX)
            load_lora: Whether to load the Turbo LoRA weights.
                      Set to False to use base FLUX.2-dev model.
            enable_cpu_offload: Enable sequential CPU offloading to reduce VRAM usage.
                               Useful for GPUs with limited memory.
            enable_attention_slicing: Enable attention slicing to reduce VRAM usage.
                                     May slightly reduce speed.
            cache_dir: Directory to cache downloaded model weights.
                      Uses HuggingFace default if None.
        
        Raises:
            ImportError: If diffusers is not installed
        """
        try:
            from diffusers import Flux2Pipeline
        except ImportError:
            raise ImportError(
                "diffusers is required for FLUX.2-dev Turbo. "
                "Install it with: pip install diffusers>=0.29.0 transformers accelerate"
            )
        
        # Set device
        self.device = device or check_gpu_availability()
        self.torch_dtype = torch_dtype
        self.lora_loaded = False
        
        print(f"Loading FLUX.2-dev Turbo on {self.device}...")
        print(f"  Base model: {BASE_MODEL_ID}")
        
        # Load pipeline
        pipeline_kwargs = {
            "torch_dtype": torch_dtype,
        }
        if cache_dir:
            pipeline_kwargs["cache_dir"] = cache_dir
            
        self.pipe = Flux2Pipeline.from_pretrained(
            BASE_MODEL_ID,
            **pipeline_kwargs
        )
        
        # Apply memory optimizations
        if enable_cpu_offload:
            print("  Enabling CPU offloading...")
            self.pipe.enable_sequential_cpu_offload()
        else:
            self.pipe = self.pipe.to(self.device)
            
        if enable_attention_slicing:
            print("  Enabling attention slicing...")
            self.pipe.enable_attention_slicing()
        
        # Load Turbo LoRA weights
        if load_lora:
            print(f"  Loading Turbo LoRA: {LORA_MODEL_ID}")
            self.pipe.load_lora_weights(
                LORA_MODEL_ID,
                weight_name=LORA_WEIGHT_NAME
            )
            self.lora_loaded = True
            print("FLUX.2-dev Turbo loaded successfully!")
            print("  8-step inference enabled (6x faster)")
        else:
            print("FLUX.2-dev Turbo base model loaded (LoRA not applied)")
    
    def generate_text_to_image(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        guidance_scale: float = 2.5,
        num_inference_steps: int = 8,
        num_images: int = 1,
        seed: Optional[int] = None,
        use_turbo_sigmas: bool = True,
        caption_upsample_temperature: Optional[float] = None
    ) -> List[Image.Image]:
        """
        Generate images from text prompts using FLUX.2-dev Turbo.
        
        Args:
            prompt: Text description of the image to generate
            width: Output image width in pixels (default: 1024)
            height: Output image height in pixels (default: 1024)
            guidance_scale: How closely to follow the prompt (default: 2.5)
                           Lower values = more creative, higher = more literal
            num_inference_steps: Number of denoising steps (default: 8 for Turbo)
                                Use 8 with Turbo LoRA, 28-50 without
            num_images: Number of images to generate (default: 1)
            seed: Random seed for reproducibility (optional)
            use_turbo_sigmas: Use pre-shifted sigmas optimized for Turbo (default: True)
                             Set to False if not using Turbo LoRA
            caption_upsample_temperature: When specified, performs caption upsampling 
                                         for potentially improved outputs. Recommended: 0.15
        
        Returns:
            List of PIL Image objects
            
        Example:
            >>> images = adapter.generate_text_to_image(
            ...     prompt="A fashion model wearing a red dress on a runway",
            ...     width=1024,
            ...     height=1024,
            ...     seed=42
            ... )
            >>> images[0].save("output.png")
        """
        # Set up generator for reproducibility
        generator = None
        if seed is not None:
            generator = torch.Generator(device=self.device if self.device != "cpu" else "cpu")
            generator.manual_seed(seed)
        
        # Build generation kwargs
        gen_kwargs = {
            "prompt": prompt,
            "width": width,
            "height": height,
            "guidance_scale": guidance_scale,
            "num_inference_steps": num_inference_steps,
            "num_images_per_prompt": num_images,
        }
            
        if generator:
            gen_kwargs["generator"] = generator
            
        # Use Turbo-optimized sigmas
        if use_turbo_sigmas and self.lora_loaded:
            gen_kwargs["sigmas"] = TURBO_SIGMAS
        
        # Caption upsampling for improved outputs
        if caption_upsample_temperature is not None:
            gen_kwargs["caption_upsample_temperature"] = caption_upsample_temperature
        
        # Generate
        with torch.inference_mode():
            output = self.pipe(**gen_kwargs)
        
        return output.images
    
    def generate_image_to_image(
        self,
        image: Union[str, Image.Image],
        prompt: str,
        guidance_scale: float = 2.5,
        num_inference_steps: int = 8,
        seed: Optional[int] = None,
        use_turbo_sigmas: bool = True,
        caption_upsample_temperature: Optional[float] = None
    ) -> List[Image.Image]:
        """
        Generate images conditioned on an input image using text prompts.
        
        Args:
            image: Input image (file path or PIL Image) to condition generation
            prompt: Text description of the desired output
            guidance_scale: How closely to follow the prompt (default: 2.5)
            num_inference_steps: Number of denoising steps (default: 8 for Turbo)
            seed: Random seed for reproducibility (optional)
            use_turbo_sigmas: Use pre-shifted sigmas optimized for Turbo (default: True)
            caption_upsample_temperature: When specified, performs caption upsampling 
                                         for potentially improved outputs. Recommended: 0.15
        
        Returns:
            List of PIL Image objects
            
        Example:
            >>> output = adapter.generate_image_to_image(
            ...     image="model.jpg",
            ...     prompt="A fashion model in an elegant evening gown"
            ... )
            >>> output[0].save("output.png")
        """
        # Load image if path provided
        if isinstance(image, str):
            if os.path.exists(image):
                image = Image.open(image).convert("RGB")
            else:
                raise FileNotFoundError(f"Image not found: {image}")
        elif isinstance(image, Image.Image):
            image = image.convert("RGB")
        else:
            raise ValueError("image must be a file path or PIL Image")
        
        # Set up generator
        generator = None
        if seed is not None:
            generator = torch.Generator(device=self.device if self.device != "cpu" else "cpu")
            generator.manual_seed(seed)
        
        # Build generation kwargs
        gen_kwargs = {
            "prompt": prompt,
            "image": image,
            "guidance_scale": guidance_scale,
            "num_inference_steps": num_inference_steps,
        }
            
        if generator:
            gen_kwargs["generator"] = generator
            
        # Use Turbo-optimized sigmas
        if use_turbo_sigmas and self.lora_loaded:
            gen_kwargs["sigmas"] = TURBO_SIGMAS
        
        # Caption upsampling for improved outputs
        if caption_upsample_temperature is not None:
            gen_kwargs["caption_upsample_temperature"] = caption_upsample_temperature
        
        # Generate
        with torch.inference_mode():
            output = self.pipe(**gen_kwargs)
        
        return output.images
    
    def unload_lora(self):
        """Unload the Turbo LoRA weights to use base FLUX.2-dev model."""
        if self.lora_loaded:
            self.pipe.unload_lora_weights()
            self.lora_loaded = False
            print("LoRA weights unloaded. Using base FLUX.2-dev model.")
    
    def reload_lora(self):
        """Reload the Turbo LoRA weights."""
        if not self.lora_loaded:
            self.pipe.load_lora_weights(
                LORA_MODEL_ID,
                weight_name=LORA_WEIGHT_NAME
            )
            self.lora_loaded = True
            print("Turbo LoRA weights reloaded.")
    
    @staticmethod
    def get_recommended_settings() -> dict:
        """
        Get recommended settings for FLUX.2-dev Turbo.
        
        Returns:
            Dictionary with recommended parameter values
        """
        return {
            "num_inference_steps": 8,
            "guidance_scale": 2.5,
            "sigmas": TURBO_SIGMAS,
            "recommended_resolutions": [
                (1024, 1024),  # Square
                (1024, 768),   # Landscape 4:3
                (768, 1024),   # Portrait 3:4
                (1280, 720),   # Landscape 16:9
                (720, 1280),   # Portrait 9:16
            ],
            "torch_dtype": "torch.bfloat16",
            "min_vram_gb": 12,
        }
    
    def __repr__(self) -> str:
        return (
            f"Flux2TurboAdapter("
            f"device='{self.device}', "
            f"lora_loaded={self.lora_loaded}, "
            f"dtype={self.torch_dtype})"
        )

