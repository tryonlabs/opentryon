"""
Local Models Module

This module provides adapters for local inference models that run on user's hardware.
Unlike the API adapters in tryon.api which call cloud services, these models require
local GPU resources for inference.

Available Models:
    - Flux2TurboAdapter: FLUX.2-dev Turbo for fast image generation (8 steps)

Example:
    >>> from tryon.models import Flux2TurboAdapter
    >>> 
    >>> adapter = Flux2TurboAdapter()
    >>> images = adapter.generate_text_to_image("A fashion model wearing a dress")
    >>> images[0].save("output.png")

Requirements:
    - CUDA-capable GPU (recommended: 12GB+ VRAM)
    - PyTorch 2.1+
    - diffusers >= 0.29.0
"""

from .flux2_turbo import Flux2TurboAdapter

__all__ = [
    "Flux2TurboAdapter",
]

