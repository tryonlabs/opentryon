"""
Virtual Try-On Tools

This module provides LangChain tools for virtual try-on operations using:
- Kling AI (Kolors Virtual Try-On)
- Amazon Nova Canvas
- Segmind Try-On Diffusion

All tools follow a consistent pattern and store full outputs in a global cache.
"""

import json
import hashlib
from typing import Optional, List
from pydantic import BaseModel, Field
from langchain.tools import tool

from tryon.api import (
    KlingAIVTONAdapter,
    AmazonNovaCanvasVTONAdapter,
    SegmindVTONAdapter,
)

# Global cache (will be initialized in __init__.py)
_tool_output_cache = {}


class KlingAIVTONToolInput(BaseModel):
    """Input schema for Kling AI virtual try-on tool."""
    person_image: str = Field(description="Path or URL to the person/model image")
    garment_image: str = Field(description="Path or URL to the garment/cloth image")
    model: Optional[str] = Field(
        default=None,
        description="Optional model version (e.g., 'kolors-virtual-try-on-v1-5')"
    )


class NovaCanvasVTONToolInput(BaseModel):
    """Input schema for Amazon Nova Canvas virtual try-on tool."""
    person_image: str = Field(description="Path or URL to the person/model image")
    garment_image: str = Field(description="Path or URL to the garment/cloth image")
    mask_type: str = Field(
        default="GARMENT",
        description="Mask type: 'GARMENT' (automatic) or 'IMAGE' (custom mask)"
    )
    garment_class: Optional[str] = Field(
        default="UPPER_BODY",
        description="Garment class: 'UPPER_BODY', 'LOWER_BODY', 'FULL_BODY', or 'FOOTWEAR'"
    )


class SegmindVTONToolInput(BaseModel):
    """Input schema for Segmind virtual try-on tool."""
    person_image: str = Field(description="Path or URL to the person/model image")
    garment_image: str = Field(description="Path or URL to the garment/cloth image")
    category: str = Field(
        default="Upper body",
        description="Garment category: 'Upper body', 'Lower body', or 'Dresses'"
    )


@tool("kling_ai_virtual_tryon", args_schema=KlingAIVTONToolInput)
def kling_ai_virtual_tryon(
    person_image: str,
    garment_image: str,
    model: Optional[str] = None
) -> str:
    """
    Generate virtual try-on images using Kling AI's Kolors Virtual Try-On API.
    
    Kling AI provides high-quality virtual try-on with asynchronous processing
    and automatic polling. Supports high-resolution images (up to 16M pixels).
    
    Use this tool when the user mentions "kling ai" or "kling" in their request.
    
    Args:
        person_image: Path or URL to the person/model image
        garment_image: Path or URL to the garment/cloth image
        model: Optional model version (e.g., 'kolors-virtual-try-on-v1-5')
    
    Returns:
        JSON string containing status, provider, image_count, cache_key, and message
    """
    try:
        print(" Initializing Kling AI adapter...")
        adapter = KlingAIVTONAdapter()
        print("Generating virtual try-on images (this may take a moment)...")
        images = adapter.generate(
            source_image=person_image,
            reference_image=garment_image,
            model=model
        )
        print(" Kling AI generation completed")
        
        # Store full images in cache
        cache_key = hashlib.md5(
            f"kling_ai_{person_image}_{garment_image}_{model}".encode()
        ).hexdigest()
        _tool_output_cache[cache_key] = {
            "provider": "kling_ai",
            "images": images if isinstance(images, list) else [images],
            "person_image": person_image,
            "garment_image": garment_image,
            "model": model,
        }
        
        image_count = len(images) if isinstance(images, list) else 1
        
        return json.dumps({
            "status": "success",
            "provider": "kling_ai",
            "image_count": image_count,
            "cache_key": cache_key,
            "message": f"Successfully generated {image_count} virtual try-on image(s) using Kling AI"
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "provider": "kling_ai",
            "error": str(e),
            "message": f"Failed to generate virtual try-on: {str(e)}"
        })


