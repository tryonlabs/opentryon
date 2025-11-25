from dotenv import load_dotenv
load_dotenv()

import os
import argparse
from pathlib import Path
from tryon.api.nano_banana import NanoBananaAdapter, NanoBananaProAdapter

def main():
    parser = argparse.ArgumentParser(
        description="Generate images using Google's Nano Banana (Gemini Image Generation) models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Text-to-image with Nano Banana (Fast)
  python image_gen.py --provider nano-banana --prompt "A stylish fashion model wearing a modern casual outfit in a studio setting"
  
  # Text-to-image with Nano Banana Pro (4K)
  python image_gen.py --provider nano-banana-pro --prompt "Professional fashion photography of elegant evening wear on a runway" --resolution 4K
  
  # Image editing
  python image_gen.py --provider nano-banana --mode edit --image person.jpg --prompt "Change the outfit to a formal business suit"
  
  # Multi-image composition
  python image_gen.py --provider nano-banana --mode compose --images outfit1.jpg outfit2.jpg --prompt "Create a fashion catalog layout combining these clothing styles"
  
  # Batch generation from file
  python image_gen.py --provider nano-banana --batch prompts.txt --output-dir results/
  
  # Specify aspect ratio
  python image_gen.py --provider nano-banana --prompt "A fashion model showcasing seasonal clothing collection" --aspect-ratio "16:9"
  
  # Use search grounding (Nano Banana Pro only)
  python image_gen.py --provider nano-banana-pro --prompt "Latest fashion trends from Paris Fashion Week 2024" --use-search-grounding
        """
    )
    
    # Provider selection
    parser.add_argument(
        '--provider',
        type=str,
        required=True,
        choices=['nano-banana', 'nano-banana-pro'],
        help='Image generation provider. Options: nano-banana (Gemini 2.5 Flash Image), nano-banana-pro (Gemini 3 Pro Image Preview)'
    )
    
    # Mode selection
    parser.add_argument(
        '--mode',
        type=str,
        default='text',
        choices=['text', 'edit', 'compose'],
        help='Generation mode. Options: text (text-to-image), edit (image editing), compose (multi-image composition). Default: text'
    )
    
    # Prompt (required for text mode, optional for edit/compose)
    parser.add_argument(
        '-p', '--prompt',
        type=str,
        default=None,
        help='Text prompt describing the image to generate or edits to make'
    )
    
    # Image input (required for edit/compose modes)
    parser.add_argument(
        '-i', '--image',
        type=str,
        default=None,
        help='Path to input image (required for edit mode)'
    )
    
    parser.add_argument(
        '--images',
        type=str,
        nargs='+',
        default=None,
        help='Paths to input images (required for compose mode, can specify multiple)'
    )
    
    # Batch file
    parser.add_argument(
        '--batch',
        type=str,
        default=None,
        help='Path to text file with prompts (one per line) for batch generation'
    )
    
    # Resolution (Nano Banana Pro only)
    parser.add_argument(
        '--resolution',
        type=str,
        default='1K',
        choices=['1K', '2K', '4K'],
        help='Resolution level (Nano Banana Pro only). Options: 1K, 2K, 4K. Default: 1K'
    )
    
    # Aspect ratio
    parser.add_argument(
        '--aspect-ratio',
        type=str,
        default=None,
        choices=['1:1', '2:3', '3:2', '3:4', '4:3', '4:5', '5:4', '9:16', '16:9', '21:9'],
        help='Aspect ratio for generated images. Options: 1:1, 2:3, 3:2, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 21:9'
    )
    
    # Search grounding (Nano Banana Pro only)
    parser.add_argument(
        '--use-search-grounding',
        action='store_true',
        help='Use Google Search for real-world grounding (Nano Banana Pro only)'
    )
    
    # Output directory
    parser.add_argument(
        '-o', '--output-dir',
        type=str,
        default='outputs',
        help='Directory to save generated images. Default: outputs/'
    )
    
    args = parser.parse_args()
    
    # Validate arguments based on mode
    if args.mode == 'text' and not args.prompt and not args.batch:
        raise ValueError("--prompt or --batch is required for text mode")
    
    if args.mode == 'edit':
        if not args.image:
            raise ValueError("--image is required for edit mode")
        if not args.prompt:
            raise ValueError("--prompt is required for edit mode")
        if not os.path.exists(args.image):
            raise FileNotFoundError(f"Image not found: {args.image}")
    
    if args.mode == 'compose':
        if not args.images:
            raise ValueError("--images is required for compose mode")
        if not args.prompt:
            raise ValueError("--prompt is required for compose mode")
        for img_path in args.images:
            if not os.path.exists(img_path):
                raise FileNotFoundError(f"Image not found: {img_path}")
    
    # Validate resolution for Nano Banana (not supported)
    if args.provider == 'nano-banana' and args.resolution != '1K':
        print("Warning: Resolution option is only available for Nano Banana Pro. Using default resolution.")
        args.resolution = '1K'
    
    # Validate search grounding for Nano Banana (not supported)
    if args.provider == 'nano-banana' and args.use_search_grounding:
        print("Warning: Search grounding is only available for Nano Banana Pro. Ignoring --use-search-grounding.")
        args.use_search_grounding = False
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Check for API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("\n✗ Error: GEMINI_API_KEY environment variable is required.")
        print("   Please set it in your .env file or environment.")
        print("   Get your API key from: https://aistudio.google.com/app/apikey")
        return 1
    
    # Initialize adapter
    if args.provider == 'nano-banana':
        print("Initializing Nano Banana (Gemini 2.5 Flash Image) adapter...")
        adapter = NanoBananaAdapter(api_key=api_key)
    else:
        print(f"Initializing Nano Banana Pro (Gemini 3 Pro Image Preview) adapter...")
        print(f"  Resolution: {args.resolution}")
        if args.use_search_grounding:
            print("  Search grounding: Enabled")
        adapter = NanoBananaProAdapter(api_key=api_key)
    
    # try:
    # Handle batch generation
    if args.batch:
        print(f"Batch generation mode: Reading prompts from {args.batch}")
        with open(args.batch, 'r') as f:
            prompts = [line.strip() for line in f if line.strip()]
        
        print(f"Found {len(prompts)} prompts")
        
        if args.provider == 'nano-banana':
            results = adapter.generate_batch(
                prompts=prompts,
                aspect_ratio=args.aspect_ratio
            )
        else:
            results = adapter.generate_batch(
                prompts=prompts,
                resolution=args.resolution,
                aspect_ratio=args.aspect_ratio,
                use_search_grounding=args.use_search_grounding
            )
        
        # Save batch results
        for prompt_idx, images in enumerate(results):
            for img_idx, image in enumerate(images):
                output_path = output_dir / f"batch_{prompt_idx}_{img_idx}.png"
                image.save(output_path)
                print(f"✓ Saved: {output_path}")
        
        print(f"\n✓ Successfully generated {sum(len(r) for r in results)} image(s) from {len(prompts)} prompt(s)")
        return 0
    
    # Handle single generation
    images = []
    
    if args.mode == 'text':
        print(f"Generating image from text prompt...")
        print(f"  Prompt: {args.prompt}")
        if args.aspect_ratio:
            print(f"  Aspect ratio: {args.aspect_ratio}")
        
        if args.provider == 'nano-banana':
            images = adapter.generate_text_to_image(
                prompt=args.prompt,
                aspect_ratio=args.aspect_ratio
            )
        else:
            images = adapter.generate_text_to_image(
                prompt=args.prompt,
                resolution=args.resolution,
                aspect_ratio=args.aspect_ratio,
                use_search_grounding=args.use_search_grounding
            )
    
    elif args.mode == 'edit':
        print(f"Editing image...")
        print(f"  Image: {args.image}")
        print(f"  Prompt: {args.prompt}")
        if args.aspect_ratio:
            print(f"  Aspect ratio: {args.aspect_ratio}")
        
        if args.provider == 'nano-banana':
            images = adapter.generate_image_edit(
                image=args.image,
                prompt=args.prompt,
                aspect_ratio=args.aspect_ratio
            )
        else:
            images = adapter.generate_image_edit(
                image=args.image,
                prompt=args.prompt,
                resolution=args.resolution,
                aspect_ratio=args.aspect_ratio
            )
    
    elif args.mode == 'compose':
        print(f"Composing images...")
        print(f"  Images: {', '.join(args.images)}")
        print(f"  Prompt: {args.prompt}")
        if args.aspect_ratio:
            print(f"  Aspect ratio: {args.aspect_ratio}")
        
        if args.provider == 'nano-banana':
            images = adapter.generate_multi_image(
                images=args.images,
                prompt=args.prompt,
                aspect_ratio=args.aspect_ratio
            )
        else:
            images = adapter.generate_multi_image(
                images=args.images,
                prompt=args.prompt,
                resolution=args.resolution,
                aspect_ratio=args.aspect_ratio
            )
    
    # Save images
    for idx, image in enumerate(images):
        output_path = output_dir / f"generated_{idx}.png"
        image.save(output_path)
        print(f"✓ Saved image {idx + 1}: {output_path}")
    
    print(f"\n✓ Successfully generated {len(images)} image(s)")
    return 0
        
    # except ValueError as e:
    #     print(f"\n✗ Error: {e}")
    #     return 1
    # except Exception as e:
    #     print(f"\n✗ Unexpected error: {e}")
    #     import traceback
    #     traceback.print_exc()
    #     return 1

if __name__ == "__main__":
    exit(main())

