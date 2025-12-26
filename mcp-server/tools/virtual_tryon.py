"""Virtual try-on tools for OpenTryOn MCP Server."""

from typing import Optional, List
from pathlib import Path

from tryon.api import AmazonNovaCanvasVTONAdapter, KlingAIVTONAdapter, SegmindVTONAdapter
from config import config
from utils import validate_image_path, validate_image_url, save_image


def virtual_tryon_nova(
    source_image: str,
    reference_image: str,
    mask_type: str = "GARMENT",
    garment_class: str = "UPPER_BODY",
    region: Optional[str] = None,
    output_dir: Optional[str] = None,
) -> dict:
    """
    Generate virtual try-on using Amazon Nova Canvas.
    
    Args:
        source_image: Path or URL to person image
        reference_image: Path or URL to garment image
        mask_type: "GARMENT" or "IMAGE"
        garment_class: "UPPER_BODY", "LOWER_BODY", "FULL_BODY", or "FOOTWEAR"
        region: AWS region (optional, uses config default)
        output_dir: Directory to save results (optional)
        
    Returns:
        Dictionary with status and result information
    """
    try:
        # Validate inputs
        if not (validate_image_path(source_image) or validate_image_url(source_image)):
            return {
                "success": False,
                "error": f"Invalid source image: {source_image}"
            }
        
        if not (validate_image_path(reference_image) or validate_image_url(reference_image)):
            return {
                "success": False,
                "error": f"Invalid reference image: {reference_image}"
            }
        
        # Initialize adapter
        adapter = AmazonNovaCanvasVTONAdapter(region=region or config.AMAZON_NOVA_REGION)
        
        # Generate virtual try-on
        images = adapter.generate_and_decode(
            source_image=source_image,
            reference_image=reference_image,
            mask_type=mask_type,
            garment_class=garment_class,
        )
        
        # Save results
        output_paths = []
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            for idx, image in enumerate(images):
                save_path = save_image(image, output_path / f"nova_result_{idx}.png")
                output_paths.append(str(save_path))
        else:
            # Save to temp directory
            for idx, image in enumerate(images):
                save_path = save_image(image, config.TEMP_DIR / f"nova_result_{idx}.png")
                output_paths.append(str(save_path))
        
        return {
            "success": True,
            "provider": "amazon_nova_canvas",
            "num_images": len(images),
            "output_paths": output_paths,
            "message": f"Generated {len(images)} virtual try-on image(s)"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def virtual_tryon_kling(
    source_image: str,
    reference_image: str,
    model: Optional[str] = None,
    output_dir: Optional[str] = None,
) -> dict:
    """
    Generate virtual try-on using Kling AI.
    
    Args:
        source_image: Path or URL to person image
        reference_image: Path or URL to garment image
        model: Model version (optional, uses API default)
        output_dir: Directory to save results (optional)
        
    Returns:
        Dictionary with status and result information
    """
    try:
        # Validate inputs
        if not (validate_image_path(source_image) or validate_image_url(source_image)):
            return {
                "success": False,
                "error": f"Invalid source image: {source_image}"
            }
        
        if not (validate_image_path(reference_image) or validate_image_url(reference_image)):
            return {
                "success": False,
                "error": f"Invalid reference image: {reference_image}"
            }
        
        # Initialize adapter
        adapter = KlingAIVTONAdapter()
        
        # Generate virtual try-on
        images = adapter.generate_and_decode(
            source_image=source_image,
            reference_image=reference_image,
            model=model,
        )
        
        # Save results
        output_paths = []
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            for idx, image in enumerate(images):
                save_path = save_image(image, output_path / f"kling_result_{idx}.png")
                output_paths.append(str(save_path))
        else:
            # Save to temp directory
            for idx, image in enumerate(images):
                save_path = save_image(image, config.TEMP_DIR / f"kling_result_{idx}.png")
                output_paths.append(str(save_path))
        
        return {
            "success": True,
            "provider": "kling_ai",
            "num_images": len(images),
            "output_paths": output_paths,
            "message": f"Generated {len(images)} virtual try-on image(s)"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def virtual_tryon_segmind(
    model_image: str,
    cloth_image: str,
    category: str = "Upper body",
    num_inference_steps: int = 25,
    guidance_scale: float = 2.0,
    seed: int = -1,
    output_dir: Optional[str] = None,
) -> dict:
    """
    Generate virtual try-on using Segmind.
    
    Args:
        model_image: Path or URL to person image
        cloth_image: Path or URL to garment image
        category: "Upper body", "Lower body", or "Dress"
        num_inference_steps: Number of denoising steps (20-100)
        guidance_scale: Classifier-free guidance scale (1-25)
        seed: Random seed (-1 for random)
        output_dir: Directory to save results (optional)
        
    Returns:
        Dictionary with status and result information
    """
    try:
        # Validate inputs
        if not (validate_image_path(model_image) or validate_image_url(model_image)):
            return {
                "success": False,
                "error": f"Invalid model image: {model_image}"
            }
        
        if not (validate_image_path(cloth_image) or validate_image_url(cloth_image)):
            return {
                "success": False,
                "error": f"Invalid cloth image: {cloth_image}"
            }
        
        if category not in ["Upper body", "Lower body", "Dress"]:
            return {
                "success": False,
                "error": f"Invalid category: {category}. Must be 'Upper body', 'Lower body', or 'Dress'"
            }
        
        # Initialize adapter
        adapter = SegmindVTONAdapter()
        
        # Generate virtual try-on
        images = adapter.generate_and_decode(
            model_image=model_image,
            cloth_image=cloth_image,
            category=category,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
            seed=seed,
        )
        
        # Save results
        output_paths = []
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            for idx, image in enumerate(images):
                save_path = save_image(image, output_path / f"segmind_result_{idx}.png")
                output_paths.append(str(save_path))
        else:
            # Save to temp directory
            for idx, image in enumerate(images):
                save_path = save_image(image, config.TEMP_DIR / f"segmind_result_{idx}.png")
                output_paths.append(str(save_path))
        
        return {
            "success": True,
            "provider": "segmind",
            "num_images": len(images),
            "output_paths": output_paths,
            "message": f"Generated {len(images)} virtual try-on image(s)"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