@tool("nova_canvas_virtual_tryon", args_schema=NovaCanvasVTONToolInput)
def nova_canvas_virtual_tryon(
    person_image: str,
    garment_image: str,
    mask_type: str = "GARMENT",
    garment_class: Optional[str] = "UPPER_BODY"
) -> str:
    """
    Generate virtual try-on images using Amazon Nova Canvas API.
    
    Amazon Nova Canvas provides high-quality virtual try-on through AWS Bedrock.
    Supports automatic garment detection and custom mask images.
    
    Use this tool when the user mentions "amazon", "nova canvas", "aws", or "bedrock".
    
    Args:
        person_image: Path or URL to the person/model image
        garment_image: Path or URL to the garment/cloth image
        mask_type: Mask type - 'GARMENT' (automatic) or 'IMAGE' (custom mask)
        garment_class: Garment class - 'UPPER_BODY', 'LOWER_BODY', 'FULL_BODY', or 'FOOTWEAR'
    
    Returns:
        JSON string containing status, provider, image_count, cache_key, and message
    """
    try:
        print(" Initializing Amazon Nova Canvas adapter...")
        adapter = AmazonNovaCanvasVTONAdapter()
        print("Generating virtual try-on images...")
        images = adapter.generate(
            source_image=person_image,
            reference_image=garment_image,
            mask_type=mask_type,
            garment_class=garment_class
        )
        print(" Nova Canvas generation completed")
        
        # Store full images in cache
        cache_key = hashlib.md5(
            f"nova_canvas_{person_image}_{garment_image}_{mask_type}_{garment_class}".encode()
        ).hexdigest()
        _tool_output_cache[cache_key] = {
            "provider": "nova_canvas",
            "images": images if isinstance(images, list) else [images],
            "person_image": person_image,
            "garment_image": garment_image,
            "mask_type": mask_type,
            "garment_class": garment_class,
        }
        
        image_count = len(images) if isinstance(images, list) else 1
        
        return json.dumps({
            "status": "success",
            "provider": "nova_canvas",
            "image_count": image_count,
            "cache_key": cache_key,
            "message": f"Successfully generated {image_count} virtual try-on image(s) using Amazon Nova Canvas"
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "provider": "nova_canvas",
            "error": str(e),
            "message": f"Failed to generate virtual try-on: {str(e)}"
        })


@tool("segmind_virtual_tryon", args_schema=SegmindVTONToolInput)
def segmind_virtual_tryon(
    person_image: str,
    garment_image: str,
    category: str = "Upper body"
) -> str:
    """
    Generate virtual try-on images using Segmind Try-On Diffusion API.
    
    Segmind provides fast and efficient virtual try-on capabilities with
    support for different garment categories.
    
    Use this tool when the user mentions "segmind" in their request.
    
    Args:
        person_image: Path or URL to the person/model image
        garment_image: Path or URL to the garment/cloth image
        category: Garment category - 'Upper body', 'Lower body', or 'Dresses'
    
    Returns:
        JSON string containing status, provider, image_count, cache_key, and message
    """
    try:
        print(" Initializing Segmind adapter...")
        adapter = SegmindVTONAdapter()
        print("Generating virtual try-on images...")
        images = adapter.generate(
            model_image=person_image,
            cloth_image=garment_image,
            category=category
        )
        print(" Segmind generation completed")
        
        # Store full images in cache
        cache_key = hashlib.md5(
            f"segmind_{person_image}_{garment_image}_{category}".encode()
        ).hexdigest()
        _tool_output_cache[cache_key] = {
            "provider": "segmind",
            "images": images if isinstance(images, list) else [images],
            "person_image": person_image,
            "garment_image": garment_image,
            "category": category,
        }
        
        image_count = len(images) if isinstance(images, list) else 1
        
        return json.dumps({
            "status": "success",
            "provider": "segmind",
            "image_count": image_count,
            "cache_key": cache_key,
            "message": f"Successfully generated {image_count} virtual try-on image(s) using Segmind"
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "provider": "segmind",
            "error": str(e),
            "message": f"Failed to generate virtual try-on: {str(e)}"
        })


def get_virtual_tryon_tools() -> List:
    """
    Get all virtual try-on tools.
    
    Returns:
        List of LangChain tool objects for virtual try-on
    """
    return [
        kling_ai_virtual_tryon,
        nova_canvas_virtual_tryon,
        segmind_virtual_tryon,
    ]

