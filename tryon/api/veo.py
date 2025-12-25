"""
Google Veo Video Generation API Adapter

Adapter for Google's Veo video generation models, providing structured
interfaces for multiple video creation workflows including text-driven
generation, image-conditioned generation, and frame-controlled synthesis.

Supported Models:
- veo-3.1-generate-preview
- veo-3.1-fast-generate-preview
- veo-3.0-generate-001
- veo-3.0-fast-generate-001

Capabilities:
1) Text-to-Video
   Generate high-quality cinematic videos purely from a natural language prompt.

2) Image-to-Video
   Use a single reference image to establish style, composition, and scene
   context while the model animates motion forward in time.

3) Video Generation with Reference Images (up to 3)
   Provide one or more guiding images (maximum three). These images help
   influence scene structure, visual continuity, and thematic consistency.

4) First Frame + Last Frame Controlled Generation
   Supply both an initial frame and a final target frame. Veo interpolates
   motion and visual development between the two frames to create a smooth
   evolving sequence.
   (Full frame-to-frame control is primarily supported in Veo 3.1 models.)

Behavior Notes:
- Not all control modes are equally supported across Veo 3.0 vs 3.1.
  Veo 3.1 provides better guided control and stability.
- Generation is asynchronous; polling is required until completion.
- Output is returned as raw video bytes for downstream streaming/storage.
- Duration, resolution, and aspect-ratio constraints depend on model config.

Typical Workflow:
1) Submit generation request with prompt (+ optional frames / references)
2) Poll until operation finishes
3) Download or extract MP4 video bytes

Reference:
https://ai.google.dev/gemini-api/docs/video

Usage Examples:

    Text-to-Video:
        >>> adapter.generate_text_video(
        ...     prompt="A cinematic aerial shot of a futuristic neon city at night",
        ...     model="veo-3.1-generate-preview"
        ... )

    Image-to-Video:
        >>> adapter.generate_image_to_video(
        ...     prompt="Continue motion through a windy canyon",
        ...     image="start.png",
        ...     model="veo-3.1-generate-preview"
        ... )

    Reference Images (up to 3):
        >>> adapter.generate_video_with_references(
        ...     prompt="Epic fantasy battlefield reveal",
        ...     reference_images=["a.png", "b.png", "c.png"],
        ...     model="veo-3.1-fast-generate-preview"
        ... )

    First + Last Frame Controlled Generation:
        >>> adapter.generate_video_with_frames(
        ...     prompt="Smooth cinematic transition through cyberpunk streets",
        ...     first_image="start.png",
        ...     last_image="end.png",
        ...     model="veo-3.1-generate-preview"
        ... )
"""

import time
import os
import io
import base64
from PIL import Image
from typing import Optional, Union

try:
    from google import genai
    from google.genai import types
    GEMINI_API_KEY = True
except ImportError:
    GEMINI_API_KEY = False
    genai = None

DURATION = {"4", "6", "8"}
ASPECT_RATIO = {"16:9", "9:16"}
RESOLUTION = {"720p", "1080p"}
MODELS = {"veo-3.1-generate-preview", "veo-3.1-fast-generate-preview", "veo-3.0-generate-001", "veo-3.0-fast-generate-001"}

