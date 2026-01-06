"""
SANA Model Adapters

SANA is a series of efficient diffusion models from NVIDIA for high-resolution 
image and video generation with Linear Diffusion Transformer architecture.

Models:
    - SANA: Text-to-image up to 4K, 20x smaller and 100x faster than Flux-12B
    - SANA-1.5: Better quality with efficient compute scaling
    - SANA-Sprint: One/few-step generation, 0.1s per 1024px image
    - SANA-Video: Efficient video generation with Block Linear Attention

Repository: https://github.com/NVlabs/Sana
License: Apache-2.0
"""

from .adapter import (
    SanaAdapter,
    SanaVideoAdapter,
    SANA_MODELS,
    SANA_VIDEO_MODELS,
    DEFAULT_VIDEO_NEGATIVE_PROMPT,
)

__all__ = [
    "SanaAdapter",
    "SanaVideoAdapter", 
    "SANA_MODELS",
    "SANA_VIDEO_MODELS",
    "DEFAULT_VIDEO_NEGATIVE_PROMPT",
]

