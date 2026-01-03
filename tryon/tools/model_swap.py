"""
Model Swap Tools

This module provides LangChain tools for swapping models in images while preserving outfits.
Uses image generation models with intelligent prompt engineering to maintain clothing consistency.

All tools follow a consistent pattern and store full outputs in a global cache.
"""

import json
import hashlib
from typing import Optional
from pydantic import BaseModel, Field
from langchain.tools import tool

from tryon.api.nano_banana import NanoBananaProAdapter
from tryon.api.flux2 import Flux2ProAdapter, Flux2FlexAdapter

# Global cache (shared across all tools)
_tool_output_cache = {}


class ModelSwapToolInput(BaseModel):
    """Input schema for model swap tools."""
    image: str = Field(
        description="Path or URL to the image of person wearing the outfit to preserve"
    )
    model_description: str = Field(
        description=(
            "Detailed description of the desired model/person to generate. "
            "Should include specific attributes like: "
            "gender, age range, ethnicity, body type, facial features, pose, expression, "
            "and importantly must emphasize preserving the exact outfit, clothing, and styling. "
            "Example: 'Professional fashion photography showing an athletic Asian woman in her 30s "
            "wearing the exact same outfit with all clothing details preserved, maintaining original "
            "lighting and background.'"
        )
    )
    resolution: Optional[str] = Field(
        default="4K",
        description="Output resolution for Nano Banana Pro. Options: '1K', '2K', '4K'. Default: '4K'"
    )
    width: Optional[int] = Field(
        default=None,
        description="Image width in pixels for FLUX models (minimum: 64)"
    )
    height: Optional[int] = Field(
        default=None,
        description="Image height in pixels for FLUX models (minimum: 64)"
    )
    seed: Optional[int] = Field(
        default=None,
        description="Random seed for reproducibility"
    )


@tool("nano_banana_pro_model_swap", args_schema=ModelSwapToolInput)
def nano_banana_pro_model_swap(
    image: str,
    model_description: str,
    resolution: str = "4K",
    use_search_grounding: bool = False,
    **kwargs
) -> str:
    """
    Swap the model/person in an image while preserving the outfit using Nano Banana Pro.
    
    This tool uses Google's Gemini 3 Pro Image Preview (Nano Banana Pro) to:
    1. Take an image of a person wearing an outfit
    2. Generate a new image with a different model/person based on the description
    3. Preserve the exact outfit, clothing details, patterns, and styling
    4. Maintain professional photography quality and composition
    
    Perfect for e-commerce and fashion brands to create professional product imagery
    with diverse models while keeping the clothing exactly the same.
    
    Args:
        image: Path or URL to the image of person wearing the outfit
        model_description: Detailed prompt describing the desired model and emphasizing
                          outfit preservation. Should be comprehensive and specific.
        resolution: Output resolution ('1K', '2K', or '4K'). Default: '4K'
        use_search_grounding: Use Google Search for real-world references. Default: False
    
    Returns:
        JSON string containing status, provider, image_count, cache_key, and message
    """
    try:
        print(" Initializing Nano Banana Pro adapter...")
        adapter = NanoBananaProAdapter()
        
        # Enhance prompt to emphasize outfit preservation
        enhanced_prompt = (
            f"{model_description} "
            "The person must be wearing the exact same outfit, clothing, and accessories "
            "as shown in the reference image. All clothing details, colors, patterns, "
            "textures, and styling must be preserved perfectly. Maintain the same "
            "photography style, lighting, and background."
        )
        
        print("Generating model swap (this may take a moment)...")
        images = adapter.generate_image_edit(
            image=image,
            prompt=enhanced_prompt,
            resolution=resolution,
            use_search_grounding=use_search_grounding,
            **kwargs
        )
        print(" Nano Banana Pro model swap completed")
        
        # Store full images in cache
        cache_key = hashlib.md5(
            f"nano_banana_pro_swap_{image}_{model_description}_{resolution}".encode()
        ).hexdigest()
        _tool_output_cache[cache_key] = {
            "provider": "nano_banana_pro",
            "images": images if isinstance(images, list) else [images],
            "original_image": image,
            "model_description": model_description,
            "resolution": resolution,
        }
        
        image_count = len(images) if isinstance(images, list) else 1
        
        return json.dumps({
            "status": "success",
            "provider": "nano_banana_pro",
            "image_count": image_count,
            "cache_key": cache_key,
            "message": f"Successfully swapped model while preserving outfit using Nano Banana Pro"
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "provider": "nano_banana_pro",
            "error": str(e),
            "message": f"Failed to swap model: {str(e)}"
        })


