"""
QIE-2511-Extract-Outfit (Apache-2.0 LoRA on Qwen-Image-Edit-2511) -- garment
extraction ("try-off"): worn outfit photo -> flat studio mockup.
See :mod:`tryon.models.extract_outfit.adapter`.
"""

from .adapter import ExtractOutfitAdapter

__all__ = ["ExtractOutfitAdapter"]
