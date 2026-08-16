"""
Qwen 3.8 (DashScope / Qwen Cloud) Multimodal Understanding API Adapter

Hosted Alibaba Cloud Model Studio / DashScope OpenAI-compatible chat API for
Qwen3.8-Max — native text, image, and video understanding.

Reference:
https://docs.qwencloud.com/developer-guides/multimodal/vision
https://www.alibabacloud.com/help/en/model-studio/vision
"""

from .adapter import QwenUnderstandAdapter

__all__ = [
    "QwenUnderstandAdapter",
]
