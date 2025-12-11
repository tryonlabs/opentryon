"""Preprocessing tools for OpenTryOn MCP Server."""

from typing import Optional
from pathlib import Path

from tryon.preprocessing import segment_garment as _segment_garment
from tryon.preprocessing import extract_garment as _extract_garment
from tryon.preprocessing import segment_human as _segment_human


def segment_garment(
    input_path: str,
    output_dir: str,
    garment_class: str = "upper",
) -> dict:
    """
    Segment garments from images using U2Net.
    
    Args:
        input_path: Path to input image or directory
        output_dir: Output directory
        garment_class: "upper", "lower", or "all"
        
    Returns:
        Dictionary with status and result information
    """
    try:
        # Validate garment class
        if garment_class not in ["upper", "lower", "all"]:
            return {
                "success": False,
                "error": f"Invalid garment_class: {garment_class}. Must be 'upper', 'lower', or 'all'"
            }
        
        # Validate input path
        input_p = Path(input_path)
        if not input_p.exists():
            return {
                "success": False,
                "error": f"Input path does not exist: {input_path}"
            }
        
        # Create output directory
        output_p = Path(output_dir)
        output_p.mkdir(parents=True, exist_ok=True)
        
        # Perform segmentation
        _segment_garment(
            inputs_dir=str(input_p) if input_p.is_dir() else str(input_p.parent),
            outputs_dir=str(output_p),
            cls=garment_class
        )
        
        return {
            "success": True,
            "operation": "segment_garment",
            "input_path": str(input_p),
            "output_dir": str(output_p),
            "garment_class": garment_class,
            "message": f"Successfully segmented garments to {output_dir}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def extract_garment(
    input_path: str,
    output_dir: str,
    garment_class: str = "upper",
    resize_width: Optional[int] = 400,
) -> dict:
    """
    Extract and preprocess garments.
    
    Args:
        input_path: Path to input image or directory
        output_dir: Output directory
        garment_class: "upper", "lower", or "all"
        resize_width: Target width for resizing (optional)
        
    Returns:
        Dictionary with status and result information
    """
    try:
        # Validate garment class
        if garment_class not in ["upper", "lower", "all"]:
            return {
                "success": False,
                "error": f"Invalid garment_class: {garment_class}. Must be 'upper', 'lower', or 'all'"
            }
        
        # Validate input path
        input_p = Path(input_path)
        if not input_p.exists():
            return {
                "success": False,
                "error": f"Input path does not exist: {input_path}"
            }
        
        # Create output directory
        output_p = Path(output_dir)
        output_p.mkdir(parents=True, exist_ok=True)
        
        # Perform extraction
        _extract_garment(
            inputs_dir=str(input_p) if input_p.is_dir() else str(input_p.parent),
            outputs_dir=str(output_p),
            cls=garment_class,
            resize_to_width=resize_width
        )
        
        return {
            "success": True,
            "operation": "extract_garment",
            "input_path": str(input_p),
            "output_dir": str(output_p),
            "garment_class": garment_class,
            "resize_width": resize_width,
            "message": f"Successfully extracted garments to {output_dir}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def segment_human(
    image_path: str,
    output_dir: str,
) -> dict:
    """
    Segment human subjects from images.
    
    Args:
        image_path: Path to input image
        output_dir: Output directory
        
    Returns:
        Dictionary with status and result information
    """
    try:
        # Validate input path
        input_p = Path(image_path)
        if not input_p.exists():
            return {
                "success": False,
                "error": f"Input image does not exist: {image_path}"
            }
        
        if not input_p.is_file():
            return {
                "success": False,
                "error": f"Input path is not a file: {image_path}"
            }
        
        # Create output directory
        output_p = Path(output_dir)
        output_p.mkdir(parents=True, exist_ok=True)
        
        # Perform segmentation
        _segment_human(
            image_path=str(input_p),
            output_dir=str(output_p)
        )
        
        return {
            "success": True,
            "operation": "segment_human",
            "input_path": str(input_p),
            "output_dir": str(output_p),
            "message": f"Successfully segmented human to {output_dir}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

