import os
from pathlib import Path
from tryon.api.lumaAI import LumaAIVideoAdapter

from dotenv import load_dotenv
load_dotenv()

adapter = LumaAIVideoAdapter()


def save_video(name: str, video_bytes: bytes):
    """Save video bytes to disk."""
    Path("outputs").mkdir(exist_ok=True)
    path = Path("outputs") / f"{name}.mp4"
    with open(path, "wb") as f:
        f.write(video_bytes)
    print(f"[SAVED] {path.absolute()}")
    return path


def test_text_to_video(adapter):
    print("\n=== TEST: TEXT → VIDEO ===")
    video_bytes = adapter.generate_text_to_video(
        prompt="a neon city full of cars on the road",
        resolution="540p",
        duration="5s",
        model="ray-2",
    )
    save_video("text_to_video", video_bytes)


def test_image_to_video(adapter, start_image: str, end_image: str):
    print("\n=== TEST: IMAGE → VIDEO ===")
    video_bytes = adapter.generate_image_to_video(
        prompt="Man riding a bike",
        start_image=start_image,
        end_image=end_image,
        resolution="540p",
        duration="5s",
        model="ray-2",
    )
    save_video("image_to_video", video_bytes)


if __name__ == "__main__":
    print("=== LUMA VIDEO GENERATION TEST ===")

    START_IMAGE = "Image for start keyframe"
    END_IMAGE = "Image for end keyframe"

    # Run tests
    test_text_to_video(adapter)
    test_image_to_video(adapter, START_IMAGE, END_IMAGE)

    print("\n=== ALL TESTS COMPLETED ===")
