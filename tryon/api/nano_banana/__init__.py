"""
Nano Banana (Gemini Image Generation) API Adapter

This module provides adapters for Google's Gemini image generation models:
- Gemini 2.5 Flash Image (Nano Banana): Fast, efficient image generation
- Gemini 3 Pro Image Preview (Nano Banana Pro): Advanced image generation with 4K support

Reference: https://ai.google.dev/gemini-api/docs/image-generation
"""

from .adapter import NanoBananaAdapter, NanoBananaProAdapter

__all__ = [
    'NanoBananaAdapter',
    'NanoBananaProAdapter',
]

