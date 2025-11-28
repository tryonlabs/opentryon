"""
FastAPI server for Virtual Try-On using Nano Banana models.

This server provides a simple REST API endpoint for virtual try-on generation
using Google's Gemini image generation models (Nano Banana and Nano Banana Pro).
"""

import os
import io
import base64
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import adapters
from tryon.api.nano_banana import NanoBananaAdapter, NanoBananaProAdapter

# Create output directory for generated images
OUTPUT_DIR = Path("outputs/virtual_tryon")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Supported aspect ratios for both adapters
SUPPORTED_ASPECT_RATIOS = [
    "1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"
]


def calculate_aspect_ratio(image: Image.Image) -> str:
    """
    Calculate the aspect ratio from an image and return the closest supported ratio.
    
    Args:
        image: PIL Image object
        
    Returns:
        str: Aspect ratio string in format "W:H" (e.g., "16:9")
    """
    width, height = image.size
    ratio = width / height
    
    # Map of supported ratios to their decimal values
    ratio_map = {
        "1:1": 1.0,
        "2:3": 2/3,
        "3:2": 3/2,
        "3:4": 3/4,
        "4:3": 4/3,
        "4:5": 4/5,
        "5:4": 5/4,
        "9:16": 9/16,
        "16:9": 16/9,
        "21:9": 21/9,
    }
    
    # Find the closest matching aspect ratio
    closest_ratio = "1:1"  # Default
    min_diff = float('inf')
    
    for ratio_str, ratio_value in ratio_map.items():
        diff = abs(ratio - ratio_value)
        if diff < min_diff:
            min_diff = diff
            closest_ratio = ratio_str
    
    return closest_ratio


def get_image_dimensions(image: Image.Image) -> Tuple[int, int]:
    """
    Get image dimensions (width, height).
    
    Args:
        image: PIL Image object
        
    Returns:
        tuple: (width, height)
    """
    return image.size


def calculate_resolution(image: Image.Image) -> str:
    """
    Calculate resolution from image dimensions in "widthxheight" format.
    
    Args:
        image: PIL Image object
        
    Returns:
        str: Resolution string in format "widthxheight" (e.g., "1024x1024")
    """
    width, height = image.size
    return f"{width}x{height}"


def map_resolution_to_pro_format(image: Image.Image) -> str:
    """
    Map image resolution to Nano Banana Pro format ("1K", "2K", or "4K").
    
    The mapping is based on the maximum dimension:
    - max_dimension <= 1500: "1K"
    - max_dimension <= 3000: "2K"
    - max_dimension > 3000: "4K"
    
    Args:
        image: PIL Image object
        
    Returns:
        str: Resolution in format "1K", "2K", or "4K"
    """
    width, height = image.size
    max_dimension = max(width, height)
    
    if max_dimension <= 1500:
        return "1K"
    elif max_dimension <= 3000:
        return "2K"
    else:
        return "4K"

app = FastAPI(
    title="TryOn AI Virtual Try-On API",
    description="Virtual try-on API using Nano Banana (Gemini Image Generation) models",
    version="1.0.0"
)

