"""
Image Generation Tools

This module provides LangChain tools for image generation using:
- Nano Banana (Gemini 2.5 Flash Image)
- Nano Banana Pro (Gemini 3 Pro Image Preview)
- Nano Banana 2 (Gemini 3.1 Flash Image)
- FLUX 2 Pro
- FLUX 2 Flex
- GPT-Image (OpenAI)
- Luma AI

All tools follow a consistent pattern and store full outputs in a global cache.
"""

import json
import hashlib
from typing import Optional, List
from pydantic import BaseModel, Field
from langchain.tools import tool

from tryon.api.nano_banana import NanoBananaAdapter, NanoBananaProAdapter, NanoBanana2Adapter
from tryon.api.flux2 import Flux2ProAdapter, Flux2FlexAdapter
from tryon.api.openAI.image_adapter import GPTImageAdapter
from tryon.api.lumaAI import LumaAIAdapter

# Global cache (will be initialized in __init__.py)
_tool_output_cache = {}


class TextToImageToolInput(BaseModel):
    """Base input schema for text-to-image generation."""
    prompt: str = Field(description="Text description of the image to generate")
    aspect_ratio: Optional[str] = Field(
        default=None,
        description="Aspect ratio (for Nano Banana models: '1:1', '16:9', '9:16', etc.)"
    )
    width: Optional[int] = Field(
        default=None,
        description="Image width in pixels (for FLUX models)"
    )
    height: Optional[int] = Field(
        default=None,
        description="Image height in pixels (for FLUX models)"
    )
    size: Optional[str] = Field(
        default=None,
        description="Image size for GPT-Image (e.g., '1024x1024', '1536x1024')"
    )
    quality: Optional[str] = Field(
        default=None,
        description="Quality setting for GPT-Image ('low', 'high', 'medium', 'auto')"
    )
    seed: Optional[int] = Field(
        default=None,
        description="Random seed for reproducibility"
    )


@tool("nano_banana_text_to_image", args_schema=TextToImageToolInput)
def nano_banana_text_to_image(
    prompt: str,
    aspect_ratio: Optional[str] = None,
    **kwargs
) -> str:
    """
    Generate images from text using Google's Nano Banana (Gemini 2.5 Flash Image).
    
    Fast and efficient image generation with support for various aspect ratios.
    Good for quick iterations and general fashion image generation.
    
    Args:
        prompt: Text description of the image to generate
        aspect_ratio: Optional aspect ratio ('1:1', '2:3', '3:2', '16:9', '9:16', etc.)
    
    Returns:
        JSON string containing status, provider, image_count, cache_key, and message
    """
    try:
        print(" Initializing Nano Banana adapter...")
        adapter = NanoBananaAdapter()
        print("Generating images...")
        images = adapter.generate_text_to_image(
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            **kwargs
        )
        print(" Nano Banana generation completed")
        
        # Store full images in cache
        cache_key = hashlib.md5(
            f"nano_banana_{prompt}_{aspect_ratio}".encode()
        ).hexdigest()
        _tool_output_cache[cache_key] = {
            "provider": "nano_banana",
            "images": images if isinstance(images, list) else [images],
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
        }
        
        image_count = len(images) if isinstance(images, list) else 1
        
        return json.dumps({
            "status": "success",
            "provider": "nano_banana",
            "image_count": image_count,
            "cache_key": cache_key,
            "message": f"Successfully generated {image_count} image(s) using Nano Banana"
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "provider": "nano_banana",
            "error": str(e),
            "message": f"Failed to generate images: {str(e)}"
        })


@tool("nano_banana_pro_text_to_image", args_schema=TextToImageToolInput)
def nano_banana_pro_text_to_image(
    prompt: str,
    aspect_ratio: Optional[str] = None,
    resolution: Optional[str] = "4K",
    use_search_grounding: Optional[bool] = False,
    **kwargs
) -> str:
    """
    Generate high-quality images from text using Google's Nano Banana Pro (Gemini 3 Pro Image Preview).
    
    Professional-grade image generation with 4K resolution support and advanced features.
    Best for high-quality fashion imagery and professional outputs.
    
    Args:
        prompt: Text description of the image to generate
        aspect_ratio: Optional aspect ratio ('1:1', '2:3', '3:2', '16:9', '9:16', etc.)
        resolution: Output resolution ('1K', '2K', '4K'). Default: '4K'
        use_search_grounding: Use Google Search grounding for real-world references. Default: False
    
    Returns:
        JSON string containing status, provider, image_count, cache_key, and message
    """
    try:
        print(" Initializing Nano Banana Pro adapter...")
        adapter = NanoBananaProAdapter()
        print("Generating high-quality images...")
        images = adapter.generate_text_to_image(
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            use_search_grounding=use_search_grounding,
            **kwargs
        )
        print(" Nano Banana Pro generation completed")
        
        # Store full images in cache
        cache_key = hashlib.md5(
            f"nano_banana_pro_{prompt}_{aspect_ratio}_{resolution}".encode()
        ).hexdigest()
        _tool_output_cache[cache_key] = {
            "provider": "nano_banana_pro",
            "images": images if isinstance(images, list) else [images],
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
        }
        
        image_count = len(images) if isinstance(images, list) else 1
        
        return json.dumps({
            "status": "success",
            "provider": "nano_banana_pro",
            "image_count": image_count,
            "cache_key": cache_key,
            "message": f"Successfully generated {image_count} high-quality image(s) using Nano Banana Pro"
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "provider": "nano_banana_pro",
            "error": str(e),
            "message": f"Failed to generate images: {str(e)}"
        })


