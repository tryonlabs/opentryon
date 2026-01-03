"""
Video Generation Tools

This module provides LangChain tools for video generation using:
- OpenAI Sora (Sora 2, Sora 2 Pro)
- Google Veo 3
- Luma AI Dream Machine

All tools follow a consistent pattern and store full outputs in a global cache.
"""

import json
import hashlib
from typing import Optional, List
from pydantic import BaseModel, Field
from langchain.tools import tool

from tryon.api.openAI.video_adapter import SoraVideoAdapter
from tryon.api.veo import VeoAdapter
from tryon.api.lumaAI.luma_video_adapter import LumaAIVideoAdapter

# Global cache (shared across all tools)
_tool_output_cache = {}


class TextToVideoToolInput(BaseModel):
    """Base input schema for text-to-video generation."""
    prompt: str = Field(description="Text description of the video to generate")
    duration: Optional[int] = Field(
        default=4,
        description="Video duration in seconds (4, 8, or 12 for Sora; 4, 6, or 8 for Veo)"
    )
    resolution: Optional[str] = Field(
        default=None,
        description="Video resolution (e.g., '1280x768', '1920x1080' for Sora; '720p', '1080p' for Veo)"
    )
    aspect_ratio: Optional[str] = Field(
        default=None,
        description="Aspect ratio for Luma AI ('16:9', '9:16', etc.)"
    )


class ImageToVideoToolInput(BaseModel):
    """Base input schema for image-to-video generation."""
    image: str = Field(description="Path or URL to the input image")
    prompt: str = Field(description="Text description of the video to generate from the image")
    duration: Optional[int] = Field(
        default=4,
        description="Video duration in seconds"
    )
    resolution: Optional[str] = Field(
        default=None,
        description="Video resolution"
    )


@tool("sora_text_to_video", args_schema=TextToVideoToolInput)
def sora_text_to_video(
    prompt: str,
    duration: int = 4,
    resolution: Optional[str] = None,
    model_version: str = "sora-2",
    **kwargs
) -> str:
    """
    Generate videos from text using OpenAI's Sora models.
    
    High-quality video generation with excellent temporal consistency.
    Supports text-to-video generation with flexible duration and resolution.
    
    Args:
        prompt: Text description of the video to generate
        duration: Video duration in seconds (4, 8, or 12). Default: 4
        resolution: Video resolution (e.g., '1280x768', '1920x1080'). Default: model default
        model_version: Model version ('sora-2' or 'sora-2-pro'). Default: 'sora-2'
    
    Returns:
        JSON string containing status, provider, cache_key, and message
    """
    try:
        print(f" Initializing Sora ({model_version}) adapter...")
        adapter = SoraVideoAdapter(model_version=model_version)
        print("Generating video (this may take several minutes)...")
        video_bytes = adapter.generate_text_to_video(
            prompt=prompt,
            duration=duration,
            resolution=resolution,
            **kwargs
        )
        print(" Sora video generation completed")
        
        # Store full video in cache
        cache_key = hashlib.md5(
            f"sora_{model_version}_{prompt}_{duration}_{resolution}".encode()
        ).hexdigest()
        _tool_output_cache[cache_key] = {
            "provider": f"sora_{model_version}",
            "video_bytes": video_bytes,
            "prompt": prompt,
            "duration": duration,
            "resolution": resolution,
        }
        
        return json.dumps({
            "status": "success",
            "provider": f"sora_{model_version}",
            "cache_key": cache_key,
            "message": f"Successfully generated video using Sora {model_version}"
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "provider": f"sora_{model_version}",
            "error": str(e),
            "message": f"Failed to generate video: {str(e)}"
        })


