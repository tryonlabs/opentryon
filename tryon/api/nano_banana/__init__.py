"""
Nano Banana (Gemini Image Generation) API Adapter

This module provides adapters for Google's Gemini image generation models:
- Gemini 2.5 Flash Image (Nano Banana): Fast, efficient image generation
- Gemini 3 Pro Image Preview (Nano Banana Pro): Advanced image generation with 4K support
- Gemini 3.1 Flash Image (Nano Banana 2): Pro capabilities at Flash speed; 512px–4K
- Gemini 3.1 Flash-Lite Image (Nano Banana 2 Lite): Fastest/cheapest tier; 1K only

Reference: https://ai.google.dev/gemini-api/docs/image-generation
Nano Banana 2: https://blog.google/innovation-and-ai/technology/ai/nano-banana-2/
Nano Banana 2 Lite: https://deepmind.google/models/gemini-image/flash-lite/
"""

from .adapter import (
    NanoBananaAdapter,
    NanoBananaProAdapter,
    NanoBanana2Adapter,
    NanoBanana2LiteAdapter,
)

__all__ = [
    "NanoBananaAdapter",
    "NanoBananaProAdapter",
    "NanoBanana2Adapter",
    "NanoBanana2LiteAdapter",
]
