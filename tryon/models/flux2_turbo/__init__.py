"""
FLUX.2-dev Turbo - Local Inference Adapter

A distilled LoRA adapter for FLUX.2 [dev] that enables high-quality image generation
in just 8 inference steps (6x faster than the base model).

Features:
    - Text-to-image generation: Generate images from text prompts
    - Image-to-image generation: Transform and edit existing images based on text prompts
    - 8-step inference: 6x faster than base FLUX.2 [dev] model
    - Quality preserved: Maintains or surpasses original FLUX.2 [dev] quality

Model: https://huggingface.co/fal/FLUX.2-dev-Turbo
License: FLUX [dev] Non-Commercial License

Requirements:
    - CUDA-capable GPU (recommended: 12GB+ VRAM)
    - PyTorch 2.1+
    - diffusers >= 0.29.0

Examples:
    Text-to-image generation:
    >>> from tryon.models.flux2_turbo import Flux2TurboAdapter
    >>> 
    >>> adapter = Flux2TurboAdapter()
    >>> images = adapter.generate_text_to_image(
    ...     prompt="A fashion model wearing elegant evening wear",
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
    ...     prompt="A fashion model in an elegant blue evening gown"
    ... )
    >>> edited_images[0].save("edited_output.png")
"""

from .adapter import Flux2TurboAdapter

__version__ = "0.0.1"

__all__ = [
    "Flux2TurboAdapter",
]
