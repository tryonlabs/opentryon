"""
Tools for Virtual Try-On Agent

This module provides LangChain tools for each virtual try-on adapter,
allowing the agent to select and use the appropriate adapter based on user input.

Note: Tools store full image data in a global cache to avoid token limit issues
when returning results to the LLM. The agent extracts images from this cache.
"""

import json
from typing import Optional, Union
from pydantic import BaseModel, Field
from langchain.tools import tool

from tryon.api import (
    KlingAIVTONAdapter,
    AmazonNovaCanvasVTONAdapter,
    SegmindVTONAdapter,
)

# Global cache to store full tool outputs (to avoid token limits)
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
        JSON string containing image URLs or base64-encoded images
    """
    try:
        print("  🔄 Initializing Kling AI adapter...")
        adapter = KlingAIVTONAdapter()
        print("  ⚙️  Generating virtual try-on images (this may take a moment)...")
        images = adapter.generate(
            source_image=person_image,
            reference_image=garment_image,
            model=model
        )
        print("  ✅ Kling AI generation completed")
        
        # Store full images in cache (keyed by a hash of inputs)
        import hashlib
        cache_key = hashlib.md5(
            f"{person_image}_{garment_image}_{model}".encode()
        ).hexdigest()
        _tool_output_cache[cache_key] = {
            "provider": "kling_ai",
            "images": images if isinstance(images, list) else [images]
        }
        
        # Return only metadata to avoid token limits
        result = {
            "status": "success",
            "provider": "kling_ai",
            "image_count": len(images) if isinstance(images, list) else 1,
            "cache_key": cache_key,  # Reference to full data
            "message": "Images generated successfully. Use cache_key to retrieve full image data."
        }
        return json.dumps(result)
    except Exception as e:
        result = {
            "status": "error",
            "provider": "kling_ai",
            "error": str(e)
        }
        return json.dumps(result)


@tool("nova_canvas_virtual_tryon", args_schema=NovaCanvasVTONToolInput)
def nova_canvas_virtual_tryon(
    person_image: str,
    garment_image: str,
    mask_type: str = "GARMENT",
    garment_class: Optional[str] = "UPPER_BODY"
) -> str:
    """
    Generate virtual try-on images using Amazon Nova Canvas (AWS Bedrock).
    
    Amazon Nova Canvas provides virtual try-on through AWS Bedrock with automatic
    garment detection and masking. Supports multiple garment classes and custom masks.
    Maximum image size: 4.1M pixels (2048x2048).
    
    Use this tool when the user mentions "nova canvas", "amazon nova", "aws", or "bedrock".
    
    Args:
        person_image: Path or URL to the person/model image
        garment_image: Path or URL to the garment/cloth image
        mask_type: 'GARMENT' for automatic detection or 'IMAGE' for custom mask
        garment_class: 'UPPER_BODY', 'LOWER_BODY', 'FULL_BODY', or 'FOOTWEAR'
    
    Returns:
        JSON string containing base64-encoded images
    """
    try:
        print("  🔄 Initializing Amazon Nova Canvas adapter...")
        adapter = AmazonNovaCanvasVTONAdapter()
        print("  ⚙️  Generating virtual try-on images...")
        images = adapter.generate(
            source_image=person_image,
            reference_image=garment_image,
            mask_type=mask_type,
            garment_class=garment_class
        )
        print("  ✅ Nova Canvas generation completed")
        
        # Store full images in cache
        import hashlib
        cache_key = hashlib.md5(
            f"{person_image}_{garment_image}_{mask_type}_{garment_class}".encode()
        ).hexdigest()
        _tool_output_cache[cache_key] = {
            "provider": "nova_canvas",
            "images": images if isinstance(images, list) else [images]
        }
        
        # Return only metadata to avoid token limits
        result = {
            "status": "success",
            "provider": "nova_canvas",
            "image_count": len(images) if isinstance(images, list) else 1,
            "cache_key": cache_key,
            "message": "Images generated successfully. Use cache_key to retrieve full image data."
        }
        return json.dumps(result)
    except Exception as e:
        result = {
            "status": "error",
            "provider": "nova_canvas",
            "error": str(e)
        }
        return json.dumps(result)


@tool("segmind_virtual_tryon", args_schema=SegmindVTONToolInput)
def segmind_virtual_tryon(
    person_image: str,
    garment_image: str,
    category: str = "Upper body"
) -> str:
    """
    Generate virtual try-on images using Segmind Try-On Diffusion API.
    
    Segmind provides fast and efficient virtual try-on generation with support for
    multiple garment categories. Good for quick iterations and testing.
    
    Use this tool when the user mentions "segmind" in their request.
    
    Args:
        person_image: Path or URL to the person/model image
        garment_image: Path or URL to the garment/cloth image
        category: 'Upper body', 'Lower body', or 'Dresses'
    
    Returns:
        JSON string containing base64-encoded images or URLs
    """
    try:
        print("  🔄 Initializing Segmind adapter...")
        adapter = SegmindVTONAdapter()
        print("  ⚙️  Generating virtual try-on images...")
        images = adapter.generate(
            model_image=person_image,
            cloth_image=garment_image,
            category=category
        )
        print("  ✅ Segmind generation completed")
        # Handle both single image and list responses
        if not isinstance(images, list):
            images = [images]
        
        # Store full images in cache
        import hashlib
        cache_key = hashlib.md5(
            f"{person_image}_{garment_image}_{category}".encode()
        ).hexdigest()
        _tool_output_cache[cache_key] = {
            "provider": "segmind",
            "images": images
        }
        
        # Return only metadata to avoid token limits
        result = {
            "status": "success",
            "provider": "segmind",
            "image_count": len(images),
            "cache_key": cache_key,
            "message": "Images generated successfully. Use cache_key to retrieve full image data."
        }
        return json.dumps(result)
    except Exception as e:
        result = {
            "status": "error",
            "provider": "segmind",
            "error": str(e)
        }
        return json.dumps(result)


def get_vton_tools():
    """
    Get all available virtual try-on tools.
    
    Returns:
        List of LangChain tools for virtual try-on
    """
    return [
        kling_ai_virtual_tryon,
        nova_canvas_virtual_tryon,
        segmind_virtual_tryon,
    ]


def get_tool_output_from_cache(cache_key: str) -> Optional[dict]:
    """
    Retrieve full tool output from cache using cache_key.
    
    Args:
        cache_key: Cache key returned in tool output
        
    Returns:
        Dictionary with provider and images, or None if not found
    """
    return _tool_output_cache.get(cache_key)

