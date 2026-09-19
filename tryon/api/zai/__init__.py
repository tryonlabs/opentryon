"""
GLM-5.3-FlashX (Z.ai / Zhipu) Multimodal Understanding API Adapter

High-speed serving tier of GLM-5.3-Flash: text, image, and video
understanding via Z.ai's OpenAI-compatible Chat Completions API. General
purpose -- useful for the fashion domain (describing garments, outfits,
lookbook videos) as well as any other domain (documents, UI, product
photography).

Reference: https://docs.z.ai/guides/vlm/glm-5.3-flash
"""

from .adapter import GLMUnderstandAdapter

__all__ = [
    "GLMUnderstandAdapter",
]
