"""
Use-case directory for virtual try-on cloud API adapters that don't warrant
their own top-level vendor package (single-file adapters whose *primary*
purpose is VTON). Single-garment-VTON-model vendors with just one adapter
file land here rather than getting a new `tryon/api/<vendor>/` directory
each -- keeps the vendor count from growing the top-level `tryon/api/`
directory listing unbounded as more VTON-capable providers are added.
"""

from .flux_vto import FluxVTONAdapter
from .p_image_tryon import PImageTryOnAdapter

__all__ = [
    "FluxVTONAdapter",
    "PImageTryOnAdapter",
]
