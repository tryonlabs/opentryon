"""
Local Models Module

This module provides adapters for local inference models that run on user's hardware.
Unlike the API adapters in tryon.api which call cloud services, these models require
local GPU resources for inference.

Available Models:
    - Flux2TurboAdapter: FLUX.2-dev Turbo for fast image generation (8 steps)
      Supports both text-to-image and image-to-image generation
    - KimiVLAdapter: Kimi-VL open-weight multimodal model (image/video
      understanding), the local counterpart to the Kimi K2.6/K2.7 Code APIs
    - Qwen38Adapter: Qwen3.8-27B open-weight multimodal understanding,
      the local counterpart to the hosted qwen3.8-max DashScope API
    - QwenImageLocalAdapter: Qwen-Image-2512 T2I + Qwen-Image-Edit-2511
      I2I/VTON, the local counterpart to the hosted qwen-image DashScope API
    - LTX25Adapter: LTX-2.5 open-weight text/image-to-video with synced audio
    - Wan22Adapter: Wan 2.2 open-weight text/image-to-video (Diffusers)

Examples:
    Text-to-image generation:
    >>> from tryon.models import Flux2TurboAdapter
    >>> 
    >>> adapter = Flux2TurboAdapter()
    >>> images = adapter.generate_text_to_image(
    ...     prompt="A fashion model wearing a dress",
    ...     width=1024,
    ...     height=1024
    ... )
    >>> images[0].save("output.png")
    
    Image-to-image generation:
    >>> from PIL import Image
    >>> 
    >>> input_image = Image.open("input.jpg")
    >>> edited_images = adapter.generate_image_to_image(
    ...     image=input_image,
    ...     prompt="A fashion model in an elegant blue dress"
    ... )
    >>> edited_images[0].save("edited_output.png")

Requirements:
    - CUDA-capable GPU (recommended: 12GB+ VRAM)
    - PyTorch 2.1+
    - diffusers >= 0.29.0
"""

from .flux2_turbo import Flux2TurboAdapter
from .kimi_vl import KimiVLAdapter
from .ltx25 import LTX25Adapter
from .qwen38 import Qwen38Adapter
from .qwen_image import QwenImageLocalAdapter
from .wan22 import Wan22Adapter

__all__ = [
    "Flux2TurboAdapter",
    "KimiVLAdapter",
    "LTX25Adapter",
    "Qwen38Adapter",
    "QwenImageLocalAdapter",
    "Wan22Adapter",
]