@tool("nano_banana_2_text_to_image", args_schema=TextToImageToolInput)
def nano_banana_2_text_to_image(
    prompt: str,
    aspect_ratio: Optional[str] = None,
    resolution: Optional[str] = "2K",
    use_search_grounding: Optional[bool] = False,
    **kwargs,
) -> str:
    """
    Generate images from text using Google's Nano Banana 2 (Gemini 3.1 Flash Image).

    Combines Pro-level quality with Flash speed: 1K/2K/4K resolution, subject consistency,
    and precise instruction following. Ideal for rapid iteration and production-ready assets.

    Args:
        prompt: Text description of the image to generate
        aspect_ratio: Optional aspect ratio ('1:1', '2:3', '16:9', '9:16', etc.)
        resolution: Output resolution ('1K', '2K', '4K'). Default: '2K'
        use_search_grounding: Use Google Search for real-world grounding. Default: False

    Returns:
        JSON string containing status, provider, image_count, cache_key, and message
    """
    try:
        print(" Initializing Nano Banana 2 adapter...")
        adapter = NanoBanana2Adapter()
        print("Generating images...")
        images = adapter.generate_text_to_image(
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            resolution=resolution or "2K",
            use_search_grounding=use_search_grounding,
            **kwargs,
        )
        print(" Nano Banana 2 generation completed")

        cache_key = hashlib.md5(
            f"nano_banana_2_{prompt}_{aspect_ratio}_{resolution}".encode()
        ).hexdigest()
        _tool_output_cache[cache_key] = {
            "provider": "nano_banana_2",
            "images": images if isinstance(images, list) else [images],
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
        }

        image_count = len(images) if isinstance(images, list) else 1
        return json.dumps({
            "status": "success",
            "provider": "nano_banana_2",
            "image_count": image_count,
            "cache_key": cache_key,
            "message": f"Successfully generated {image_count} image(s) using Nano Banana 2",
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "provider": "nano_banana_2",
            "error": str(e),
            "message": f"Failed to generate images: {str(e)}",
        })


@tool("flux2_pro_text_to_image", args_schema=TextToImageToolInput)
def flux2_pro_text_to_image(
    prompt: str,
    width: Optional[int] = None,
    height: Optional[int] = None,
    seed: Optional[int] = None,
    **kwargs
) -> str:
    """
    Generate images from text using FLUX 2 Pro.
    
    High-quality image generation with fine-grained control over dimensions.
    Excellent for fashion photography and detailed imagery.
    
    Args:
        prompt: Text description of the image to generate
        width: Image width in pixels (minimum: 64)
        height: Image height in pixels (minimum: 64)
        seed: Optional seed for reproducibility
    
    Returns:
        JSON string containing status, provider, image_count, cache_key, and message
    """
    try:
        print(" Initializing FLUX 2 Pro adapter...")
        adapter = Flux2ProAdapter()
        print("Generating images...")
        images = adapter.generate_text_to_image(
            prompt=prompt,
            width=width,
            height=height,
            seed=seed,
            **kwargs
        )
        print(" FLUX 2 Pro generation completed")
        
        # Store full images in cache
        cache_key = hashlib.md5(
            f"flux2_pro_{prompt}_{width}_{height}_{seed}".encode()
        ).hexdigest()
        _tool_output_cache[cache_key] = {
            "provider": "flux2_pro",
            "images": images if isinstance(images, list) else [images],
            "prompt": prompt,
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
            "message": f"Successfully generated {image_count} image(s) using FLUX 2 Pro"
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "provider": "flux2_pro",
            "error": str(e),
            "message": f"Failed to generate images: {str(e)}"
        })


