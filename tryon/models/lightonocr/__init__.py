"""
LightOnOCR-3 (open-weight) local OCR package.

In-process Hugging Face Transformers adapter for LightOn's Apache-2.0 OCR models. No
first-party hosted API exists. See :mod:`tryon.models.lightonocr.adapter`.
"""

from .adapter import LightOnOCRLocalAdapter

__all__ = ["LightOnOCRLocalAdapter"]
