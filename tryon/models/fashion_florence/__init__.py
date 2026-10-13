"""
Fashion Florence (open-weight, local) -- structured fashion attribute tagging.

Florence-2-large LoRA that turns a garment photo into JSON tags
(category, primary_color, material, style_tags). See
:mod:`tryon.models.fashion_florence.adapter`.
"""

from .adapter import FashionFlorenceAdapter

__all__ = ["FashionFlorenceAdapter"]
