"""
Image Editing Tools

This module provides LangChain tools for image editing and composition using:
- OpenAI GPT-Image (image editing, mask-based editing, multi-image composition)

All tools follow a consistent pattern and store full outputs in a global cache.
"""

import json
import hashlib
from typing import Optional, List, Union
from pydantic import BaseModel, Field
from langchain.tools import tool

from tryon.api.openAI.image_adapter import GPTImageAdapter

# Global cache (shared across all tools)
_tool_output_cache = {}


class ImageEditToolInput(BaseModel):
    """Input schema for basic image editing."""
    image: str = Field(description="Path or URL to the input image")
    prompt: str = Field(description="Text description of the edits to make")
    size: Optional[str] = Field(
        default=None,
        description="Output size ('1024x1024', '1536x1024', '1024x1536', 'auto')"
    )
    quality: Optional[str] = Field(
        default=None,
        description="Quality setting ('low', 'high', 'medium', 'auto')"
    )
    model_version: Optional[str] = Field(
        default="gpt-image-1.5",
        description="Model version ('gpt-image-1' or 'gpt-image-1.5')"
    )


class MaskEditToolInput(BaseModel):
    """Input schema for mask-based image editing."""
    image: str = Field(description="Path or URL to the input image")
    mask: str = Field(description="Path or URL to the mask image (white areas will be edited)")
    prompt: str = Field(description="Text description of what to generate in the masked area")
    size: Optional[str] = Field(
        default=None,
        description="Output size ('1024x1024', '1536x1024', '1024x1536', 'auto')"
    )
    quality: Optional[str] = Field(
        default=None,
        description="Quality setting ('low', 'high', 'medium', 'auto')"
    )
    model_version: Optional[str] = Field(
        default="gpt-image-1.5",
        description="Model version ('gpt-image-1' or 'gpt-image-1.5')"
    )


class MultiImageEditToolInput(BaseModel):
    """Input schema for multi-image composition/editing."""
    images: List[str] = Field(description="List of paths or URLs to input images (2-5 images)")
    prompt: str = Field(description="Text description of how to compose/edit the images")
    size: Optional[str] = Field(
        default=None,
        description="Output size ('1024x1024', '1536x1024', '1024x1536', 'auto')"
    )
    quality: Optional[str] = Field(
        default=None,
        description="Quality setting ('low', 'high', 'medium', 'auto')"
    )
    model_version: Optional[str] = Field(
        default="gpt-image-1.5",
        description="Model version ('gpt-image-1' or 'gpt-image-1.5')"
    )


@tool("gpt_image_edit", args_schema=ImageEditToolInput)
def gpt_image_edit(
    image: str,
    prompt: str,
    size: Optional[str] = None,
    quality: Optional[str] = None,
    model_version: str = "gpt-image-1.5",
    **kwargs
) -> str:
    """
    Edit an image using OpenAI's GPT-Image models.
    
    Modify existing images using text prompts. Can change colors, styles, add/remove elements,
    and make various edits while maintaining image coherence.
    
    Args:
        image: Path or URL to the input image
        prompt: Text description of the edits to make
        size: Output size ('1024x1024', '1536x1024', '1024x1536', 'auto')
        quality: Quality setting ('low', 'high', 'medium', 'auto')
        model_version: Model version ('gpt-image-1' or 'gpt-image-1.5'). Default: 'gpt-image-1.5'
    
    Returns:
        JSON string containing status, provider, image_count, cache_key, and message
    """
    try:
        print(f" Initializing GPT-Image ({model_version}) adapter...")
        adapter = GPTImageAdapter(model_version=model_version)
        print("Editing image...")
        images = adapter.generate_image_edit(
            images=image,
            prompt=prompt,
            size=size,
            quality=quality,
            **kwargs
        )
        print(" GPT-Image editing completed")
        
        # Store full images in cache
        cache_key = hashlib.md5(
            f"gpt_image_edit_{model_version}_{image}_{prompt}_{size}_{quality}".encode()
        ).hexdigest()
        _tool_output_cache[cache_key] = {
            "provider": f"gpt_image_{model_version}",
            "images": images if isinstance(images, list) else [images],
            "original_image": image,
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
            "message": f"Successfully edited image using GPT-Image {model_version}"
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "provider": f"gpt_image_{model_version}",
            "error": str(e),
            "message": f"Failed to edit image: {str(e)}"
        })


