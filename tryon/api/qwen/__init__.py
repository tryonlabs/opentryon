"""
Qwen family (DashScope / Qwen Cloud) API adapters.

- ``QwenUnderstandAdapter`` — Qwen3.8-Max multimodal understanding
  (OpenAI-compatible chat).
- ``QwenImageAdapter`` — Qwen-Image 3.0 T2I / I2I / virtual try-on
  (DashScope multimodal-generation).

Same ``DASHSCOPE_API_KEY``. Different endpoints (chat vs ``/api/v1`` image).

Reference:
https://docs.qwencloud.com/developer-guides/multimodal/vision
https://docs.qwencloud.com/api-reference/image-generation/qwen-text-to-image
https://www.alibabacloud.com/help/en/model-studio/vision
"""

from .adapter import QwenUnderstandAdapter
from .image_adapter import QwenImageAdapter

__all__ = [
    "QwenUnderstandAdapter",
    "QwenImageAdapter",
]
