"""
FLUX.2-dev Turbo - Local Inference Adapter

A distilled LoRA adapter for FLUX.2 [dev] that enables high-quality image generation
in just 8 inference steps (6x faster than the base model).

Model: https://huggingface.co/fal/FLUX.2-dev-Turbo
License: FLUX [dev] Non-Commercial License

Requirements:
    - CUDA-capable GPU (recommended: 12GB+ VRAM)
    - PyTorch 2.1+
    - diffusers >= 0.29.0

Example:
    >>> from tryon.models.flux2_turbo import Flux2TurboAdapter
    >>> 
    >>> adapter = Flux2TurboAdapter()
    >>> images = adapter.generate_text_to_image(
    ...     prompt="A fashion model wearing elegant evening wear",
    ...     width=1024,
    ...     height=1024
    ... )
    >>> images[0].save("output.png")
"""

from .adapter import Flux2TurboAdapter

__version__ = "0.0.1"

__all__ = [
    "Flux2TurboAdapter",
]