# CORS middleware to allow requests from Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "TryOn AI Virtual Try-On API",
        "version": "1.0.0",
        "endpoints": {
            "POST /api/v1/virtual-tryon": "Generate virtual try-on image"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/api/v1/virtual-tryon")
async def virtual_tryon(
    model_image: UploadFile = File(..., description="Model/person image"),
    garment_images: List[UploadFile] = File(..., description="Garment images"),
    provider: str = Form(default="nano-banana", description="Provider: 'nano-banana' or 'nano-banana-pro'"),
    prompt: Optional[str] = Form(default=None, description="Optional custom prompt"),
    resolution: Optional[str] = Form(default="1K", description="Resolution for nano-banana-pro: '1K', '2K', or '4K'"),
    aspect_ratio: Optional[str] = Form(default=None, description="Optional aspect ratio (e.g., '16:9')")
):
    """
    Generate virtual try-on image from model image and garment images.
    
    Uses multi-image composition feature of Nano Banana models to combine
    the model image with multiple garment images.
    
    Args:
        model_image: Single model/person image
        garment_images: List of garment images (top, jeans, scarf, hat, etc.)
        provider: Model provider ('nano-banana' or 'nano-banana-pro')
        prompt: Optional custom prompt for generation
        resolution: Resolution for nano-banana-pro ('1K', '2K', or '4K')
        aspect_ratio: Optional aspect ratio
        
    Returns:
        JSON response with base64-encoded result image
    """
    # try:
    # Validate provider
    if provider not in ["nano-banana", "nano-banana-pro"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid provider '{provider}'. Must be 'nano-banana' or 'nano-banana-pro'"
        )
    
    # Validate inputs
    if not model_image:
        raise HTTPException(status_code=400, detail="Model image is required")
    
    if not garment_images or len(garment_images) == 0:
        raise HTTPException(status_code=400, detail="At least one garment image is required")
    
    # Read model image
    model_image_bytes = await model_image.read()
    model_pil = Image.open(io.BytesIO(model_image_bytes))
    
    # Calculate aspect ratio and resolution from model image
    calculated_aspect_ratio = calculate_aspect_ratio(model_pil)
    calculated_resolution = calculate_resolution(model_pil)
    model_width, model_height = get_image_dimensions(model_pil)
    
    # Use calculated aspect ratio if not provided, otherwise use the provided one
    final_aspect_ratio = aspect_ratio if aspect_ratio else calculated_aspect_ratio
    
    # Map resolution to appropriate format based on provider
    # For nano-banana-pro, use "1K", "2K", or "4K" format
    # For nano-banana, resolution is not used (only aspect ratio)
    if provider == "nano-banana-pro":
        # Use provided resolution if valid, otherwise map from image dimensions
        if resolution and resolution in ["1K", "2K", "4K"]:
            final_resolution = resolution
        else:
            final_resolution = map_resolution_to_pro_format(model_pil)
    else:
        # For nano-banana, resolution is not used, but keep calculated for reference
        final_resolution = calculated_resolution
    
    # Read garment images and combine with model image
    # First image should be model, followed by garments
    images_list = [model_pil]
    for garment_file in garment_images:
        garment_bytes = await garment_file.read()
        garment_pil = Image.open(io.BytesIO(garment_bytes))
        images_list.append(garment_pil)
    
    # Prepare prompt
    if not prompt:
        prompt = (
            "Create a realistic virtual try-on image showing the person wearing the provided garments. "
            "CRITICAL REQUIREMENTS - Preserve all details exactly:\n"
            "1. GARMENT EXTRACTION: The garment images may contain people wearing the garments. "
            "IGNORE and EXTRACT ONLY the garment itself - do not use any person, model, or human figure "
            "from the garment images. Focus solely on the garment: its shape, design, patterns, colors, "
            "textures, and all visual details. Remove or ignore any human elements from garment images.\n"
            "2. GARMENT PRESERVATION: Keep ALL garment details completely intact - patterns, colors, textures, "
            "designs, prints, logos, text, embroidery, sequins, and any decorative elements must remain "
            "identical to the original garment images. Do not alter, fade, or modify any garment features.\n"
            "3. PERSON PRESERVATION: Keep the person's face, body shape, skin tone, hair, and physical "
            "characteristics exactly as shown in the FIRST image (model image). Only apply the extracted "
            "garments from the subsequent images to this person. Do not use any person from garment images.\n"
            "4. PARTIAL GARMENT HANDLING: If the person in the model image is wearing a full-body outfit "
            "(dress, jumpsuit, etc.) but the provided garment is only upper-body (top, shirt, blouse) or "
            "lower-body (pants, jeans, skirt), place the provided garment correctly over the corresponding "
            "body part. For the remaining uncovered body parts, generate an appropriate complementary garment "
            "that matches: (a) the person's physical characteristics and body type, (b) the person's style "
            "and personality traits visible in the model image, (c) the style, color scheme, and design "
            "aesthetic of the provided garment. The complementary garment should create a cohesive, "
            "harmonious outfit that looks natural and well-coordinated.\n"
            "5. FITTING: The extracted garments should fit naturally on the person's body from the first image, "
            "following their body contours and proportions realistically, while maintaining all original "
            "garment details from the garment images.\n"
            "6. COMPOSITION: The first image is the model/person to dress. The following images contain "
            "garments (top, bottom, accessories, etc.) - extract ONLY the garments from these images, "
            "ignoring any people shown. Combine the extracted garments to create a cohesive outfit where "
            "each garment maintains its original appearance and fits the person naturally.\n"
            "7. REALISM: The final image should look like a professional photograph of the person from the "
            "first image wearing the exact extracted garments (and complementary garments if needed), with "
            "realistic lighting, shadows, and fabric draping."
        )
    
    # Initialize adapter and generate
    if provider == "nano-banana":
        adapter = NanoBananaAdapter()
        # Generate with basic adapter using calculated aspect ratio
        result_images = adapter.generate_multi_image(
            images=images_list,
            prompt=prompt,
            aspect_ratio=final_aspect_ratio
        )
    else:  # nano-banana-pro
        adapter = NanoBananaProAdapter()
        # Generate with Pro adapter (supports resolution) using calculated resolution and aspect ratio
        result_images = adapter.generate_multi_image(
            images=images_list,
            prompt=prompt,
            resolution=final_resolution,
            aspect_ratio=final_aspect_ratio
        )
    
    if not result_images:
        raise HTTPException(status_code=500, detail="No images generated")
    
    # Get first result image and convert to PIL Image
    result_image = result_images[0]
    
    # Convert Google GenAI image type to PIL Image
    if not isinstance(result_image, Image.Image):
        # Google GenAI image type has image_bytes attribute
        if hasattr(result_image, 'image_bytes'):
            # Convert bytes to PIL Image
            result_image = Image.open(io.BytesIO(result_image.image_bytes))
        elif hasattr(result_image, 'to_pil'):
            # If it has a to_pil method, use it
            result_image = result_image.to_pil()
        else:
            # Try to get bytes from the image object
            try:
                # Some GenAI image types expose bytes directly
                image_bytes = bytes(result_image)
                result_image = Image.open(io.BytesIO(image_bytes))
            except (TypeError, AttributeError):
                raise HTTPException(
                    status_code=500,
                    detail=f"Unable to convert image type {type(result_image)} to PIL Image. "
                           f"Image attributes: {dir(result_image)}"
                )
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"tryon_{provider}_{timestamp}.png"
    filepath = OUTPUT_DIR / filename
    
    # Save image to disk
    try:
        # Ensure image is in RGB mode for saving
        if result_image.mode != 'RGB':
            result_image = result_image.convert('RGB')
        
        # Save to file
        result_image.save(str(filepath), 'PNG')
        
        # Also save to BytesIO for base64 encoding
        img_buffer = io.BytesIO()
        result_image.save(img_buffer, 'PNG')
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.read()).decode('utf-8')
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error saving image: {str(e)}"
        )
    
    return JSONResponse({
        "success": True,
        "image": f"data:image/png;base64,{img_base64}",
        "provider": provider,
        "num_garments": len(garment_images),
        "saved_path": str(filepath),
        "filename": filename,
        "model_dimensions": {"width": model_width, "height": model_height},
        "aspect_ratio": final_aspect_ratio,
        "calculated_aspect_ratio": calculated_aspect_ratio,
        "resolution": final_resolution,
        "calculated_resolution": calculated_resolution
    })
    
    # except ValueError as e:
    #     raise HTTPException(status_code=400, detail=str(e))
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=f"Error generating try-on: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

