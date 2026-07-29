from dotenv import load_dotenv
load_dotenv()

import os
import json
import argparse
from pathlib import Path
from tryon.api.lumaAI import LumaAIAdapter


# -------------------------------------------------------
# Build Character Reference Map
# -------------------------------------------------------
def build_character_ref(args):
    """
    Convert:
        --char_id identity0  --char_images url1 url2
        --char_id identity1  --char_images url3
    into:
        {
            "identity0": {"images": [url1, url2]},
            "identity1": {"images": [url3]}
        }
    """
    if not args.char_id and not args.char_images:
        return None

    if not args.char_id or not args.char_images:
        raise ValueError("Both --char-id and --char-images must be provided for char-ref mode.")

    if len(args.char_id) != len(args.char_images):
        raise ValueError("The number of --char-id entries must match --char-images entries.")

    ref = {}
    for identity, urls in zip(args.char_id, args.char_images):
        ref[identity] = {"images": urls}

    return ref


# -------------------------------------------------------
# CLI ARGUMENT PARSER
# -------------------------------------------------------
def build_parser():
    parser = argparse.ArgumentParser(
        description="Generate images using Luma AI image generation models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Provider selection
    parser.add_argument(
        '--provider',
        type=str,
        default="photon-flash-1",
        help='Image generation provider. Options: photon-1, photon-flash-1'
    )

    # Mode selection
    parser.add_argument(
        '--mode',
        type=str,
        default='text',
        choices=['text', 'img-ref', 'char-ref', 'style-ref', 'modify'],
        help='Generation mode'
    )

    # Prompt
    parser.add_argument(
        '-p', '--prompt',
        type=str,
        help='Text prompt'
    )

    # Unified Images Input (single or multiple)
    parser.add_argument(
        '--images',
        nargs="+",
        type=str,
        help="One or more image paths/URLs (used for img-ref, style-ref, modify)"
    )

    # Unified Weights Input (single or multiple)
    parser.add_argument(
        '--weights',
        nargs="+",
        type=float,
        default= None,
        required=False,
        help="One or more weights (must match number of --images)"
    )

    # Character Reference Args
    parser.add_argument(
        '--char_id',
        action='append',
        help='Identity key (identity0, identity1). Repeat for multiple identities.'
    )

    parser.add_argument(
        '--char_images',
        action='append',
        nargs="+",
        help='List of image URLs for each identity. Repeat in same order as --char_id.'
    )

    # Output directory
    parser.add_argument(
        '--output_dir',
        type=str,
        default="outputs",
        help="Folder to save generated images"
    )

    # Aspect Ratio
    parser.add_argument(
        '--aspect_ratio',
        type=str,
        required=False,
        default='16:9',
        choices=['1:1', '4:3', '3:4', '9:16', '16:9', '9:21', '21:9'],
        help="Aspect ratio Options are ('1:1', '4:3', '3:4', '9:16', '16:9', '9:21', '21:9')"
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

    auth_token = os.environ.get("LUMA_AI_API_KEY")
    if not auth_token:
        raise RuntimeError("Set LUMA_AI_API_KEY in environment.")

    character_ref = build_character_ref(args)

    # ------------- Argument Validation ------------------

    if args.mode == 'text':
        if not args.prompt:
            raise ValueError("--prompt is required for text mode")

    if args.mode in ['img-ref', 'style-ref']:
        if not args.images:
            raise ValueError(f"--images is required for {args.mode} mode")
    
    if args.mode == 'modify':
        if not args.images:
            raise ValueError(f" --images is required for {args.mode} mode")
        if len(args.images) != 1:
            raise ValueError(f"{args.mode} mode only accepts one image for modification")

    if args.mode == 'char-ref':
        if not character_ref:
            raise ValueError("Both --char-id and --char-images are required for char-ref mode")
        if not args.prompt:
            raise ValueError("--prompt is required for char-ref mode")

    # ------------- Initialize Adapter ------------------

    adapter = LumaAIAdapter(auth_token=auth_token)

    # ------------- Dispatch by Mode -------------------

    if args.mode == "text":
        images = adapter.generate_text_to_image(
            prompt=args.prompt,
            aspect_ratio=args.aspect_ratio,
            model=args.provider
        )

    elif args.mode == "img-ref":
        # If weights are not provided
        if not args.weights:
            weights = [0.85] * len(args.images)
        else:
            weights = args.weights
        
        if len(weights) != len(args.images):
            raise ValueError("--weights count must match --images count")
        
        # Build list of {"url": "value", "weight": value} for input
        image_ref = [
            {"url": im, "weight": w}
            for im, w in zip(args.images, weights)
        ]

        images = adapter.generate_with_image_reference(
            prompt=args.prompt,
            model=args.provider,
            aspect_ratio=args.aspect_ratio,
            image_ref=image_ref
        )

    elif args.mode == "style-ref":
        # If weights are not provided
        if not args.weights:
            weights = [0.85] * len(args.images)
        else:
            weights = args.weights
        
        if len(weights) != len(args.images):
            raise ValueError("--weights count must match --images count")
        
        # Build list of {"url": "value", "weight": "value"} for input
        style_ref = [
            {"url": im, "weight": w}
            for im, w in zip(args.images, weights)
        ]

        images = adapter.generate_with_style_reference(
            prompt=args.prompt,
            model=args.provider,
            aspect_ratio=args.aspect_ratio,
            style_ref=style_ref
        )

    elif args.mode == "modify":
        # If weight is not given
        if not args.weights:
            weight = 0.85
        else:
            weight = args.weights[0]      # Taking a single value bacuase a list of weights are provided

        images = adapter.generate_with_modify_image(
            prompt=args.prompt,
            model=args.provider,
            image=args.images[0],         # Taking a single image because a list of images are provided
            weight=weight,
            aspect_ratio=args.aspect_ratio,
        )

    elif args.mode == "char-ref":
        images = adapter.generate_with_character_reference(
            prompt=args.prompt,
            model=args.provider,
            character_ref=character_ref,
            aspect_ratio=args.aspect_ratio,
        )

    else:
        raise ValueError("Unknown mode")

    # --------------------- SAVE RESULTS ---------------------
    for idx, img in enumerate(images):
        save_path = output_dir / f"generated_{idx}.png"
        img.save(save_path)
        print(f"Saved {save_path}")

    print(f"\n✓ Generated {len(images)} image(s)")
    return 0


if __name__ == "__main__":
    main()
