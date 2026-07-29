from dotenv import load_dotenv
load_dotenv()

import os
import argparse
from pathlib import Path
from tryon.api.openAI import GPTImageAdapter

# -------------------------------------------------------
# CLI ARGUMENT PARSER
# -------------------------------------------------------
def build_parser():
    parser = argparse.ArgumentParser(
        description="Generate images using OpenAI GPT Image generation models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Mode selection
    parser.add_argument(
        '--mode',
        type=str,
        default='text',
        choices=['text', 'image'],
        help='Generation mode'
    )

    # Prompt
    parser.add_argument(
        '--prompt',
        type=str,
        help='Text prompt'
    )

    # Unified Images Input (single or multiple)
    parser.add_argument(
        '--images',
        nargs="+",
        type=str,
        help="One or more image paths/URLs"
    )

    # Output directory
    parser.add_argument(
        '--output_dir',
        type=str,
        default="outputs",
        help="Folder to save generated images"
    )

    # Size
    parser.add_argument(
        '--size',
        type=str,
        default="auto",
        help="Size of the Output Images. Available options are: ['1024x1024', '1536x1024', '1024x1536', 'auto']"
    )

    # Quality
    parser.add_argument(
        '--quality',
        type=str,
        default="auto",
        help="Quality of the output Images. Available options are: ['low', 'high', 'medium', 'auto']"
    )

    # Background
    parser.add_argument(
        '--background',
        type=str,
        default="auto",
        help="Background of the output Image. Options: 'transparent', 'auto'"
    )

    # n (number of images to generate)
    parser.add_argument(
        '--n',
        type=int,
        default=1,
        help="Number of images to generate."
    )

    # Input Fidelity
    parser.add_argument(
        '--inp_fid',
        type=str,
        default="low",
        help="Input Fidelity allows you to better preserve details from the input images in the output. Options: 'low', 'high'"
    )

    # Mask Image
    parser.add_argument(
        '--mask',
        type=str,
        help="One image paths/URLs for mask."
    )

    # Model Version
    parser.add_argument(
        '--model',
        type=str,
        default="gpt-image-1.5",
        choices=['gpt-image-1', 'gpt-image-1.5'],
        help="Model version to use. Default: gpt-image-1.5 (latest)"
    )

    return parser


# -------------------------------------------------------
# MAIN FUNCTION
# -------------------------------------------------------
def main():
    parser = build_parser()
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Set OPENAI_API_KEY in environment.")
    
    # ------------- Argument Validation ------------------

    if args.mode == 'text':
        if not args.prompt:
            raise ValueError("--prompt is required for text mode")
    
    if args.mode == 'image':
        if not args.images:
            raise ValueError(f"--images is required for {args.mode} mode")
        
        if args.mask:
            if not args.images:
                raise ValueError(f"One base image is required for mask feature.")
        
    
    # ------------- Initialize Adapter ------------------

    adapter = GPTImageAdapter(api_key=api_key, model_version=args.model)

    # ------------- Dispatch by Mode -------------------
    
    if args.mode == "text":
        images = adapter.generate_text_to_image(
            prompt=args.prompt,
            size=args.size,
            quality=args.quality,
            background=args.background,
            n=args.n
        )
    
    elif args.mode == "image":
        images = adapter.generate_image_edit(
            prompt=args.prompt if args.prompt else None,
            images=args.images,
            mask=args.mask,
            size=args.size,
            quality=args.quality,
            background=args.background,
            n=args.n,
            input_fidelity=args.inp_fid
        )
    
    else:
        raise ValueError("Unknown mode")
    
    # --------------------- SAVE RESULTS ---------------------
    for idx, img_bytes in enumerate(images):
        save_path = output_dir / f"generated_{idx}.png"
        with open(save_path, "wb") as f:
            f.write(img_bytes)
        print(f"Saved {save_path}")

    print(f"\n✓ Generated {len(images)} image(s)")

    return 0

if __name__ == "__main__":
    main()
