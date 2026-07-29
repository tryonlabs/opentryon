from dotenv import load_dotenv
load_dotenv()

import os
import time
import argparse
from pathlib import Path

from tryon.api.veo import VeoAdapter


# -------------------------------------------------------
# CLI ARGUMENT PARSER
# -------------------------------------------------------
def build_parser():
    parser = argparse.ArgumentParser(
        description="Generate Videos using Google Veo Video Generation API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Provider selection
    parser.add_argument(
        "--provider",
        type=str,
        default="veo-3.1-generate-preview",
        choices=[
            "veo-3.1-generate-preview",
            "veo-3.1-fast-generate-preview",
            "veo-3.0-generate-001",
            "veo-3.0-fast-generate-001",
        ],
        help="Veo model to use"
    )

    # Mode
    parser.add_argument(
        "--mode",
        type=str,
        default="text",
        choices=["text", "image", "reference", "frames"],
        help="Generation Mode: "
             "'text' = text-to-video, "
             "'image' = image-to-video, "
             "'reference' = reference image guided video, "
             "'frames' = first+last frame guided video"
    )

    # Prompt
    parser.add_argument(
        "-p", "--prompt",
        type=str,
        help="Prompt (required for all modes)"
    )

    # Duration
    parser.add_argument(
        "--duration",
        type=str,
        default="8",
        choices=["4", "6", "8"],
        help="Video duration (seconds)"
    )

    # Aspect Ratio
    parser.add_argument(
        "--aspect",
        type=str,
        default="16:9",
        choices=["16:9", "9:16"],
        help="Aspect Ratio"
    )

    # Resolution
    parser.add_argument(
        "--resolution",
        type=str,
        default="720p",
        choices=["720p", "1080p"],
        help="Resolution"
    )

    # Negative Prompt
    parser.add_argument(
        "--negative_prompt",
        type=str,
        default=None,
        help="Optional negative prompt"
    )

    # Images (Single / Multiple)
    parser.add_argument(
        "--images",
        type=str,
        nargs="+",
        help="Images for video generation"
    )

    # Start Image
    parser.add_argument(
        "--start_image",
        type=str,
        help="Start image for frames mode"
    )

    # End Image
    parser.add_argument(
        "--end_image",
        type=str,
        help="End image for frames mode"
    )

    # Output Directory
    parser.add_argument(
        "--output_dir",
        type=str,
        default="outputs",
        help="Folder to save generated videos"
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

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY must be set in environment")

    # -------- Validation --------
    if not args.prompt:
        raise ValueError("--prompt is required for all modes")

    # Validate resolution for Veo 3.1
    if args.provider in {"veo-3.1-generate-preview", "veo-3.1-fast-generate-preview"}:
        if args.resolution == "1080p" and args.duration != "8":
            raise ValueError("1080p supports ONLY 8s duration in Veo 3.1")

    # ---------- Mode: TEXT ----------
    if args.mode == "text":
        pass  # only prompt required


    # ---------- Mode: IMAGE ----------
    if args.mode == "image":
        if not args.images:
            raise ValueError("image mode requires --images")
        
        if len(args.images) != 1:
            raise ValueError("image mode requires exactly ONE image")

        if not (args.images[0].startswith("http") or os.path.exists(args.images[0])):
            raise ValueError(f"Image not found: {args.images[0]}")


    # ---------- Mode: REFERENCE ----------
    if args.mode == "reference":
        if args.provider in {"veo-3.0-generate-001", "veo-3.0-fast-generate-001"}:
            raise ValueError("Reference images supported ONLY in Veo 3.1 models")

        if not args.images:
            raise ValueError("reference mode requires --images")

        if len(args.images) > 3:
            raise ValueError("Maximum 3 reference images supported")

        if args.duration != "8":
            raise ValueError("Reference video requires duration = 8s")

        if args.aspect != "16:9":
            raise ValueError("Reference videos only support 16:9")

        for r in args.images:
            if not (r.startswith("http") or os.path.exists(r)):
                raise ValueError(f"Reference image not found: {r}")


    # ---------- Mode: FRAMES ----------
    if args.mode == "frames":
        if args.provider in {"veo-3.0-generate-001", "veo-3.0-fast-generate-001"}:
            raise ValueError("Frames mode supported ONLY in Veo 3.1 models")
        
        if args.images:
            raise ValueError("--images is not supported for frames mode. Use --start_image and --end_image")

        if args.duration != "8":
            raise ValueError("Frames mode requires duration = 8s")

        if not args.start_image or not args.end_image:
            raise ValueError("frames mode requires BOTH --start_image AND --end_image")

        if not (args.start_image.startswith("http") or os.path.exists(args.start_image)):
            raise ValueError(f"Start image not found: {args.start_image}")

        if not (args.end_image.startswith("http") or os.path.exists(args.end_image)):
            raise ValueError(f"End image not found: {args.end_image}")


    # -------- Initialize Adapter --------
    adapter = VeoAdapter(api_key=api_key)

    # -------- Dispatch --------
    if args.mode == "text":
        video_bytes = adapter.generate_text_to_video(
            prompt=args.prompt,
            duration_seconds=args.duration,
            aspect_ratio=args.aspect,
            resolution=args.resolution,
            model=args.provider,
            negative_prompt=args.negative_prompt
        )

    elif args.mode == "image":
        video_bytes = adapter.generate_image_to_video(
            image=args.images[0],
            prompt=args.prompt,
            duration_seconds=args.duration,
            aspect_ratio=args.aspect,
            resolution=args.resolution,
            model=args.provider,
            negative_prompt=args.negative_prompt
        )

    elif args.mode == "reference":
        video_bytes = adapter.generate_video_with_references(
            prompt=args.prompt,
            reference_images=args.images,
            duration_seconds=args.duration,
            aspect_ratio=args.aspect,
            resolution=args.resolution,
            model=args.provider,
            negative_prompt=args.negative_prompt
        )

    elif args.mode == "frames":
        video_bytes = adapter.generate_video_with_frames(
            prompt=args.prompt,
            first_image=args.start_image,
            last_image=args.end_image,
            duration_seconds=args.duration,
            aspect_ratio=args.aspect,
            resolution=args.resolution,
            model=args.provider,
            negative_prompt=args.negative_prompt
        )

    else:
        raise ValueError("Invalid mode")

    # -------- Save Output --------
    name = f"{args.mode}_{int(time.time())}.mp4"
    path = output_dir / name
    path.write_bytes(video_bytes)

    print(f"\n✓ Saved: {path}\n")
    return 0

if __name__ == "__main__":
    main()
