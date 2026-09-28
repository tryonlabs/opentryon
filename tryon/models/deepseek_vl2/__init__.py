"""
DeepSeek-VL2 (open-weight) local model package.

Local Hugging Face Transformers + ``deepseek_vl2`` adapter -- no
first-party hosted API exists for DeepSeek-VL2. See
:mod:`tryon.models.deepseek_vl2.adapter` for details.
"""

from .adapter import DeepSeekVL2Adapter

__all__ = [
    "DeepSeekVL2Adapter",
]