@tool("flux2_pro_model_swap", args_schema=ModelSwapToolInput)
def flux2_pro_model_swap(
    image: str,
    model_description: str,
    width: Optional[int] = None,
    height: Optional[int] = None,
    seed: Optional[int] = None,
    **kwargs
) -> str:
    """
    Swap the model/person in an image while preserving the outfit using FLUX 2 Pro.
    
    Uses FLUX 2 Pro's image editing capabilities to replace the model while maintaining
    outfit consistency. Excellent for high-resolution professional outputs.
    
    Args:
        image: Path or URL to the image of person wearing the outfit
        model_description: Detailed prompt describing the desired model and emphasizing
                          outfit preservation
        width: Image width in pixels (minimum: 64)
        height: Image height in pixels (minimum: 64)
        seed: Optional seed for reproducibility
    
    Returns:
        JSON string containing status, provider, image_count, cache_key, and message
    """
    try:
        print(" Initializing FLUX 2 Pro adapter...")
        adapter = Flux2ProAdapter()
        
        # Enhance prompt to emphasize outfit preservation
        enhanced_prompt = (
            f"{model_description} "
            "The person must be wearing the exact same outfit, clothing, and accessories "
            "as shown in the reference image. All clothing details, colors, patterns, "
            "textures, and styling must be preserved perfectly. Maintain the same "
            "photography style, lighting, and background."
        )
        
        print("Generating model swap...")
        images = adapter.generate_image_edit(
            image=image,
            prompt=enhanced_prompt,
            width=width,
            height=height,
            seed=seed,
            **kwargs
        )
        print(" FLUX 2 Pro model swap completed")
        
        # Store full images in cache
        cache_key = hashlib.md5(
            f"flux2_pro_swap_{image}_{model_description}_{width}_{height}_{seed}".encode()
        ).hexdigest()
        _tool_output_cache[cache_key] = {
            "provider": "flux2_pro",
            "images": images if isinstance(images, list) else [images],
            "original_image": image,
            "model_description": model_description,
            "width": width,
            "height": height,
            "seed": seed,
        }
        
        image_count = len(images) if isinstance(images, list) else 1
        
        return json.dumps({
            "status": "success",
            "provider": "flux2_pro",
            "image_count": image_count,
            "cache_key": cache_key,
            "message": f"Successfully swapped model while preserving outfit using FLUX 2 Pro"
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "provider": "flux2_pro",
            "error": str(e),
            "message": f"Failed to swap model: {str(e)}"
        })


@tool("flux2_flex_model_swap", args_schema=ModelSwapToolInput)
def flux2_flex_model_swap(
    image: str,
    model_description: str,
    width: Optional[int] = None,
    height: Optional[int] = None,
    seed: Optional[int] = None,
    **kwargs
) -> str:
    """
    Swap the model/person in an image while preserving the outfit using FLUX 2 Flex.
    
    Uses FLUX 2 Flex's image editing capabilities for faster model swapping with good quality.
    Good balance between speed and quality.
    
    Args:
        image: Path or URL to the image of person wearing the outfit
        model_description: Detailed prompt describing the desired model and emphasizing
                          outfit preservation
        width: Image width in pixels (minimum: 64)
        height: Image height in pixels (minimum: 64)
        seed: Optional seed for reproducibility
    
    Returns:
        JSON string containing status, provider, image_count, cache_key, and message
    """
    try:
        print(" Initializing FLUX 2 Flex adapter...")
        adapter = Flux2FlexAdapter()
        
        # Enhance prompt to emphasize outfit preservation
        enhanced_prompt = (
            f"{model_description} "
            "The person must be wearing the exact same outfit, clothing, and accessories "
            "as shown in the reference image. All clothing details, colors, patterns, "
            "textures, and styling must be preserved perfectly. Maintain the same "
            "photography style, lighting, and background."
        )
        
        print("Generating model swap...")
        images = adapter.generate_image_edit(
            image=image,
            prompt=enhanced_prompt,
            width=width,
            height=height,
            seed=seed,
            **kwargs
        )
        print(" FLUX 2 Flex model swap completed")
        
        # Store full images in cache
        cache_key = hashlib.md5(
            f"flux2_flex_swap_{image}_{model_description}_{width}_{height}_{seed}".encode()
        ).hexdigest()
        _tool_output_cache[cache_key] = {
            "provider": "flux2_flex",
            "images": images if isinstance(images, list) else [images],
            "original_image": image,
            "model_description": model_description,
            "width": width,
            "height": height,
            "seed": seed,
        }
        
        image_count = len(images) if isinstance(images, list) else 1
        
        return json.dumps({
            "status": "success",
            "provider": "flux2_flex",
            "image_count": image_count,
            "cache_key": cache_key,
            "message": f"Successfully swapped model while preserving outfit using FLUX 2 Flex"
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "provider": "flux2_flex",
            "error": str(e),
            "message": f"Failed to swap model: {str(e)}"
        })


def get_model_swap_tools() -> list:
    """
    Get all model swap tools.
    
    Returns:
        List of LangChain tool objects for model swapping
    """
    return [
        nano_banana_pro_model_swap,
        flux2_pro_model_swap,
        flux2_flex_model_swap,
    ]

