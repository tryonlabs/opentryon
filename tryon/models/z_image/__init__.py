"""
Z-Image Model Integration

Z-Image is a powerful and highly efficient image generation model family with 6B parameters
from Tongyi-MAI. This module provides adapters for all Z-Image variants.

Model Variants:
    - Z-Image-Turbo: Distilled version with 8 NFEs, sub-second inference
    - Z-Image: Foundation model with high-quality generation
    - Z-Image-Omni-Base: Versatile foundation for generation and editing
    - Z-Image-Edit: Fine-tuned specifically for image editing

Reference: https://github.com/Tongyi-MAI/Z-Image

Example:
    >>> from tryon.models.z_image import ZImageAdapter
    >>> 
    >>> # Fast generation with Turbo
    >>> adapter = ZImageAdapter(model_variant="turbo")
    >>> images = adapter.generate(prompt="A cute baby polar bear")
    >>> images[0].save("output.png")
    >>> 
    >>> # High-quality generation
    >>> adapter = ZImageAdapter(model_variant="base")
    >>> images = adapter.generate(
    ...     prompt="Professional fashion photograph",
    ...     negative_prompt="blurry, low quality",
    ...     guidance_scale=4.0
    ... )
"""

from tryon.models.z_image.adapter import (
    ZImageAdapter,
    ZImageModelVariant,
    ZImageModelConfig,
    GenerationParams,
    EditingParams,
    MODEL_CONFIGS,
    create_turbo_adapter,
    create_base_adapter,
    create_omni_adapter,
    create_edit_adapter,
)

__all__ = [
    # Main adapter
    "ZImageAdapter",
    # Enums and configs
    "ZImageModelVariant",
    "ZImageModelConfig",
    "MODEL_CONFIGS",
    # Parameter dataclasses
    "GenerationParams",
    "EditingParams",
    # Factory functions
    "create_turbo_adapter",
    "create_base_adapter",
    "create_omni_adapter",
    "create_edit_adapter",
]
