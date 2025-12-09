"""
LumaAI API adapter

This module provides adapters for Luma AI's image generation models:
- Photon-Flash-1 (Luma AI): Fast and cost efficient image generation, ideal for rapid iteration and scale
- Photon-1 (Luma AI): High-fidelity default model for professional-grade quality, creativity and detailed prompt handling

This module provides adapters for Luma AI's Video generation model (Dream Machine):
- ray-1-6: “Balanced quality model for general video generation; slower but stable.”
- ray-2: “High-quality flagship model with the best motion, detail, and consistency.”
- ray-flash-2: “Fast, lower-latency model optimized for quick iterations and previews.”

Reference: https://docs.lumalabs.ai/docs/image-generation
"""

from .adapter import LumaAIAdapter
from .luma_video_adapter import LumaAIVideoAdapter

__all__ = [
    'LumaAIAdapter',
    'LumaAIVideoAdapter',
]