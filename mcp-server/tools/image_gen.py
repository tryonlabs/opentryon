"""Image generation tools for OpenTryOn MCP Server."""

from typing import Optional, List
from pathlib import Path

from tryon.api.nano_banana import NanoBananaAdapter, NanoBananaProAdapter
from tryon.api.flux2 import Flux2ProAdapter, Flux2FlexAdapter
from tryon.api.lumaAI import LumaAIAdapter
from config import config
from utils import save_image


def generate_image_nano_banana(
    prompt: str,
    aspect_ratio: str = "1:1",
    mode: str = "text_to_image",
    image: Optional[str] = None,
    images: Optional[List[str]] = None,
    output_dir: Optional[str] = None,
) -> dict:
    """
    Generate images using Nano Banana (Gemini 2.5 Flash).
    
    Args:
        prompt: Text description
        aspect_ratio: Aspect ratio (e.g., "16:9", "1:1")
        mode: "text_to_image", "edit", or "compose"
        image: Input image for edit mode
        images: Input images for compose mode
        output_dir: Directory to save results (optional)
        
    Returns:
        Dictionary with status and result information
    """
    try:
        adapter = NanoBananaAdapter()
        
        # Generate based on mode
        if mode == "text_to_image":
            result_images = adapter.generate_text_to_image(
                prompt=prompt,
                aspect_ratio=aspect_ratio
            )
        elif mode == "edit":
            if not image:
                return {"success": False, "error": "Image required for edit mode"}
            result_images = adapter.generate_image_edit(
                image=image,
                prompt=prompt
            )
        elif mode == "compose":
            if not images:
                return {"success": False, "error": "Images required for compose mode"}
            result_images = adapter.generate_multi_image(
                images=images,
                prompt=prompt
            )
        else:
            return {"success": False, "error": f"Invalid mode: {mode}"}
        
        # Save results
        output_paths = []
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            for idx, img in enumerate(result_images):
                save_path = save_image(img, output_path / f"nano_banana_{idx}.png")
                output_paths.append(str(save_path))
        else:
            for idx, img in enumerate(result_images):
                save_path = save_image(img, config.TEMP_DIR / f"nano_banana_{idx}.png")
                output_paths.append(str(save_path))
        
        return {
            "success": True,
            "provider": "nano_banana",
            "model": "gemini-2.5-flash-image",
            "num_images": len(result_images),
            "output_paths": output_paths,
            "message": f"Generated {len(result_images)} image(s)"
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


def generate_image_nano_banana_pro(
    prompt: str,
    resolution: str = "1K",
    aspect_ratio: str = "1:1",
    use_search_grounding: bool = False,
    mode: str = "text_to_image",
    image: Optional[str] = None,
    output_dir: Optional[str] = None,
) -> dict:
    """
    Generate high-resolution images using Nano Banana Pro (Gemini 3 Pro).
    
    Args:
        prompt: Text description
        resolution: "1K", "2K", or "4K"
        aspect_ratio: Aspect ratio (e.g., "16:9", "1:1")
        use_search_grounding: Enable Google Search grounding
        mode: "text_to_image" or "edit"
        image: Input image for edit mode
        output_dir: Directory to save results (optional)
        
    Returns:
        Dictionary with status and result information
    """
    try:
        adapter = NanoBananaProAdapter()
        
        # Generate based on mode
        if mode == "text_to_image":
            result_images = adapter.generate_text_to_image(
                prompt=prompt,
                resolution=resolution,
                aspect_ratio=aspect_ratio,
                use_search_grounding=use_search_grounding
            )
        elif mode == "edit":
            if not image:
                return {"success": False, "error": "Image required for edit mode"}
            result_images = adapter.generate_image_edit(
                image=image,
                prompt=prompt,
                resolution=resolution
            )
        else:
            return {"success": False, "error": f"Invalid mode: {mode}"}
        
        # Save results
        output_paths = []
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            for idx, img in enumerate(result_images):
                save_path = save_image(img, output_path / f"nano_banana_pro_{idx}.png")
                output_paths.append(str(save_path))
        else:
            for idx, img in enumerate(result_images):
                save_path = save_image(img, config.TEMP_DIR / f"nano_banana_pro_{idx}.png")
                output_paths.append(str(save_path))
        
        return {
            "success": True,
            "provider": "nano_banana_pro",
            "model": "gemini-3-pro-image",
            "resolution": resolution,
            "num_images": len(result_images),
            "output_paths": output_paths,
            "message": f"Generated {len(result_images)} {resolution} image(s)"
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


def generate_image_flux2_pro(
    prompt: str,
    width: int = 1024,
    height: int = 1024,
    seed: Optional[int] = None,
    mode: str = "text_to_image",
    input_image: Optional[str] = None,
    images: Optional[List[str]] = None,
    output_dir: Optional[str] = None,
) -> dict:
    """
    Generate images using FLUX.2 PRO.
    
    Args:
        prompt: Text description
        width: Image width
        height: Image height
        seed: Random seed (optional)
        mode: "text_to_image", "edit", or "compose"
        input_image: Input image for edit mode
        images: Input images for compose mode
        output_dir: Directory to save results (optional)
        
    Returns:
        Dictionary with status and result information
    """
    try:
        adapter = Flux2ProAdapter()
        
        # Generate based on mode
        if mode == "text_to_image":
            result_images = adapter.generate_text_to_image(
                prompt=prompt,
                width=width,
                height=height,
                seed=seed
            )
        elif mode == "edit":
            if not input_image:
                return {"success": False, "error": "Input image required for edit mode"}
            result_images = adapter.generate_image_edit(
                prompt=prompt,
                input_image=input_image,
                width=width,
                height=height
            )
        elif mode == "compose":
            if not images:
                return {"success": False, "error": "Images required for compose mode"}
            result_images = adapter.generate_multi_image(
                prompt=prompt,
                images=images,
                width=width,
                height=height
            )
        else:
            return {"success": False, "error": f"Invalid mode: {mode}"}
        
        # Save results
        output_paths = []
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            for idx, img in enumerate(result_images):
                save_path = save_image(img, output_path / f"flux2_pro_{idx}.png")
                output_paths.append(str(save_path))
        else:
            for idx, img in enumerate(result_images):
                save_path = save_image(img, config.TEMP_DIR / f"flux2_pro_{idx}.png")
                output_paths.append(str(save_path))
        
        return {
            "success": True,
            "provider": "flux2_pro",
            "model": "flux-2-pro",
            "dimensions": f"{width}x{height}",
            "num_images": len(result_images),
            "output_paths": output_paths,
            "message": f"Generated {len(result_images)} image(s)"
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


def generate_image_flux2_flex(
    prompt: str,
    width: int = 1024,
    height: int = 1024,
    guidance: float = 7.5,
    steps: int = 28,
    prompt_upsampling: bool = False,
    seed: Optional[int] = None,
    mode: str = "text_to_image",
    input_image: Optional[str] = None,
    output_dir: Optional[str] = None,
) -> dict:
    """
    Generate images using FLUX.2 FLEX with advanced controls.
    
    Args:
        prompt: Text description
        width: Image width
        height: Image height
        guidance: Guidance scale (1.5-10)
        steps: Number of steps
        prompt_upsampling: Enable prompt enhancement
        seed: Random seed (optional)
        mode: "text_to_image" or "edit"
        input_image: Input image for edit mode
        output_dir: Directory to save results (optional)
        
    Returns:
        Dictionary with status and result information
    """
    try:
        adapter = Flux2FlexAdapter()
        
        # Generate based on mode
        if mode == "text_to_image":
            result_images = adapter.generate_text_to_image(
                prompt=prompt,
                width=width,
                height=height,
                guidance=guidance,
                steps=steps,
                prompt_upsampling=prompt_upsampling,
                seed=seed
            )
        elif mode == "edit":
            if not input_image:
                return {"success": False, "error": "Input image required for edit mode"}
            result_images = adapter.generate_image_edit(
                prompt=prompt,
                input_image=input_image,
                width=width,
                height=height,
                guidance=guidance,
                steps=steps,
                prompt_upsampling=prompt_upsampling
            )
        else:
            return {"success": False, "error": f"Invalid mode: {mode}"}
        
        # Save results
        output_paths = []
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            for idx, img in enumerate(result_images):
                save_path = save_image(img, output_path / f"flux2_flex_{idx}.png")
                output_paths.append(str(save_path))
        else:
            for idx, img in enumerate(result_images):
                save_path = save_image(img, config.TEMP_DIR / f"flux2_flex_{idx}.png")
                output_paths.append(str(save_path))
        
        return {
            "success": True,
            "provider": "flux2_flex",
            "model": "flux-2-flex",
            "dimensions": f"{width}x{height}",
            "guidance": guidance,
            "steps": steps,
            "num_images": len(result_images),
            "output_paths": output_paths,
            "message": f"Generated {len(result_images)} image(s)"
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


def generate_image_luma_photon_flash(
    prompt: str,
    aspect_ratio: str = "1:1",
    mode: str = "text_to_image",
    images: Optional[List[str]] = None,
    weights: Optional[List[float]] = None,
    char_id: Optional[str] = None,
    char_images: Optional[List[str]] = None,
    output_dir: Optional[str] = None,
) -> dict:
    """
    Generate images using Luma AI Photon-Flash-1.
    
    Args:
        prompt: Text description
        aspect_ratio: Aspect ratio (e.g., "16:9", "1:1")
        mode: "text_to_image", "img_ref", "style_ref", "char_ref", or "modify"
        images: Input images for reference/modify modes
        weights: Weights for reference images
        char_id: Character ID for character reference
        char_images: Character reference images
        output_dir: Directory to save results (optional)
        
    Returns:
        Dictionary with status and result information
    """
    try:
        adapter = LumaAIAdapter(model="photon-flash-1")
        
        # Generate based on mode
        if mode == "text_to_image":
            result_images = adapter.generate_text_to_image(
                prompt=prompt,
                aspect_ratio=aspect_ratio
            )
        elif mode == "img_ref":
            if not images:
                return {"success": False, "error": "Images required for img_ref mode"}
            image_ref = [{"url": img, "weight": w} for img, w in zip(images, weights or [0.8] * len(images))]
            result_images = adapter.generate_with_image_reference(
                prompt=prompt,
                aspect_ratio=aspect_ratio,
                image_ref=image_ref
            )
        elif mode == "style_ref":
            if not images:
                return {"success": False, "error": "Images required for style_ref mode"}
            style_ref = [{"url": img, "weight": w} for img, w in zip(images, weights or [0.75] * len(images))]
            result_images = adapter.generate_with_style_reference(
                prompt=prompt,
                aspect_ratio=aspect_ratio,
                style_ref=style_ref
            )
        elif mode == "char_ref":
            if not char_id or not char_images:
                return {"success": False, "error": "Character ID and images required for char_ref mode"}
            character_ref = {char_id: {"images": char_images}}
            result_images = adapter.generate_with_character_reference(
                prompt=prompt,
                aspect_ratio=aspect_ratio,
                character_ref=character_ref
            )
        elif mode == "modify":
            if not images or len(images) != 1:
                return {"success": False, "error": "Single image required for modify mode"}
            result_images = adapter.generate_with_modify_image(
                prompt=prompt,
                images=images[0],
                weights=weights[0] if weights else 0.85,
                aspect_ratio=aspect_ratio
            )
        else:
            return {"success": False, "error": f"Invalid mode: {mode}"}
        
        # Save results
        output_paths = []
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            for idx, img in enumerate(result_images):
                save_path = save_image(img, output_path / f"luma_photon_flash_{idx}.png")
                output_paths.append(str(save_path))
        else:
            for idx, img in enumerate(result_images):
                save_path = save_image(img, config.TEMP_DIR / f"luma_photon_flash_{idx}.png")
                output_paths.append(str(save_path))
        
        return {
            "success": True,
            "provider": "luma_ai",
            "model": "photon-flash-1",
            "num_images": len(result_images),
            "output_paths": output_paths,
            "message": f"Generated {len(result_images)} image(s)"
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


def generate_image_luma_photon(
    prompt: str,
    aspect_ratio: str = "1:1",
    mode: str = "text_to_image",
    images: Optional[List[str]] = None,
    weights: Optional[List[float]] = None,
    char_id: Optional[str] = None,
    char_images: Optional[List[str]] = None,
    output_dir: Optional[str] = None,
) -> dict:
    """
    Generate images using Luma AI Photon-1.
    
    Args:
        prompt: Text description
        aspect_ratio: Aspect ratio (e.g., "16:9", "1:1")
        mode: "text_to_image", "img_ref", "style_ref", "char_ref", or "modify"
        images: Input images for reference/modify modes
        weights: Weights for reference images
        char_id: Character ID for character reference
        char_images: Character reference images
        output_dir: Directory to save results (optional)
        
    Returns:
        Dictionary with status and result information
    """
    try:
        adapter = LumaAIAdapter(model="photon-1")
        
        # Generate based on mode
        if mode == "text_to_image":
            result_images = adapter.generate_text_to_image(
                prompt=prompt,
                aspect_ratio=aspect_ratio
            )
        elif mode == "img_ref":
            if not images:
                return {"success": False, "error": "Images required for img_ref mode"}
            image_ref = [{"url": img, "weight": w} for img, w in zip(images, weights or [0.8] * len(images))]
            result_images = adapter.generate_with_image_reference(
                prompt=prompt,
                aspect_ratio=aspect_ratio,
                image_ref=image_ref
            )
        elif mode == "style_ref":
            if not images:
                return {"success": False, "error": "Images required for style_ref mode"}
            style_ref = [{"url": img, "weight": w} for img, w in zip(images, weights or [0.75] * len(images))]
            result_images = adapter.generate_with_style_reference(
                prompt=prompt,
                aspect_ratio=aspect_ratio,
                style_ref=style_ref
            )
        elif mode == "char_ref":
            if not char_id or not char_images:
                return {"success": False, "error": "Character ID and images required for char_ref mode"}
            character_ref = {char_id: {"images": char_images}}
            result_images = adapter.generate_with_character_reference(
                prompt=prompt,
                aspect_ratio=aspect_ratio,
                character_ref=character_ref
            )
        elif mode == "modify":
            if not images or len(images) != 1:
                return {"success": False, "error": "Single image required for modify mode"}
            result_images = adapter.generate_with_modify_image(
                prompt=prompt,
                images=images[0],
                weights=weights[0] if weights else 0.85,
                aspect_ratio=aspect_ratio
            )
        else:
            return {"success": False, "error": f"Invalid mode: {mode}"}
        
        # Save results
        output_paths = []
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            for idx, img in enumerate(result_images):
                save_path = save_image(img, output_path / f"luma_photon_{idx}.png")
                output_paths.append(str(save_path))
        else:
            for idx, img in enumerate(result_images):
                save_path = save_image(img, config.TEMP_DIR / f"luma_photon_{idx}.png")
                output_paths.append(str(save_path))
        
        return {
            "success": True,
            "provider": "luma_ai",
            "model": "photon-1",
            "num_images": len(result_images),
            "output_paths": output_paths,
            "message": f"Generated {len(result_images)} image(s)"
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