@tool("flux2_flex_text_to_image", args_schema=TextToImageToolInput)
def flux2_flex_text_to_image(
    prompt: str,
    width: Optional[int] = None,
    height: Optional[int] = None,
    seed: Optional[int] = None,
    **kwargs
) -> str:
    """
    Generate images from text using FLUX 2 Flex.
    
    Fast and flexible image generation with good quality.
    Good balance between speed and quality for fashion imagery.
    
    Args:
        prompt: Text description of the image to generate
        width: Image width in pixels (minimum: 64)
        height: Image height in pixels (minimum: 64)
        seed: Optional seed for reproducibility
    
    Returns:
        JSON string containing status, provider, image_count, cache_key, and message
    """
    try:
        print(" Initializing FLUX 2 Flex adapter...")
        adapter = Flux2FlexAdapter()
        print("Generating images...")
        images = adapter.generate_text_to_image(
            prompt=prompt,
            width=width,
            height=height,
            seed=seed,
            **kwargs
        )
        print(" FLUX 2 Flex generation completed")
        
        # Store full images in cache
        cache_key = hashlib.md5(
            f"flux2_flex_{prompt}_{width}_{height}_{seed}".encode()
        ).hexdigest()
        _tool_output_cache[cache_key] = {
            "provider": "flux2_flex",
            "images": images if isinstance(images, list) else [images],
            "prompt": prompt,
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
            "message": f"Successfully generated {image_count} image(s) using FLUX 2 Flex"
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "provider": "flux2_flex",
            "error": str(e),
            "message": f"Failed to generate images: {str(e)}"
        })


@tool("gpt_image_text_to_image", args_schema=TextToImageToolInput)
def gpt_image_text_to_image(
    prompt: str,
    size: Optional[str] = "1024x1024",
    quality: Optional[str] = "high",
    model_version: Optional[str] = "gpt-image-1.5",
    **kwargs
) -> str:
    """
    Generate images from text using OpenAI's GPT-Image models.
    
    High-quality image generation with excellent prompt understanding.
    Supports multiple output images and various quality settings.
    
    Args:
        prompt: Text description of the image to generate
        size: Image size ('1024x1024', '1536x1024', '1024x1536', 'auto')
        quality: Quality setting ('low', 'high', 'medium', 'auto')
        model_version: Model version ('gpt-image-1' or 'gpt-image-1.5'). Default: 'gpt-image-1.5'
    
    Returns:
        JSON string containing status, provider, image_count, cache_key, and message
    """
    try:
        print(f" Initializing GPT-Image ({model_version}) adapter...")
        adapter = GPTImageAdapter(model_version=model_version)
        print("Generating images...")
        images = adapter.generate_text_to_image(
            prompt=prompt,
            size=size,
            quality=quality,
            **kwargs
        )
        print(" GPT-Image generation completed")
        
        # Store full images in cache
        cache_key = hashlib.md5(
            f"gpt_image_{model_version}_{prompt}_{size}_{quality}".encode()
        ).hexdigest()
        _tool_output_cache[cache_key] = {
            "provider": f"gpt_image_{model_version}",
            "images": images if isinstance(images, list) else [images],
            "prompt": prompt,
            "size": size,
            "quality": quality,
        }
        
        image_count = len(images) if isinstance(images, list) else 1
        
        return json.dumps({
            "status": "success",
            "provider": f"gpt_image_{model_version}",
            "image_count": image_count,
            "cache_key": cache_key,
            "message": f"Successfully generated {image_count} image(s) using GPT-Image {model_version}"
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "provider": f"gpt_image_{model_version}",
            "error": str(e),
            "message": f"Failed to generate images: {str(e)}"
        })


@tool("luma_ai_text_to_image", args_schema=TextToImageToolInput)
def luma_ai_text_to_image(
    prompt: str,
    **kwargs
) -> str:
    """
    Generate images from text using Luma AI.
    
    High-quality image generation with various style and reference options.
    Good for fashion imagery with specific style requirements.
    
    Args:
        prompt: Text description of the image to generate
        **kwargs: Additional parameters (style, aspect_ratio, etc.)
    
    Returns:
        JSON string containing status, provider, image_count, cache_key, and message
    """
    try:
        print(" Initializing Luma AI adapter...")
        adapter = LumaAIAdapter()
        print("Generating images...")
        images = adapter.generate_text_to_image(
            prompt=prompt,
            **kwargs
        )
        print(" Luma AI generation completed")
        
        # Store full images in cache
        cache_key = hashlib.md5(
            f"luma_ai_{prompt}".encode()
        ).hexdigest()
        _tool_output_cache[cache_key] = {
            "provider": "luma_ai",
            "images": images if isinstance(images, list) else [images],
            "prompt": prompt,
        }
        
        image_count = len(images) if isinstance(images, list) else 1
        
        return json.dumps({
            "status": "success",
            "provider": "luma_ai",
            "image_count": image_count,
            "cache_key": cache_key,
            "message": f"Successfully generated {image_count} image(s) using Luma AI"
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "provider": "luma_ai",
            "error": str(e),
            "message": f"Failed to generate images: {str(e)}"
        })


def get_image_generation_tools() -> List:
    """
    Get all image generation tools.
    
    Returns:
        List of LangChain tool objects for image generation
    """
    return [
        nano_banana_text_to_image,
        nano_banana_pro_text_to_image,
        nano_banana_2_text_to_image,
        flux2_pro_text_to_image,
        flux2_flex_text_to_image,
        gpt_image_text_to_image,
        luma_ai_text_to_image,
    ]

