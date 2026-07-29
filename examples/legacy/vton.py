from dotenv import load_dotenv
load_dotenv()

import os
import argparse
from pathlib import Path
from tryon.api import AmazonNovaCanvasVTONAdapter, KlingAIVTONAdapter, SegmindVTONAdapter

def main():
    parser = argparse.ArgumentParser(
        description="Generate virtual try-on images using Amazon Nova Canvas, Kling AI, or Segmind",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Amazon Nova Canvas - Basic usage with GARMENT mask (default)
  python vton.py --provider nova --source data/original_human/model.jpg --reference data/original_cloth/model.jpg
  
  # Amazon Nova Canvas - Specify garment class
  python vton.py --provider nova --source person.jpg --reference garment.jpg --garment-class LOWER_BODY
  
  # Amazon Nova Canvas - Use IMAGE mask type
  python vton.py --provider nova --source person.jpg --reference garment.jpg --mask-type IMAGE --mask-image mask.png
  
  # Kling AI - Basic usage
  python vton.py --provider kling --source person.jpg --reference garment.jpg
  
  # Kling AI - Specify model version
  python vton.py --provider kling --source person.jpg --reference garment.jpg --model kolors-virtual-try-on-v1-5
  
  # Segmind - Basic usage
  python vton.py --provider segmind --source person.jpg --reference garment.jpg --category "Upper body"
  
  # Segmind - Specify inference parameters
  python vton.py --provider segmind --source person.jpg --reference garment.jpg --category "Lower body" --num-steps 35 --guidance-scale 2.5
  
  # Save output to specific directory
  python vton.py --provider nova --source person.jpg --reference garment.jpg --output-dir results/
  
  # Use different AWS region (Nova Canvas only)
  python vton.py --provider nova --source person.jpg --reference garment.jpg --region ap-northeast-1
        """
    )
    
    # Provider selection
    parser.add_argument(
        '--provider',
        type=str,
        required=True,
        choices=['nova', 'kling', 'segmind'],
        help='Virtual try-on provider to use. Options: nova (Amazon Nova Canvas), kling (Kling AI), segmind (Segmind Try-On Diffusion)'
    )
    
    # Required arguments
    parser.add_argument(
        '-s', '--source',
        type=str,
        required=True,
        help='Path to source image (person/model)'
    )
    
    parser.add_argument(
        '-r', '--reference',
        type=str,
        required=True,
        help='Path to reference image (garment/product)'
    )
    
    # Optional arguments for Nova Canvas
    parser.add_argument(
        '--mask-type',
        type=str,
        default='GARMENT',
        choices=['GARMENT', 'IMAGE'],
        help='Type of mask to use (Nova Canvas only). Options: GARMENT (default), IMAGE'
    )
    
    parser.add_argument(
        '--garment-class',
        type=str,
        default='UPPER_BODY',
        choices=['UPPER_BODY', 'LOWER_BODY', 'FULL_BODY', 'FOOTWEAR'],
        help='Garment class for GARMENT mask type (Nova Canvas only). Required when mask-type is GARMENT. Default: UPPER_BODY'
    )
    
    parser.add_argument(
        '--mask-image',
        type=str,
        default=None,
        help='Path to mask image for IMAGE mask type (Nova Canvas only). Required when mask-type is IMAGE'
    )
    
    parser.add_argument(
        '--region',
        type=str,
        default=None,
        help='AWS region name (Nova Canvas only). Defaults to AMAZON_NOVA_REGION env var or us-east-1. Supported: us-east-1, ap-northeast-1, eu-west-1'
    )
    
    parser.add_argument(
        '--model-id',
        type=str,
        default=None,
        help='Model ID to use (Nova Canvas only). Defaults to AMAZON_NOVA_MODEL_ID env var or amazon.nova-canvas-v1:0'
    )
    
    # Optional arguments for Kling AI
    parser.add_argument(
        '--model',
        type=str,
        default=None,
        help='Model version to use (Kling AI only). Examples: kolors-virtual-try-on-v1, kolors-virtual-try-on-v1-5'
    )
    
    parser.add_argument(
        '--base-url',
        type=str,
        default=None,
        help='Base URL for API (Kling AI only). Defaults to KLING_AI_BASE_URL env var or https://api-singapore.klingai.com'
    )
    
    # Optional arguments for Segmind
    parser.add_argument(
        '--category',
        type=str,
        default='Upper body',
        choices=['Upper body', 'Lower body', 'Dress'],
        help='Garment category (Segmind only). Options: Upper body, Lower body, Dress. Default: Upper body'
    )
    
    parser.add_argument(
        '--num-steps',
        type=int,
        default=None,
        help='Number of inference steps (Segmind only). Default: 25. Range: 20-100'
    )
    
    parser.add_argument(
        '--guidance-scale',
        type=float,
        default=None,
        help='Guidance scale for classifier-free guidance (Segmind only). Default: 2. Range: 1-25'
    )
    
    parser.add_argument(
        '--seed',
        type=int,
        default=None,
        help='Seed for image generation (Segmind only). Default: -1. Range: -1 to 999999999999999'
    )
    
    parser.add_argument(
        '-o', '--output-dir',
        type=str,
        default='outputs',
        help='Directory to save generated images. Default: outputs/'
    )
    
    parser.add_argument(
        '--save-base64',
        action='store_true',
        help='Also save Base64 encoded strings to .txt files (in addition to PNG images)'
    )
    
    args = parser.parse_args()
    
    # Validate file paths
    if not os.path.exists(args.source):
        raise FileNotFoundError(f"Source image not found: {args.source}")
    
    if not os.path.exists(args.reference):
        raise FileNotFoundError(f"Reference image not found: {args.reference}")
    
    # Provider-specific validation
    if args.provider == 'nova':
        if args.mask_type == 'IMAGE' and not args.mask_image:
            raise ValueError("--mask-image is required when --mask-type is IMAGE")
    elif args.provider == 'kling':
        # Kling AI doesn't use mask types, so no validation needed here
        pass
    
    # Create output directory if it doesn't exist
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize adapter based on provider
    if args.provider == 'nova':
        print(f"Initializing Amazon Nova Canvas adapter...")
        if args.region:
            print(f"  Region: {args.region}")
        if args.model_id:
            print(f"  Model ID: {args.model_id}")
            os.environ['AMAZON_NOVA_MODEL_ID'] = args.model_id
        adapter = AmazonNovaCanvasVTONAdapter(region=args.region)
        
        # Generate images
        print(f"Generating virtual try-on image...")
        print(f"  Source: {args.source}")
        print(f"  Reference: {args.reference}")
        print(f"  Mask type: {args.mask_type}")
        
        if args.mask_type == 'GARMENT':
            print(f"  Garment class: {args.garment_class}")
        elif args.mask_type == 'IMAGE':
            print(f"  Mask image: {args.mask_image}")
        
        try:
            import base64
            from PIL import Image
            import io
            
            # Generate images (decode to PIL Image objects for saving)
            print("Generating images...")
            images_pil = adapter.generate_and_decode(
                source_image=args.source,
                reference_image=args.reference,
                mask_type=args.mask_type,
                garment_class=args.garment_class,
                mask_image=args.mask_image
            )
            
        except ValueError as e:
            print(f"\n✗ Error: {e}")
            return 1
        except Exception as e:
            print(f"\n✗ Unexpected error: {e}")
            return 1
            
    elif args.provider == 'kling':
        print(f"Initializing Kling AI adapter...")
        if args.base_url:
            print(f"  Base URL: {args.base_url}")
        if args.model:
            print(f"  Model: {args.model}")
        
        # Check for required environment variables
        api_key = os.getenv("KLING_AI_API_KEY")
        secret_key = os.getenv("KLING_AI_SECRET_KEY")
        
        if not api_key or not secret_key:
            print("\n✗ Error: Kling AI requires KLING_AI_API_KEY and KLING_AI_SECRET_KEY environment variables.")
            print("   Please set them in your .env file or environment.")
            return 1
        
        adapter = KlingAIVTONAdapter(
            api_key=api_key,
            secret_key=secret_key,
            base_url=args.base_url
        )
        
        # Generate images
        print(f"Generating virtual try-on image...")
        print(f"  Source: {args.source}")
        print(f"  Reference: {args.reference}")
        if args.model:
            print(f"  Model: {args.model}")
        
        try:
            import base64
            from PIL import Image
            import io
            
            # Generate images (decode to PIL Image objects for saving)
            print("Generating images...")
            images_pil = adapter.generate_and_decode(
                source_image=args.source,
                reference_image=args.reference,
                model=args.model
            )
            
        except ValueError as e:
            print(f"\n✗ Error: {e}")
            return 1
        except Exception as e:
            print(f"\n✗ Unexpected error: {e}")
            return 1
    
    elif args.provider == 'segmind':
        print(f"Initializing Segmind adapter...")
        
        # Check for required environment variable
        api_key = os.getenv("SEGMIND_API_KEY")
        
        if not api_key:
            print("\n✗ Error: Segmind requires SEGMIND_API_KEY environment variable.")
            print("   Please set it in your .env file or environment.")
            return 1
        
        adapter = SegmindVTONAdapter(api_key=api_key)
        
        # Generate images
        print(f"Generating virtual try-on image...")
        print(f"  Model image: {args.source}")
        print(f"  Cloth image: {args.reference}")
        print(f"  Category: {args.category}")
        if args.num_steps:
            print(f"  Inference steps: {args.num_steps}")
        if args.guidance_scale:
            print(f"  Guidance scale: {args.guidance_scale}")
        if args.seed is not None:
            print(f"  Seed: {args.seed}")
        
        try:
            import base64
            from PIL import Image
            import io
            
            # Generate images (decode to PIL Image objects for saving)
            print("Generating images...")
            images_pil = adapter.generate_and_decode(
                model_image=args.source,
                cloth_image=args.reference,
                category=args.category,
                num_inference_steps=args.num_steps,
                guidance_scale=args.guidance_scale,
                seed=args.seed
            )
            
        except ValueError as e:
            print(f"\n✗ Error: {e}")
            return 1
        except Exception as e:
            print(f"\n✗ Unexpected error: {e}")
            return 1
    
    # Save images as PNG
    for idx, image in enumerate(images_pil):
        output_path = output_dir / f"vton_result_{idx}.png"
        image.save(output_path)
        print(f"✓ Saved PNG image {idx + 1}: {output_path}")
    
    # Optionally save Base64 strings
    if args.save_base64:
        print("\nSaving Base64 strings...")
        for idx, image in enumerate(images_pil):
            # Convert PIL Image to Base64
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            image_bytes = buffer.getvalue()
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            
            output_path = output_dir / f"vton_result_{idx}.txt"
            with open(output_path, 'w') as f:
                f.write(image_base64)
            print(f"✓ Saved Base64 string {idx + 1}: {output_path}")
    
    print(f"\n✓ Successfully generated {len(images_pil)} image(s)")
    return 0

if __name__ == "__main__":
    exit(main())
