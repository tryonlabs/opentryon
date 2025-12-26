"""Tool implementations for OpenTryOn MCP Server."""

from .virtual_tryon import (
    virtual_tryon_nova,
    virtual_tryon_kling,
    virtual_tryon_segmind,
)
from .image_gen import (
    generate_image_nano_banana,
    generate_image_nano_banana_pro,
    generate_image_flux2_pro,
    generate_image_flux2_flex,
    generate_image_luma_photon_flash,
    generate_image_luma_photon,
)
from .video_gen import (
    generate_video_luma_ray,
)
from .preprocessing import (
    segment_garment,
    extract_garment,
    segment_human,
)
from .datasets import (
    load_fashion_mnist,
    load_viton_hd,
)

__all__ = [
    # Virtual Try-On
    "virtual_tryon_nova",
    "virtual_tryon_kling",
    "virtual_tryon_segmind",
    # Image Generation
    "generate_image_nano_banana",
    "generate_image_nano_banana_pro",
    "generate_image_flux2_pro",
    "generate_image_flux2_flex",
    "generate_image_luma_photon_flash",
    "generate_image_luma_photon",
    # Video Generation
    "generate_video_luma_ray",
    # Preprocessing
    "segment_garment",
    "extract_garment",
    "segment_human",
    # Datasets
    "load_fashion_mnist",
    "load_viton_hd",
]

