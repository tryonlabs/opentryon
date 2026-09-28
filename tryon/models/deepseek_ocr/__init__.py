"""
DeepSeek-OCR (open-weight) local model package.

Local Hugging Face Transformers adapter for document/image OCR -- no
first-party hosted API exists. See
:mod:`tryon.models.deepseek_ocr.adapter` for details.
"""

from .adapter import DeepSeekOCRAdapter

__all__ = [
    "DeepSeekOCRAdapter",
]
