"""
Pruna P-Video-Avatar — talking-head video from a portrait + script or audio.

  Model header: p-video-avatar
  Docs: https://docs.api.pruna.ai/guides/models/p-video-avatar
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .client import MediaInput, PrunaClient

VALID_RESOLUTION = {"720p", "1080p"}

VALID_VOICES = {
    "Zephyr (Female)",
    "Puck (Male)",
    "Charon (Male)",
    "Kore (Female)",
    "Fenrir (Male)",
    "Leda (Female)",
    "Orus (Male)",
    "Aoede (Female)",
    "Callirrhoe (Female)",
    "Autonoe (Female)",
    "Enceladus (Male)",
    "Iapetus (Male)",
    "Umbriel (Male)",
    "Algenib (Male)",
    "Despina (Female)",
    "Erinome (Female)",
    "Laomedeia (Female)",
    "Achernar (Female)",
    "Algieba (Male)",
    "Schedar (Male)",
    "Gacrux (Female)",
    "Pulcherrima (Female)",
    "Achird (Male)",
    "Zubenelgenubi (Male)",
    "Vindemiatrix (Female)",
    "Sadachbia (Male)",
    "Sadaltager (Male)",
    "Sulafat (Female)",
    "Alnilam (Male)",
    "Rasalgethi (Male)",
}

VALID_LANGUAGES = {
    "English (US)",
    "English (UK)",
    "Spanish",
    "French",
    "German",
    "Italian",
    "Portuguese (Brazil)",
    "Japanese",
    "Korean",
    "Hindi",
}


class PVideoAvatarAdapter:
    """Pruna P-Video-Avatar adapter (portrait + voice_script and/or audio)."""

    MODEL = "p-video-avatar"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self._client = PrunaClient(api_key=api_key, base_url=base_url)

    def generate_video_avatar(
        self,
        image: MediaInput,
        voice_script: str = "",
        audio: Optional[MediaInput] = None,
        voice: str = "Zephyr (Female)",
        voice_language: str = "English (US)",
        resolution: str = "720p",
        video_prompt: str = "The person is talking.",
        voice_prompt: str = "Say the following.",
        negative_prompt: str = "",
        strength_negative_prompt: float = 0.5,
        seed: Optional[int] = None,
        disable_safety_filter: bool = True,
        disable_prompt_upsampling: bool = False,
        wait: bool = True,
        max_wait_time: int = 900,
        **kwargs: Any,
    ) -> bytes:
        if image is None:
            raise ValueError("image is required (portrait / first frame).")
        if not audio and not (voice_script or "").strip():
            raise ValueError(
                "Provide voice_script and/or audio (audio takes priority when both are set)."
            )
        if resolution not in VALID_RESOLUTION:
            raise ValueError(f"resolution must be one of {sorted(VALID_RESOLUTION)}")
        if voice not in VALID_VOICES:
            raise ValueError(f"voice must be one of {sorted(VALID_VOICES)}")
        if voice_language not in VALID_LANGUAGES:
            raise ValueError(f"voice_language must be one of {sorted(VALID_LANGUAGES)}")

        payload: Dict[str, Any] = {
            "image": self._client.prepare_url(image, default_filename="portrait.png"),
            "voice": voice,
            "voice_language": voice_language,
            "resolution": resolution,
            "video_prompt": video_prompt,
            "voice_prompt": voice_prompt,
            "negative_prompt": negative_prompt or "",
            "strength_negative_prompt": float(strength_negative_prompt),
            "disable_safety_filter": bool(disable_safety_filter),
            "disable_prompt_upsampling": bool(disable_prompt_upsampling),
        }
        if voice_script:
            payload["voice_script"] = voice_script
        if audio is not None:
            payload["audio"] = self._client.prepare_url(
                audio, default_filename="speech.mp3"
            )
        if seed is not None:
            payload["seed"] = int(seed)
        payload.update(kwargs)

        url = self._client.predict(
            self.MODEL,
            payload,
            wait=wait,
            max_wait_time=max_wait_time,
            poll_interval=2.0,
            label="P-Video-Avatar",
        )
        return self._client.download(url, timeout=180)
