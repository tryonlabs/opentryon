"""
Pruna AI adapters (image + video).

Shared client: :class:`tryon.api.pruna.client.PrunaClient`
VTON try-on remains at :class:`tryon.api.vton.PImageTryOnAdapter` and reuses
the same client under the hood.
"""

from .p_image import PImageAdapter
from .p_image_edit import PImageEditAdapter
from .p_image_ideogram import PImageIdeogramAdapter
from .p_image_upscale import PImageUpscaleAdapter
from .p_video import PVideoAdapter
from .p_video_animate import PVideoAnimateAdapter
from .p_video_avatar import PVideoAvatarAdapter
from .p_video_replace import PVideoReplaceAdapter

__all__ = [
    "PImageAdapter",
    "PImageEditAdapter",
    "PImageIdeogramAdapter",
    "PImageUpscaleAdapter",
    "PVideoAdapter",
    "PVideoAnimateAdapter",
    "PVideoAvatarAdapter",
    "PVideoReplaceAdapter",
]
