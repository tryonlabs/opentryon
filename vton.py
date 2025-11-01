from dotenv import load_dotenv
load_dotenv()

import os
import argparse
from pathlib import Path
from tryon.api import AmazonNovaCanvasVTONAdapter

def main():
    parser = argparse.ArgumentParser(
        description="Generate virtual try-on images using Amazon Nova Canvas",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with GARMENT mask (default)
  python vton.py --source data/original_human/model.jpg --reference data/original_cloth/model.jpg
  
  # Specify garment class
  python vton.py --source person.jpg --reference garment.jpg --garment-class LOWER_BODY
  
  # Use IMAGE mask type
  python vton.py --source person.jpg --reference garment.jpg --mask-type IMAGE --mask-image mask.png
  
  # Save output to specific directory
  python vton.py --source person.jpg --reference garment.jpg --output-dir results/
  
  # Use different AWS region
  python vton.py --source person.jpg --reference garment.jpg --region ap-northeast-1
  
  # Use specific model ID
  python vton.py --source person.jpg --reference garment.jpg --model-id amazon.nova-canvas-v1:0
        """
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
    
    # Optional arguments
    parser.add_argument(
        '--mask-type',
        type=str,
        default='GARMENT',
        choices=['GARMENT', 'IMAGE'],
        help='Type of mask to use. Options: GARMENT (default), IMAGE'
    )
    
    parser.add_argument(
        '--garment-class',
        type=str,
        default='UPPER_BODY',
        choices=['UPPER_BODY', 'LOWER_BODY', 'FULL_BODY', 'FOOTWEAR'],
        help='Garment class for GARMENT mask type. Required when mask-type is GARMENT. Default: UPPER_BODY'
    )
    
    parser.add_argument(
        '--mask-image',
        type=str,
        default=None,
        help='Path to mask image for IMAGE mask type. Required when mask-type is IMAGE'
    )
    
    parser.add_argument(
        '--region',
        type=str,
        default=None,
        help='AWS region name. Defaults to AMAZON_NOVA_REGION env var or us-east-1. Supported: us-east-1, ap-northeast-1, eu-west-1'
    )
    
    parser.add_argument(
        '--model-id',
        type=str,
        default=None,
        help='Model ID to use. Defaults to AMAZON_NOVA_MODEL_ID env var or amazon.nova-canvas-v1:0'
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
    
    if args.mask_type == 'IMAGE' and not args.mask_image:
        raise ValueError("--mask-image is required when --mask-type is IMAGE")
    
    # Set model ID environment variable if provided
    if args.model_id:
        os.environ['AMAZON_NOVA_MODEL_ID'] = args.model_id
    
    # Create output directory if it doesn't exist
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize adapter
    print(f"Initializing Amazon Nova Canvas adapter...")
    if args.region:
        print(f"  Region: {args.region}")
    if args.model_id:
        print(f"  Model ID: {args.model_id}")
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
        
    except ValueError as e:
        print(f"\n✗ Error: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
