"""
DeepSeek-V4.1-Flash (deepseek-flash) Multimodal Understanding API Adapter

Text and image understanding via DeepSeek's OpenAI-compatible Chat
Completions API. General purpose -- useful for the fashion domain
(describing garments, outfits) as well as any other domain (documents, UI,
product photography). Image only -- DeepSeek's API does not accept video.

Reference: https://api-docs.deepseek.com/quick_start/pricing/
"""

from .adapter import DeepSeekUnderstandAdapter

__all__ = [
    "DeepSeekUnderstandAdapter",
]
