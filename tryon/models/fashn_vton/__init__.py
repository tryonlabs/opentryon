"""
FASHN VTON v1.5 (Apache-2.0, open weights) local virtual try-on package.

Open-weight, maskless, pixel-space try-on from FASHN AI -- the local twin of the
hosted ``fashn-tryon-*`` APIs. See :mod:`tryon.models.fashn_vton.adapter`.
"""

from .adapter import FashnVTONLocalAdapter

__all__ = ["FashnVTONLocalAdapter"]
