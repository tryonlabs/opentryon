"""
FASHN AI catalogue-workflow endpoints (product-to-model, model-create,
model-swap, face-to-model, reframe, edit, image-to-video, background-remove).

Extends the try-on adapter in :mod:`tryon.api.vton.fashn` (same key, same
``/v1/run`` + ``/v1/status`` protocol). See :mod:`tryon.api.fashn.adapter`.
"""

from .adapter import FashnAdapter

__all__ = ["FashnAdapter"]
