"""Video generation tools for OpenTryOn MCP Server."""

from typing import Optional
from pathlib import Path

from tryon.api.lumaAI import LumaAIVideoAdapter
from ..config import config


def generate_video_luma_ray(
    prompt: str,
    model: str = "ray-2",
    mode: str = "text_video",
    resolution: str = "720p",
    duration: str = "5s",
    aspect_ratio: str = "16:9",
    start_image: Optional[str] = None,
    end_image: Optional[str] = None,
    loop: bool = False,
    output_dir: Optional[str] = None,
) -> dict:
    """
    Generate videos using Luma AI Ray models.
    
    Args:
        prompt: Text description
        model: "ray-1-6", "ray-2", or "ray-flash-2"
        mode: "text_video" or "image_video"
        resolution: "540p", "720p", "1080p", or "4k"
        duration: "5s", "9s", or "10s"
        aspect_ratio: Aspect ratio (e.g., "16:9", "1:1")
        start_image: Start keyframe for image_video mode
        end_image: End keyframe for image_video mode
        loop: Enable seamless looping
        output_dir: Directory to save results (optional)
        
    Returns:
        Dictionary with status and result information
    """
    try:
        adapter = LumaAIVideoAdapter()
        
        # Validate model
        if model not in ["ray-1-6", "ray-2", "ray-flash-2"]:
            return {
                "success": False,
                "error": f"Invalid model: {model}. Must be 'ray-1-6', 'ray-2', or 'ray-flash-2'"
            }
        
        # Generate based on mode
        if mode == "text_video":
            video_bytes = adapter.generate_text_to_video(
                prompt=prompt,
                resolution=resolution,
                duration=duration,
                aspect_ratio=aspect_ratio,
                loop=loop,
                model=model
            )
        elif mode == "image_video":
            video_bytes = adapter.generate_image_to_video(
                prompt=prompt,
                start_image=start_image,
                end_image=end_image,
                resolution=resolution,
                duration=duration,
                aspect_ratio=aspect_ratio,
                loop=loop,
                model=model
            )
        else:
            return {
                "success": False,
                "error": f"Invalid mode: {mode}. Must be 'text_video' or 'image_video'"
            }
        
        # Save result
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            video_path = output_path / f"luma_{model}_video.mp4"
        else:
            video_path = config.TEMP_DIR / f"luma_{model}_video.mp4"
        
        with open(video_path, "wb") as f:
            f.write(video_bytes)
        
        return {
            "success": True,
            "provider": "luma_ai",
            "model": model,
            "mode": mode,
            "resolution": resolution,
            "duration": duration,
            "aspect_ratio": aspect_ratio,
            "output_path": str(video_path),
            "message": f"Generated video with {model}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

