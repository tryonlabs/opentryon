"""
Pruna P-Video-2-Pro — fast, natively-audio text/image-conditioned video.

Pruna's own optimized endpoint built on MiniMax H3 (launched 17 Sep 2026).
Faster and cheaper than :class:`~tryon.api.pruna.p_video.PVideoAdapter`;
generated audio is always included and cannot be supplied as an input
(unlike ``p-video``, which accepts a conditioning ``audio`` file).

  Model header: p-video-2-pro
  Docs: https://docs.pruna.ai/en/stable/docs_pruna_endpoints/performance_models/p-video-2-pro.html
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .client import MediaInput, PrunaClient

VALID_RESOLUTION = {"480p", "768p"}
VALID_ASPECT = {"16:9", "9:16", "4:3", "3:4", "3:2", "2:3", "1:1"}
VALID_MODE = {"speed", "quality"}
VALID_PROMPT_UPSAMPLER = {"off", "turbo", "max"}


class PVideo2ProAdapter:
    """Pruna P-Video-2-Pro adapter (T2V / I2V, MiniMax H3-based, native audio)."""

    MODEL = "p-video-2-pro"

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
        last_frame_image: Optional[MediaInput] = None,
        duration: int = 5,
        resolution: str = "768p",
        aspect_ratio: str = "16:9",
        mode: str = "speed",
        prompt_upsampler: str = "turbo",
        seed: Optional[int] = None,
        wait: bool = True,
        max_wait_time: int = 600,
        **kwargs: Any,
    ) -> bytes:
        if not prompt:
            raise ValueError("prompt is required.")
        if resolution not in VALID_RESOLUTION:
            raise ValueError(f"resolution must be one of {sorted(VALID_RESOLUTION)}")
        if aspect_ratio not in VALID_ASPECT:
            raise ValueError(f"aspect_ratio must be one of {sorted(VALID_ASPECT)}")
        if mode not in VALID_MODE:
            raise ValueError(f"mode must be one of {sorted(VALID_MODE)}")
        if prompt_upsampler not in VALID_PROMPT_UPSAMPLER:
            raise ValueError(
                f"prompt_upsampler must be one of {sorted(VALID_PROMPT_UPSAMPLER)}"
            )
        if not (5 <= int(duration) <= 15):
            raise ValueError("duration must be between 5 and 15 seconds.")

        payload: Dict[str, Any] = {
            "prompt": prompt,
            "duration": int(duration),
            "resolution": resolution,
            "aspect_ratio": aspect_ratio,
            "mode": mode,
            "prompt_upsampler": prompt_upsampler,
        }
        if seed is not None:
            payload["seed"] = int(seed)
        if image is not None:
            payload["image"] = self._client.prepare_url(
                image, default_filename="image.png"
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
            label="P-Video-2-Pro",
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
