"""
Google Gemini Omni 1.1 Flash Video Generation API Adapter

Adapter for Gemini Omni 1.1 Flash (``gemini-omni-1.1-flash``, GA 27 Aug 2026)
-- Google's fast multimodal video generation / conversational editing model.
Uses the Interactions API via the ``google-genai`` SDK (not
``generate_videos`` / Veo). The earlier ``gemini-omni-flash-preview``
endpoint was deprecated on 30 Sep 2026 and is no longer accepted here.

Capabilities:
1) Text-to-video -- generate a short clip (3-10s, 24 FPS) from a prompt
2) Image-to-video -- animate a still (or multiple reference subjects) with a prompt
3) Conversational editing -- refine a prior generation via
   ``previous_interaction_id`` without re-uploading the video
4) Video extension -- append 3-10s to the end of an existing clip
   (input clip <= 10s) via the ``extend`` task
5) Resolution control -- ``360p`` / ``720p`` (default) / ``1080p`` / ``4k``

Reference:
    https://ai.google.dev/gemini-api/docs/omni
    https://ai.google.dev/gemini-api/docs/models/gemini-omni-flash
    https://deepmind.google/models/gemini-omni/
    https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-omni/

Authentication:
    Requires ``GEMINI_API_KEY`` (same key as Nano Banana / Veo).

Example:
    >>> adapter = GeminiOmniAdapter()
    >>> video = adapter.generate_text_to_video(
    ...     prompt="A fashion model walking a runway under soft studio lights",
    ...     aspect_ratio="9:16",
    ... )
    >>> with open("runway.mp4", "wb") as f:
    ...     f.write(video)
    >>> # Conversational edit using the interaction id from the prior turn
    >>> edited = adapter.edit_video(
    ...     prompt="Dim the lights and add a slow dolly-in",
    ...     previous_interaction_id=adapter.last_interaction_id,
    ... )
"""

from __future__ import annotations

import base64
import io
import mimetypes
import os
from typing import Any, Dict, List, Optional, Union

from PIL import Image

try:
    from google import genai
    GOOGLE_GENAI_AVAILABLE = True
except ImportError:
    GOOGLE_GENAI_AVAILABLE = False
    genai = None


ASPECT_RATIOS = {"16:9", "9:16"}
RESOLUTIONS = {"360p", "720p", "1080p", "4k"}
VIDEO_TASKS = {"text_to_video", "image_to_video", "reference_to_video", "edit", "extend"}
VALID_MODELS = {"gemini-omni-1.1-flash"}
DEFAULT_MODEL = "gemini-omni-1.1-flash"


