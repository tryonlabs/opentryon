"""
SANA Model Adapters

Local inference adapters for SANA family of efficient diffusion models from NVIDIA.
SANA uses Linear Diffusion Transformer architecture for fast, high-quality generation.

Repository: https://github.com/NVlabs/Sana
Paper: https://arxiv.org/abs/2410.10629

Key Features:
    - 20x smaller and 100x faster than Flux-12B
    - Up to 4K resolution image generation
    - SANA-Sprint: 0.1s per 1024px image (one-step generation)
    - SANA-Video: Efficient video generation

Requirements:
    - CUDA-capable GPU (recommended: 8GB+ VRAM for 0.6B, 12GB+ for 1.6B+)
    - PyTorch 2.1+
    - diffusers >= 0.32.0
    - transformers
    - accelerate
"""

import torch
from typing import List, Optional, Union, Literal
from PIL import Image
import warnings
import os


# Available SANA image models with their HuggingFace identifiers
SANA_MODELS = {
    # SANA 1.0 models
    "sana-0.6b-1024": "Efficient-Large-Model/Sana_600M_1024px",
    "sana-1.6b-1024": "Efficient-Large-Model/Sana_1600M_1024px_MultiLing",
    
    # SANA 1.5 models (better quality)
    "sana-1.5-1.6b-1024": "Efficient-Large-Model/SANA1.5_1.6B_1024px_diffusers",
    "sana-1.5-4.8b-1024": "Efficient-Large-Model/SANA1.5_4.8B_1024px_diffusers",
    
    # SANA-Sprint models (few-step, ultra-fast)
    "sana-sprint-0.6b-1024": "Efficient-Large-Model/Sana_Sprint_0.6B_1024px_diffusers",
    "sana-sprint-1.6b-1024": "Efficient-Large-Model/Sana_Sprint_1.6B_1024px_diffusers",
}

# Available SANA video models
SANA_VIDEO_MODELS = {
    "sana-video-2b-480p": "Efficient-Large-Model/SANA-Video_2B_480p_diffusers",
}

# Default negative prompt for video generation (recommended by SANA team)
DEFAULT_VIDEO_NEGATIVE_PROMPT = (
    "A chaotic sequence with misshapen, deformed limbs in heavy motion blur, "
    "sudden disappearance, jump cuts, jerky movements, rapid shot changes, "
    "frames out of sync, inconsistent character shapes, temporal artifacts, "
    "jitter, and ghosting effects, creating a disorienting visual experience."
)

# Default model for each category
DEFAULT_IMAGE_MODEL = "sana-1.5-1.6b-1024"
DEFAULT_VIDEO_MODEL = "sana-video-2b-480p"


def check_gpu_availability():
    """Check if CUDA is available and return device info."""
    if not torch.cuda.is_available():
        warnings.warn(
            "CUDA is not available. SANA models require a GPU for efficient inference. "
            "Running on CPU will be extremely slow."
        )
        return "cpu"
    
    device_name = torch.cuda.get_device_name(0)
    total_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
    
    if total_memory < 8:
        warnings.warn(
            f"GPU memory ({total_memory:.1f}GB) may be insufficient for SANA models. "
            "Consider using sana-0.6b or enable CPU offloading."
        )
    
    return "cuda"


