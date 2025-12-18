"""
Sora (OpenAI Video Generation) API Adapter

Adapter for OpenAI's Sora video generation models (Sora 2 and Sora 2 Pro).

These models support high-quality video generation from text prompts and optional
reference images. This adapter provides a clean, unified interface for the following workflows:

- Text-to-Video: Generate videos from text descriptions
- Text+Image-to-Video: Generate videos from text and a reference image
- Multiple wait strategies: Polling (sync) and callback-based (async)
- Flexible output control: Duration, resolution, quality, and frame rate

The adapter can return video bytes directly or provide status tracking for
long-running video generation tasks.

Reference:
https://platform.openai.com/docs/guides/video-generation

Models:
- Sora 2 (sora-2): Fast, high-quality video generation (recommended for most use cases)
- Sora 2 Pro (sora-2-pro): Enhanced quality, better temporal consistency, superior prompt understanding

Examples:
    Text-to-video with latest model:
        >>> from tryon.api.openAI.video_adapter import SoraVideoAdapter
        >>> adapter = SoraVideoAdapter()  # Uses sora-2 by default
        >>> video_bytes = adapter.generate_text_to_video(
        ...     prompt="A fashion model walking down a runway wearing an elegant evening gown",
        ...     duration=4,
        ...     resolution="1280x720"
        ... )
        >>> with open("result.mp4", "wb") as f:
        ...     f.write(video_bytes)

    Using Sora 2 Pro for higher quality:
        >>> adapter = SoraVideoAdapter(model_version="sora-2-pro")
        >>> video_bytes = adapter.generate_text_to_video(
        ...     prompt="A cinematic shot of fabric flowing in slow motion",
        ...     duration=8,
        ...     resolution="1920x1080"
        ... )

    Text+Image-to-video:
        >>> adapter = SoraVideoAdapter()
        >>> video_bytes = adapter.generate_image_to_video(
        ...     image="reference.jpg",
        ...     prompt="Animate this image with the model turning and smiling",
        ...     duration=4
        ... )
        >>> with open("animated.mp4", "wb") as f:
        ...     f.write(video_bytes)

    Async generation with callback:
        >>> def on_complete(video_bytes):
        ...     print("Video ready!")
        ...     with open("result.mp4", "wb") as f:
        ...         f.write(video_bytes)
        >>> 
        >>> def on_error(error):
        ...     print(f"Generation failed: {error}")
        >>> 
        >>> adapter.generate_text_to_video_async(
        ...     prompt="A person trying on different outfits",
        ...     duration=8,
        ...     on_complete=on_complete,
        ...     on_error=on_error
        ... )
"""

import io
import os
import time
from typing import Optional, Union, Callable, Dict, Any
from PIL import Image

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None

# Valid configuration options
VALID_MODELS = {"sora-2", "sora-2-pro"}

# Model-specific supported resolutions
MODEL_RESOLUTIONS = {
    "sora-2": {
        "720x1280",   # Vertical (9:16)
        "1280x720",   # Horizontal (16:9)
    },
    "sora-2-pro": {
        "720x1280",   # Vertical (9:16)
        "1280x720",   # Horizontal (16:9)
        "1024x1792",  # Tall vertical
        "1792x1024",  # Wide horizontal
    }
}

# All supported resolutions (union of all models)
VALID_RESOLUTIONS = set().union(*MODEL_RESOLUTIONS.values())

VALID_DURATIONS = {4, 8, 12}  # seconds


