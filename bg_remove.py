from dotenv import load_dotenv
load_dotenv()

import argparse
from pathlib import Path
from tryon.api.ben2.adapter import BEN2BackgroundRemoverAdapter


# -------------------------------------------------------
# CLI ARG PARSER
# -------------------------------------------------------
def build_parser():
    parser = argparse.ArgumentParser(
        description="Background removal using BEN2 model",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Mode
    parser.add_argument(
        '--mode',
        type=str,
        default='single',
        choices=['single', 'batch'],
        help='Select single image processing or batch processing'
    )

    # Single image
    parser.add_argument(
        '--image',
        type=str,
        help='Path/URL of a single image'
    )

    # Batch images
    parser.add_argument(
        '--images',
        nargs="+",
        type=str,
        help="Multiple image paths/URLs for batch mode"
    )

    # Output directory
    parser.add_argument(
        '--output_dir',
        type=str,
        default="ben2_outputs",
        help="Folder to save output images"
    )

    # Refine toggle
    parser.add_argument(
        '--refine',
        action='store_true',
        help="Enable refined foreground enhancement"
    )

    return parser


# -------------------------------------------------------
# MAIN
# -------------------------------------------------------
def main():
    parser = build_parser()
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    adapter = BEN2BackgroundRemoverAdapter()

    # ---------------- SINGLE MODE ----------------
    if args.mode == "single":
        if not args.image:
            raise ValueError("--image is required in single mode")

        results = adapter.remove_background(
            image=args.image,
            refine=args.refine
        )

        save_path = output_dir / "ben2_output.png"
        results[0].save(save_path)
        print(f"Saved: {save_path}")
        return

    # ---------------- BATCH MODE ----------------
    if args.mode == "batch":
        if not args.images or len(args.images) == 0:
            raise ValueError("--images is required in batch mode")

        results = adapter.remove_background_batch(
            images=args.images,
            refine=args.refine
        )

        for idx, img in enumerate(results):
            save_path = output_dir / f"ben2_batch_output_{idx+1}.png"
            img.save(save_path)
            print(f"Saved: {save_path}")

        print(f"\n✓ Processed {len(results)} image(s)")
        return


if __name__ == "__main__":
    main()
