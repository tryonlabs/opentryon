"""Input validation utilities for OpenTryOn MCP Server."""

from typing import Literal


# Valid aspect ratios for different models
VALID_ASPECT_RATIOS = {
    "1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", 
    "9:16", "16:9", "21:9", "9:21"
}

# Valid resolutions
VALID_RESOLUTIONS = {
    "1K", "2K", "4K",  # Nano Banana Pro
    "540p", "720p", "1080p", "4k"  # Luma AI Video
}

# Valid garment classes
VALID_GARMENT_CLASSES = {
    "upper", "lower", "all",  # Preprocessing
    "UPPER_BODY", "LOWER_BODY", "FULL_BODY", "FOOTWEAR"  # Amazon Nova
}

# Valid categories
VALID_CATEGORIES = {
    "Upper body", "Lower body", "Dress"  # Segmind
}

# Valid video durations
VALID_DURATIONS = {"5s", "9s", "10s"}

# Valid Luma AI models
VALID_LUMA_MODELS = {
    "photon-1", "photon-flash-1",  # Image
    "ray-1-6", "ray-2", "ray-flash-2"  # Video
}

# Valid FLUX models
VALID_FLUX_MODELS = {"flux2-pro", "flux2-flex"}

# Valid image generation modes
VALID_IMAGE_MODES = {
    "text_to_image", "edit", "compose",  # Nano Banana
    "img_ref", "style_ref", "char_ref", "modify"  # Luma AI
}

# Valid video generation modes
VALID_VIDEO_MODES = {"text_video", "image_video"}


def validate_aspect_ratio(aspect_ratio: str) -> bool:
    """Validate aspect ratio string."""
    return aspect_ratio in VALID_ASPECT_RATIOS


def validate_resolution(resolution: str) -> bool:
    """Validate resolution string."""
    return resolution in VALID_RESOLUTIONS


def validate_garment_class(garment_class: str) -> bool:
    """Validate garment class string."""
    return garment_class in VALID_GARMENT_CLASSES


def validate_category(category: str) -> bool:
    """Validate category string."""
    return category in VALID_CATEGORIES


def validate_duration(duration: str) -> bool:
    """Validate video duration string."""
    return duration in VALID_DURATIONS


def validate_luma_model(model: str) -> bool:
    """Validate Luma AI model name."""
    return model in VALID_LUMA_MODELS


def validate_flux_model(model: str) -> bool:
    """Validate FLUX model name."""
    return model in VALID_FLUX_MODELS


def validate_image_mode(mode: str) -> bool:
    """Validate image generation mode."""
    return mode in VALID_IMAGE_MODES


def validate_video_mode(mode: str) -> bool:
    """Validate video generation mode."""
    return mode in VALID_VIDEO_MODES


def validate_range(value: float, min_val: float, max_val: float, name: str) -> None:
    """
    Validate that a value is within a specified range.
    
    Args:
        value: Value to validate
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        name: Name of the parameter (for error messages)
        
    Raises:
        ValueError: If value is out of range
    """
    if not min_val <= value <= max_val:
        raise ValueError(f"{name} must be between {min_val} and {max_val}, got {value}")

