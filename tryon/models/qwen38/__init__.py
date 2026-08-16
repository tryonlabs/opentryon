"""
Qwen3.8 (open-weight) Local Model

Local GPU inference adapter for Qwen's open-weight Qwen3.8 family on
Hugging Face — the open-weight counterpart to the hosted Qwen3.8-Max API
(see ``tryon.api.qwen.QwenUnderstandAdapter``).

Default: ``Qwen/Qwen3.8-27B`` (dense multimodal, practical single-/multi-GPU).
Flagship MoE ``Qwen/Qwen3.8-2.4T-A95B`` needs cluster serving (vLLM/SGLang).

Reference: https://huggingface.co/Qwen/Qwen3.8-27B
"""

from .adapter import Qwen38Adapter

__all__ = [
    "Qwen38Adapter",
]
