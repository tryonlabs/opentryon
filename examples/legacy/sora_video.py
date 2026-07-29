"""
Sora Video Generation CLI

Command-line interface for generating videos using OpenAI's Sora models.

This script provides easy access to Sora 2 and Sora 2 Pro for:
- Text-to-video generation
- Image-to-video generation (animate static images)
- Both synchronous (blocking) and asynchronous (non-blocking) modes

Examples:
    Text-to-video (synchronous):
        python sora_video.py --prompt "A fashion model walking down a runway" \\
                             --duration 8 --resolution 1920x1080 --output runway.mp4

    Text-to-video (async):
        python sora_video.py --prompt "Fabric flowing in slow motion" \\
                             --duration 4 --async --output fabric.mp4

    Image-to-video:
        python sora_video.py --image model.jpg \\
                             --prompt "The model turns and smiles" \\
                             --duration 4 --output animated.mp4

    Using Sora 2 Pro:
        python sora_video.py --prompt "Cinematic fashion shoot" \\
                             --model sora-2-pro --duration 12 --output cinematic.mp4

Requirements:
    - OpenAI API key (set OPENAI_API_KEY environment variable or use --api-key)
    - openai Python package (pip install openai)
"""

from dotenv import load_dotenv
load_dotenv()

import argparse
import os
import sys
from pathlib import Path


def build_parser():
    """Build the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        description="Generate videos using OpenAI's Sora models (Sora 2 and Sora 2 Pro)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic text-to-video
  python sora_video.py --prompt "A person walking in the rain" --output walk.mp4

  # High-quality with Sora 2 Pro
  python sora_video.py --prompt "Fashion runway show" --model sora-2-pro \\
                       --duration 12 --resolution 1920x1080 --output runway.mp4

  # Animate a static image
  python sora_video.py --image photo.jpg --prompt "The person waves" \\
                       --duration 4 --output animated.mp4

  # Asynchronous generation (non-blocking)
  python sora_video.py --prompt "Fabric in slow motion" --async --output fabric.mp4

For more information, visit: https://platform.openai.com/docs/guides/video-generation
        """
    )

    # Required arguments
    parser.add_argument(
        '--prompt',
        type=str,
        required=True,
        help="Text description of the video to generate or animation instructions"
    )

    parser.add_argument(
        '--output',
        '-o',
        type=str,
        required=True,
        help="Output video file path (e.g., output.mp4)"
    )

    # Optional: Image input for image-to-video
    parser.add_argument(
        '--image',
        '-i',
        type=str,
        default=None,
        help="Input image path for image-to-video generation (optional)"
    )

    # Model selection
    parser.add_argument(
        '--model',
        type=str,
        default="sora-2",
        choices=['sora-2', 'sora-2-pro'],
        help="Sora model version. Default: sora-2 (fast). Use sora-2-pro for higher quality."
    )

    # Video parameters
    parser.add_argument(
        '--duration',
        '-d',
        type=int,
        default=4,
        choices=[4, 8, 12],
        help="Video duration in seconds. Options: 4, 8, 12. Default: 4"
    )

    parser.add_argument(
        '--resolution',
        '-r',
        type=str,
        default="1280x720",
        choices=['720x1280', '1280x720', '1024x1792', '1792x1024', '1920x1080', '1080x1920'],
        help="Video resolution. Default: 1280x720 (16:9 horizontal)"
    )

    # Wait mode
    parser.add_argument(
        '--async',
        dest='async_mode',
        action='store_true',
        help="Use asynchronous mode (non-blocking, returns immediately)"
    )

    # API configuration
    parser.add_argument(
        '--api-key',
        type=str,
        default=None,
        help="OpenAI API key (optional, reads from OPENAI_API_KEY env var if not provided)"
    )

    parser.add_argument(
        '--polling-interval',
        type=int,
        default=5,
        help="Seconds between status checks when polling. Default: 5"
    )

    parser.add_argument(
        '--max-wait-time',
        type=int,
        default=300,
        help="Maximum wait time in seconds. Default: 300 (5 minutes)"
    )

    # Verbosity
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help="Enable verbose output"
    )

    return parser


