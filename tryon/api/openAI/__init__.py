"""
GPT Image 1 API Adapter

This module provides an adapter for OpenAI's image generation model:
- GPT Image 1 (gpt-image-1): High-quality image generation and image editing
  with support for text-to-image, image-to-image edits, masks, background
  control, quality settings, and multiple output images.

The adapter normalizes OpenAI SDK responses and returns decoded image bytes
suitable for saving, post-processing, or further transformation.

Reference:
https://platform.openai.com/docs/guides/image-generation
"""

from .image_adapter import GPTImageAdapter

__all__ = [
    'GPTImageAdapter',
]