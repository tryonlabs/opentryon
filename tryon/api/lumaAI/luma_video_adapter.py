"""
Luma AI Dream Machine Video Generation API Adapter

Adapter for Luma AI’s Dream Machine models, supporting text-to-video,
image-to-video, and controlled keyframe-based generation.

Supported Models:
- ray-flash-2 : Ray 2 Flash (fast, lower latency)
- ray-2       : Ray 2 (high-quality, standard model)
- ray-1-6     : Ray 1.6 (previous-generation model)

Keyframe Rules:
- Image-based generation supports *exactly two* keyframes.
- Only frame0 and frame1 are allowed.
- You cannot supply more than two images.

Capabilities:
- Text-to-Video: Generate videos from a text prompt.
- Image-to-Video: Use a single image as the start frame.
- Start + End Frame Generation: image → video → image transitions.

Reference: https://docs.lumalabs.ai/docs/video-generation

Examples:

    Text-to-Video:
        >>> adapter.generate_text_to_video(
        ...     prompt="A cyberpunk drone flying through neon streets"
        ... )

    Image-to-Video (single start frame):
        >>> adapter.generate_image_to_video(
        ...     start_image="start.png",
        ...     prompt="Continue motion into a windy canyon"
        ... )

"""

import os
import io
from typing import Optional, Union
from PIL import Image
import requests
import time

try:
    from lumaai import LumaAI
    LUMA_AI_AVAILABLE = True
except ImportError:
    LUMA_AI_AVAILABLE = False
    LumaAI = None


# Supported aspect ratios for Luma AI Video
LUMA_AI_ASPECT_RATIO = {
    "1:1": {"resolution": "1024x1024"},
    "3:4": {"resolution": "864x1152"},
    "4:3": {"resolution": "1152x864"},
    "9:16": {"resolution": "720x1280"},
    "16:9": {"resolution": "1280x720"},
    "9:21": {"resolution": "656x1552"},
    "21:9": {"resolution": "1552x656"},
}


