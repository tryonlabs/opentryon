from dotenv import load_dotenv
load_dotenv()

import os
import argparse
from pathlib import Path
from tryon.api.nano_banana import NanoBananaAdapter, NanoBananaProAdapter
from tryon.api.flux2 import Flux2ProAdapter, Flux2FlexAdapter

def main():
    parser = argparse.ArgumentParser(
        description="Generate images using Nano Banana (Gemini) or FLUX.2 image generation models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Nano Banana (Fast)
  python image_gen.py --provider nano-banana --prompt "A stylish fashion model wearing a modern casual outfit in a studio setting"
  
  # Nano Banana Pro (4K)
  python image_gen.py --provider nano-banana-pro --prompt "Professional fashion photography of elegant evening wear on a runway" --resolution 4K
  
  # FLUX.2 PRO
  python image_gen.py --provider flux2-pro --prompt "A professional fashion model wearing elegant evening wear" --width 1024 --height 1024
  
  # FLUX.2 FLEX (Advanced controls)
  python image_gen.py --provider flux2-flex --prompt "A stylish fashion model wearing elegant evening wear" --width 1024 --height 1024 --guidance 7.5 --steps 50
  
  # Image editing
  python image_gen.py --provider nano-banana --mode edit --image person.jpg --prompt "Change the outfit to a formal business suit"
  python image_gen.py --provider flux2-pro --mode edit --image person.jpg --prompt "Change the outfit to casual streetwear"
  
  # Multi-image composition
  python image_gen.py --provider nano-banana --mode compose --images outfit1.jpg outfit2.jpg --prompt "Create a fashion catalog layout combining these clothing styles"
  python image_gen.py --provider flux2-pro --mode compose --images outfit1.jpg outfit2.jpg --prompt "Combine these clothing styles into a cohesive outfit"
  
  # Batch generation from file
  python image_gen.py --provider nano-banana --batch prompts.txt --output-dir results/
  
  # Specify aspect ratio (Nano Banana only)
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
        choices=['nano-banana', 'nano-banana-pro', 'flux2-pro', 'flux2-flex'],
        help='Image generation provider. Options: nano-banana (Gemini 2.5 Flash Image), nano-banana-pro (Gemini 3 Pro Image Preview), flux2-pro (FLUX.2 PRO), flux2-flex (FLUX.2 FLEX)'
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
    
    # Width/Height (FLUX.2 only)
    parser.add_argument(
        '--width',
        type=int,
        default=None,
        help='Image width in pixels (FLUX.2 only, minimum: 64)'
    )
    
    parser.add_argument(
        '--height',
        type=int,
        default=None,
        help='Image height in pixels (FLUX.2 only, minimum: 64)'
    )
    
    # Aspect ratio (Nano Banana only)
    parser.add_argument(
        '--aspect-ratio',
        type=str,
        default=None,
        choices=['1:1', '2:3', '3:2', '3:4', '4:3', '4:5', '5:4', '9:16', '16:9', '21:9'],
        help='Aspect ratio for generated images (Nano Banana only). Options: 1:1, 2:3, 3:2, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 21:9'
    )
    
    # Search grounding (Nano Banana Pro only)
    parser.add_argument(
        '--use-search-grounding',
        action='store_true',
        help='Use Google Search for real-world grounding (Nano Banana Pro only)'
    )
    
    # FLUX.2 FLEX specific parameters
    parser.add_argument(
        '--guidance',
        type=float,
        default=3.5,
        help='Guidance scale for FLUX.2 FLEX (1.5-10). Higher = more adherence to prompt. Default: 3.5'
    )
    
    parser.add_argument(
        '--steps',
        type=int,
        default=28,
        help='Number of generation steps for FLUX.2 FLEX. More steps = higher quality. Default: 28'
    )
    
    parser.add_argument(
        '--seed',
        type=int,
        default=None,
        help='Seed for reproducible results (FLUX.2 only)'
    )
    
    parser.add_argument(
        '--safety-tolerance',
        type=int,
        default=2,
        choices=[0, 1, 2, 3, 4, 5],
        help='Safety tolerance level (FLUX.2 only, 0-5). 0 = most strict, 5 = least strict. Default: 2'
    )
    
    parser.add_argument(
        '--output-format',
        type=str,
        default='png',
        choices=['jpeg', 'png'],
        help='Output format (FLUX.2 only). Options: jpeg, png. Default: png'
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
    
    # Validate provider-specific arguments
    if args.provider in ['nano-banana', 'nano-banana-pro']:
        # Validate resolution for Nano Banana (not supported)
        if args.provider == 'nano-banana' and args.resolution != '1K':
            print("Warning: Resolution option is only available for Nano Banana Pro. Using default resolution.")
            args.resolution = '1K'
        
        # Validate search grounding for Nano Banana (not supported)
        if args.provider == 'nano-banana' and args.use_search_grounding:
            print("Warning: Search grounding is only available for Nano Banana Pro. Ignoring --use-search-grounding.")
            args.use_search_grounding = False
        
        # Check for Gemini API key
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("\n✗ Error: GEMINI_API_KEY environment variable is required for Nano Banana providers.")
            print("   Please set it in your .env file or environment.")
            print("   Get your API key from: https://aistudio.google.com/app/apikey")
            return 1
    
    elif args.provider in ['flux2-pro', 'flux2-flex']:
        # Validate FLUX.2 specific arguments
        if args.width is not None and args.width < 64:
            raise ValueError(f"Width must be at least 64 pixels, got {args.width}")
        if args.height is not None and args.height < 64:
            raise ValueError(f"Height must be at least 64 pixels, got {args.height}")
        
        if args.provider == 'flux2-flex':
            if args.guidance < 1.5 or args.guidance > 10:
                raise ValueError(f"Guidance must be between 1.5 and 10, got {args.guidance}")
        
        # Check for BFL API key
        api_key = os.getenv("BFL_API_KEY")
        if not api_key:
            print("\n✗ Error: BFL_API_KEY environment variable is required for FLUX.2 providers.")
            print("   Please set it in your .env file or environment.")
            print("   Get your API key from: https://docs.bfl.ai/")
            return 1
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize adapter
    if args.provider == 'nano-banana':
        print("Initializing Nano Banana (Gemini 2.5 Flash Image) adapter...")
        adapter = NanoBananaAdapter(api_key=api_key)
    elif args.provider == 'nano-banana-pro':
        print(f"Initializing Nano Banana Pro (Gemini 3 Pro Image Preview) adapter...")
        print(f"  Resolution: {args.resolution}")
        if args.use_search_grounding:
            print("  Search grounding: Enabled")
        adapter = NanoBananaProAdapter(api_key=api_key)
    elif args.provider == 'flux2-pro':
        print("Initializing FLUX.2 [PRO] adapter...")
        if args.width:
            print(f"  Width: {args.width}")
        if args.height:
            print(f"  Height: {args.height}")
        adapter = Flux2ProAdapter(api_key=api_key)
    elif args.provider == 'flux2-flex':
        print("Initializing FLUX.2 [FLEX] adapter...")
        if args.width:
            print(f"  Width: {args.width}")
        if args.height:
            print(f"  Height: {args.height}")
        print(f"  Guidance: {args.guidance}")
        print(f"  Steps: {args.steps}")
        adapter = Flux2FlexAdapter(api_key=api_key)
    
    # try:
    # Handle batch generation (Nano Banana only)
    if args.batch:
        if args.provider in ['flux2-pro', 'flux2-flex']:
            print("Warning: Batch generation is not supported for FLUX.2 providers. Processing prompts individually...")
            with open(args.batch, 'r') as f:
                prompts = [line.strip() for line in f if line.strip()]
            
            for prompt_idx, prompt in enumerate(prompts):
                print(f"\nProcessing prompt {prompt_idx + 1}/{len(prompts)}: {prompt}")
                if args.provider == 'flux2-pro':
                    images = adapter.generate_text_to_image(
                        prompt=prompt,
                        width=args.width,
                        height=args.height,
                        seed=args.seed,
                        safety_tolerance=args.safety_tolerance,
                        output_format=args.output_format
                    )
                else:  # flux2-flex
                    images = adapter.generate_text_to_image(
                        prompt=prompt,
                        width=args.width,
                        height=args.height,
                        seed=args.seed,
                        guidance=args.guidance,
                        steps=args.steps,
                        safety_tolerance=args.safety_tolerance,
                        output_format=args.output_format
                    )
                
                for img_idx, image in enumerate(images):
                    output_path = output_dir / f"batch_{prompt_idx}_{img_idx}.png"
                    image.save(output_path)
                    print(f"✓ Saved: {output_path}")
            
            print(f"\n✓ Successfully generated images from {len(prompts)} prompt(s)")
            return 0
        else:
            print(f"Batch generation mode: Reading prompts from {args.batch}")
            with open(args.batch, 'r') as f:
                prompts = [line.strip() for line in f if line.strip()]
            
            print(f"Found {len(prompts)} prompts")
            
            if args.provider == 'nano-banana':
                results = adapter.generate_batch(
                    prompts=prompts,
                    aspect_ratio=args.aspect_ratio
                )
            else:  # nano-banana-pro
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
        
        if args.provider == 'nano-banana':
            if args.aspect_ratio:
                print(f"  Aspect ratio: {args.aspect_ratio}")
            images = adapter.generate_text_to_image(
                prompt=args.prompt,
                aspect_ratio=args.aspect_ratio
            )
        elif args.provider == 'nano-banana-pro':
            if args.aspect_ratio:
                print(f"  Aspect ratio: {args.aspect_ratio}")
            images = adapter.generate_text_to_image(
                prompt=args.prompt,
                resolution=args.resolution,
                aspect_ratio=args.aspect_ratio,
                use_search_grounding=args.use_search_grounding
            )
        elif args.provider == 'flux2-pro':
            if args.width:
                print(f"  Width: {args.width}")
            if args.height:
                print(f"  Height: {args.height}")
            images = adapter.generate_text_to_image(
                prompt=args.prompt,
                width=args.width,
                height=args.height,
                seed=args.seed,
                safety_tolerance=args.safety_tolerance,
                output_format=args.output_format
            )
        else:  # flux2-flex
            if args.width:
                print(f"  Width: {args.width}")
            if args.height:
                print(f"  Height: {args.height}")
            print(f"  Guidance: {args.guidance}, Steps: {args.steps}")
            images = adapter.generate_text_to_image(
                prompt=args.prompt,
                width=args.width,
                height=args.height,
                seed=args.seed,
                guidance=args.guidance,
                steps=args.steps,
                safety_tolerance=args.safety_tolerance,
                output_format=args.output_format
            )
    
    elif args.mode == 'edit':
        print(f"Editing image...")
        print(f"  Image: {args.image}")
        print(f"  Prompt: {args.prompt}")
        
        if args.provider == 'nano-banana':
            if args.aspect_ratio:
                print(f"  Aspect ratio: {args.aspect_ratio}")
            images = adapter.generate_image_edit(
                image=args.image,
                prompt=args.prompt,
                aspect_ratio=args.aspect_ratio
            )
        elif args.provider == 'nano-banana-pro':
            if args.aspect_ratio:
                print(f"  Aspect ratio: {args.aspect_ratio}")
            images = adapter.generate_image_edit(
                image=args.image,
                prompt=args.prompt,
                resolution=args.resolution,
                aspect_ratio=args.aspect_ratio
            )
        elif args.provider == 'flux2-pro':
            if args.width:
                print(f"  Width: {args.width}")
            if args.height:
                print(f"  Height: {args.height}")
            images = adapter.generate_image_edit(
                prompt=args.prompt,
                input_image=args.image,
                width=args.width,
                height=args.height,
                seed=args.seed,
                safety_tolerance=args.safety_tolerance,
                output_format=args.output_format
            )
        else:  # flux2-flex
            if args.width:
                print(f"  Width: {args.width}")
            if args.height:
                print(f"  Height: {args.height}")
            print(f"  Guidance: {args.guidance}, Steps: {args.steps}")
            images = adapter.generate_image_edit(
                prompt=args.prompt,
                input_image=args.image,
                width=args.width,
                height=args.height,
                seed=args.seed,
                guidance=args.guidance,
                steps=args.steps,
                safety_tolerance=args.safety_tolerance,
                output_format=args.output_format
            )
    
    elif args.mode == 'compose':
        print(f"Composing images...")
        print(f"  Images: {', '.join(args.images)}")
        print(f"  Prompt: {args.prompt}")
        
        if args.provider == 'nano-banana':
            if args.aspect_ratio:
                print(f"  Aspect ratio: {args.aspect_ratio}")
            images = adapter.generate_multi_image(
                images=args.images,
                prompt=args.prompt,
                aspect_ratio=args.aspect_ratio
            )
        elif args.provider == 'nano-banana-pro':
            if args.aspect_ratio:
                print(f"  Aspect ratio: {args.aspect_ratio}")
            images = adapter.generate_multi_image(
                images=args.images,
                prompt=args.prompt,
                resolution=args.resolution,
                aspect_ratio=args.aspect_ratio
            )
        elif args.provider == 'flux2-pro':
            if args.width:
                print(f"  Width: {args.width}")
            if args.height:
                print(f"  Height: {args.height}")
            images = adapter.generate_multi_image(
                prompt=args.prompt,
                images=args.images,
                width=args.width,
                height=args.height,
                seed=args.seed,
                safety_tolerance=args.safety_tolerance,
                output_format=args.output_format
            )
        else:  # flux2-flex
            if args.width:
                print(f"  Width: {args.width}")
            if args.height:
                print(f"  Height: {args.height}")
            print(f"  Guidance: {args.guidance}, Steps: {args.steps}")
            images = adapter.generate_multi_image(
                prompt=args.prompt,
                images=args.images,
                width=args.width,
                height=args.height,
                seed=args.seed,
                guidance=args.guidance,
                steps=args.steps,
                safety_tolerance=args.safety_tolerance,
                output_format=args.output_format
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

