"""
OpenAI API Adapters

This module provides adapters for OpenAI's generative models:

Image Generation:
- GPT Image 1 (gpt-image-1): High-quality image generation and editing
- GPT Image 1.5 (gpt-image-1.5): Enhanced quality and prompt understanding
  with support for text-to-image, image-to-image edits, masks, background
  control, quality settings, and multiple output images.

Video Generation:
- Sora 2 (sora-2): Fast, high-quality video generation
- Sora 2 Pro (sora-2-pro): Enhanced quality with superior temporal consistency
  with support for text-to-video, image-to-video, and multiple wait strategies.

The adapters normalize OpenAI SDK responses and return decoded bytes
suitable for saving, post-processing, or further transformation.

References:
- Image: https://platform.openai.com/docs/guides/image-generation
- Video: https://platform.openai.com/docs/guides/video-generation
"""

from .image_adapter import GPTImageAdapter
from .video_adapter import SoraVideoAdapter

__all__ = [
    'GPTImageAdapter',
    'SoraVideoAdapter',
]