@tool("sora_image_to_video", args_schema=ImageToVideoToolInput)
def sora_image_to_video(
    image: str,
    prompt: str,
    duration: int = 4,
    resolution: Optional[str] = None,
    model_version: str = "sora-2",
    **kwargs
) -> str:
    """
    Generate videos from an image using OpenAI's Sora models.
    
    Animate static images into videos with motion and temporal consistency.
    
    Args:
        image: Path or URL to the input image
        prompt: Text description of the video to generate
        duration: Video duration in seconds (4, 8, or 12). Default: 4
        resolution: Video resolution. Default: model default
        model_version: Model version ('sora-2' or 'sora-2-pro'). Default: 'sora-2'
    
    Returns:
        JSON string containing status, provider, cache_key, and message
    """
    try:
        print(f" Initializing Sora ({model_version}) adapter...")
        adapter = SoraVideoAdapter(model_version=model_version)
        print("Generating video from image (this may take several minutes)...")
        video_bytes = adapter.generate_image_to_video(
            image=image,
            prompt=prompt,
            duration=duration,
            resolution=resolution,
            **kwargs
        )
        print(" Sora video generation completed")
        
        # Store full video in cache
        cache_key = hashlib.md5(
            f"sora_{model_version}_image_{image}_{prompt}_{duration}".encode()
        ).hexdigest()
        _tool_output_cache[cache_key] = {
            "provider": f"sora_{model_version}",
            "video_bytes": video_bytes,
            "image": image,
            "prompt": prompt,
            "duration": duration,
            "resolution": resolution,
        }
        
        return json.dumps({
            "status": "success",
            "provider": f"sora_{model_version}",
            "cache_key": cache_key,
            "message": f"Successfully generated video from image using Sora {model_version}"
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "provider": f"sora_{model_version}",
            "error": str(e),
            "message": f"Failed to generate video: {str(e)}"
        })


@tool("veo_text_to_video", args_schema=TextToVideoToolInput)
def veo_text_to_video(
    prompt: str,
    duration: int = 4,
    resolution: Optional[str] = None,
    model: str = "veo-3.1-generate-preview",
    **kwargs
) -> str:
    """
    Generate videos from text using Google's Veo 3 models.
    
    High-quality, cinematic video generation with realistic motion.
    Supports various durations and resolutions.
    
    Args:
        prompt: Text description of the video to generate
        duration: Video duration in seconds (4, 6, or 8). Default: 4
        resolution: Video resolution ('720p' or '1080p'). Default: model default
        model: Model version. Options: 'veo-3.1-generate-preview', 'veo-3.1-fast-generate-preview',
               'veo-3.0-generate-001', 'veo-3.0-fast-generate-001'. Default: 'veo-3.1-generate-preview'
    
    Returns:
        JSON string containing status, provider, cache_key, and message
    """
    try:
        print(f" Initializing Veo ({model}) adapter...")
        adapter = VeoAdapter()
        print("Generating video (this may take several minutes)...")
        video_bytes = adapter.generate_text_to_video(
            prompt=prompt,
            duration=str(duration),
            resolution=resolution,
            model=model,
            **kwargs
        )
        print(" Veo video generation completed")
        
        # Store full video in cache
        cache_key = hashlib.md5(
            f"veo_{model}_{prompt}_{duration}_{resolution}".encode()
        ).hexdigest()
        _tool_output_cache[cache_key] = {
            "provider": f"veo_{model}",
            "video_bytes": video_bytes,
            "prompt": prompt,
            "duration": duration,
            "resolution": resolution,
        }
        
        return json.dumps({
            "status": "success",
            "provider": f"veo_{model}",
            "cache_key": cache_key,
            "message": f"Successfully generated video using Veo {model}"
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "provider": f"veo_{model}",
            "error": str(e),
            "message": f"Failed to generate video: {str(e)}"
        })


@tool("veo_image_to_video", args_schema=ImageToVideoToolInput)
def veo_image_to_video(
    image: str,
    prompt: str,
    duration: int = 4,
    resolution: Optional[str] = None,
    model: str = "veo-3.1-generate-preview",
    **kwargs
) -> str:
    """
    Generate videos from an image using Google's Veo 3 models.
    
    Animate static images into cinematic videos with realistic motion.
    
    Args:
        image: Path or URL to the input image
        prompt: Text description of the video to generate
        duration: Video duration in seconds (4, 6, or 8). Default: 4
        resolution: Video resolution ('720p' or '1080p'). Default: model default
        model: Model version. Default: 'veo-3.1-generate-preview'
    
    Returns:
        JSON string containing status, provider, cache_key, and message
    """
    try:
        print(f" Initializing Veo ({model}) adapter...")
        adapter = VeoAdapter()
        print("Generating video from image (this may take several minutes)...")
        video_bytes = adapter.generate_image_to_video(
            prompt=prompt,
            image=image,
            duration=str(duration),
            resolution=resolution,
            model=model,
            **kwargs
        )
        print(" Veo video generation completed")
        
        # Store full video in cache
        cache_key = hashlib.md5(
            f"veo_{model}_image_{image}_{prompt}_{duration}".encode()
        ).hexdigest()
        _tool_output_cache[cache_key] = {
            "provider": f"veo_{model}",
            "video_bytes": video_bytes,
            "image": image,
            "prompt": prompt,
            "duration": duration,
            "resolution": resolution,
        }
        
        return json.dumps({
            "status": "success",
            "provider": f"veo_{model}",
            "cache_key": cache_key,
            "message": f"Successfully generated video from image using Veo {model}"
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "provider": f"veo_{model}",
            "error": str(e),
            "message": f"Failed to generate video: {str(e)}"
        })


