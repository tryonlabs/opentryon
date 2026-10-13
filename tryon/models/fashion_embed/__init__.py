"""
Fashion-specific retrieval embeddings (open weights): Marqo-FashionSigLIP,
MODA (HopitAI) and ZooClaw-FashionSigLIP2. See :mod:`tryon.models.fashion_embed.adapter`.
"""

from .adapter import FashionOpenCLIPAdapter, ZooClawFashionSigLIP2Adapter

__all__ = ["FashionOpenCLIPAdapter", "ZooClawFashionSigLIP2Adapter"]