class VeoAdapter:

    def __init__(self, api_key: Optional[str] = None):

        if not GEMINI_API_KEY:
            raise ImportError(
                "google-genai library is not available. " \
                "Please install it with 'pip install google-genai'."
            )
        
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI API key must be provided either as a parameter or through the GEMINI_API_KEY environment variable.")
        
        self.client = genai.Client(api_key=self.api_key)

    
    def _prepare_image_input(self, image_input: Union[str, io.BytesIO, Image.Image]) -> types.Image:
        
        """
        Converts various image inputs into a Veo-compatible `types.Image`.

        Supports:
        - PIL Image
        - file-like objects (BytesIO / file handles)
        - strings (URL, local path, or Base64)

        Ensures:
        - image is valid
        - converted to RGB
        - encoded as PNG
        - returned as `types.Image(image_bytes, mime_type="image/png")`

        Raises:
            ValueError: If the input type is unsupported or the image cannot be decoded.
        """
        
        # A PIL Image
        if isinstance(image_input, Image.Image):
            pil = image_input.convert("RGB")
        
        # File-like object (BytesIO, file handle)
        elif hasattr(image_input, "read"):
            image_input.seek(0)
            image_bytes = image_input.read()
            try:
                pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            except Exception as e:
                raise ValueError(f"Invalid image data in file-like object: {e}")
        
        # String (URL, file path, or base64)
        elif isinstance(image_input, str):
            # URL
            if image_input.startswith(("http://", "https://")):
                try:
                    import requests
                    r = requests.get(image_input, timeout=10)
                    r.raise_for_status()
                    image_bytes = r.content
                except Exception as e:
                    raise ValueError(f"Failed to download image from URL: {e}")
            
            # File path
            elif os.path.exists(image_input):
                try:
                    with open(image_input, "rb") as f:
                        image_bytes = f.read()
                except Exception as e:
                    raise ValueError(f"Failed to read image file: {e}")
            
            # Base64 string
            else:
                try:
                    image_bytes = base64.b64decode(image_input, validate=True)
                except Exception as e:
                    raise ValueError(f"Invalid base64 image string: {e}")
            
            # Convert bytes to PIL Image
            try:
                pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            except Exception as e:
                raise ValueError(f"Invalid image data: {e}")
        
        else:
            raise ValueError(f"Unsupported image input type: {type(image_input)}")
        
        # Convert to PNG bytes
        buffer = io.BytesIO()
        pil.save(buffer, format="PNG")
        png_bytes = buffer.getvalue() 
        
        # Return raw bytes
        return types.Image(
            image_bytes=png_bytes,
            mime_type="image/png",
        )

    
    def generate_text_to_video(
        self,
        prompt: str,
        duration_seconds: str = "4",
        aspect_ratio: str = "16:9",
        resolution: str = "720p",
        negative_prompt: Optional[str] = None,
        model: str = "veo-3.1-generate-preview",
    ) -> bytes:
        
        """
        Generate a video from a text prompt using Google Veo.

        This function sends a text prompt to a Veo video generation model, polls the
        operation until the video is ready, then downloads and returns the raw MP4 bytes.
        Supports duration, aspect-ratio, resolution constraints and optional
        negative prompts. Automatically validates parameters and ensures only valid
        Veo model + configuration combinations are used.

        Args:
            prompt:
                The primary text prompt describing what the video should depict.
            duration_seconds:
                Length of the generated clip in seconds.
                Supported values depend on the model (commonly: "4", "6", "8").
            aspect_ratio:
                Output aspect ratio (e.g., "16:9" or "9:16").
            resolution:
                Output resolution preset ("720p" or "1080p", depending on model limits).
            negative_prompt:
                Optional text describing content to avoid in the generation.
            model:
                Veo model identifier.
                Examples:
                    - "veo-3.1-generate-preview"
                    - "veo-3.1-fast-generate-preview"
                    - "veo-3.0-generate-001"
                    - "veo-3.0-fast-generate-001"

        Returns:
            bytes:
                Raw MP4 video bytes

        Raises:
            ValueError:
                If prompt is missing, configuration is invalid,
                or no video was generated.
            RuntimeError:
                If Veo returns an unexpected structure and video bytes
                cannot be extracted.

        Example:
            >>> video_bytes = adapter.generate_text_to_video(
            ...     prompt="A cinematic shot of a dragon flying over a medieval city",
            ...     duration_seconds="8",
            ...     aspect_ratio="16:9",
            ...     resolution="1080p",
            ...     model="veo-3.1-generate-preview"
            ... )
            >>> with open("dragon_city.mp4", "wb") as f:
            ...     f.write(video_bytes)
        """

        # Validation Check
        if not prompt:
            raise ValueError("prompt is required")
        
        if model not in MODELS:
            raise ValueError(f"{model} is not a recognized model. Available models are {MODELS}")

        if duration_seconds not in DURATION:
            raise ValueError("duration_seconds must be one of: 4, 6, 8")

        if aspect_ratio not in ASPECT_RATIO:
            raise ValueError("aspect_ratio must be '16:9' or '9:16'")

        if resolution not in RESOLUTION:
            raise ValueError("resolution must be '720p' or '1080p'")

        if model in {"veo-3.1-generate-preview", "veo-3.1-fast-generate-preview"}:
            if resolution == "1080p" and duration_seconds != "8":
                raise ValueError("1080p resolution only supports 8s duration for veo 3.1 models.")
        
        if model in {"veo-3.0-generate-001", "veo-3.0-fast-generate-001"}:
            if resolution == "1080p" and aspect_ratio != "16:9":
                raise ValueError("1080p resolution only supportes 16:9 aspect ratio for veo 3 models.")
            
        # Create Configurations
        kwargs = {
            "duration_seconds": duration_seconds,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
        }

        # Negative Prompt
        if negative_prompt:
            kwargs["negative_prompt"] = negative_prompt

        # Create a generation object
        operation = self.client.models.generate_videos(
            model=model,
            prompt=prompt,
            config=types.GenerateVideosConfig(**kwargs),
        )

        # Polling
        while not operation.done:
            operation = self.client.operations.get(operation)
            time.sleep(1)
        
        # Check for video error after polling completes
        if getattr(operation, "error", None):
            raise RuntimeError(f"Video generation failed: {operation.error}")

        if operation.response is None:
            raise RuntimeError("Video generation completed but no response was returned")

        generated = getattr(operation.response, "generated_videos", None)
        if not generated:
            raise RuntimeError(
                f"No videos were generated. operation.error={getattr(operation, 'error', None)}; "
                f"operation_name={getattr(operation, 'name', None)}; response={operation.response}"
            )

        # Extract the generated video
        video = operation.response.generated_videos[0].video
        if not video:
            raise ValueError("No video was generated.")


        # If Video bytes are returned
        if hasattr(video, "video_bytes") and video.video_bytes:
            return video.video_bytes

        # Else download the file via the files API
        downloaded = self.client.files.download(file=video)

        if isinstance(downloaded, (bytes, bytearray)):
            return bytes(downloaded)
        
        if hasattr(downloaded, "read"):
            try:
                downloaded.seek(0)
            except Exception:
                pass
            return downloaded.read()
        
        if hasattr(downloaded, "bytes"):
            return downloaded.bytes
        
        if hasattr(downloaded, "data"):
            return downloaded.data
        
        if hasattr(downloaded, "content"):
            return downloaded.content

        raise RuntimeError(f"Error occured. Video cannot be generated...")
    

    def generate_image_to_video(
        self,
        image: Union[str, io.BytesIO, Image.Image],
        prompt: str,
        duration_seconds: str = "4",
        aspect_ratio: str = "16:9",
        resolution: str = "720p",
        negative_prompt: Optional[str] = None,
        model: str = "veo-3.1-generate-preview",
    ) -> bytes:
        
        """
        Animate a still image into a video using Google Veo.

        This function takes a single reference image and a guiding text prompt, sends
        them to a Veo image-to-video model, polls until generation completes, and
        returns the resulting MP4 video as raw bytes. The animation respects the
        specified duration, aspect ratio, and resolution constraints. Supports optional
        negative prompts and enforces model capability rules to prevent invalid requests.

        Args:
            image:
                The input image to animate. Can be one of:
                - str: Path to an image file.
                - io.BytesIO: In-memory binary image stream.
                - PIL.Image.Image: Loaded PIL image object.
            prompt:
                Text description guiding how the image should animate.
            duration_seconds:
                Length of the generated clip in seconds.
                Supported values depend on the model (commonly: "4", "6", "8").
            aspect_ratio:
                Output aspect ratio (e.g., "16:9" or "9:16").
            resolution:
                Output video resolution preset ("720p" or "1080p", depending on model limits).
            negative_prompt:
                Optional text describing what should be avoided in the generated video.
            model:
                Veo model identifier to use for generation, such as:
                    - "veo-3.1-generate-preview"
                    - "veo-3.1-fast-generate-preview"
                    - "veo-3.0-generate-001"
                    - "veo-3.0-fast-generate-001"

        Returns:
            bytes:
                Raw MP4 video bytes

        Raises:
            ValueError:
                If required parameters are missing, invalid combinations are used,
                or no video is returned from Veo.
            RuntimeError:
                If Veo produces an unexpected response structure and
                video bytes cannot be extracted.

        Example:
            >>> with open("person.png", "rb") as img:
            ...     video = adapter.generate_image_to_video(
            ...         image=img,
            ...         prompt="The person begins walking through a snowy forest",
            ...         duration_seconds="8",
            ...         aspect_ratio="16:9",
            ...         resolution="1080p",
            ...         model="veo-3.1-generate-preview",
            ...     )
            >>> with open("animated_person.mp4", "wb") as f:
            ...     f.write(video)
        """

        # Validation Check
        if not image:
            raise ValueError("image is required")

        if not prompt:
            raise ValueError("prompt is required")
        
        if model not in MODELS:
            raise ValueError(f"{model} is not a recognized model. Available models are {MODELS}")

        if duration_seconds not in DURATION:
            raise ValueError("duration_seconds must be one of: 4, 6, 8")

        if aspect_ratio not in ASPECT_RATIO:
            raise ValueError("aspect_ratio must be '16:9' or '9:16'")

        if resolution not in RESOLUTION:
            raise ValueError("resolution must be '720p' or '1080p'")
        
        if model in {"veo-3.1-generate-preview", "veo-3.1-fast-generate-preview"}:
            if resolution == "1080p" and duration_seconds != "8":
                raise ValueError("1080p resolution only supports 8s duration for veo 3.1 models.")
        
        if model in {"veo-3.0-generate-001", "veo-3.0-fast-generate-001"}:
            if resolution == "1080p" and aspect_ratio != "16:9":
                raise ValueError("1080p resolution only supportes 16:9 aspect ratio for veo 3 models.")
        

        # Create Configurations
        kwargs = {
            "duration_seconds": duration_seconds,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
        }

        # Negative Prompt
        if negative_prompt:
            kwargs["negative_prompt"] = negative_prompt

        # Create a generation object
        operation = self.client.models.generate_videos(
            model=model,
            prompt=prompt,
            image=self._prepare_image_input(image),
            config=types.GenerateVideosConfig(**kwargs),
        )

        # Polling
        while not operation.done:
            operation = self.client.operations.get(operation)
            time.sleep(1)
        
        # Check for video error after polling completes
        if getattr(operation, "error", None):
            raise RuntimeError(f"Video generation failed: {operation.error}")

        if operation.response is None:
            raise RuntimeError("Video generation completed but no response was returned")

        generated = getattr(operation.response, "generated_videos", None)
        if not generated:
            raise RuntimeError(
                f"No videos were generated. operation.error={getattr(operation, 'error', None)}; "
                f"operation_name={getattr(operation, 'name', None)}; response={operation.response}"
            )
        
        # Extract the generated video
        video = operation.response.generated_videos[0].video
        if not video:
            raise ValueError("Video was not generated.")

        # If Video bytes are returned
        if hasattr(video, 'video_bytes') and video.video_bytes:
            return video.video_bytes

        # Else download the file
        downloaded = self.client.files.download(file=video)

        if isinstance(downloaded, (bytes, bytearray)):
            return bytes(downloaded)
        
        if hasattr(downloaded, "read"):
            try:
                downloaded.seek(0)
            except Exception:
                pass
            return downloaded.read()
        
        if hasattr(downloaded, "bytes"):
            return downloaded.bytes
        
        if hasattr(downloaded, "data"):
            return downloaded.data
        
        if hasattr(downloaded, "content"):
            return downloaded.content

        raise ValueError("Error occured. Video cannot be generated...")
    

    def generate_video_with_references(
        self,
        prompt: str,
        reference_images: list[Union[str, io.BytesIO, Image.Image]],
        duration_seconds: str = "8",
        aspect_ratio: str = "16:9",
        resolution: str = "720p",
        model: str = "veo-3.1-generate-preview",
        negative_prompt: Optional[str] = None
    ) -> bytes:
        
        """
        Generate a video using reference images as visual/style guidance with Google Veo.

        This function generates a video guided by one or more reference images. The
        images help Veo preserve identity, visual style, composition, or scene
        continuity depending on how they are interpreted by the model. Supports up
        to three reference images and automatically enforces Veo 3.1 model constraints
        (8 seconds, 16:9, supported resolutions). The function polls the generation
        operation until completion and returns the final MP4 video bytes.

        Args:
            prompt:
                Text description guiding how the scene should animate and what should happen.
            reference_images:
                List of up to three images used as visual guidance.
                Each element may be:
                - str: Path to an image file
                - io.BytesIO: In-memory binary stream
                - PIL.Image.Image: Loaded PIL image object
            duration_seconds:
                Length of the generated clip in seconds.
                For reference-guided generation, Veo requires `"8"`.
            aspect_ratio:
                Output aspect ratio. Reference-guided video currently supports `"16:9"` only.
            resolution:
                Output resolution preset, typically `"720p"` or `"1080p"` depending on model limits.
            model:
                Veo model identifier. Reference-guided generation is only supported
                on Veo 3.1 preview / fast-preview models, e.g.:
                    - "veo-3.1-generate-preview"
                    - "veo-3.1-fast-generate-preview"
            negative_prompt:
                Optional text describing what should be avoided in the generated video.

        Returns:
            bytes:
                Raw MP4 video bytes

        Raises:
            ValueError:
                If required parameters are missing, invalid configurations are used,
                unsupported models are selected, or no video is returned.
            RuntimeError:
                If Veo returns an unexpected response structure and the video
                file bytes cannot be extracted.

        Example:
            >>> video_bytes = adapter.generate_video_with_references(
            ...     prompt="A heroic knight walking through a ruined castle courtyard",
            ...     reference_images=[
            ...         "face_ref.png",
            ...         "armor_style.jpg"
            ...     ],
            ...     resolution="1080p",
            ...     model="veo-3.1-generate-preview"
            ... )
            >>> with open("knight_scene.mp4", "wb") as f:
            ...     f.write(video_bytes)
        """

        # Valdiation Check
        if not prompt:
            raise ValueError("prompt is required")
        
        if model not in MODELS:
            raise ValueError(f"{model} is not a recognized model. Available models are {MODELS}")
        
        if model in {"veo-3.0-generate-001", "veo-3.0-fast-generate-001"}:
            raise ValueError("Video generation using reference images is only supported for veo 3.1 models.")

        if not reference_images:
            raise ValueError("At least one reference image is required")

        if len(reference_images) > 3:
            raise ValueError("Veo 3.1 supports a maximum of 3 reference images")

        if resolution not in RESOLUTION:
            raise ValueError("resolution must be '720p' or '1080p'")

        if duration_seconds != "8":
            raise ValueError("Video generation using reference images require duration_seconds='8'")

        if aspect_ratio != "16:9":
            raise ValueError("Video generation using reference images only support aspect_ratio='16:9'")
        

        # Prepare reference images
        refs = []

        for img in reference_images:
            refs.append(
                types.VideoGenerationReferenceImage(
                    image=self._prepare_image_input(img),
                    reference_type="asset"
                )
            )
        
        # Create Configurations
        kwargs = {
            "duration_seconds": duration_seconds,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
            "reference_images": refs
        }

        # Negative prompt
        if negative_prompt:
            kwargs["negative_prompt"] = negative_prompt

        # Create a generation object
        operation = self.client.models.generate_videos(
            model=model,
            prompt=prompt,
            config=types.GenerateVideosConfig(**kwargs),
        )

        # Polling
        while not operation.done:
            operation = self.client.operations.get(operation)
            time.sleep(1)
        
        # Check for video error after polling completes
        if getattr(operation, "error", None):
            raise RuntimeError(f"Video generation failed: {operation.error}")

        if operation.response is None:
            raise RuntimeError("Video generation completed but no response was returned")

        generated = getattr(operation.response, "generated_videos", None)
        if not generated:
            raise RuntimeError(
                f"No videos were generated. operation.error={getattr(operation, 'error', None)}; "
                f"operation_name={getattr(operation, 'name', None)}; response={operation.response}"
            )

        # Extract the generated video
        video = operation.response.generated_videos[0].video
        if not video:
            raise ValueError("No video was generated")

        # If Video bytes are returned
        if hasattr(video, "video_bytes") and video.video_bytes:
            return video.video_bytes

        # Else download the file
        downloaded = self.client.files.download(file=video)

        if isinstance(downloaded, (bytes, bytearray)):
            return bytes(downloaded)
        
        if hasattr(downloaded, "read"):
            try:
                downloaded.seek(0)
            except Exception:
                pass
            return downloaded.read()
        
        if hasattr(downloaded, "bytes"):
            return downloaded.bytes
        
        if hasattr(downloaded, "data"):
            return downloaded.data
        
        if hasattr(downloaded, "content"):
            return downloaded.content

        raise RuntimeError(f"Error occured. Video cannot be generated...")
    

    def generate_video_with_frames(
        self,
        prompt: str,
        first_image: Union[str, io.BytesIO, Image.Image],
        last_image: Union[str, io.BytesIO, Image.Image],
        duration_seconds: str = "8",
        aspect_ratio: str = "16:9",
        resolution: str = "720p",
        model: str = "veo-3.1-generate-preview",
        negative_prompt: Optional[str] = None
    ) -> bytes:
        
        """
        Generate a video using a starting frame and ending frame as guidance with Google Veo.

        This function generates a video using a specified first frame and last frame to
        guide motion, composition, and visual consistency throughout the clip. The
        first frame determines how the video begins and the last frame influences how
        the animation resolves. The generation respects Veo 3.1 constraints
        (8-second clips, supported aspect ratios, supported resolutions) and polls the
        operation until the output is ready, finally returning raw MP4 bytes.

        Args:
            prompt:
                Text description guiding what happens between the first and last frames.
            first_image:
                The starting frame of the video. May be:
                - str: Path to an image file
                - io.BytesIO: Binary image stream
                - PIL.Image.Image: Loaded PIL image
            last_image:
                The ending frame of the video. Must be provided in the same supported
                formats as `first_image`.
            duration_seconds:
                Duration of the generated clip. Frame-guided generation currently
                requires `"8"`.
            aspect_ratio:
                Output aspect ratio (e.g., `"16:9"` or `"9:16"`, depending on model support).
            resolution:
                Output video resolution preset such as `"720p"` or `"1080p"`.
            model:
                Veo model identifier. Frame-guided generation is only supported on
                Veo 3.1 preview / fast-preview models, such as:
                    - "veo-3.1-generate-preview"
                    - "veo-3.1-fast-generate-preview"
            negative_prompt:
                Optional text describing what should be avoided in the generation.

        Returns:
            bytes:
                Raw MP4 video bytes

        Raises:
            ValueError:
                If required parameters are missing, unsupported models are used,
                invalid configurations are passed, or the API does not return a video.
            RuntimeError:
                If the API response structure is unexpected and the video bytes
                cannot be extracted.

        Example:
            >>> video = adapter.generate_video_with_frames(
            ...     prompt="A dramatic camera move through a futuristic city at night",
            ...     first_image="start_frame.png",
            ...     last_image="end_frame.png",
            ...     resolution="1080p",
            ...     model="veo-3.1-generate-preview"
            ... )
            >>> with open("city_transition.mp4", "wb") as f:
            ...     f.write(video)
        """

        # Validation Check
        if not prompt:
            raise ValueError("Prompt is required for video generation.")
        
        if model not in MODELS:
            raise ValueError(f"{model} is not a recognized model. Available models are {MODELS}")
        
        if model in {"veo-3.0-generate-001", "veo-3.0-fast-generate-001"}:
            raise ValueError("Video generation using first frame and last frame is only supported for veo 3.1 models.")

        if aspect_ratio not in ASPECT_RATIO:
            raise ValueError("aspect_ratio must be '16:9' or '9:16'")

        if resolution not in RESOLUTION:
            raise ValueError("resolution must be '720p' or '1080p'")
        
        if duration_seconds != "8":
            raise ValueError("Video generation using frames require duration_seconds='8'")
        
        if not first_image and not last_image:
            raise ValueError("Both first frame and last frame are required for video generation.")
        
        # Preparing images for input
        first_frame = self._prepare_image_input(first_image)
        last_frame = self._prepare_image_input(last_image)

        # Create Configurations
        kwargs = {
            "duration_seconds": duration_seconds,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
            "last_frame": last_frame,
        }

        # Negative prompt
        if negative_prompt:
            kwargs["negative_prompt"] = negative_prompt

        # Create a generation object
        operation = self.client.models.generate_videos(
            model=model,
            prompt=prompt,
            image=first_frame,
            config=types.GenerateVideosConfig(**kwargs),
        )

        # Polling
        while not operation.done:
            operation = self.client.operations.get(operation)
            time.sleep(1)
        
        # Check for video error after polling completes
        if getattr(operation, "error", None):
            raise RuntimeError(f"Video generation failed: {operation.error}")

        if operation.response is None:
            raise RuntimeError("Video generation completed but no response was returned")

        generated = getattr(operation.response, "generated_videos", None)
        if not generated:
            raise RuntimeError(
                f"No videos were generated. operation.error={getattr(operation, 'error', None)}; "
                f"operation_name={getattr(operation, 'name', None)}; response={operation.response}"
            )
        
        # Extract the generated video
        video = operation.response.generated_videos[0].video
        if not video:
            raise ValueError("Video was not generated.")

        # If Video bytes are returned
        if hasattr(video, 'video_bytes') and video.video_bytes:
            return video.video_bytes

        # Else download the file
        downloaded = self.client.files.download(file=video)

        if isinstance(downloaded, (bytes, bytearray)):
            return bytes(downloaded)
        
        if hasattr(downloaded, "read"):
            try:
                downloaded.seek(0)
            except Exception:
                pass
            return downloaded.read()
        
        if hasattr(downloaded, "bytes"):
            return downloaded.bytes
        
        if hasattr(downloaded, "data"):
            return downloaded.data
        
        if hasattr(downloaded, "content"):
            return downloaded.content

        raise ValueError("Error occured. Video cannot be generated...")