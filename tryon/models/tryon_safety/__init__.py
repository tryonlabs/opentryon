"""
Genlook try-on safety classifier (Apache-2.0, local).

Gates garments before they are rendered onto a shopper's photo. See
:mod:`tryon.models.tryon_safety.adapter`.
"""

from .adapter import TryOnSafetyAdapter

__all__ = ["TryOnSafetyAdapter"]
