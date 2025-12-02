"""
LumaAI API adapter

This module provides adapters for Luma AI's image generation models:
- Photon-Flash-1 (Luma AI): Fast and cost efficient image generation, ideal for rapid iteration and scale
- Photon-1 (Luma AI): High-fidelity default model for professional-grade quality, creativity and detailed prompt handling

Reference: https://docs.lumalabs.ai/docs/image-generation
"""

from .adapter import LumaAIAdapter

__all__ = [
    'LumaAIAdapter',
]