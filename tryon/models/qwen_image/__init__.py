"""
Qwen-Image (open-weight) local model.

Local GPU Diffusers adapter for the Qwen-Image series — the open-weight
counterpart to the hosted Qwen-Image DashScope API
(see ``tryon.api.qwen.QwenImageAdapter``).

Default T2I: ``Qwen/Qwen-Image-2512``.
Default edit / VTON: ``Qwen/Qwen-Image-Edit-2511`` (Edit-Plus, 1–3 refs).

Reference: https://huggingface.co/docs/diffusers/main/en/api/pipelines/qwenimage
"""

from .adapter import QwenImageLocalAdapter

__all__ = [
    "QwenImageLocalAdapter",
]
