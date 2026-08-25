"""
OpenTryOn Tools Module

DEPRECATED: frozen LangChain ``@tool`` wrappers from v0.0.2. Do not add new
tools here. Planner chat and MCP both use ``tryon.cli.registry`` +
``invoke_model``. These wrappers remain only so old example scripts that
import ``get_tool_output_cache`` keep importing.

Prefer::

    from tryon.cli.runner import invoke_model
    invoke_model("vton", "kling-ai", source_image=..., reference_image=..., dry_run=True)
"""

from .virtual_tryon import (
    get_virtual_tryon_tools,
    kling_ai_virtual_tryon,
    nova_canvas_virtual_tryon,
    segmind_virtual_tryon,
)

from .image_generation import (
    get_image_generation_tools,
    nano_banana_text_to_image,
    nano_banana_pro_text_to_image,
    nano_banana_2_text_to_image,
    flux2_pro_text_to_image,
    flux2_flex_text_to_image,
    gpt_image_text_to_image,
    luma_ai_text_to_image,
)

from .video_generation import (
    get_video_generation_tools,
    sora_text_to_video,
    sora_image_to_video,
    veo_text_to_video,
    veo_image_to_video,
    luma_ai_text_to_video,
    luma_ai_image_to_video,
)

from .model_swap import (
    get_model_swap_tools,
    nano_banana_pro_model_swap,
    flux2_pro_model_swap,
    flux2_flex_model_swap,
)

from .image_editing import (
    get_image_editing_tools,
    gpt_image_edit,
    gpt_image_mask_edit,
    gpt_image_multi_edit,
)

from .fashion import (
    get_fashion_tools,
)

# Global cache for tool outputs (shared across all tools)
# This cache stores full outputs to avoid token limits when returning results to LLMs
_tool_output_cache = {}

# Import all tool modules and share the cache
from . import (
    virtual_tryon,
    image_generation,
    video_generation,
    model_swap,
    image_editing,
    fashion,
)

# Share the cache across all modules
virtual_tryon._tool_output_cache = _tool_output_cache
image_generation._tool_output_cache = _tool_output_cache
video_generation._tool_output_cache = _tool_output_cache
model_swap._tool_output_cache = _tool_output_cache
image_editing._tool_output_cache = _tool_output_cache
fashion._tool_output_cache = _tool_output_cache


def get_all_tools():
    """
    Get all available tools from all categories.
    
    Returns:
        List of LangChain tool objects
    """
    tools = []
    tools.extend(get_virtual_tryon_tools())
    tools.extend(get_image_generation_tools())
    tools.extend(get_video_generation_tools())
    tools.extend(get_model_swap_tools())
    tools.extend(get_image_editing_tools())
    tools.extend(get_fashion_tools())
    return tools


def get_tool_output_cache():
    """
    Get the global tool output cache.
    
    Returns:
        Dictionary containing cached tool outputs
    """
    return _tool_output_cache


def clear_tool_output_cache():
    """
    Clear the global tool output cache.
    """
    global _tool_output_cache
    _tool_output_cache.clear()


__all__ = [
    # Virtual Try-On
    "get_virtual_tryon_tools",
    "kling_ai_virtual_tryon",
    "nova_canvas_virtual_tryon",
    "segmind_virtual_tryon",
    # Image Generation
    "get_image_generation_tools",
    "nano_banana_text_to_image",
    "nano_banana_pro_text_to_image",
    "nano_banana_2_text_to_image",
    "flux2_pro_text_to_image",
    "flux2_flex_text_to_image",
    "gpt_image_text_to_image",
    "luma_ai_text_to_image",
    # Video Generation
    "get_video_generation_tools",
    "sora_text_to_video",
    "sora_image_to_video",
    "veo_text_to_video",
    "veo_image_to_video",
    "luma_ai_text_to_video",
    "luma_ai_image_to_video",
    # Model Swap
    "get_model_swap_tools",
    "nano_banana_pro_model_swap",
    "flux2_pro_model_swap",
    "flux2_flex_model_swap",
    # Image Editing
    "get_image_editing_tools",
    "gpt_image_edit",
    "gpt_image_mask_edit",
    "gpt_image_multi_edit",
    # Fashion
    "get_fashion_tools",
    # Utilities
    "get_all_tools",
    "get_tool_output_cache",
    "clear_tool_output_cache",
]