class SanaAdapter:
    """
    Local inference adapter for SANA image generation models.
    
    SANA (Efficient High-Resolution Image Synthesis with Linear Diffusion Transformer)
    provides fast, high-quality text-to-image generation that is 20x smaller and 
    100x faster than Flux-12B.
    
    Available models:
        - sana-0.6b-1024: 0.6B params, fastest, good quality
        - sana-1.6b-1024: 1.6B params, better quality, multilingual
        - sana-1.5-1.6b-1024: 1.6B params, SANA 1.5 with improved quality
        - sana-1.5-4.8b-1024: 4.8B params, best quality
        - sana-sprint-0.6b-1024: Ultra-fast one-step generation
        - sana-sprint-1.6b-1024: Ultra-fast one-step, better quality
    
    Example:
        >>> from tryon.models.sana import SanaAdapter
        >>> 
        >>> # Initialize with default model (SANA 1.5 1.6B)
        >>> adapter = SanaAdapter()
        >>> 
        >>> # Or specify a model
        >>> adapter = SanaAdapter(model="sana-sprint-1.6b-1024")
        >>> 
        >>> # Generate image
        >>> images = adapter.generate(
        ...     prompt="A fashion model in an elegant dress",
        ...     width=1024,
        ...     height=1024
        ... )
        >>> images[0].save("output.png")
    """
    
    def __init__(
        self,
        model: str = DEFAULT_IMAGE_MODEL,
        device: Optional[str] = None,
        torch_dtype: torch.dtype = torch.bfloat16,
        enable_cpu_offload: bool = False,
        enable_vae_slicing: bool = False,
        cache_dir: Optional[str] = None
    ):
        """
        Initialize the SANA image adapter.
        
        Args:
            model: Model identifier. Use SANA_MODELS.keys() to see available models.
                  Default: "sana-1.5-1.6b-1024"
            device: Device to run inference on. Auto-detected if None.
            torch_dtype: Data type for model weights. Default: torch.bfloat16
            enable_cpu_offload: Enable sequential CPU offloading for low VRAM.
            enable_vae_slicing: Enable VAE slicing to reduce memory usage.
            cache_dir: Directory to cache downloaded model weights.
        
        Raises:
            ImportError: If diffusers is not installed
            ValueError: If model identifier is not recognized
        """
        try:
            from diffusers import SanaPipeline
        except ImportError:
            raise ImportError(
                "diffusers >= 0.32.0 is required for SANA models. "
                "Install it with: pip install diffusers>=0.32.0 transformers accelerate"
            )
        
        # Resolve model ID
        if model in SANA_MODELS:
            model_id = SANA_MODELS[model]
            self.model_name = model
        elif model.startswith("Efficient-Large-Model/"):
            model_id = model
            self.model_name = model.split("/")[-1]
        else:
            raise ValueError(
                f"Unknown model: {model}. "
                f"Available models: {list(SANA_MODELS.keys())}"
            )
        
        self.device = device or check_gpu_availability()
        self.torch_dtype = torch_dtype
        self.is_sprint = "sprint" in model.lower()
        
        print(f"Loading SANA model on {self.device}...")
        print(f"  Model: {model_id}")
        
        # Load pipeline
        pipeline_kwargs = {"torch_dtype": torch_dtype}
        if cache_dir:
            pipeline_kwargs["cache_dir"] = cache_dir
        
        self.pipe = SanaPipeline.from_pretrained(model_id, **pipeline_kwargs)
        
        # Apply memory optimizations
        if enable_cpu_offload:
            print("  Enabling CPU offloading...")
            self.pipe.enable_sequential_cpu_offload()
        else:
            self.pipe.to(self.device)
        
        # Ensure VAE and text encoder use correct dtype
        self.pipe.vae.to(torch_dtype)
        self.pipe.text_encoder.to(torch_dtype)
        
        if enable_vae_slicing:
            print("  Enabling VAE slicing...")
            self.pipe.enable_vae_slicing()
        
        print("SANA loaded successfully!")
        if self.is_sprint:
            print("  SANA-Sprint mode: Ultra-fast 1-4 step inference")
    
    def generate(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        guidance_scale: float = 4.5,
        num_inference_steps: Optional[int] = None,
        num_images: int = 1,
        seed: Optional[int] = None
    ) -> List[Image.Image]:
        """
        Generate images from text prompts using SANA.
        
        Args:
            prompt: Text description of the image to generate
            width: Output image width in pixels (default: 1024)
            height: Output image height in pixels (default: 1024)
            guidance_scale: How closely to follow the prompt (default: 4.5)
            num_inference_steps: Number of denoising steps. 
                                Default: 1-4 for Sprint, 20 for standard models
            num_images: Number of images to generate (default: 1)
            seed: Random seed for reproducibility (optional)
        
        Returns:
            List of PIL Image objects
            
        Example:
            >>> images = adapter.generate(
            ...     prompt="A professional fashion photoshoot",
            ...     width=1024,
            ...     height=1024,
            ...     seed=42
            ... )
            >>> images[0].save("output.png")
        """
        # Set default steps based on model type
        if num_inference_steps is None:
            num_inference_steps = 2 if self.is_sprint else 20
        
        # Set up generator for reproducibility
        generator = None
        if seed is not None:
            generator = torch.Generator(device="cuda" if self.device == "cuda" else "cpu")
            generator.manual_seed(seed)
        
        # Generate
        with torch.inference_mode():
            output = self.pipe(
                prompt=prompt,
                height=height,
                width=width,
                guidance_scale=guidance_scale,
                num_inference_steps=num_inference_steps,
                num_images_per_prompt=num_images,
                generator=generator,
            )
        
        return output.images
    
    @staticmethod
    def list_models() -> dict:
        """
        List all available SANA image models.
        
        Returns:
            Dictionary mapping model names to HuggingFace model IDs
        """
        return SANA_MODELS.copy()
    
    @staticmethod
    def get_recommended_settings(model: str = DEFAULT_IMAGE_MODEL) -> dict:
        """
        Get recommended settings for a SANA model.
        
        Args:
            model: Model identifier
            
        Returns:
            Dictionary with recommended parameter values
        """
        is_sprint = "sprint" in model.lower()
        is_large = "4.8b" in model.lower()
        
        return {
            "num_inference_steps": 2 if is_sprint else 20,
            "guidance_scale": 4.5,
            "recommended_resolutions": [
                (1024, 1024),
                (1024, 768),
                (768, 1024),
                (2048, 2048),  # SANA supports up to 4K
                (1920, 1080),
            ],
            "torch_dtype": "torch.bfloat16",
            "min_vram_gb": 16 if is_large else (8 if "0.6b" in model else 12),
        }
    
    def __repr__(self) -> str:
        return (
            f"SanaAdapter("
            f"model='{self.model_name}', "
            f"device='{self.device}', "
            f"sprint={self.is_sprint})"
        )


