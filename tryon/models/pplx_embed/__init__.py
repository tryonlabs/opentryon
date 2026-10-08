"""
Perplexity pplx-embed-v2-late (open-weight multi-vector embeddings) local package.

Late-interaction (ColBERT-style, MaxSim) retrievers for text, images and
visual documents. See :mod:`tryon.models.pplx_embed.adapter`.
"""

from .adapter import PplxEmbedLateAdapter

__all__ = ["PplxEmbedLateAdapter"]
