"""
Local Models Module

This module provides adapters for local inference models that run on user's hardware.
Unlike the API adapters in tryon.api which call cloud services, these models require
local GPU resources for inference.

Available Models:
    - Flux2TurboAdapter: FLUX.2-dev Turbo for fast image generation (8 steps)
      Supports both text-to-image and image-to-image generation
    - ZImageAdapter: Z-Image family of models (6B parameters)
      Supports text-to-image and image editing with multiple variants

Examples:
    Text-to-image generation with Flux2:
    >>> from tryon.models import Flux2TurboAdapter
    >>> 
    >>> adapter = Flux2TurboAdapter()
    >>> images = adapter.generate_text_to_image(
    ...     prompt="A fashion model wearing a dress",
    ...     width=1024,
    ...     height=1024
    ... )
    >>> images[0].save("output.png")
    
    Text-to-image with Z-Image-Turbo:
    >>> from tryon.models import ZImageAdapter
    >>> 
    >>> adapter = ZImageAdapter(model_variant="turbo")
    >>> images = adapter.generate(prompt="A cute baby polar bear")
    >>> images[0].save("output.png")
    
    High-quality generation with Z-Image:
    >>> adapter = ZImageAdapter(model_variant="base")
    >>> images = adapter.generate(
    ...     prompt="Professional fashion photograph",
    ...     negative_prompt="blurry, low quality",
    ...     guidance_scale=4.0
    ... )

Requirements:
    - CUDA-capable GPU (recommended: 12GB+ VRAM, 16GB+ for Z-Image)
    - PyTorch 2.1+
    - diffusers >= 0.29.0 (latest from source for Z-Image)
"""

from .flux2_turbo import Flux2TurboAdapter
from .z_image import (
    ZImageAdapter,
    ZImageModelVariant,
    GenerationParams,
    EditingParams,
    create_turbo_adapter,
    create_base_adapter,
    create_omni_adapter,
    create_edit_adapter,
)

__all__ = [
    # Flux2 models
    "Flux2TurboAdapter",
    # Z-Image models
    "ZImageAdapter",
    "ZImageModelVariant",
    "GenerationParams",
    "EditingParams",
    "create_turbo_adapter",
    "create_base_adapter",
    "create_omni_adapter",
    "create_edit_adapter",
]
