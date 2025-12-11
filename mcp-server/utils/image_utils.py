"""Image handling utilities for OpenTryOn MCP Server."""

import base64
import io
from pathlib import Path
from typing import Union
from urllib.parse import urlparse

from PIL import Image
import requests

from ..config import config


def validate_image_path(path: str) -> bool:
    """Validate that a file path points to a valid image."""
    try:
        p = Path(path)
        if not p.exists():
            return False
        if not p.is_file():
            return False
        if p.suffix.lower() not in config.ALLOWED_IMAGE_EXTENSIONS:
            return False
        # Check file size
        if p.stat().st_size > config.MAX_FILE_SIZE_MB * 1024 * 1024:
            return False
        return True
    except Exception:
        return False


def validate_image_url(url: str) -> bool:
    """Validate that a URL points to a valid image."""
    try:
        parsed = urlparse(url)
        if not parsed.scheme in ("http", "https"):
            return False
        # Check if URL ends with image extension
        path = parsed.path.lower()
        return any(path.endswith(ext) for ext in config.ALLOWED_IMAGE_EXTENSIONS)
    except Exception:
        return False


def load_image(source: str) -> Image.Image:
    """
    Load an image from a file path, URL, or base64 string.
    
    Args:
        source: File path, URL, or base64-encoded image string
        
    Returns:
        PIL Image object
        
    Raises:
        ValueError: If the source is invalid or cannot be loaded
    """
    # Try as file path first
    if Path(source).exists():
        try:
            return Image.open(source)
        except Exception as e:
            raise ValueError(f"Failed to load image from path: {e}")
    
    # Try as URL
    if source.startswith(("http://", "https://")):
        try:
            response = requests.get(source, timeout=30)
            response.raise_for_status()
            return Image.open(io.BytesIO(response.content))
        except Exception as e:
            raise ValueError(f"Failed to load image from URL: {e}")
    
    # Try as base64
    try:
        # Remove data URL prefix if present
        if "," in source:
            source = source.split(",", 1)[1]
        image_data = base64.b64decode(source)
        return Image.open(io.BytesIO(image_data))
    except Exception as e:
        raise ValueError(f"Failed to load image from base64: {e}")


def save_image(image: Image.Image, output_path: Union[str, Path]) -> Path:
    """
    Save a PIL Image to a file.
    
    Args:
        image: PIL Image object
        output_path: Destination file path
        
    Returns:
        Path to saved file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)
    return output_path


def encode_image_base64(image: Union[Image.Image, str, Path]) -> str:
    """
    Encode an image as base64 string.
    
    Args:
        image: PIL Image object or path to image file
        
    Returns:
        Base64-encoded image string
    """
    if isinstance(image, (str, Path)):
        image = Image.open(image)
    
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode("utf-8")


def decode_image_base64(base64_string: str) -> Image.Image:
    """
    Decode a base64 string to PIL Image.
    
    Args:
        base64_string: Base64-encoded image string
        
    Returns:
        PIL Image object
    """
    # Remove data URL prefix if present
    if "," in base64_string:
        base64_string = base64_string.split(",", 1)[1]
    
    image_data = base64.b64decode(base64_string)
    return Image.open(io.BytesIO(image_data))

