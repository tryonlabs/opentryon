from dotenv import load_dotenv
load_dotenv()

import os
import time
import argparse
from pathlib import Path
from tryon.api.lumaAI import LumaAIVideoAdapter


# -------------------------------------------------------
# CLI ARGUMENT PARSER
# -------------------------------------------------------
def build_parser():
    parser = argparse.ArgumentParser(
        description="Generate Videos using Luma AI Video generation model (Dream Machine)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Provider selection
    parser.add_argument(
        '--provider',
        type=str,
        default="ray-2",
        required=False,
        choices=['ray-1-6', 'ray-2', 'ray-flash-2'],
        help="Video generation provider. Options: 'ray-1-6', 'ray-2', 'ray-flash-2'"
    )

    # prompt, loop, resolution, duration, aspect_ratio, start_image, end_image

    # Prompt
    parser.add_argument(
        '-p', '--prompt',
        type=str,
        help="Text Prompt for video generation"
    )

    # Mode
    parser.add_argument(
        '--mode',
        type=str,
        default='text_video',
        choices=['text_video', 'image_video'],
        help="Generation Mode"
    )

    # Resolution
    parser.add_argument(
        '--resolution',
        type=str,
        default='540p',
        choices=['540p', '720p', '1080p', '4k'],
        help="Resolution of the output video. Options are: '540p', '720p', '1080p', '4k'"
    )

    # Duration
    parser.add_argument(
        '--duration',
        type=str,
        default='5s',
        choices=['5s', '9s', '10s'],
        help="Duration of the output video in seconds. Options are: '5s', '9s', '10s'"
    )

    # Aspect Ratio
    parser.add_argument(
        '--aspect',
        type=str,
        default="16:9",
        choices=['1:1', '4:3', '3:4', '9:16', '16:9', '9:21', '21:9'],
        help="Aspect Ratio of generated video. Options are: ('1:1', '4:3', '3:4', '9:16', '16:9', '9:21', '21:9')"
    )

    # loop
    parser.add_argument(
        '--loop',
        action="store_true",
        help="Loop the output (only valid for single-image mode)"
    )

    # Start Image
    parser.add_argument(
        '--start_image',
        type=str,
        help="One image path/URL (used as start image for image to video generation)"
    )

    # End Image
    parser.add_argument(
        '--end_image',
        type=str,
        help="One image path/URL (used as end image for image to video generation)"
    )

    # Output Directory
    parser.add_argument(
        '--output_dir',
        type=str,
        default="outputs",
        help="Folder to save generated videos"
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
        raise ValueError("set LUMA_AI_API_KEY in environment.")
    
    # ---------- Argument Validation ----------

    # Text to Video Mode
    if args.mode == "text_video":
        if not args.prompt:
            raise ValueError(f"--prompt is required for {args.mode} mode")
    

    # Check the Image Paths
    if args.start_image and not args.start_image.startswith("http") and not os.path.exists(args.start_image):
        raise ValueError(f"Start image path not found: {args.start_image}")
    
    if args.end_image and not args.end_image.startswith("http") and not os.path.exists(args.end_image):
        raise ValueError(f"End image path not found: {args.end_image}")
    
    
    # Image to Video Mode
    if args.mode == "image_video":
        if not args.start_image and not args.end_image:
            raise ValueError("image_video mode requires at least --start_image OR --end_image")
        
        if args.loop:
            if args.end_image:
                raise ValueError("Loop is only supported with a single start_image")
            if not args.start_image:
                raise ValueError("Loop requires --start_image")
            

    # ---------- Initialize Adapter ----------

    adapter = LumaAIVideoAdapter(auth_token=auth_token)

    # ---------- Dispatch by Mode ----------

    if args.mode == "text_video":
        video_bytes = adapter.generate_text_to_video(
            prompt=args.prompt,
            loop=args.loop,
            resolution=args.resolution,
            duration=args.duration,
            model=args.provider,
            aspect_ratio=args.aspect
        )
    
    elif args.mode == "image_video":
        video_bytes = adapter.generate_image_to_video(
            prompt=args.prompt if args.prompt else None,
            start_image=args.start_image,
            end_image=args.end_image,
            loop=args.loop,
            resolution=args.resolution,
            duration=args.duration,
            model=args.provider,
            aspect_ratio=args.aspect
        )
    
    else:
        raise ValueError("Unknown mode")
    
    # Save output with timestamp
    name = f"{args.mode}_{int(time.time())}.mp4"
    output_path = output_dir / name
    output_path.write_bytes(video_bytes)

    print(f"\n✓ Saved: {output_path}\n")
    return 0

if __name__ == "__main__":
    main()

    

    