class LumaAIVideoAdapter:
    def __init__(self, auth_token: Optional[str] = None):
        """
        Initialize the Luma AI Video adapter.

        Args:
            auth_token: Luma AI API key. Defaults to LUMA_AI_API_KEY environment variable.
                If not provided via parameter or environment variable, raises ValueError.
        
        Raises:
            ValueError: If API key is not provided.
            ImportError: If lumaai is not available.

        Example:
            >>> # Using environment variable
            >>> import os
            >>> os.environ['LUMA_AI_API_KEY'] = 'your_api_key'
            >>> adapter = LumaAIAdapter()
            
            >>> # Using parameter
            >>> adapter = LumaAIAdapter(auth_token="your_api_key")    
        """

        if not LUMA_AI_AVAILABLE:
            raise ImportError(
                "Luma AI library is not available. " \
                "Please install it with 'pip install lumaai'."
            )
        
        self.auth_token = auth_token or os.getenv("LUMA_AI_API_KEY")
        if not self.auth_token:
            raise ValueError("Luma AI API key must be provided either as a parameter or through the LUMA_AI_API_KEY environment variable.")
        
        self.client = LumaAI(auth_token=self.auth_token)
    

    def _prepare_image_input(self, image_input: Union[str, io.BytesIO, Image.Image]) -> str:
        """
        LumaAI requires a CDN URL. No local files, no base64, no bytes, no PIL Images.
        This function normalizes input into a URL.

        Args:
            image_input: Image input in one of the following formats:
                       - File path (str): Path to local image file
                       - URL (str): HTTP/HTTPS URL to image
                       - Base64 string (str): Base64-encoded image data
                       - File-like object (io.BytesIO): BytesIO or similar object
                       - PIL Image: PIL Image object

        Returns:
            str: CDN URL pointing to the uploaded image
        """
        # Case 1: Already a URL
        if isinstance(image_input, str) and image_input.startswith(("http://", "https://")):
            return image_input

        # Case 2: Local file path
        if isinstance(image_input, str) and os.path.exists(image_input):
            return self._upload_to_cdn(open(image_input, "rb"))

        # Case 3: File-like object (BytesIO)
        if hasattr(image_input, "read"):
            image_file = image_input
            image_file.seek(0)
            return self._upload_to_cdn(image_file)

        # Case 4: PIL Image
        if isinstance(image_input, Image.Image):
            buffer = io.BytesIO()
            image_input.save(buffer, format="PNG")
            buffer.seek(0)
            return self._upload_to_cdn(buffer)

        raise ValueError(
            "Invalid image input: must be a file path, URL, PIL Image, file-like object, or base64 string."
        )

    def _upload_to_cdn(self, file_obj: io.BytesIO) -> str:
        """
        Uploads file_obj to your CDN and returns a public URL.
        """
        raise NotImplementedError("CDN upload must be implemented before using local images.")
    
    def generate_text_to_video(
        self,
        prompt: str,
        loop: bool = False,
        resolution: str = "540p",
        duration: str = "5s",
        model: str = "ray-2",
        aspect_ratio: Optional[str] = None,
    ) -> bytes:
        
        """
        Generate a video from a text prompt using Luma AI (Dream Machine).

        Args:
            prompt: The text prompt used for video generation.
            loop: Whether to generate a loop-friendly clip.
            resolution: Output resolution ("540p", "720p", "1080p", "4k").
            duration: Duration of the generated video (e.g., "5s", "9s", "10s").
            model: Luma AI model ("ray-2", "ray-flash-2", "ray-1-6").
            aspect_ratio: Optional aspect ratio ("1:1", "16:9", etc.).

        Returns:
            Raw MP4 video bytes.

        Example:
            >>> adapter = LumaAIAdapter()
            >>> video_bytes = adapter.generate_text_to_video(
            ...     prompt="A futuristic robot walking through neon streets",
            ...     resolution="720p",
            ...     duration="5s"
            ... )
            >>> with open("output.mp4", "wb") as f:
            ...     f.write(video_bytes)
        """
        if not prompt:
            raise ValueError("Prompt is required for video generation.")

        if len(prompt) < 3 or len(prompt) > 5000:
            raise ValueError("Prompt must be between 3 and 5000 characters.")

        if aspect_ratio and aspect_ratio not in LUMA_AI_ASPECT_RATIO:
            raise ValueError(
                f"Invalid aspect ratio '{aspect_ratio}'. "
                f"Valid options: {', '.join(LUMA_AI_ASPECT_RATIO.keys())}"
            )

        generation = self.client.generations.create(
            prompt=prompt,
            model=model,
            resolution=resolution,
            duration=duration,
            loop=loop,
            aspect_ratio=aspect_ratio,
        )

        while True:
            gen = self.client.generations.get(id=generation.id)

            if gen.state == "completed":
                break
            if gen.state == "failed":
                raise RuntimeError(f"Generation failed: {gen.failure_reason}")

            time.sleep(1)

        video_url = gen.assets.video
        if not video_url:
            raise RuntimeError("No video returned by Luma AI.")

        response = requests.get(video_url, stream=True)
        if response.status_code != 200:
            raise RuntimeError("Failed to download generated video.")

        return response.content


    def generate_image_to_video(
        self,
        start_image: Optional[Union[str, io.BytesIO, Image.Image]] = None,
        end_image: Optional[Union[str, io.BytesIO, Image.Image]] = None,
        prompt: Optional[str] = None,
        loop: bool = False,
        resolution: str = "540p",
        duration: str = "5s",
        model: str = "ray-2",
        aspect_ratio: Optional[str] = None,
    ) -> bytes:
        
        """
        Generate a video using one or two images with optional prompt guidance.

        Supports:
            - Single start image → motion clip
            - Two images → interpolation
            - Looping clips (start-only scenarios)

        Args:
            start_image: First keyframe (path, BytesIO, or PIL Image).
            end_image: Optional second keyframe for interpolation.
            prompt: Optional text prompt.
            loop: Only valid when end_image is NOT provided.
            resolution: Output resolution.
            duration: "5s", "9s", "10s".
            model: Luma AI model name.
            aspect_ratio: Optional aspect ratio key.

        Returns:
            Raw MP4 video bytes.

        Example (interpolation):
            >>> video_bytes = adapter.generate_image_to_video(
            ...     start_image="frame0.png",
            ...     end_image="frame1.png",
            ...     prompt="Smooth transition between two poses"
            ... )
            >>> with open("interpolated.mp4", "wb") as f:
            ...     f.write(video_bytes)

        Example (motion from single frame):
            >>> video_bytes = adapter.generate_image_to_video(
            ...     start_image="portrait.jpg",
            ...     prompt="Slow push-in cinematic motion"
            ... )
            >>> with open("motion.mp4", "wb") as f:
            ...     f.write(video_bytes)
        """


        if not start_image and not end_image:
            raise ValueError("At least one of start_image or end_image is required.")

        if end_image and loop:
            raise ValueError("Looping is only supported when NO end_image is provided.")

        if prompt and (len(prompt) < 3 or len(prompt) > 5000):
            raise ValueError("Prompt must be 3 – 5000 characters.")

        if aspect_ratio and aspect_ratio not in LUMA_AI_ASPECT_RATIO:
            raise ValueError(
                f"Invalid aspect ratio '{aspect_ratio}'. "
                f"Valid options: {', '.join(LUMA_AI_ASPECT_RATIO.keys())}"
            )

        keyframes = {}

        if start_image:
            start_url = self._prepare_image_input(start_image)
            keyframes["frame0"] = {"type": "image", "url": start_url}

        if end_image:
            end_url = self._prepare_image_input(end_image)
            keyframes["frame1"] = {"type": "image", "url": end_url}

        generation = self.client.generations.create(
            prompt=prompt,
            model=model,
            resolution=resolution,
            duration=duration,
            loop=loop,
            aspect_ratio=aspect_ratio,
            keyframes=keyframes,
        )

        while True:
            gen = self.client.generations.get(id=generation.id)

            if gen.state == "completed":
                break
            if gen.state == "failed":
                raise RuntimeError(f"Generation failed: {gen.failure_reason}")

            time.sleep(1)

        video_url = gen.assets.video
        if not video_url:
            raise RuntimeError("No video returned by Luma AI.")

        response = requests.get(video_url, stream=True)
        if response.status_code != 200:
            raise RuntimeError("Failed to download generated video.")

        return response.content
