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
QUANTIZED_8BIT_MODEL_ID = "diffusers/FLUX.2-dev-bnb-8bit"
QUANTIZED_4BIT_MODEL_ID = "diffusers/FLUX.2-dev-bnb-4bit"
LORA_MODEL_ID = "fal/FLUX.2-dev-Turbo"
LORA_WEIGHT_NAME = "flux.2-turbo-lora.safetensors"


def get_available_vram() -> Optional[float]:
    """
    Get available VRAM in GB.
    
    Returns:
        Available VRAM in GB, or None if CUDA is not available
    """
    if not torch.cuda.is_available():
        return None
    
    # Get free and total memory
    free_memory = torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_reserved(0)
    free_memory_gb = free_memory / (1024**3)
    
    return free_memory_gb


def select_model_by_vram(available_vram: Optional[float] = None, verbose: bool = True) -> tuple[str, bool]:
    """
    Select appropriate FLUX.2-dev model based on available VRAM.
    
    Args:
        available_vram: Available VRAM in GB. If None, will be auto-detected.
        verbose: If True, print selection messages.
    
    Returns:
        Tuple of (model_id, requires_bitsandbytes)
        
    Model selection:
        - >= 64GB: Full model (black-forest-labs/FLUX.2-dev)
        - >= 48GB: 8-bit quantized (diffusers/FLUX.2-dev-bnb-8bit)
        - >= 38GB: 4-bit quantized (diffusers/FLUX.2-dev-bnb-4bit)
        - < 38GB: 4-bit quantized (with warning)
    """
    if available_vram is None:
        available_vram = get_available_vram()
    
    if available_vram is None:
        # No CUDA, return full model (will run on CPU)
        return BASE_MODEL_ID, False
    
    if available_vram >= 64:
        model_id = BASE_MODEL_ID
        requires_bnb = False
        if verbose:
            print(f"[INFO] Sufficient VRAM detected ({available_vram:.1f}GB). Using full model.")
    elif available_vram >= 48:
        model_id = QUANTIZED_8BIT_MODEL_ID
        requires_bnb = True
        if verbose:
            print(f"[INFO] Available VRAM: {available_vram:.1f}GB. Using 8-bit quantized model.")
    elif available_vram >= 38:
        model_id = QUANTIZED_4BIT_MODEL_ID
        requires_bnb = True
        if verbose:
            print(f"[WARN] Limited VRAM detected ({available_vram:.1f}GB). Using 4-bit quantized model.")
    else:
        model_id = QUANTIZED_4BIT_MODEL_ID
        requires_bnb = True
        if verbose:
            warnings.warn(
                f"Very limited VRAM ({available_vram:.1f}GB). "
                "4-bit quantized model selected, but may still encounter OOM errors. "
                "Consider enabling CPU offloading or attention slicing."
            )
    
    return model_id, requires_bnb


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
        cache_dir: Optional[str] = None,
        model_id: Optional[str] = None,
        auto_select_model: bool = True
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
            model_id: Explicit model ID to use. If None and auto_select_model=True,
                     will auto-select based on available VRAM.
            auto_select_model: If True, automatically select model based on VRAM.
                              If False, use BASE_MODEL_ID or provided model_id.
        
        Raises:
            ImportError: If diffusers is not installed or bitsandbytes is missing
                        for quantized models
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
        
        # Select model based on VRAM if auto-selection is enabled
        if model_id is None and auto_select_model:
            available_vram = get_available_vram() if self.device == "cuda" else None
            selected_model_id, requires_bnb = select_model_by_vram(available_vram)
            
            if requires_bnb:
                try:
                    import bitsandbytes as bnb
                except ImportError:
                    raise ImportError(
                        "bitsandbytes is required for quantized models. "
                        "Install it with: pip install bitsandbytes"
                    )
            
            model_id = selected_model_id
        elif model_id is None:
            model_id = BASE_MODEL_ID
        
        self.model_id = model_id
        
        print("\n" + "="*70)
        print(f"[INFO] Initializing FLUX.2-dev Turbo Adapter")
        print(f"[INFO] Device: {self.device}")
        print(f"[INFO] Model: {model_id}")
        print("="*70)
        
        # Load pipeline with sequential component loading to optimize memory
        pipeline_kwargs = {
            "torch_dtype": torch_dtype,
        }
        if cache_dir:
            pipeline_kwargs["cache_dir"] = cache_dir
        
        # Load pipeline (this loads all components)
        # For quantized models, diffusers handles quantization automatically
        print("[INFO] Loading pipeline components from HuggingFace...")
        try:
            self.pipe = Flux2Pipeline.from_pretrained(
                model_id,
                **pipeline_kwargs
            )
            print("[INFO] Pipeline components loaded successfully.")
        except Exception as e:
            if "bitsandbytes" in str(e).lower():
                raise ImportError(
                    f"Failed to load quantized model {model_id}. "
                    "bitsandbytes may not be properly installed. "
                    "Install it with: pip install bitsandbytes"
                ) from e
            raise
        
        # Sequential loading: Move components to device one by one to avoid OOM
        cpu_offload_enabled = False
        if not enable_cpu_offload and self.device != "cpu":
            print("[INFO] Loading model components sequentially to optimize VRAM usage...")
            
            try:
                # Move text encoder first (smallest component)
                if hasattr(self.pipe, 'text_encoder') and self.pipe.text_encoder is not None:
                    print("  [INFO] Transferring text encoder to GPU...")
                    self.pipe.text_encoder = self.pipe.text_encoder.to(self.device)
                    torch.cuda.empty_cache()
                
                # Move VAE next
                if hasattr(self.pipe, 'vae') and self.pipe.vae is not None:
                    print("  [INFO] Transferring VAE to GPU...")
                    self.pipe.vae = self.pipe.vae.to(self.device)
                    torch.cuda.empty_cache()
                
                # Move transformer last (largest component)
                if hasattr(self.pipe, 'transformer') and self.pipe.transformer is not None:
                    print("  [INFO] Transferring transformer to GPU...")
                    self.pipe.transformer = self.pipe.transformer.to(self.device)
                    torch.cuda.empty_cache()
                
                # Move any other components that support .to()
                for component_name in ['tokenizer', 'scheduler']:
                    if hasattr(self.pipe, component_name):
                        component = getattr(self.pipe, component_name)
                        if component is not None and hasattr(component, 'to'):
                            try:
                                component = component.to(self.device)
                                setattr(self.pipe, component_name, component)
                            except (AttributeError, TypeError):
                                # Some components don't support .to() or are not tensors
                                pass
            except torch.cuda.OutOfMemoryError as e:
                warnings.warn(
                    f"OOM during sequential loading: {e}. "
                    "Falling back to CPU offloading. Consider using a quantized model."
                )
                enable_cpu_offload = True
                cpu_offload_enabled = True
                self.pipe.enable_sequential_cpu_offload()
        
        # Apply memory optimizations if not already done
        if enable_cpu_offload and not cpu_offload_enabled:
            print("[INFO] Enabling sequential CPU offloading to reduce VRAM usage...")
            self.pipe.enable_sequential_cpu_offload()
        elif self.device == "cpu":
            # Already on CPU, no need to move
            pass
        elif not cpu_offload_enabled:
            # Check if components are already on the correct device
            # If not, try to move the entire pipeline (fallback)
            try:
                # Check if transformer is already on device
                if hasattr(self.pipe, 'transformer') and self.pipe.transformer is not None:
                    transformer_device = next(self.pipe.transformer.parameters()).device
                    if transformer_device.type != self.device.split(':')[0]:
                        self.pipe = self.pipe.to(self.device)
                else:
                    # No transformer, just move the pipeline
                    self.pipe = self.pipe.to(self.device)
            except torch.cuda.OutOfMemoryError as e:
                warnings.warn(
                    f"OOM when moving pipeline to {self.device}: {e}. "
                    "Enabling CPU offloading as fallback."
                )
                self.pipe.enable_sequential_cpu_offload()
            
        if enable_attention_slicing:
            print("[INFO] Enabling attention slicing to reduce VRAM usage...")
            self.pipe.enable_attention_slicing()
        
        # Load Turbo LoRA weights
        if load_lora:
            print(f"[INFO] Loading Turbo LoRA weights from: {LORA_MODEL_ID}")
            try:
                self.pipe.load_lora_weights(
                    LORA_MODEL_ID,
                    weight_name=LORA_WEIGHT_NAME
                )
                self.lora_loaded = True
                print("[INFO] FLUX.2-dev Turbo adapter initialized successfully.")
                print("[INFO] Turbo mode enabled: 8-step inference (6x faster than base model)")
                print("="*70 + "\n")
            except Exception as e:
                warnings.warn(
                    f"Failed to load Turbo LoRA: {e}. "
                    "Continuing with base model only."
                )
                self.lora_loaded = False
                print("[WARN] Turbo LoRA loading failed. Using base FLUX.2-dev model.")
                print("="*70 + "\n")
        else:
            print("[INFO] FLUX.2-dev base model loaded (LoRA not applied)")
            print("="*70 + "\n")
    
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
            print("[INFO] Turbo LoRA weights unloaded. Using base FLUX.2-dev model.")
    
    def reload_lora(self):
        """Reload the Turbo LoRA weights."""
        if not self.lora_loaded:
            self.pipe.load_lora_weights(
                LORA_MODEL_ID,
                weight_name=LORA_WEIGHT_NAME
            )
            self.lora_loaded = True
            print("[INFO] Turbo LoRA weights reloaded successfully.")
    
    @staticmethod
    def get_vram_info() -> dict:
        """
        Get current VRAM information.
        
        Returns:
            Dictionary with VRAM info including total, free, and recommended model
        """
        if not torch.cuda.is_available():
            return {
                "cuda_available": False,
                "message": "CUDA is not available"
            }
        
        total_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        reserved_memory = torch.cuda.memory_reserved(0) / (1024**3)
        allocated_memory = torch.cuda.memory_allocated(0) / (1024**3)
        free_memory = total_memory - reserved_memory
        
        available_vram = get_available_vram()
        recommended_model, requires_bnb = select_model_by_vram(available_vram, verbose=False)
        
        return {
            "cuda_available": True,
            "device_name": torch.cuda.get_device_name(0),
            "total_memory_gb": round(total_memory, 2),
            "reserved_memory_gb": round(reserved_memory, 2),
            "allocated_memory_gb": round(allocated_memory, 2),
            "free_memory_gb": round(free_memory, 2),
            "available_vram_gb": round(available_vram, 2) if available_vram else None,
            "recommended_model": recommended_model,
            "requires_bitsandbytes": requires_bnb
        }
    
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
            f"model_id='{self.model_id}', "
            f"device='{self.device}', "
            f"lora_loaded={self.lora_loaded}, "
            f"dtype={self.torch_dtype})"
        )
