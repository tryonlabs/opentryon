"""
Google EmbeddingGemma 2 (open-weight multimodal embeddings) local package.

One shared 768-d space for text, code, images, video and audio. See
:mod:`tryon.models.embeddinggemma.adapter`.
"""

from .adapter import EmbeddingGemma2Adapter

__all__ = ["EmbeddingGemma2Adapter"]
