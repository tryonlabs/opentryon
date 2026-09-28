"""
ElevenLabs Eleven v4 / Eleven v4 Turbo Text-to-Speech Adapter

First-party adapter for ElevenLabs' Text-to-Speech API
(https://api.elevenlabs.io) -- OpenTryOn's first ``tts`` service model.
Synchronous REST call: POST text + a voice id, get audio bytes back
directly (no job/poll cycle, unlike the video adapters).

Models:
- eleven_v4: "Most emotionally rich, expressive" model. 90+ languages,
  10,000 char limit (~10 min of audio).
- eleven_v4_turbo: Real-time-oriented sibling (~100ms median latency),
  adds audio tags for fine-grained delivery control (e.g. "[whispers]").

Voice-over for OpenTryOn lookbook/runway clips, or feeding a script into
Pruna's ``p-video-avatar`` (which accepts pre-generated ``--audio``) for a
talking-head avatar with a specific cloned/branded voice.

Reference:
https://elevenlabs.io/docs/api-reference/text-to-speech/convert
https://elevenlabs.io/docs/overview/models

Env:
  ELEVENLABS_API_KEY (required)
  ELEVENLABS_BASE_URL -- default https://api.elevenlabs.io

Examples:
    >>> from tryon.api.elevenlabs import ElevenLabsAdapter
    >>> adapter = ElevenLabsAdapter()  # eleven_v4 by default
    >>> audio = adapter.generate_speech("Welcome to the spring collection.")
    >>> open("voiceover.mp3", "wb").write(audio)
"""

from __future__ import annotations

import os
from typing import Optional

import requests

DEFAULT_BASE_URL = "https://api.elevenlabs.io"

VALID_MODELS = {
    "eleven_v4",
    "eleven_v4_turbo",
}

# ElevenLabs' well-known premade voice "Rachel" -- a sane, always-available
# default so callers can try the adapter without first looking up a voice id
# in their ElevenLabs account (https://elevenlabs.io/app/voice-library).
DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"

VALID_OUTPUT_FORMATS = {
    "mp3_22050_32", "mp3_24000_48", "mp3_44100_32", "mp3_44100_64",
    "mp3_44100_96", "mp3_44100_128", "mp3_44100_192",
    "pcm_8000", "pcm_16000", "pcm_22050", "pcm_24000", "pcm_32000",
    "pcm_44100", "pcm_48000",
    "wav_8000", "wav_16000", "wav_22050", "wav_24000", "wav_32000",
    "wav_44100", "wav_48000",
    "opus_48000_32", "opus_48000_64", "opus_48000_96", "opus_48000_128",
    "opus_48000_192",
    "ulaw_8000", "alaw_8000",
}


class ElevenLabsAdapter:
    """
    Adapter for ElevenLabs' Text-to-Speech API (Eleven v4 / v4 Turbo).

    Args:
        api_key: ElevenLabs key. Defaults to ``ELEVENLABS_API_KEY``.
        model: Default model id. Defaults to ``"eleven_v4"``.
        base_url: API base URL. Defaults to ``ELEVENLABS_BASE_URL`` or the
            official ElevenLabs endpoint.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "eleven_v4",
        base_url: Optional[str] = None,
    ):
        if model not in VALID_MODELS:
            raise ValueError(f"Invalid model: {model!r}. Supported models: {sorted(VALID_MODELS)}")

        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        if not self.api_key:
            raise ValueError(
                "ElevenLabs API key must be provided either as a parameter or "
                "through the ELEVENLABS_API_KEY environment variable."
            )

        self.model = model
        self.base_url = (
            base_url or os.getenv("ELEVENLABS_BASE_URL") or DEFAULT_BASE_URL
        ).rstrip("/")

    def generate_speech(
        self,
        text: str,
        voice_id: str = DEFAULT_VOICE_ID,
        model: Optional[str] = None,
        output_format: str = "mp3_44100_128",
        language_code: Optional[str] = None,
        stability: float = 0.5,
        similarity_boost: float = 0.75,
        style: float = 0.0,
        speed: float = 1.0,
        use_speaker_boost: bool = True,
        seed: Optional[int] = None,
    ) -> bytes:
        """Convert ``text`` to speech and return raw audio bytes.

        Args:
            text: Text to speak (Eleven v4: up to 10,000 characters).
            voice_id: ElevenLabs voice id. Defaults to the premade "Rachel"
                voice; find others at https://elevenlabs.io/app/voice-library
                or via ``GET /v1/voices``.
            model: ``"eleven_v4"`` or ``"eleven_v4_turbo"``. Defaults to the
                adapter's configured model.
            output_format: See ``VALID_OUTPUT_FORMATS``. Default matches the
                API's own default (``mp3_44100_128``).
            language_code: Optional ISO 639-1 code to force text
                normalization for a specific language.
            stability/similarity_boost/style/speed/use_speaker_boost: Voice
                settings; see the ElevenLabs docs for the emotional-range /
                voice-adherence tradeoffs.
            seed: Optional integer (0-4294967295) for deterministic sampling.
        """
        text = (text or "").strip()
        if not text:
            raise ValueError("text is required.")
        if not voice_id:
            raise ValueError("voice_id is required.")

        chosen_model = model or self.model
        if chosen_model not in VALID_MODELS:
            raise ValueError(
                f"Invalid model: {chosen_model!r}. Supported models: {sorted(VALID_MODELS)}"
            )
        if output_format not in VALID_OUTPUT_FORMATS:
            raise ValueError(
                f"Invalid output_format: {output_format!r}. "
                f"Supported values: {sorted(VALID_OUTPUT_FORMATS)}"
            )

        payload = {
            "text": text,
            "model_id": chosen_model,
            "voice_settings": {
                "stability": float(stability),
                "similarity_boost": float(similarity_boost),
                "style": float(style),
                "speed": float(speed),
                "use_speaker_boost": bool(use_speaker_boost),
            },
        }
        if language_code is not None:
            payload["language_code"] = language_code
        if seed is not None:
            payload["seed"] = int(seed)

        resp = requests.post(
            f"{self.base_url}/v1/text-to-speech/{voice_id}",
            headers={"xi-api-key": self.api_key, "Content-Type": "application/json"},
            params={"output_format": output_format},
            json=payload,
            timeout=120,
        )
        if resp.status_code >= 400:
            try:
                detail = resp.json()
            except Exception:
                detail = resp.text
            raise RuntimeError(
                f"ElevenLabs TTS API error ({resp.status_code}): {detail}"
            )
        return resp.content
