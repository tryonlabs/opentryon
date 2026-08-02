"""
Pruna P-Video-Animate — animate a subject using motion from a source video.

  Model header: p-video-animate
  Docs: https://docs.api.pruna.ai/guides/models/p-video-animate
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .client import MediaInput, PrunaClient

VALID_RESOLUTION = {"720p", "1080p"}
VALID_FPS = {"original", "24", "48"}


class PVideoAnimateAdapter:
    """Pruna P-Video-Animate adapter (source video + subject reference image)."""

    MODEL = "p-video-animate"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self._client = PrunaClient(api_key=api_key, base_url=base_url)

    def generate_video_animate(
        self,
        video: MediaInput,
        image: MediaInput,
        instruction_prompt: str = "",
        resolution: str = "720p",
        target_fps: str = "original",
        turbo: bool = False,
        save_audio: bool = True,
        ignore_audio: bool = False,
        seed: Optional[int] = None,
        disable_safety_checker: bool = False,
        wait: bool = True,
        max_wait_time: int = 900,
        **kwargs: Any,
    ) -> bytes:
        if video is None:
            raise ValueError("video is required (motion / audio source).")
        if image is None:
            raise ValueError("image is required (subject reference).")
        if resolution not in VALID_RESOLUTION:
            raise ValueError(f"resolution must be one of {sorted(VALID_RESOLUTION)}")
        if str(target_fps) not in VALID_FPS:
            raise ValueError(f"target_fps must be one of {sorted(VALID_FPS)}")

        payload: Dict[str, Any] = {
            "video": self._client.prepare_url(video, default_filename="source.mp4"),
            "image": self._client.prepare_url(image, default_filename="subject.png"),
            "instruction_prompt": instruction_prompt or "",
            "resolution": resolution,
            "target_fps": str(target_fps),
            "turbo": bool(turbo),
            "save_audio": bool(save_audio),
            "ignore_audio": bool(ignore_audio),
            "disable_safety_checker": bool(disable_safety_checker),
        }
        if seed is not None:
            payload["seed"] = int(seed)
        payload.update(kwargs)

        url = self._client.predict(
            self.MODEL,
            payload,
            wait=wait,
            max_wait_time=max_wait_time,
            poll_interval=2.0,
            label="P-Video-Animate",
        )
        return self._client.download(url, timeout=180)