class SoraVideoAdapter:
    """
    Adapter for OpenAI Sora Video Generation API (supports Sora 2 and Sora 2 Pro).
    
    Args:
        api_key (str, optional): OpenAI API key. If not provided, reads from OPENAI_API_KEY environment variable.
        model_version (str, optional): Model version to use. Options: "sora-2", "sora-2-pro". 
                                       Defaults to "sora-2" (fast and high-quality).
        polling_interval (int, optional): Seconds to wait between status checks when polling. Defaults to 5.
        max_polling_time (int, optional): Maximum time (seconds) to wait for video generation. Defaults to 300 (5 minutes).
    
    Examples:
        >>> # Use default model (Sora 2)
        >>> adapter = SoraVideoAdapter()
        
        >>> # Use Sora 2 Pro for higher quality
        >>> adapter = SoraVideoAdapter(model_version="sora-2-pro")
        
        >>> # With explicit API key
        >>> adapter = SoraVideoAdapter(api_key="sk-...", model_version="sora-2")
    """

    def __init__(
        self, 
        api_key: Optional[str] = None, 
        model_version: str = "sora-2",
        polling_interval: int = 5,
        max_polling_time: int = 300
    ):
        
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "OpenAI SDK is not available. "
                "Please install it with 'pip install openai'."
            )
        
        if model_version not in VALID_MODELS:
            raise ValueError(
                f"Invalid model_version: {model_version}. "
                f"Supported models: {VALID_MODELS}"
            )
        
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key must be provided either as a parameter "
                "or through the OPENAI_API_KEY environment variable."
            )
        
        self.model_version = model_version
        self.polling_interval = polling_interval
        self.max_polling_time = max_polling_time
        self.client = OpenAI(api_key=self.api_key)

    
    def get_image_dimensions(self, image: Union[str, io.BytesIO, Image.Image]) -> tuple:
        """
        Get the dimensions (width, height) of an image.
        
        Args:
            image: Image as file path, BytesIO buffer, or PIL Image
            
        Returns:
            Tuple of (width, height)
        """
        if isinstance(image, str):
            with Image.open(image) as img:
                return img.size
        
        if isinstance(image, Image.Image):
            return image.size
        
        if isinstance(image, io.BytesIO):
            image.seek(0)
            with Image.open(image) as img:
                size = img.size
            image.seek(0)  # Reset position after reading
            return size
        
        raise TypeError(f"Unsupported image type: {type(image)}")
    
    
    def get_matching_resolution(self, width: int, height: int) -> str:
        """
        Find the closest valid video resolution that matches the image dimensions.
        
        Args:
            width: Image width in pixels
            height: Image height in pixels
            
        Returns:
            Valid resolution string (e.g., "1280x720")
            
        Raises:
            ValueError: If no matching resolution is found
        """
        resolution_str = f"{width}x{height}"
        
        # Get model-specific supported resolutions
        model_resolutions = MODEL_RESOLUTIONS.get(self.model_version, VALID_RESOLUTIONS)
        
        # Check if exact match exists
        if resolution_str in model_resolutions:
            return resolution_str
        
        # If not exact match, raise error with suggestions
        raise ValueError(
            f"Image dimensions {resolution_str} do not match any supported video resolution for {self.model_version}. "
            f"Supported resolutions for {self.model_version}: {sorted(model_resolutions)}. "
            f"Please resize your image to one of these resolutions before generating video."
        )
    
    
    def get_closest_resolution(self, width: int, height: int) -> str:
        """
        Find the closest supported video resolution based on image aspect ratio.
        
        Args:
            width: Image width in pixels
            height: Image height in pixels
            
        Returns:
            Closest valid resolution string (e.g., "1280x720")
        """
        aspect_ratio = width / height
        
        # Get model-specific supported resolutions
        model_resolutions = MODEL_RESOLUTIONS.get(self.model_version, VALID_RESOLUTIONS)
        
        # Parse all valid resolutions and find closest aspect ratio match
        closest_resolution = None
        min_aspect_diff = float('inf')
        
        for res in model_resolutions:
            res_w, res_h = map(int, res.split('x'))
            res_aspect = res_w / res_h
            aspect_diff = abs(aspect_ratio - res_aspect)
            
            if aspect_diff < min_aspect_diff:
                min_aspect_diff = aspect_diff
                closest_resolution = res
        
        return closest_resolution
    
    
    def resize_image_to_resolution(
        self, 
        image: Union[str, io.BytesIO, Image.Image], 
        target_resolution: str
    ) -> Image.Image:
        """
        Resize an image to match a target video resolution.
        
        Args:
            image: Image as file path, BytesIO buffer, or PIL Image
            target_resolution: Target resolution string (e.g., "1280x720")
            
        Returns:
            Resized PIL Image
        """
        # Load image as PIL Image
        if isinstance(image, str):
            img = Image.open(image)
        elif isinstance(image, io.BytesIO):
            image.seek(0)
            img = Image.open(image)
        elif isinstance(image, Image.Image):
            img = image
        else:
            raise TypeError(f"Unsupported image type: {type(image)}")
        
        # Parse target resolution
        target_width, target_height = map(int, target_resolution.split('x'))
        
        # Resize image to exact dimensions
        resized_img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        return resized_img
    
    
    def prepare_image(self, image: Union[str, io.BytesIO, Image.Image]) -> io.BytesIO:
        """
        Prepare an image for the API request.
        
        Args:
            image: Image as file path, BytesIO buffer, or PIL Image
            
        Returns:
            BytesIO buffer ready for API submission (file-like object)
        """
        if isinstance(image, str):
            with open(image, "rb") as f:
                buffer = io.BytesIO(f.read())
                buffer.name = "image.png"  # Add filename for multipart upload
                buffer.seek(0)
                return buffer

        if isinstance(image, Image.Image):
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            buffer.name = "image.png"  # Add filename for multipart upload
            buffer.seek(0)
            return buffer

        if isinstance(image, io.BytesIO):
            image.seek(0)
            if not hasattr(image, 'name'):
                image.name = "image.png"  # Add filename for multipart upload
            return image

        raise TypeError(f"Unsupported image type: {type(image)}")

    
    def _validate_common_params(self, duration: int, resolution: str) -> None:
        """Validate common parameters across generation methods."""
        if duration not in VALID_DURATIONS:
            raise ValueError(
                f"Invalid duration: {duration}. "
                f"Supported durations (seconds): {VALID_DURATIONS}"
            )
        
        # Check if resolution is supported by the current model
        model_supported_resolutions = MODEL_RESOLUTIONS.get(self.model_version, VALID_RESOLUTIONS)
        if resolution not in model_supported_resolutions:
            raise ValueError(
                f"Invalid resolution: {resolution} for model {self.model_version}. "
                f"Supported resolutions for {self.model_version}: {sorted(model_supported_resolutions)}"
            )

    
    def _poll_video_status(self, video_id: str) -> bytes:
        """
        Poll video generation status until completion (synchronous wait).
        
        Args:
            video_id: The ID of the video generation request
            
        Returns:
            Video bytes when generation is complete
            
        Raises:
            TimeoutError: If video generation exceeds max_polling_time
            RuntimeError: If video generation fails
        """
        start_time = time.time()
        
        while True:
            elapsed = time.time() - start_time
            if elapsed > self.max_polling_time:
                raise TimeoutError(
                    f"Video generation exceeded maximum wait time of {self.max_polling_time} seconds"
                )
            
            # Check status
            status_response = self.client.videos.retrieve(video_id)
            status = status_response.status
            
            if status == "completed":
                # Download the video using the correct API
                content = self.client.videos.download_content(video_id, variant="video")
                return content.read()
            
            elif status == "failed":
                error_msg = getattr(status_response, 'error', 'Unknown error')
                raise RuntimeError(f"Video generation failed: {error_msg}")
            
            elif status in ["queued", "in_progress"]:
                # Still generating, wait and retry
                time.sleep(self.polling_interval)
                continue
            
            else:
                raise RuntimeError(f"Unknown video status: {status}")

    
    def _start_video_generation(
        self,
        prompt: str,
        duration: int,
        resolution: str,
        image: Optional[io.BytesIO] = None,
    ) -> str:
        """
        Start a video generation request and return the video ID.
        
        Args:
            prompt: Text prompt describing the video
            duration: Video length in seconds
            resolution: Video resolution (e.g., "1280x720")
            image: Optional reference image file-like object for image-to-video
            
        Returns:
            Video generation ID for status tracking
        """
        kwargs = {
            "model": self.model_version,
            "prompt": prompt,
            "seconds": str(duration),  # API expects string: "4", "8", or "12"
            "size": resolution,
        }
        
        # Add image if provided (for image-to-video)
        if image is not None:
            # Pass the file-like object directly as input_reference
            image.seek(0)  # Ensure we're at the start of the buffer
            kwargs["input_reference"] = image

        response = self.client.videos.create(**kwargs)
        return response.id

    
    def generate_text_to_video(
        self,
        prompt: str,
        duration: int = 4,
        resolution: str = "1280x720",
        wait: bool = True,
    ) -> Union[bytes, str]:
        """
        Generate a video from a text prompt using OpenAI's Sora model.

        This method performs text-to-video generation and can either wait for completion
        (returning video bytes) or return immediately with a video ID for manual tracking.

        Args:
            prompt (str):
                Text description of the desired video content.
                Must be a non-empty string with clear, detailed instructions.

            duration (int, optional):
                Video length in seconds.
                Allowed values: {4, 8, 12}.
                Defaults to 4.

            resolution (str, optional):
                Output video resolution.
                Allowed values: See VALID_RESOLUTIONS.
                Common options: "1280x720" (16:9), "720x1280" (9:16), "1920x1080" (Full HD).
                Defaults to "1280x720".

            wait (bool, optional):
                If True, polls the API until video generation completes and returns video bytes.
                If False, returns the video ID immediately for manual status tracking.
                Defaults to True.

        Returns:
            Union[bytes, str]:
                - If wait=True: Video data as bytes (ready to save as .mp4)
                - If wait=False: Video generation ID (str) for tracking

        Raises:
            ValueError:
                - If prompt is empty
                - If duration or resolution is invalid
            TimeoutError:
                - If video generation exceeds max_polling_time (only when wait=True)
            RuntimeError:
                - If video generation fails

        Example:
            >>> adapter = SoraVideoAdapter()
            >>> 
            >>> # Synchronous generation (wait for completion)
            >>> video_bytes = adapter.generate_text_to_video(
            ...     prompt="A fashion model walking down a runway in an elegant dress",
            ...     duration=8,
            ...     resolution="1920x1080"
            ... )
            >>> with open("runway.mp4", "wb") as f:
            ...     f.write(video_bytes)
            >>> 
            >>> # Asynchronous generation (manual tracking)
            >>> video_id = adapter.generate_text_to_video(
            ...     prompt="Fabric flowing in slow motion",
            ...     duration=4,
            ...     wait=False
            ... )
            >>> print(f"Video generation started: {video_id}")
        """
        
        if not prompt:
            raise ValueError("Prompt is required for text-to-video generation.")
        
        self._validate_common_params(duration, resolution)
        
        # Start generation
        video_id = self._start_video_generation(
            prompt=prompt,
            duration=duration,
            resolution=resolution,
            image=None
        )
        
        # Wait for completion or return ID
        if wait:
            return self._poll_video_status(video_id)
        else:
            return video_id

    
    def generate_image_to_video(
        self,
        image: Union[str, io.BytesIO, Image.Image],
        prompt: str,
        duration: int = 4,
        resolution: str = "1280x720",
        wait: bool = True,
        auto_resize: bool = True,
    ) -> Union[bytes, str]:
        """
        Generate a video from an image and text prompt using OpenAI's Sora model.

        This method performs image+text-to-video generation, animating a reference image
        based on the provided text prompt. Can wait for completion or return a video ID.

        Args:
            image (Union[str, io.BytesIO, Image.Image]):
                Reference image to animate.
                Can be a file path, BytesIO buffer, or PIL Image.

            prompt (str):
                Text description of how to animate the image.
                Must be a non-empty string with clear animation instructions.

            duration (int, optional):
                Video length in seconds.
                Allowed values: {4, 8, 12}.
                Defaults to 4.

            resolution (str, optional):
                Output video resolution.
                Allowed values: See VALID_RESOLUTIONS.
                Defaults to "1280x720".

            wait (bool, optional):
                If True, polls until completion and returns video bytes.
                If False, returns video ID for manual tracking.
                Defaults to True.
            
            auto_resize (bool, optional):
                If True, automatically resizes the image to the closest supported resolution
                when image dimensions don't match. If False, raises an error on mismatch.
                Defaults to True.

        Returns:
            Union[bytes, str]:
                - If wait=True: Video data as bytes
                - If wait=False: Video generation ID for tracking

        Raises:
            ValueError:
                - If prompt is empty
                - If duration or resolution is invalid
            TypeError:
                - If image type is not supported
            TimeoutError:
                - If generation exceeds max_polling_time (only when wait=True)
            RuntimeError:
                - If video generation fails

        Example:
            >>> adapter = SoraVideoAdapter()
            >>> 
            >>> # Animate a static image
            >>> video_bytes = adapter.generate_image_to_video(
            ...     image="model_photo.jpg",
            ...     prompt="The model turns and smiles at the camera",
            ...     duration=4,
            ...     resolution="1280x720"
            ... )
            >>> with open("animated_model.mp4", "wb") as f:
            ...     f.write(video_bytes)
        """
        
        if not prompt:
            raise ValueError("Prompt is required for image-to-video generation.")
        
        # Get image dimensions to validate/auto-detect resolution
        width, height = self.get_image_dimensions(image)
        image_resolution = f"{width}x{height}"
        
        # Get model-specific supported resolutions
        model_resolutions = MODEL_RESOLUTIONS.get(self.model_version, VALID_RESOLUTIONS)
        
        # Check if image dimensions match a supported resolution
        if image_resolution in model_resolutions:
            # Exact match - use image dimensions
            if resolution == "1280x720":  # Default resolution
                resolution = image_resolution
                print(f"✓ Using image resolution: {resolution}")
            elif resolution != image_resolution:
                # User specified different resolution than image
                if auto_resize:
                    print(f"⚠ Image is {image_resolution}, resizing to requested {resolution}...")
                    image = self.resize_image_to_resolution(image, resolution)
                else:
                    raise ValueError(
                        f"Image dimensions ({image_resolution}) don't match requested resolution ({resolution}). "
                        f"Set auto_resize=True to automatically resize, or resize your image manually."
                    )
        else:
            # Image dimensions don't match any supported resolution
            if auto_resize:
                # Find closest supported resolution
                target_resolution = self.get_closest_resolution(width, height)
                print(f"⚠ Image is {image_resolution}, auto-resizing to closest supported resolution: {target_resolution}")
                image = self.resize_image_to_resolution(image, target_resolution)
                resolution = target_resolution
            else:
                raise ValueError(
                    f"Image dimensions {image_resolution} do not match any supported video resolution. "
                    f"Supported resolutions: {VALID_RESOLUTIONS}. "
                    f"Set auto_resize=True to automatically resize, or resize your image manually."
                )
        
        self._validate_common_params(duration, resolution)
        
        # Prepare image (returns BytesIO file-like object)
        image_buffer = self.prepare_image(image)
        
        # Start generation
        video_id = self._start_video_generation(
            prompt=prompt,
            duration=duration,
            resolution=resolution,
            image=image_buffer
        )
        
        # Wait for completion or return ID
        if wait:
            return self._poll_video_status(video_id)
        else:
            return video_id

    
    def get_video_status(self, video_id: str) -> Dict[str, Any]:
        """
        Check the status of a video generation request.
        
        Args:
            video_id: The ID returned from a video generation request
            
        Returns:
            Dict containing status information:
                - status: "queued", "in_progress", "completed", or "failed"
                - progress: Optional progress percentage (0-100)
                - url: Video URL (only when status is "completed")
                - error: Error message (only when status is "failed")
        
        Example:
            >>> video_id = adapter.generate_text_to_video(prompt="...", wait=False)
            >>> status = adapter.get_video_status(video_id)
            >>> print(f"Status: {status['status']}")
        """
        response = self.client.videos.retrieve(video_id)
        
        result = {
            "status": response.status,
            "id": video_id,
        }
        
        if hasattr(response, 'progress'):
            result["progress"] = response.progress
        
        if response.status == "completed":
            result["url"] = response.url
        
        if response.status == "failed":
            result["error"] = getattr(response, 'error', 'Unknown error')
        
        return result

    
    def download_video(self, video_id: str) -> bytes:
        """
        Download a completed video by its ID.
        
        Args:
            video_id: The ID of a completed video generation
            
        Returns:
            Video bytes ready to save
            
        Raises:
            RuntimeError: If video is not yet completed or has failed
        
        Example:
            >>> video_id = adapter.generate_text_to_video(prompt="...", wait=False)
            >>> # ... wait some time or check status ...
            >>> video_bytes = adapter.download_video(video_id)
            >>> with open("video.mp4", "wb") as f:
            ...     f.write(video_bytes)
        """
        status = self.get_video_status(video_id)
        
        if status["status"] != "completed":
            raise RuntimeError(
                f"Video is not ready for download. Current status: {status['status']}"
            )
        
        # Download using the correct API
        content = self.client.videos.download_content(video_id, variant="video")
        return content.read()

    
    def generate_text_to_video_async(
        self,
        prompt: str,
        duration: int = 4,
        resolution: str = "1280x720",
        on_complete: Optional[Callable[[bytes], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
        on_progress: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> str:
        """
        Generate a video asynchronously with callback functions.
        
        This method starts video generation and immediately returns the video ID.
        It spawns a background thread to monitor progress and invoke callbacks.
        
        Args:
            prompt: Text description of the video
            duration: Video length in seconds
            resolution: Output resolution
            on_complete: Callback function called with video bytes when ready
            on_error: Callback function called with error message if generation fails
            on_progress: Callback function called with status dict during generation
            
        Returns:
            Video generation ID for reference
            
        Example:
            >>> def handle_complete(video_bytes):
            ...     with open("output.mp4", "wb") as f:
            ...         f.write(video_bytes)
            ...     print("Video saved!")
            >>> 
            >>> def handle_error(error):
            ...     print(f"Error: {error}")
            >>> 
            >>> def handle_progress(status):
            ...     print(f"Progress: {status.get('progress', 'processing')}")
            >>> 
            >>> video_id = adapter.generate_text_to_video_async(
            ...     prompt="A cinematic fashion show",
            ...     duration=8,
            ...     on_complete=handle_complete,
            ...     on_error=handle_error,
            ...     on_progress=handle_progress
            ... )
        """
        import threading
        
        if not prompt:
            raise ValueError("Prompt is required for text-to-video generation.")
        
        self._validate_common_params(duration, resolution)
        
        # Start generation
        video_id = self._start_video_generation(
            prompt=prompt,
            duration=duration,
            resolution=resolution,
            image=None
        )
        
        # Background monitoring thread
        def monitor():
            try:
                start_time = time.time()
                while True:
                    elapsed = time.time() - start_time
                    if elapsed > self.max_polling_time:
                        if on_error:
                            on_error(f"Timeout after {self.max_polling_time} seconds")
                        return
                    
                    status = self.get_video_status(video_id)
                    
                    if on_progress:
                        on_progress(status)
                    
                    if status["status"] == "completed":
                        video_bytes = self.download_video(video_id)
                        if on_complete:
                            on_complete(video_bytes)
                        return
                    
                    elif status["status"] == "failed":
                        if on_error:
                            on_error(status.get("error", "Unknown error"))
                        return
                    
                    time.sleep(self.polling_interval)
            
            except Exception as e:
                if on_error:
                    on_error(str(e))
        
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
        
        return video_id

    
    def generate_image_to_video_async(
        self,
        image: Union[str, io.BytesIO, Image.Image],
        prompt: str,
        duration: int = 4,
        resolution: str = "1280x720",
        on_complete: Optional[Callable[[bytes], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
        on_progress: Optional[Callable[[Dict[str, Any]], None]] = None,
        auto_resize: bool = True,
    ) -> str:
        """
        Generate a video from image asynchronously with callback functions.
        
        This method starts image-to-video generation and immediately returns the video ID.
        It spawns a background thread to monitor progress and invoke callbacks.
        
        Args:
            image: Reference image to animate
            prompt: Text description of the animation
            duration: Video length in seconds
            resolution: Output resolution
            on_complete: Callback function called with video bytes when ready
            on_error: Callback function called with error message if generation fails
            on_progress: Callback function called with status dict during generation
            
        Returns:
            Video generation ID for reference
            
        Example:
            >>> adapter = SoraVideoAdapter()
            >>> 
            >>> def save_video(video_bytes):
            ...     with open("animated.mp4", "wb") as f:
            ...         f.write(video_bytes)
            >>> 
            >>> video_id = adapter.generate_image_to_video_async(
            ...     image="photo.jpg",
            ...     prompt="The person waves and smiles",
            ...     duration=4,
            ...     on_complete=save_video
            ... )
        """
        import threading
        
        if not prompt:
            raise ValueError("Prompt is required for image-to-video generation.")
        
        # Get image dimensions to validate/auto-detect resolution
        width, height = self.get_image_dimensions(image)
        image_resolution = f"{width}x{height}"
        
        # Get model-specific supported resolutions
        model_resolutions = MODEL_RESOLUTIONS.get(self.model_version, VALID_RESOLUTIONS)
        
        # Check if image dimensions match a supported resolution
        if image_resolution in model_resolutions:
            # Exact match - use image dimensions
            if resolution == "1280x720":  # Default resolution
                resolution = image_resolution
                print(f"✓ Using image resolution: {resolution}")
            elif resolution != image_resolution:
                # User specified different resolution than image
                if auto_resize:
                    print(f"⚠ Image is {image_resolution}, resizing to requested {resolution}...")
                    image = self.resize_image_to_resolution(image, resolution)
                else:
                    raise ValueError(
                        f"Image dimensions ({image_resolution}) don't match requested resolution ({resolution}). "
                        f"Set auto_resize=True to automatically resize, or resize your image manually."
                    )
        else:
            # Image dimensions don't match any supported resolution
            if auto_resize:
                # Find closest supported resolution
                target_resolution = self.get_closest_resolution(width, height)
                print(f"⚠ Image is {image_resolution}, auto-resizing to closest supported resolution: {target_resolution}")
                image = self.resize_image_to_resolution(image, target_resolution)
                resolution = target_resolution
            else:
                raise ValueError(
                    f"Image dimensions {image_resolution} do not match any supported video resolution. "
                    f"Supported resolutions: {VALID_RESOLUTIONS}. "
                    f"Set auto_resize=True to automatically resize, or resize your image manually."
                )
        
        self._validate_common_params(duration, resolution)
        
        # Prepare image (returns BytesIO file-like object)
        image_buffer = self.prepare_image(image)
        
        # Start generation
        video_id = self._start_video_generation(
            prompt=prompt,
            duration=duration,
            resolution=resolution,
            image=image_buffer
        )
        
        # Background monitoring thread (same logic as text-to-video)
        def monitor():
            try:
                start_time = time.time()
                while True:
                    elapsed = time.time() - start_time
                    if elapsed > self.max_polling_time:
                        if on_error:
                            on_error(f"Timeout after {self.max_polling_time} seconds")
                        return
                    
                    status = self.get_video_status(video_id)
                    
                    if on_progress:
                        on_progress(status)
                    
                    if status["status"] == "completed":
                        video_bytes = self.download_video(video_id)
                        if on_complete:
                            on_complete(video_bytes)
                        return
                    
                    elif status["status"] == "failed":
                        if on_error:
                            on_error(status.get("error", "Unknown error"))
                        return
                    
                    time.sleep(self.polling_interval)
            
            except Exception as e:
                if on_error:
                    on_error(str(e))
        
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
        
        return video_id