class GeminiOmniAdapter:
    """
    Adapter for Gemini Omni 1.1 Flash (``gemini-omni-1.1-flash``) video generation.

    Uses ``client.interactions.create(...)`` and returns raw MP4 bytes.
    After each successful call, ``last_interaction_id`` is set so you can
    chain conversational edits without re-uploading prior video.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = DEFAULT_MODEL):
        """
        Initialize the Gemini Omni 1.1 Flash adapter.

        Args:
            api_key: Google Gemini API key. Defaults to ``GEMINI_API_KEY``.
            model: Omni model id. Only ``gemini-omni-1.1-flash`` is valid
                (the ``-preview`` endpoint was deprecated 30 Sep 2026).
        """
        if model not in VALID_MODELS:
            raise ValueError(
                f"Invalid model {model!r}. Supported: {sorted(VALID_MODELS)}. "
                "gemini-omni-flash-preview was deprecated on 30 Sep 2026."
            )
        self.model = model
        if not GOOGLE_GENAI_AVAILABLE:
            raise ImportError(
                "Google GenAI SDK is required for Gemini Omni. "
                "Install it with: pip install google-genai"
            )

        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Gemini API key is required. Set GEMINI_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self.client = genai.Client(api_key=self.api_key)
        self.last_interaction_id: Optional[str] = None

    def _guess_mime(self, path_or_name: str) -> str:
        mime, _ = mimetypes.guess_type(path_or_name)
        if mime and mime.startswith("image/"):
            return mime
        return "image/png"

    def _image_to_part(self, image_input: Union[str, io.BytesIO, Image.Image, bytes]) -> Dict[str, str]:
        """Convert an image input into an Interactions API image content dict."""
        mime = "image/png"
        data: bytes

        if isinstance(image_input, Image.Image):
            buffer = io.BytesIO()
            fmt = "PNG" if image_input.mode in ("RGBA", "LA", "P") else "JPEG"
            image_input.save(buffer, format=fmt)
            data = buffer.getvalue()
            mime = "image/png" if fmt == "PNG" else "image/jpeg"
        elif isinstance(image_input, (bytes, bytearray)):
            data = bytes(image_input)
        elif hasattr(image_input, "read"):
            image_input.seek(0)
            data = image_input.read()
        elif isinstance(image_input, str):
            if image_input.startswith(("http://", "https://")):
                import requests
                response = requests.get(image_input, timeout=60)
                response.raise_for_status()
                data = response.content
                mime = response.headers.get("Content-Type", "image/jpeg").split(";")[0].strip()
                if not mime.startswith("image/"):
                    mime = "image/jpeg"
            elif os.path.exists(image_input):
                mime = self._guess_mime(image_input)
                with open(image_input, "rb") as f:
                    data = f.read()
            else:
                try:
                    data = base64.b64decode(image_input, validate=True)
                except Exception as e:
                    raise ValueError(f"Invalid image input string: {e}")
        else:
            raise ValueError(
                "Invalid image input: must be a file path, URL, PIL Image, bytes, "
                "file-like object, or base64 string"
            )

        return {
            "type": "image",
            "data": base64.b64encode(data).decode("utf-8"),
            "mime_type": mime,
        }

    def _extract_video_bytes(self, interaction: Any) -> bytes:
        """Decode MP4 bytes from an Interactions API response."""
        # Preferred SDK convenience field
        output_video = getattr(interaction, "output_video", None)
        if output_video is not None:
            raw = getattr(output_video, "data", None)
            if isinstance(raw, (bytes, bytearray)):
                return bytes(raw)
            if isinstance(raw, str) and raw:
                return base64.b64decode(raw)

        # Fallback: walk steps -> model_output -> video content (REST shape)
        steps = getattr(interaction, "steps", None) or []
        for step in steps:
            step_type = step.get("type") if isinstance(step, dict) else getattr(step, "type", None)
            if step_type != "model_output":
                continue
            content = step.get("content") if isinstance(step, dict) else getattr(step, "content", None)
            if not content:
                continue
            for part in content:
                part_type = part.get("type") if isinstance(part, dict) else getattr(part, "type", None)
                if part_type != "video":
                    continue
                raw = part.get("data") if isinstance(part, dict) else getattr(part, "data", None)
                if isinstance(raw, (bytes, bytearray)):
                    return bytes(raw)
                if isinstance(raw, str) and raw:
                    return base64.b64decode(raw)

        status = getattr(interaction, "status", None)
        raise ValueError(
            f"No video found in Gemini Omni interaction response "
            f"(status={status!r}, id={getattr(interaction, 'id', None)!r})"
        )

    def _create_interaction(
        self,
        input_payload: Union[str, List[Dict[str, Any]]],
        *,
        aspect_ratio: Optional[str] = None,
        resolution: Optional[str] = None,
        task: Optional[str] = None,
        previous_interaction_id: Optional[str] = None,
        **kwargs,
    ) -> bytes:
        if aspect_ratio is not None and aspect_ratio not in ASPECT_RATIOS:
            raise ValueError(
                f"Invalid aspect_ratio '{aspect_ratio}'. Valid options: {sorted(ASPECT_RATIOS)}"
            )
        if resolution is not None and resolution not in RESOLUTIONS:
            raise ValueError(
                f"Invalid resolution '{resolution}'. Valid options: {sorted(RESOLUTIONS)}"
            )
        if task is not None and task not in VIDEO_TASKS:
            raise ValueError(f"Invalid task '{task}'. Valid options: {sorted(VIDEO_TASKS)}")

        create_kwargs: Dict[str, Any] = {
            "model": self.model,
            "input": input_payload,
        }
        if previous_interaction_id:
            create_kwargs["previous_interaction_id"] = previous_interaction_id

        response_format: Dict[str, Any] = {"type": "video"}
        if aspect_ratio:
            response_format["aspect_ratio"] = aspect_ratio
        if resolution:
            response_format["resolution"] = resolution
        create_kwargs["response_format"] = response_format

        if task:
            create_kwargs["generation_config"] = {"video_config": {"task": task}}

        create_kwargs.update(kwargs)

        interaction = self.client.interactions.create(**create_kwargs)
        self.last_interaction_id = getattr(interaction, "id", None)

        status = getattr(interaction, "status", None)
        if status and status not in ("completed", "complete"):
            # Some SDK versions may still return an in-progress interaction;
            # surface a clear error rather than silently returning empty bytes.
            err = getattr(interaction, "error", None)
            if status in ("failed", "cancelled", "canceled"):
                raise ValueError(f"Gemini Omni interaction {status}: {err or interaction}")

        return self._extract_video_bytes(interaction)

    def generate_text_to_video(
        self,
        prompt: str,
        aspect_ratio: str = "16:9",
        resolution: Optional[str] = None,
        previous_interaction_id: Optional[str] = None,
        video: Optional[str] = None,
        **kwargs,
    ) -> bytes:
        """
        Generate (or conversationally edit / extend) a video from a text prompt.

        When ``previous_interaction_id`` is set, this becomes an edit turn on
        the prior generation (same as :meth:`edit_video`). When ``video`` is
        set, the clip is extended (same as :meth:`extend_video`).

        Args:
            prompt: Scene / edit description.
            aspect_ratio: ``16:9`` (default) or ``9:16``.
            resolution: ``360p``, ``720p`` (API default), ``1080p`` or ``4k``.
            previous_interaction_id: Optional prior interaction id for editing.
            video: Optional existing clip (local path or Gemini Files / http(s)
                URI, <= 10s) to extend by 3-10s.
            **kwargs: Extra kwargs forwarded to ``interactions.create``.

        Returns:
            Raw MP4 video bytes.
        """
        if not prompt:
            raise ValueError("prompt is required")
        if video and previous_interaction_id:
            raise ValueError("Pass either video (extend) or previous_interaction_id (edit), not both.")
        if video:
            return self.extend_video(
                video, prompt, aspect_ratio=aspect_ratio, resolution=resolution, **kwargs
            )

        task = "edit" if previous_interaction_id else "text_to_video"
        return self._create_interaction(
            prompt,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            task=task,
            previous_interaction_id=previous_interaction_id,
            **kwargs,
        )

    def _video_to_part(self, video: str) -> Dict[str, str]:
        """Return a ``{"type": "video", "uri": ...}`` part, uploading a local
        file through the Files API (and waiting for ACTIVE) when needed."""
        import time

        if video.startswith(("http://", "https://", "gs://")) or "/files/" in video:
            return {"type": "video", "uri": video}
        if not os.path.exists(video):
            raise ValueError(f"Video path does not exist: {video}")

        uploaded = self.client.files.upload(file=video)
        deadline = time.time() + 300
        while getattr(getattr(uploaded, "state", None), "name", str(getattr(uploaded, "state", ""))) in (
            "PROCESSING",
            "State.PROCESSING",
        ):
            if time.time() > deadline:
                raise TimeoutError("Timed out waiting for the uploaded video to become ACTIVE.")
            time.sleep(2)
            uploaded = self.client.files.get(name=uploaded.name)
        return {"type": "video", "uri": uploaded.uri}

    def extend_video(
        self,
        video: str,
        prompt: str,
        aspect_ratio: Optional[str] = None,
        resolution: Optional[str] = None,
        **kwargs,
    ) -> bytes:
        """
        Extend an existing clip by 3-10 seconds (``extend`` task).

        Args:
            video: Local path, or an http(s) / Gemini Files URI. Input clip
                must be <= 10s; extension only appends to the end.
            prompt: How the scene should continue.
            aspect_ratio: Optional override.
            resolution: Optional ``360p`` / ``720p`` / ``1080p`` / ``4k``.

        Returns:
            Raw MP4 bytes for the extended clip.
        """
        if not video:
            raise ValueError("video is required for extend_video")
        if not prompt:
            raise ValueError("prompt is required")
        parts: List[Dict[str, Any]] = [
            self._video_to_part(video),
            {"type": "text", "text": prompt},
        ]
        return self._create_interaction(
            parts,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            task="extend",
            **kwargs,
        )

    def generate_image_to_video(
        self,
        image: Union[str, io.BytesIO, Image.Image],
        prompt: str,
        aspect_ratio: str = "16:9",
        reference_images: Optional[List[Union[str, io.BytesIO, Image.Image]]] = None,
        previous_interaction_id: Optional[str] = None,
        resolution: Optional[str] = None,
        **kwargs,
    ) -> bytes:
        """
        Animate a still image (optionally with extra subject references).

        Args:
            image: Primary reference image (path, URL, PIL, bytes, or base64).
            prompt: Motion / scene description.
            aspect_ratio: ``16:9`` or ``9:16``.
            reference_images: Optional additional subject/style reference images.
            previous_interaction_id: Optional prior interaction id for editing.
            **kwargs: Extra kwargs forwarded to ``interactions.create``.

        Returns:
            Raw MP4 video bytes.
        """
        if image is None:
            raise ValueError("image is required")
        if not prompt:
            raise ValueError("prompt is required")

        parts: List[Dict[str, Any]] = [self._image_to_part(image)]
        if reference_images:
            for ref in reference_images:
                parts.append(self._image_to_part(ref))
        parts.append({"type": "text", "text": prompt})

        task = "edit" if previous_interaction_id else (
            "reference_to_video" if reference_images else "image_to_video"
        )
        return self._create_interaction(
            parts,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            task=task,
            previous_interaction_id=previous_interaction_id,
            **kwargs,
        )

    def edit_video(
        self,
        prompt: str,
        previous_interaction_id: Optional[str] = None,
        aspect_ratio: Optional[str] = None,
        resolution: Optional[str] = None,
        **kwargs,
    ) -> bytes:
        """
        Conversationally edit a previously generated Omni video.

        Args:
            prompt: Edit instruction, e.g. ``"Make the violin invisible"``.
            previous_interaction_id: Prior interaction id. Defaults to
                ``self.last_interaction_id`` from the most recent generation.
            aspect_ratio: Optional override; omit to keep the prior clip's ratio.
            **kwargs: Extra kwargs forwarded to ``interactions.create``.

        Returns:
            Raw MP4 video bytes for the edited clip.
        """
        if not prompt:
            raise ValueError("prompt is required")

        interaction_id = previous_interaction_id or self.last_interaction_id
        if not interaction_id:
            raise ValueError(
                "previous_interaction_id is required for edit_video "
                "(or call generate_* first so last_interaction_id is set)."
            )

        return self._create_interaction(
            prompt,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            task="edit",
            previous_interaction_id=interaction_id,
            **kwargs,
        )
