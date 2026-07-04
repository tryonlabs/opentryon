"""
Local Models Module

This module provides adapters for local inference models that run on user's hardware.
Unlike the API adapters in tryon.api which call cloud services, these models require
local GPU resources for inference.

Available Models:
    - Flux2TurboAdapter: FLUX.2-dev Turbo for fast image generation (8 steps)
      Supports both text-to-image and image-to-image generation
    - KimiVLAdapter: Kimi-VL open-weight multimodal model (image/video
      understanding), the local counterpart to the Kimi K2.6/K2.7 Code APIs

Examples:
    Text-to-image generation:
    >>> from tryon.models import Flux2TurboAdapter
    >>> 
    >>> adapter = Flux2TurboAdapter()
    >>> images = adapter.generate_text_to_image(
    ...     prompt="A fashion model wearing a dress",
    ...     width=1024,
    ...     height=1024
    ... )
    >>> images[0].save("output.png")
    
    Image-to-image generation:
    >>> from PIL import Image
    >>> 
    >>> input_image = Image.open("input.jpg")
    >>> edited_images = adapter.generate_image_to_image(
    ...     image=input_image,
    ...     prompt="A fashion model in an elegant blue dress"
    ... )
    >>> edited_images[0].save("edited_output.png")

Requirements:
    - CUDA-capable GPU (recommended: 12GB+ VRAM)
    - PyTorch 2.1+
    - diffusers >= 0.29.0
"""

from .flux2_turbo import Flux2TurboAdapter
from .kimi_vl import KimiVLAdapter

__all__ = [
    "Flux2TurboAdapter",
    "KimiVLAdapter",
]
