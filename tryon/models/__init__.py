"""
OpenTryOn Models

Local inference adapters for various AI models requiring GPU compute.
These are distinct from API adapters in tryon/api/ which integrate third-party services.

Available Models:
    - SANA: Efficient text-to-image and video generation (NVIDIA)
"""

from .sana import SanaAdapter, SanaVideoAdapter, SANA_MODELS, SANA_VIDEO_MODELS

__all__ = [
    # SANA
    "SanaAdapter",
    "SanaVideoAdapter",
    "SANA_MODELS",
    "SANA_VIDEO_MODELS",
]

