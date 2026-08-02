"""
Pruna P-Video-Replace — replace people in a source video with identity refs.

  Model header: p-video-replace
  Docs: https://docs.api.pruna.ai/guides/models/p-video-replace
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Union

from .client import MediaInput, PrunaClient

VALID_RESOLUTION = {"720p", "1080p"}
VALID_FPS = {"original", "24", "48"}


class PVideoReplaceAdapter:
    """Pruna P-Video-Replace adapter (source video + 1–3 identity images)."""

    MODEL = "p-video-replace"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self._client = PrunaClient(api_key=api_key, base_url=base_url)

    def generate_video_replace(
        self,
        video: MediaInput,
        images: Union[MediaInput, Sequence[MediaInput]],
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
            raise ValueError("video is required.")
        if not images:
            raise ValueError("At least one identity reference image is required.")
        if resolution not in VALID_RESOLUTION:
            raise ValueError(f"resolution must be one of {sorted(VALID_RESOLUTION)}")
        if str(target_fps) not in VALID_FPS:
            raise ValueError(f"target_fps must be one of {sorted(VALID_FPS)}")

        if isinstance(images, (list, tuple)):
            image_list: List[MediaInput] = list(images)
        else:
            image_list = [images]
        if not (1 <= len(image_list) <= 3):
            raise ValueError("P-Video-Replace accepts 1–3 identity reference images.")

        video_url = self._client.prepare_url(video, default_filename="source.mp4")
        image_urls = [
            self._client.prepare_url(img, default_filename="identity.png")
            for img in image_list
        ]

        payload: Dict[str, Any] = {
            "video": video_url,
            "images": image_urls,
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
            label="P-Video-Replace",
        )
        return self._client.download(url, timeout=180)
