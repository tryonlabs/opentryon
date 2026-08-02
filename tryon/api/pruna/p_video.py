"""
Pruna P-Video — text/image/audio-conditioned video generation.

  Model header: p-video
  Docs: https://docs.api.pruna.ai/guides/models/p-video
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .client import MediaInput, PrunaClient

VALID_RESOLUTION = {"720p", "1080p"}
VALID_FPS = {24, 48}
VALID_ASPECT = {"16:9", "9:16", "4:3", "3:4", "3:2", "2:3", "1:1"}


class PVideoAdapter:
    """Pruna P-Video adapter (T2V / I2V / audio-conditioned)."""

    MODEL = "p-video"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self._client = PrunaClient(api_key=api_key, base_url=base_url)

    def _run(
        self,
        prompt: str,
        *,
        image: Optional[MediaInput] = None,
        audio: Optional[MediaInput] = None,
        last_frame_image: Optional[MediaInput] = None,
        duration: int = 5,
        resolution: str = "720p",
        fps: int = 24,
        aspect_ratio: str = "16:9",
        seed: Optional[int] = None,
        draft: bool = False,
        save_audio: bool = True,
        prompt_upsampling: bool = True,
        disable_safety_filter: bool = True,
        wait: bool = True,
        max_wait_time: int = 600,
        **kwargs: Any,
    ) -> bytes:
        if not prompt:
            raise ValueError("prompt is required.")
        if resolution not in VALID_RESOLUTION:
            raise ValueError(f"resolution must be one of {sorted(VALID_RESOLUTION)}")
        if int(fps) not in VALID_FPS:
            raise ValueError(f"fps must be one of {sorted(VALID_FPS)}")
        if aspect_ratio not in VALID_ASPECT:
            raise ValueError(f"aspect_ratio must be one of {sorted(VALID_ASPECT)}")
        if not (1 <= int(duration) <= 20):
            raise ValueError("duration must be between 1 and 20 seconds.")

        payload: Dict[str, Any] = {
            "prompt": prompt,
            "duration": int(duration),
            "resolution": resolution,
            "fps": int(fps),
            "aspect_ratio": aspect_ratio,
            "draft": bool(draft),
            "save_audio": bool(save_audio),
            "prompt_upsampling": bool(prompt_upsampling),
            "disable_safety_filter": bool(disable_safety_filter),
        }
        if seed is not None:
            payload["seed"] = int(seed)
        if image is not None:
            payload["image"] = self._client.prepare_url(
                image, default_filename="image.png"
            )
        if audio is not None:
            payload["audio"] = self._client.prepare_url(
                audio, default_filename="audio.mp3"
            )
        if last_frame_image is not None:
            payload["last_frame_image"] = self._client.prepare_url(
                last_frame_image, default_filename="last_frame.png"
            )
        payload.update(kwargs)

        url = self._client.predict(
            self.MODEL,
            payload,
            wait=wait,
            max_wait_time=max_wait_time,
            poll_interval=2.0,
            label="P-Video",
        )
        return self._client.download(url, timeout=180)

    def generate_text_to_video(self, prompt: str, **kwargs: Any) -> bytes:
        return self._run(prompt, **kwargs)

    def generate_image_to_video(
        self,
        prompt: str,
        image: MediaInput,
        **kwargs: Any,
    ) -> bytes:
        if image is None:
            raise ValueError("image is required for image-to-video.")
        return self._run(prompt, image=image, **kwargs)
