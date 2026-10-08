"""
Liquid AI d1 ("System One" decision model) local package.

Open-weight multimodal decision models (``LiquidAI/d1-3B``,
``LiquidAI/d1-omni-600M``): typed, calibrated answers in a single forward pass
with zero output tokens. See :mod:`tryon.models.liquid_d1.adapter`.
"""

from .adapter import LiquidD1Adapter

__all__ = ["LiquidD1Adapter"]