@tool("luma_ai_text_to_video", args_schema=TextToVideoToolInput)
def luma_ai_text_to_video(
    prompt: str,
    duration: Optional[int] = None,
    aspect_ratio: Optional[str] = None,
    **kwargs
) -> str:
    """
    Generate videos from text using Luma AI Dream Machine.
    
    High-quality video generation with support for various aspect ratios.
    
    Args:
        prompt: Text description of the video to generate
        duration: Video duration (optional, model default if not specified)
        aspect_ratio: Aspect ratio ('16:9', '9:16', etc.). Default: model default
    
    Returns:
        JSON string containing status, provider, cache_key, and message
    """
    try:
        print(" Initializing Luma AI video adapter...")
        adapter = LumaAIVideoAdapter()
        print("Generating video (this may take several minutes)...")
        video_bytes = adapter.generate_text_to_video(
            prompt=prompt,
            duration=duration,
            aspect_ratio=aspect_ratio,
            **kwargs
        )
        print(" Luma AI video generation completed")
        
        # Store full video in cache
        cache_key = hashlib.md5(
            f"luma_ai_video_{prompt}_{duration}_{aspect_ratio}".encode()
        ).hexdigest()
        _tool_output_cache[cache_key] = {
            "provider": "luma_ai_video",
            "video_bytes": video_bytes,
            "prompt": prompt,
            "duration": duration,
            "aspect_ratio": aspect_ratio,
        }
        
        return json.dumps({
            "status": "success",
            "provider": "luma_ai_video",
            "cache_key": cache_key,
            "message": "Successfully generated video using Luma AI Dream Machine"
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "provider": "luma_ai_video",
            "error": str(e),
            "message": f"Failed to generate video: {str(e)}"
        })


@tool("luma_ai_image_to_video", args_schema=ImageToVideoToolInput)
def luma_ai_image_to_video(
    image: str,
    prompt: str,
    duration: Optional[int] = None,
    **kwargs
) -> str:
    """
    Generate videos from an image using Luma AI Dream Machine.
    
    Animate static images into videos with motion.
    
    Args:
        image: Path or URL to the input image
        prompt: Text description of the video to generate
        duration: Video duration (optional, model default if not specified)
    
    Returns:
        JSON string containing status, provider, cache_key, and message
    """
    try:
        print(" Initializing Luma AI video adapter...")
        adapter = LumaAIVideoAdapter()
        print("Generating video from image (this may take several minutes)...")
        video_bytes = adapter.generate_image_to_video(
            image=image,
            prompt=prompt,
            duration=duration,
            **kwargs
        )
        print(" Luma AI video generation completed")
        
        # Store full video in cache
        cache_key = hashlib.md5(
            f"luma_ai_video_image_{image}_{prompt}_{duration}".encode()
        ).hexdigest()
        _tool_output_cache[cache_key] = {
            "provider": "luma_ai_video",
            "video_bytes": video_bytes,
            "image": image,
            "prompt": prompt,
            "duration": duration,
        }
        
        return json.dumps({
            "status": "success",
            "provider": "luma_ai_video",
            "cache_key": cache_key,
            "message": "Successfully generated video from image using Luma AI Dream Machine"
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "provider": "luma_ai_video",
            "error": str(e),
            "message": f"Failed to generate video: {str(e)}"
        })


def get_video_generation_tools() -> List:
    """
    Get all video generation tools.
    
    Returns:
        List of LangChain tool objects for video generation
    """
    return [
        sora_text_to_video,
        sora_image_to_video,
        veo_text_to_video,
        veo_image_to_video,
        luma_ai_text_to_video,
        luma_ai_image_to_video,
    ]