@tool("gpt_image_mask_edit", args_schema=MaskEditToolInput)
def gpt_image_mask_edit(
    image: str,
    mask: str,
    prompt: str,
    size: Optional[str] = None,
    quality: Optional[str] = None,
    model_version: str = "gpt-image-1.5",
    **kwargs
) -> str:
    """
    Edit specific regions of an image using a mask with OpenAI's GPT-Image models.
    
    Use a mask image to specify which areas to edit. White areas in the mask will be edited,
    black areas will remain unchanged. Perfect for precise, localized edits.
    
    Args:
        image: Path or URL to the input image
        mask: Path or URL to the mask image (white = edit, black = preserve)
        prompt: Text description of what to generate in the masked area
        size: Output size ('1024x1024', '1536x1024', '1024x1536', 'auto')
        quality: Quality setting ('low', 'high', 'medium', 'auto')
        model_version: Model version ('gpt-image-1' or 'gpt-image-1.5'). Default: 'gpt-image-1.5'
    
    Returns:
        JSON string containing status, provider, image_count, cache_key, and message
    """
    try:
        print(f" Initializing GPT-Image ({model_version}) adapter...")
        adapter = GPTImageAdapter(model_version=model_version)
        print("Editing masked regions...")
        images = adapter.generate_image_edit(
            images=image,
            mask=mask,
            prompt=prompt,
            size=size,
            quality=quality,
            **kwargs
        )
        print(" GPT-Image mask editing completed")
        
        # Store full images in cache
        cache_key = hashlib.md5(
            f"gpt_image_mask_{model_version}_{image}_{mask}_{prompt}_{size}_{quality}".encode()
        ).hexdigest()
        _tool_output_cache[cache_key] = {
            "provider": f"gpt_image_{model_version}",
            "images": images if isinstance(images, list) else [images],
            "original_image": image,
            "mask": mask,
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
            "message": f"Successfully edited masked regions using GPT-Image {model_version}"
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "provider": f"gpt_image_{model_version}",
            "error": str(e),
            "message": f"Failed to edit masked regions: {str(e)}"
        })


@tool("gpt_image_multi_edit", args_schema=MultiImageEditToolInput)
def gpt_image_multi_edit(
    images: List[str],
    prompt: str,
    size: Optional[str] = None,
    quality: Optional[str] = None,
    model_version: str = "gpt-image-1.5",
    **kwargs
) -> str:
    """
    Compose or edit multiple images together using OpenAI's GPT-Image models.
    
    Use 2-5 input images to create composite images, combine elements, or perform
    multi-image edits. Useful for creating fashion collages, combining outfit elements,
    or merging style references.
    
    Args:
        images: List of 2-5 image paths or URLs
        prompt: Text description of how to compose/edit the images
        size: Output size ('1024x1024', '1536x1024', '1024x1536', 'auto')
        quality: Quality setting ('low', 'high', 'medium', 'auto')
        model_version: Model version ('gpt-image-1' or 'gpt-image-1.5'). Default: 'gpt-image-1.5'
    
    Returns:
        JSON string containing status, provider, image_count, cache_key, and message
    """
    try:
        if len(images) < 2 or len(images) > 5:
            raise ValueError("Multi-image editing requires 2-5 input images")
        
        print(f" Initializing GPT-Image ({model_version}) adapter...")
        adapter = GPTImageAdapter(model_version=model_version)
        print(f"Composing {len(images)} images...")
        images_result = adapter.generate_image_edit(
            images=images,
            prompt=prompt,
            size=size,
            quality=quality,
            **kwargs
        )
        print(" GPT-Image multi-image composition completed")
        
        # Store full images in cache
        images_str = "_".join(images)
        cache_key = hashlib.md5(
            f"gpt_image_multi_{model_version}_{images_str}_{prompt}_{size}_{quality}".encode()
        ).hexdigest()
        _tool_output_cache[cache_key] = {
            "provider": f"gpt_image_{model_version}",
            "images": images_result if isinstance(images_result, list) else [images_result],
            "input_images": images,
            "prompt": prompt,
            "size": size,
            "quality": quality,
        }
        
        image_count = len(images_result) if isinstance(images_result, list) else 1
        
        return json.dumps({
            "status": "success",
            "provider": f"gpt_image_{model_version}",
            "image_count": image_count,
            "cache_key": cache_key,
            "message": f"Successfully composed {len(images)} images using GPT-Image {model_version}"
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "provider": f"gpt_image_{model_version}",
            "error": str(e),
            "message": f"Failed to compose images: {str(e)}"
        })


def get_image_editing_tools() -> list:
    """
    Get all image editing tools.
    
    Returns:
        List of LangChain tool objects for image editing
    """
    return [
        gpt_image_edit,
        gpt_image_mask_edit,
        gpt_image_multi_edit,
    ]

