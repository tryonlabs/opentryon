"""Example usage of OpenTryOn MCP Server tools."""

import json
from pathlib import Path
import sys

# Add parent directory to path to import tools
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools import (
    virtual_tryon_nova,
    virtual_tryon_kling,
    virtual_tryon_segmind,
    generate_image_nano_banana,
    generate_image_nano_banana_pro,
    generate_image_flux2_pro,
    generate_video_luma_ray,
    segment_garment,
    load_fashion_mnist,
)


def example_virtual_tryon():
    """Example: Virtual try-on with different providers."""
    print("\n=== Virtual Try-On Examples ===\n")
    
    # Example 1: Amazon Nova Canvas
    print("1. Amazon Nova Canvas Virtual Try-On")
    result = virtual_tryon_nova(
        source_image="path/to/person.jpg",
        reference_image="path/to/garment.jpg",
        garment_class="UPPER_BODY",
        output_dir="outputs/nova"
    )
    print(json.dumps(result, indent=2))
    
    # Example 2: Kling AI
    print("\n2. Kling AI Virtual Try-On")
    result = virtual_tryon_kling(
        source_image="path/to/person.jpg",
        reference_image="path/to/garment.jpg",
        output_dir="outputs/kling"
    )
    print(json.dumps(result, indent=2))
    
    # Example 3: Segmind
    print("\n3. Segmind Virtual Try-On")
    result = virtual_tryon_segmind(
        model_image="path/to/person.jpg",
        cloth_image="path/to/garment.jpg",
        category="Upper body",
        num_inference_steps=35,
        guidance_scale=2.5,
        output_dir="outputs/segmind"
    )
    print(json.dumps(result, indent=2))


def example_image_generation():
    """Example: Image generation with different models."""
    print("\n=== Image Generation Examples ===\n")
    
    # Example 1: Nano Banana (Fast)
    print("1. Nano Banana - Fast Image Generation")
    result = generate_image_nano_banana(
        prompt="A professional fashion model wearing elegant evening wear on a runway",
        aspect_ratio="16:9",
        output_dir="outputs/nano_banana"
    )
    print(json.dumps(result, indent=2))
    
    # Example 2: Nano Banana Pro (4K)
    print("\n2. Nano Banana Pro - 4K Image Generation")
    result = generate_image_nano_banana_pro(
        prompt="Professional fashion photography of elegant evening wear",
        resolution="4K",
        aspect_ratio="16:9",
        use_search_grounding=True,
        output_dir="outputs/nano_banana_pro"
    )
    print(json.dumps(result, indent=2))
    
    # Example 3: FLUX.2 PRO
    print("\n3. FLUX.2 PRO - High-Quality Image Generation")
    result = generate_image_flux2_pro(
        prompt="A stylish fashion model in modern casual wear",
        width=1024,
        height=1024,
        seed=42,
        output_dir="outputs/flux2_pro"
    )
    print(json.dumps(result, indent=2))


def example_video_generation():
    """Example: Video generation with Luma AI."""
    print("\n=== Video Generation Examples ===\n")
    
    # Example 1: Text-to-Video
    print("1. Text-to-Video with Ray 2")
    result = generate_video_luma_ray(
        prompt="A fashion model walking on a runway in elegant evening wear",
        model="ray-2",
        mode="text_video",
        resolution="720p",
        duration="5s",
        aspect_ratio="16:9",
        output_dir="outputs/videos"
    )
    print(json.dumps(result, indent=2))
    
    # Example 2: Image-to-Video with Keyframes
    print("\n2. Image-to-Video with Keyframes")
    result = generate_video_luma_ray(
        prompt="Model walking gracefully",
        model="ray-2",
        mode="image_video",
        start_image="path/to/start_frame.jpg",
        end_image="path/to/end_frame.jpg",
        resolution="720p",
        duration="5s",
        output_dir="outputs/videos"
    )
    print(json.dumps(result, indent=2))


def example_preprocessing():
    """Example: Preprocessing tools."""
    print("\n=== Preprocessing Examples ===\n")
    
    # Example 1: Segment Garment
    print("1. Segment Garment")
    result = segment_garment(
        input_path="path/to/garment_images",
        output_dir="outputs/segmented",
        garment_class="upper"
    )
    print(json.dumps(result, indent=2))


def example_datasets():
    """Example: Dataset loading."""
    print("\n=== Dataset Examples ===\n")
    
    # Example 1: Fashion-MNIST
    print("1. Load Fashion-MNIST Dataset")
    result = load_fashion_mnist(
        download=True,
        normalize=True,
        flatten=False
    )
    print(json.dumps(result, indent=2))


def main():
    """Run all examples."""
    print("OpenTryOn MCP Server - Example Usage")
    print("=" * 50)
    
    # Note: These examples show the API structure
    # Actual execution requires valid image paths and API keys
    
    print("\nNote: These are example API calls.")
    print("Replace paths and ensure API keys are configured in .env file.")
    print("\nUncomment the examples you want to run:\n")
    
    # Uncomment to run examples:
    # example_virtual_tryon()
    # example_image_generation()
    # example_video_generation()
    # example_preprocessing()
    # example_datasets()
    
    print("\nExamples complete!")


if __name__ == "__main__":
    main()