def main():
    """Main CLI entry point."""
    parser = build_parser()
    args = parser.parse_args()

    # Import here to avoid loading heavy dependencies if just showing help
    try:
        from tryon.api.openAI.video_adapter import SoraVideoAdapter
    except ImportError as e:
        print(f"Error: Failed to import SoraVideoAdapter: {e}", file=sys.stderr)
        print("Please ensure OpenAI SDK is installed: pip install openai", file=sys.stderr)
        sys.exit(1)

    # Get API key
    api_key = args.api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OpenAI API key not found.", file=sys.stderr)
        print("Please provide --api-key or set OPENAI_API_KEY environment variable.", file=sys.stderr)
        sys.exit(1)

    # Initialize adapter
    if args.verbose:
        print(f"Initializing Sora adapter with model: {args.model}")

    try:
        adapter = SoraVideoAdapter(
            api_key=api_key,
            model_version=args.model,
            polling_interval=args.polling_interval,
            max_polling_time=args.max_wait_time
        )
    except Exception as e:
        print(f"Error: Failed to initialize adapter: {e}", file=sys.stderr)
        sys.exit(1)

    # Validate output path
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Generate video
    try:
        if args.image:
            # Image-to-video
            if args.verbose:
                print(f"Generating video from image: {args.image}")
                print(f"Prompt: {args.prompt}")
                print(f"Duration: {args.duration}s, Resolution: {args.resolution}")

            if args.async_mode:
                # Asynchronous mode
                def on_complete(video_bytes):
                    with open(output_path, "wb") as f:
                        f.write(video_bytes)
                    print(f"✅ Video saved to: {output_path}")

                def on_error(error):
                    print(f"❌ Video generation failed: {error}", file=sys.stderr)
                    sys.exit(1)

                def on_progress(status):
                    if args.verbose:
                        progress = status.get('progress', 'processing')
                        print(f"Status: {status['status']} - {progress}")

                video_id = adapter.generate_image_to_video_async(
                    image=args.image,
                    prompt=args.prompt,
                    duration=args.duration,
                    resolution=args.resolution,
                    on_complete=on_complete,
                    on_error=on_error,
                    on_progress=on_progress if args.verbose else None
                )

                print(f"🎬 Video generation started (ID: {video_id})")
                print("Running in async mode. The script will continue monitoring in the background...")
                print("Press Ctrl+C to exit (video will continue generating)")

                # Keep script alive
                import time
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\nExiting... (video generation continues on server)")
                    sys.exit(0)

            else:
                # Synchronous mode
                print("🎬 Generating video... (this may take a few minutes)")
                video_bytes = adapter.generate_image_to_video(
                    image=args.image,
                    prompt=args.prompt,
                    duration=args.duration,
                    resolution=args.resolution,
                    wait=True
                )

                with open(output_path, "wb") as f:
                    f.write(video_bytes)

                print(f"✅ Video saved to: {output_path}")

        else:
            # Text-to-video
            if args.verbose:
                print(f"Generating video from text prompt")
                print(f"Prompt: {args.prompt}")
                print(f"Duration: {args.duration}s, Resolution: {args.resolution}")

            if args.async_mode:
                # Asynchronous mode
                def on_complete(video_bytes):
                    with open(output_path, "wb") as f:
                        f.write(video_bytes)
                    print(f"✅ Video saved to: {output_path}")

                def on_error(error):
                    print(f"❌ Video generation failed: {error}", file=sys.stderr)
                    sys.exit(1)

                def on_progress(status):
                    if args.verbose:
                        progress = status.get('progress', 'processing')
                        print(f"Status: {status['status']} - {progress}")

                video_id = adapter.generate_text_to_video_async(
                    prompt=args.prompt,
                    duration=args.duration,
                    resolution=args.resolution,
                    on_complete=on_complete,
                    on_error=on_error,
                    on_progress=on_progress if args.verbose else None
                )

                print(f"🎬 Video generation started (ID: {video_id})")
                print("Running in async mode. The script will continue monitoring in the background...")
                print("Press Ctrl+C to exit (video will continue generating)")

                # Keep script alive
                import time
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\nExiting... (video generation continues on server)")
                    sys.exit(0)

            else:
                # Synchronous mode
                print("🎬 Generating video... (this may take a few minutes)")
                video_bytes = adapter.generate_text_to_video(
                    prompt=args.prompt,
                    duration=args.duration,
                    resolution=args.resolution,
                    wait=True
                )

                with open(output_path, "wb") as f:
                    f.write(video_bytes)

                print(f"✅ Video saved to: {output_path}")

    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

