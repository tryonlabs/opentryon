"""
Ternary Bonsai 2 27B (PrismML) local model package.

Thin OpenAI-compatible client for the llama.cpp / MLX server the model
ships with. See :mod:`tryon.models.ternary_bonsai.adapter` for details.
"""

from .adapter import TernaryBonsaiAdapter

__all__ = [
    "TernaryBonsaiAdapter",
]
