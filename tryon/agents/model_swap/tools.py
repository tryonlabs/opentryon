"""
Tools for Model Swap Agent

This module provides LangChain tools for model swapping using multiple AI models:
- Nano Banana (Gemini 2.5 Flash Image)
- Nano Banana Pro (Gemini 3 Pro Image Preview)
- FLUX 2 Pro
- FLUX 2 Flex

The tools allow intelligent extraction of person attributes from prompts and generate
professional model-swapped images while preserving outfits.

Note: Tools store full image data in a global cache to avoid token limit issues.
"""

import json
from typing import Optional, List
from pydantic import BaseModel, Field
from langchain.tools import tool

from tryon.api.nano_banana import NanoBananaAdapter, NanoBananaProAdapter
from tryon.api.flux2 import Flux2ProAdapter, Flux2FlexAdapter

# Global cache to store full tool outputs
_tool_output_cache = {}


class NanoBananaProModelSwapToolInput(BaseModel):
    """Input schema for Nano Banana Pro model swap tool."""
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
        description="Output resolution. Options: '1K', '2K', '4K'. Default: '4K' for professional quality"
    )
    use_search_grounding: Optional[bool] = Field(
        default=False,
        description="Whether to use Google Search grounding for real-world reference images"
    )


@tool("nano_banana_pro_model_swap", args_schema=NanoBananaProModelSwapToolInput)
def nano_banana_pro_model_swap(
    image: str,
    model_description: str,
    resolution: str = "4K",
    use_search_grounding: bool = False
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
    
    Nano Banana Pro Features:
    - 4K resolution support for professional-quality output
    - Google Search grounding for real-world reference images
    - Advanced "thinking" process for refined composition
    - Photorealistic results with accurate clothing preservation
    
    Args:
        image: Path or URL to the image of person wearing the outfit
        model_description: Detailed prompt describing the desired model and emphasizing
                          outfit preservation. Should be comprehensive and specific.
        resolution: Output resolution ('1K', '2K', or '4K'). Default: '4K'
        use_search_grounding: Use Google Search for real-world references. Default: False
    
    Returns:
        JSON string containing:
        - status: 'success' or 'error'
        - provider: 'nano_banana_pro'
        - image_count: Number of images generated
        - cache_key: Key to retrieve full image data from cache
        - model_description: The prompt used for generation
        - message: Status message
        
    Example Usage by Agent:
        When user says: "Replace with a professional male model in his 30s"
        Agent constructs: "Professional fashion photography showing a professional male model 
        in his early 30s with athletic build and confident posture, wearing the exact same 
        outfit with all clothing details, colors, and patterns preserved perfectly. Maintain 
        the original lighting, background, and composition. High-end e-commerce quality, 
        photorealistic."
    """
    try:
        print("Initializing Nano Banana Pro adapter...")
        adapter = NanoBananaProAdapter()
        
        print("Generating model swap (this may take a moment)...")
        print(f"Resolution: {resolution}")
        print(f"Prompt: {model_description}")
        if use_search_grounding:
            print("Using Google Search grounding")
        
        # Use generate_image_edit to modify the person while preserving outfit
        images = adapter.generate_image_edit(
            image=image,
            prompt=model_description,
            resolution=resolution
        )
        
        print("Nano Banana Pro generation completed")
        
        # Store full images in cache
        import hashlib
        cache_key = hashlib.md5(
            f"{image}_{model_description}_{resolution}_{use_search_grounding}".encode()
        ).hexdigest()
        _tool_output_cache[cache_key] = {
            "provider": "nano_banana_pro",
            "images": images if isinstance(images, list) else [images],
            "model_description": model_description
        }
        
        # Return metadata to avoid token limits
        result = {
            "status": "success",
            "provider": "nano_banana_pro",
            "image_count": len(images) if isinstance(images, list) else 1,
            "cache_key": cache_key,
            "model_description": model_description,
            "resolution": resolution,
            "message": f"Successfully generated {len(images) if isinstance(images, list) else 1} image(s) at {resolution} resolution."
        }
        return json.dumps(result)
        
    except Exception as e:
        error_message = str(e)
        print(f"Error during model swap: {error_message}")
        
        result = {
            "status": "error",
            "provider": "nano_banana_pro",
            "error": error_message,
            "model_description": model_description
        }
        return json.dumps(result)


class NanoBananaModelSwapToolInput(BaseModel):
    """Input schema for Nano Banana model swap tool."""
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
    aspect_ratio: Optional[str] = Field(
        default=None,
        description="Aspect ratio. Options: '1:1', '2:3', '3:2', '3:4', '4:3', '4:5', '5:4', '9:16', '16:9', '21:9'. Default: None (auto)"
    )


class Flux2ProModelSwapToolInput(BaseModel):
    """Input schema for FLUX 2 Pro model swap tool."""
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
    width: Optional[int] = Field(
        default=None,
        description="Width of output image. Minimum: 64. Default: Model default"
    )
    height: Optional[int] = Field(
        default=None,
        description="Height of output image. Minimum: 64. Default: Model default"
    )
    seed: Optional[int] = Field(
        default=None,
        description="Random seed for reproducibility"
    )


class Flux2FlexModelSwapToolInput(BaseModel):
    """Input schema for FLUX 2 Flex model swap tool."""
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
    width: Optional[int] = Field(
        default=None,
        description="Width of output image. Minimum: 64. Default: Model default"
    )
    height: Optional[int] = Field(
        default=None,
        description="Height of output image. Minimum: 64. Default: Model default"
    )
    seed: Optional[int] = Field(
        default=None,
        description="Random seed for reproducibility"
    )
    guidance: Optional[float] = Field(
        default=3.5,
        description="Guidance scale (1.5-10). Higher values = more adherence to prompt. Default: 3.5"
    )
    steps: Optional[int] = Field(
        default=28,
        description="Number of generation steps. More steps = higher quality. Default: 28"
    )


@tool("nano_banana_model_swap", args_schema=NanoBananaModelSwapToolInput)
def nano_banana_model_swap(
    image: str,
    model_description: str,
    aspect_ratio: Optional[str] = None
) -> str:
    """
    Swap the model/person in an image while preserving the outfit using Nano Banana (Gemini 2.5 Flash Image).
    
    This tool uses Google's Gemini 2.5 Flash Image (Nano Banana) to:
    1. Take an image of a person wearing an outfit
    2. Generate a new image with a different model/person based on the description
    3. Preserve the exact outfit, clothing details, patterns, and styling
    4. Maintain professional photography quality and composition
    
    Nano Banana Features:
    - Fast generation at 1024px resolution
    - Efficient for high-volume tasks
    - Good quality for quick iterations
    
    Args:
        image: Path or URL to the image of person wearing the outfit
        model_description: Detailed prompt describing the desired model and emphasizing
                          outfit preservation. Should be comprehensive and specific.
        aspect_ratio: Optional aspect ratio. Options: '1:1', '2:3', '3:2', '3:4', '4:3',
                     '4:5', '5:4', '9:16', '16:9', '21:9'. Default: None (auto)
    
    Returns:
        JSON string containing:
        - status: 'success' or 'error'
        - provider: 'nano_banana'
        - image_count: Number of images generated
        - cache_key: Key to retrieve full image data from cache
        - model_description: The prompt used for generation
        - message: Status message
    """
    try:
        print("Initializing Nano Banana adapter...")
        adapter = NanoBananaAdapter()
        
        print("Generating model swap (this may take a moment)...")
        print(f"Prompt: {model_description}")
        if aspect_ratio:
            print(f"Aspect ratio: {aspect_ratio}")
        
        # Use generate_image_edit to modify the person while preserving outfit
        images = adapter.generate_image_edit(
            image=image,
            prompt=model_description,
            aspect_ratio=aspect_ratio
        )
        
        print("Nano Banana generation completed")
        
        # Store full images in cache
        import hashlib
        cache_key = hashlib.md5(
            f"nano_banana_{image}_{model_description}_{aspect_ratio}".encode()
        ).hexdigest()
        _tool_output_cache[cache_key] = {
            "provider": "nano_banana",
            "images": images if isinstance(images, list) else [images],
            "model_description": model_description
        }
        
        # Return metadata to avoid token limits
        result = {
            "status": "success",
            "provider": "nano_banana",
            "image_count": len(images) if isinstance(images, list) else 1,
            "cache_key": cache_key,
            "model_description": model_description,
            "message": f"Successfully generated {len(images) if isinstance(images, list) else 1} image(s) using Nano Banana."
        }
        return json.dumps(result)
        
    except Exception as e:
        error_message = str(e)
        print(f"Error during model swap: {error_message}")
        
        result = {
            "status": "error",
            "provider": "nano_banana",
            "error": error_message,
            "model_description": model_description
        }
        return json.dumps(result)


@tool("flux2_pro_model_swap", args_schema=Flux2ProModelSwapToolInput)
def flux2_pro_model_swap(
    image: str,
    model_description: str,
    width: Optional[int] = None,
    height: Optional[int] = None,
    seed: Optional[int] = None
) -> str:
    """
    Swap the model/person in an image while preserving the outfit using FLUX 2 Pro.
    
    This tool uses FLUX 2 Pro to:
    1. Take an image of a person wearing an outfit
    2. Generate a new image with a different model/person based on the description
    3. Preserve the exact outfit, clothing details, patterns, and styling
    4. Maintain professional photography quality and composition
    
    FLUX 2 Pro Features:
    - High-quality image generation
    - Custom width/height control
    - Seed for reproducibility
    - Professional quality results
    
    Args:
        image: Path or URL to the image of person wearing the outfit
        model_description: Detailed prompt describing the desired model and emphasizing
                          outfit preservation. Should be comprehensive and specific.
        width: Width of output image. Minimum: 64. Default: Model default
        height: Height of output image. Minimum: 64. Default: Model default
        seed: Random seed for reproducibility
    
    Returns:
        JSON string containing:
        - status: 'success' or 'error'
        - provider: 'flux2_pro'
        - image_count: Number of images generated
        - cache_key: Key to retrieve full image data from cache
        - model_description: The prompt used for generation
        - message: Status message
    """
    try:
        print("Initializing FLUX 2 Pro adapter...")
        adapter = Flux2ProAdapter()
        
        print("Generating model swap (this may take a moment)...")
        print(f"Prompt: {model_description}")
        if width and height:
            print(f"Resolution: {width}x{height}")
        if seed:
            print(f"Seed: {seed}")
        
        # Use generate_image_edit to modify the person while preserving outfit
        images = adapter.generate_image_edit(
            prompt=model_description,
            input_image=image,
            width=width,
            height=height,
            seed=seed
        )
        
        print("FLUX 2 Pro generation completed")
        
        # Store full images in cache
        import hashlib
        cache_key = hashlib.md5(
            f"flux2_pro_{image}_{model_description}_{width}_{height}_{seed}".encode()
        ).hexdigest()
        _tool_output_cache[cache_key] = {
            "provider": "flux2_pro",
            "images": images if isinstance(images, list) else [images],
            "model_description": model_description
        }
        
        # Return metadata to avoid token limits
        result = {
            "status": "success",
            "provider": "flux2_pro",
            "image_count": len(images) if isinstance(images, list) else 1,
            "cache_key": cache_key,
            "model_description": model_description,
            "message": f"Successfully generated {len(images) if isinstance(images, list) else 1} image(s) using FLUX 2 Pro."
        }
        return json.dumps(result)
        
    except Exception as e:
        error_message = str(e)
        print(f"Error during model swap: {error_message}")
        
        result = {
            "status": "error",
            "provider": "flux2_pro",
            "error": error_message,
            "model_description": model_description
        }
        return json.dumps(result)


@tool("flux2_flex_model_swap", args_schema=Flux2FlexModelSwapToolInput)
def flux2_flex_model_swap(
    image: str,
    model_description: str,
    width: Optional[int] = None,
    height: Optional[int] = None,
    seed: Optional[int] = None,
    guidance: float = 3.5,
    steps: int = 28
) -> str:
    """
    Swap the model/person in an image while preserving the outfit using FLUX 2 Flex.
    
    This tool uses FLUX 2 Flex to:
    1. Take an image of a person wearing an outfit
    2. Generate a new image with a different model/person based on the description
    3. Preserve the exact outfit, clothing details, patterns, and styling
    4. Maintain professional photography quality and composition
    
    FLUX 2 Flex Features:
    - Advanced controls (guidance scale, steps)
    - Prompt upsampling for better quality
    - Custom width/height control
    - Seed for reproducibility
    - Highest quality results with fine-tuned parameters
    
    Args:
        image: Path or URL to the image of person wearing the outfit
        model_description: Detailed prompt describing the desired model and emphasizing
                          outfit preservation. Should be comprehensive and specific.
        width: Width of output image. Minimum: 64. Default: Model default
        height: Height of output image. Minimum: 64. Default: Model default
        seed: Random seed for reproducibility
        guidance: Guidance scale (1.5-10). Higher values = more adherence to prompt. Default: 3.5
        steps: Number of generation steps. More steps = higher quality. Default: 28
    
    Returns:
        JSON string containing:
        - status: 'success' or 'error'
        - provider: 'flux2_flex'
        - image_count: Number of images generated
        - cache_key: Key to retrieve full image data from cache
        - model_description: The prompt used for generation
        - message: Status message
    """
    try:
        print("Initializing FLUX 2 Flex adapter...")
        adapter = Flux2FlexAdapter()
        
        print("Generating model swap (this may take a moment)...")
        print(f"Prompt: {model_description}")
        if width and height:
            print(f"Resolution: {width}x{height}")
        if seed:
            print(f"Seed: {seed}")
        print(f"Guidance: {guidance}, Steps: {steps}")
        
        # Use generate_image_edit to modify the person while preserving outfit
        images = adapter.generate_image_edit(
            prompt=model_description,
            input_image=image,
            width=width,
            height=height,
            seed=seed,
            guidance=guidance,
            steps=steps
        )
        
        print("FLUX 2 Flex generation completed")
        
        # Store full images in cache
        import hashlib
        cache_key = hashlib.md5(
            f"flux2_flex_{image}_{model_description}_{width}_{height}_{seed}_{guidance}_{steps}".encode()
        ).hexdigest()
        _tool_output_cache[cache_key] = {
            "provider": "flux2_flex",
            "images": images if isinstance(images, list) else [images],
            "model_description": model_description
        }
        
        # Return metadata to avoid token limits
        result = {
            "status": "success",
            "provider": "flux2_flex",
            "image_count": len(images) if isinstance(images, list) else 1,
            "cache_key": cache_key,
            "model_description": model_description,
            "message": f"Successfully generated {len(images) if isinstance(images, list) else 1} image(s) using FLUX 2 Flex."
        }
        return json.dumps(result)
        
    except Exception as e:
        error_message = str(e)
        print(f"Error during model swap: {error_message}")
        
        result = {
            "status": "error",
            "provider": "flux2_flex",
            "error": error_message,
            "model_description": model_description
        }
        return json.dumps(result)


def get_model_swap_tools(model: Optional[str] = None) -> List:
    """
    Get available model swap tools.
    
    Args:
        model: Specific model to use. Options: 'nano_banana', 'nano_banana_pro', 
               'flux2_pro', 'flux2_flex'. If None, returns all tools.
    
    Returns:
        List of LangChain tools for model swapping
    """
    all_tools = {
        "nano_banana": nano_banana_model_swap,
        "nano_banana_pro": nano_banana_pro_model_swap,
        "flux2_pro": flux2_pro_model_swap,
        "flux2_flex": flux2_flex_model_swap,
    }
    
    if model:
        model_lower = model.lower().replace("-", "_").replace(" ", "_")
        if model_lower in all_tools:
            return [all_tools[model_lower]]
        else:
            # Default to nano_banana_pro if invalid model specified
            return [all_tools["nano_banana_pro"]]
    
    # Return all tools if no model specified
    return list(all_tools.values())


def get_tool_output_from_cache(cache_key: str) -> Optional[dict]:
    """
    Retrieve full tool output from cache using cache_key.
    
    Args:
        cache_key: Cache key returned in tool output
        
    Returns:
        Dictionary with provider, images, and model_description, or None if not found
    """
    return _tool_output_cache.get(cache_key)