class SanaVideoAdapter:
    """
    Local inference adapter for SANA-Video generation models.
    
    SANA-Video uses Block Linear Attention for efficient video generation,
    achieving real-time minute-length video generation. Supports both
    text-to-video and image-to-video generation.
    
    Paper: https://huggingface.co/papers/2509.24695
    Docs: https://huggingface.co/docs/diffusers/main/api/pipelines/sana_video
    
    Example:
        >>> from tryon.models.sana import SanaVideoAdapter
        >>> 
        >>> adapter = SanaVideoAdapter()
        >>> 
        >>> # Text-to-video generation
        >>> frames = adapter.generate(
        ...     prompt="A fashion model walking on a runway",
        ...     frames=81,
        ...     width=832,
        ...     height=480
        ... )
        >>> adapter.save_video(frames, "output.mp4")
        >>> 
        >>> # Image-to-video generation
        >>> frames = adapter.generate_from_image(
        ...     image="start_frame.jpg",
        ...     prompt="The model starts walking gracefully",
        ...     frames=81
        ... )
    """
    
    def __init__(
        self,
        model: str = DEFAULT_VIDEO_MODEL,
        device: Optional[str] = None,
        torch_dtype: torch.dtype = torch.bfloat16,
        enable_cpu_offload: bool = False,
        cache_dir: Optional[str] = None
    ):
        """
        Initialize the SANA-Video adapter.
        
        Args:
            model: Model identifier. Default: "sana-video-2b-480p"
            device: Device to run inference on. Auto-detected if None.
            torch_dtype: Data type for transformer weights. Default: torch.bfloat16
                        Note: VAE uses float32, text_encoder uses bfloat16 automatically.
            enable_cpu_offload: Enable sequential CPU offloading for low VRAM.
            cache_dir: Directory to cache downloaded model weights.
        
        Raises:
            ImportError: If required packages are not installed
            ValueError: If model identifier is not recognized
        """
        try:
            from diffusers import SanaVideoPipeline, SanaImageToVideoPipeline
        except ImportError:
            raise ImportError(
                "diffusers with SANA-Video support is required. "
                "Install it with: pip install diffusers transformers accelerate"
            )
        
        # Resolve model ID
        if model in SANA_VIDEO_MODELS:
            model_id = SANA_VIDEO_MODELS[model]
            self.model_name = model
        elif model.startswith("Efficient-Large-Model/"):
            model_id = model
            self.model_name = model.split("/")[-1]
        else:
            raise ValueError(
                f"Unknown model: {model}. "
                f"Available models: {list(SANA_VIDEO_MODELS.keys())}"
            )
        
        self.device = device or check_gpu_availability()
        self.torch_dtype = torch_dtype
        
        print(f"Loading SANA-Video on {self.device}...")
        print(f"  Model: {model_id}")
        
        # Load text-to-video pipeline
        pipeline_kwargs = {"torch_dtype": torch_dtype}
        if cache_dir:
            pipeline_kwargs["cache_dir"] = cache_dir
        
        self.pipe = SanaVideoPipeline.from_pretrained(model_id, **pipeline_kwargs)
        
        # Set correct dtypes as per documentation
        self.pipe.text_encoder.to(torch.bfloat16)
        self.pipe.vae.to(torch.float32)
        
        if enable_cpu_offload:
            print("  Enabling CPU offloading...")
            self.pipe.enable_sequential_cpu_offload()
        else:
            self.pipe.to(self.device)
        
        # Lazy load image-to-video pipeline
        self._i2v_pipe = None
        self._model_id = model_id
        self._cache_dir = cache_dir
        self._enable_cpu_offload = enable_cpu_offload
        
        print("SANA-Video loaded successfully!")
    
    def _get_i2v_pipeline(self):
        """Lazy load image-to-video pipeline."""
        if self._i2v_pipe is None:
            from diffusers import SanaImageToVideoPipeline, FlowMatchEulerDiscreteScheduler
            
            print("Loading SANA Image-to-Video pipeline...")
            pipeline_kwargs = {"torch_dtype": self.torch_dtype}
            if self._cache_dir:
                pipeline_kwargs["cache_dir"] = self._cache_dir
            
            self._i2v_pipe = SanaImageToVideoPipeline.from_pretrained(
                self._model_id, **pipeline_kwargs
            )
            
            # Configure scheduler with recommended flow_shift
            self._i2v_pipe.scheduler = FlowMatchEulerDiscreteScheduler.from_config(
                self._i2v_pipe.scheduler.config, flow_shift=8.0
            )
            
            # Set correct dtypes
            self._i2v_pipe.text_encoder.to(torch.bfloat16)
            self._i2v_pipe.vae.to(torch.float32)
            
            if self._enable_cpu_offload:
                self._i2v_pipe.enable_sequential_cpu_offload()
            else:
                self._i2v_pipe.to(self.device)
            
            print("SANA Image-to-Video pipeline loaded!")
        
        return self._i2v_pipe
    
    def generate(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        frames: int = 81,
        width: int = 832,
        height: int = 480,
        guidance_scale: float = 6.0,
        num_inference_steps: int = 50,
        motion_scale: Optional[int] = 30,
        seed: Optional[int] = None
    ) -> List[Image.Image]:
        """
        Generate video frames from text prompts using SANA-Video.
        
        Args:
            prompt: Text description of the video to generate
            negative_prompt: What to avoid in the video. Uses default if None.
            frames: Number of frames to generate (default: 81)
            width: Output frame width in pixels (default: 832)
            height: Output frame height in pixels (default: 480)
            guidance_scale: How closely to follow the prompt (default: 6.0)
            num_inference_steps: Number of denoising steps (default: 50)
            motion_scale: Motion intensity 0-100 (default: 30). Set None to disable.
            seed: Random seed for reproducibility (optional)
        
        Returns:
            List of PIL Image objects representing video frames
            
        Example:
            >>> frames = adapter.generate(
            ...     prompt="A model walking on a fashion runway",
            ...     frames=81,
            ...     motion_scale=30,
            ...     seed=42
            ... )
            >>> adapter.save_video(frames, "output.mp4")
        """
        # Add motion prompt if specified
        full_prompt = prompt
        if motion_scale is not None:
            full_prompt = f"{prompt} motion score: {motion_scale}."
        
        # Use default negative prompt if not provided
        if negative_prompt is None:
            negative_prompt = DEFAULT_VIDEO_NEGATIVE_PROMPT
        
        generator = None
        if seed is not None:
            generator = torch.Generator(device="cuda" if self.device == "cuda" else "cpu")
            generator.manual_seed(seed)
        
        with torch.inference_mode():
            output = self.pipe(
                prompt=full_prompt,
                negative_prompt=negative_prompt,
                height=height,
                width=width,
                frames=frames,
                guidance_scale=guidance_scale,
                num_inference_steps=num_inference_steps,
                generator=generator,
            )
        
        return output.frames[0]
    
    def generate_from_image(
        self,
        image: Union[str, Image.Image],
        prompt: str,
        negative_prompt: Optional[str] = None,
        frames: int = 81,
        width: int = 832,
        height: int = 480,
        guidance_scale: float = 6.0,
        num_inference_steps: int = 50,
        motion_scale: Optional[int] = 30,
        seed: Optional[int] = None
    ) -> List[Image.Image]:
        """
        Generate video frames from an image and text prompt (image-to-video).
        
        Args:
            image: Starting frame image (file path or PIL Image)
            prompt: Text description of the video motion/content
            negative_prompt: What to avoid in the video. Uses default if None.
            frames: Number of frames to generate (default: 81)
            width: Output frame width in pixels (default: 832)
            height: Output frame height in pixels (default: 480)
            guidance_scale: How closely to follow the prompt (default: 6.0)
            num_inference_steps: Number of denoising steps (default: 50)
            motion_scale: Motion intensity 0-100 (default: 30). Set None to disable.
            seed: Random seed for reproducibility (optional)
        
        Returns:
            List of PIL Image objects representing video frames
            
        Example:
            >>> frames = adapter.generate_from_image(
            ...     image="model_standing.jpg",
            ...     prompt="The model starts walking gracefully on the runway",
            ...     frames=81,
            ...     seed=42
            ... )
            >>> adapter.save_video(frames, "output.mp4")
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
        
        # Get image-to-video pipeline
        i2v_pipe = self._get_i2v_pipeline()
        
        # Add motion prompt if specified
        full_prompt = prompt
        if motion_scale is not None:
            full_prompt = f"{prompt} motion score: {motion_scale}."
        
        # Use default negative prompt if not provided
        if negative_prompt is None:
            negative_prompt = DEFAULT_VIDEO_NEGATIVE_PROMPT
        
        generator = None
        if seed is not None:
            generator = torch.Generator(device="cuda" if self.device == "cuda" else "cpu")
            generator.manual_seed(seed)
        
        with torch.inference_mode():
            output = i2v_pipe(
                image=image,
                prompt=full_prompt,
                negative_prompt=negative_prompt,
                height=height,
                width=width,
                frames=frames,
                guidance_scale=guidance_scale,
                num_inference_steps=num_inference_steps,
                generator=generator,
            )
        
        return output.frames[0]
    
    def save_video(
        self,
        frames: List[Image.Image],
        output_path: str,
        fps: int = 16
    ):
        """
        Save generated frames as a video file.
        
        Args:
            frames: List of PIL Image frames
            output_path: Path to save the video (e.g., "output.mp4")
            fps: Frames per second (default: 16, recommended for SANA-Video)
        """
        try:
            from diffusers.utils import export_to_video
            export_to_video(frames, output_path, fps=fps)
        except ImportError:
            # Fallback to imageio
            try:
                import imageio
                import numpy as np
                
                video_frames = [np.array(frame) for frame in frames]
                imageio.mimsave(output_path, video_frames, fps=fps)
            except ImportError:
                raise ImportError(
                    "Either diffusers.utils.export_to_video or imageio is required "
                    "to save videos. Install with: pip install imageio imageio-ffmpeg"
                )
    
    @staticmethod
    def list_models() -> dict:
        """List all available SANA video models."""
        return SANA_VIDEO_MODELS.copy()
    
    @staticmethod
    def get_recommended_settings() -> dict:
        """
        Get recommended settings for SANA-Video.
        
        Returns:
            Dictionary with recommended parameter values
        """
        return {
            "frames": 81,
            "num_inference_steps": 50,
            "guidance_scale": 6.0,
            "motion_scale": 30,
            "fps": 16,
            "recommended_resolutions": [
                (832, 480),   # 480p landscape
                (480, 832),   # 480p portrait
            ],
            "transformer_dtype": "torch.bfloat16",
            "vae_dtype": "torch.float32",
            "min_vram_gb": 16,
        }
    
    def __repr__(self) -> str:
        return (
            f"SanaVideoAdapter("
            f"model='{self.model_name}', "
            f"device='{self.device}')"
        )

