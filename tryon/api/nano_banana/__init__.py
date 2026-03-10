"""
Nano Banana (Gemini Image Generation) API Adapter

This module provides adapters for Google's Gemini image generation models:
- Gemini 2.5 Flash Image (Nano Banana): Fast, efficient image generation
- Gemini 3 Pro Image Preview (Nano Banana Pro): Advanced image generation with 4K support
- Gemini 3.1 Flash Image (Nano Banana 2): Pro capabilities at Flash speed; 512px–4K

Reference: https://ai.google.dev/gemini-api/docs/image-generation
Nano Banana 2: https://blog.google/innovation-and-ai/technology/ai/nano-banana-2/
"""

from .adapter import NanoBananaAdapter, NanoBananaProAdapter, NanoBanana2Adapter

__all__ = [
    "NanoBananaAdapter",
    "NanoBananaProAdapter",
    "NanoBanana2Adapter",
]
