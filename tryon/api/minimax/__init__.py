"""MiniMax / Hailuo API adapters."""

from .adapter import HailuoVideoAdapter
from .h3_adapter import MiniMaxH3Adapter
from .h3_image_adapter import MiniMaxH3ImageAdapter

__all__ = ["HailuoVideoAdapter", "MiniMaxH3Adapter", "MiniMaxH3ImageAdapter"]
