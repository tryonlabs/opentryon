"""
Gemini 3.8 Flash TTS / Flash-Lite TTS Adapter

Text-to-speech through the Gemini API Interactions endpoint
(``POST /v1beta/interactions``), called over plain REST so it does not depend
on a recent ``google-genai`` (the docs recommend >= 2.25.0).

Models:
- ``gemini-3.8-flash-tts``      -- maximum expressiveness, complex multi-speaker; 130+ languages
- ``gemini-3.8-flash-lite-tts`` -- faster / cheaper for high volume; 100+ languages

Features:
- 30 prebuilt voices (Kore, Puck, Charon, Zephyr, ...), the extended voice
  library, and custom ``voice_...`` / ``voicekey_...`` ids (designed or replicated voices)
- Turn-level ``style`` (emotion, pace, accent) via a ``speech_metadata`` annotation
- Inline tags such as ``<sigh>``, ``<laugh>``, ``<short pause>``, ``<long pause>`` inside the
  text (use English tags even for non-English transcripts); the transcript is read **verbatim**,
  so keep stage directions in ``style``
- Up to **two** speakers in one request when both use prebuilt voices
- Output: 24 kHz mono 16-bit WAV by default; ``audio/l16`` (raw PCM), ``audio/mulaw`` or
  ``audio/alaw`` with ``sample_rate`` 24000 / 16000 / 8000

Text in, audio out only -- no image/video input.

Reference:
https://ai.google.dev/gemini-api/docs/speech-generation
https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash-tts

Env:
  GEMINI_API_KEY (required)
  GEMINI_API_BASE_URL (optional, default https://generativelanguage.googleapis.com)

Examples:
    >>> from tryon.api.gemini import GeminiTTSAdapter
    >>> adapter = GeminiTTSAdapter()
    >>> wav = adapter.generate_speech("Welcome to the spring collection.", voice="Kore", style="warm and upbeat")
    >>> open("hello.wav", "wb").write(wav)
    >>> wav = adapter.generate_dialogue(
    ...     [{"speaker": "Joe", "text": "Which look is your favourite?", "style": "curious"},
    ...      {"speaker": "Jane", "text": "The linen set <short pause> by far.", "style": "relaxed"}],
    ...     speakers={"Joe": "Puck", "Jane": "Kore"},
    ... )
"""

from __future__ import annotations

import base64
import os
from typing import Any, Dict, List, Mapping, Optional

import requests

DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com"
VALID_MODELS = {"gemini-3.8-flash-tts", "gemini-3.8-flash-lite-tts"}
PREBUILT_VOICES = (
    "Zephyr", "Puck", "Charon", "Kore", "Fenrir", "Leda", "Orus", "Aoede", "Callirrhoe", "Autonoe",
    "Enceladus", "Iapetus", "Umbriel", "Algieba", "Despina", "Erinome", "Algenib", "Rasalgethi",
    "Laomedeia", "Achernar", "Alnilam", "Schedar", "Gacrux", "Pulcherrima", "Achird",
    "Zubenelgenubi", "Vindemiatrix", "Sadachbia", "Sadaltager", "Sulafat",
)
AUDIO_MIME_TYPES = {"audio/wav", "audio/l16", "audio/mulaw", "audio/alaw"}
SAMPLE_RATES = {8000, 16000, 24000}
DEFAULT_VOICE = "Kore"
MAX_SPEAKERS = 2


def _is_custom_voice(voice: str) -> bool:
    return voice.startswith(("voice_", "voicekey_"))


def _load_turns(dialogue: Any) -> List[Mapping[str, Any]]:
    """Accept a list of turns, a JSON string, or a path to a JSON file."""
    import json

    if isinstance(dialogue, str):
        raw = dialogue.strip()
        if os.path.isfile(raw):
            with open(raw, "r", encoding="utf-8") as f:
                raw = f.read()
        try:
            dialogue = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"dialogue must be a list, a JSON string, or a JSON file path ({exc}).") from exc
    if not isinstance(dialogue, list) or not dialogue:
        raise ValueError('dialogue must be a non-empty list of {"speaker", "text", "style"?} turns.')
    return dialogue


def _parse_speakers(speakers: Any) -> Dict[str, str]:
    """Accept ``{"Joe": "Puck"}`` or ``["Joe=Puck", "Jane=Kore"]``."""
    if not speakers:
        raise ValueError("speakers is required with dialogue (two Name=Voice entries).")
    if isinstance(speakers, Mapping):
        return dict(speakers)
    parsed: Dict[str, str] = {}
    for item in speakers:
        name, sep, voice = str(item).partition("=")
        if not sep or not name.strip() or not voice.strip():
            raise ValueError(f"speaker entries must look like Name=Voice (got {item!r}).")
        parsed[name.strip()] = voice.strip()
    return parsed


class GeminiTTSAdapter:
    """
    Gemini 3.8 TTS client.

    Args:
        api_key: Defaults to ``GEMINI_API_KEY``.
        model: ``gemini-3.8-flash-tts`` (default) or ``gemini-3.8-flash-lite-tts``.
        base_url: Defaults to ``GEMINI_API_BASE_URL`` or the public Gemini API host.
        timeout: HTTP timeout in seconds.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-3.8-flash-tts",
        base_url: Optional[str] = None,
        timeout: float = 120.0,
    ):
        if model not in VALID_MODELS:
            raise ValueError(f"Invalid model: {model!r}. Supported models: {sorted(VALID_MODELS)}")
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API key is required. Set GEMINI_API_KEY or pass api_key.")
        self.model = model
        self.base_url = (base_url or os.getenv("GEMINI_API_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout

    # -- helpers --------------------------------------------------------

    @staticmethod
    def _check_voice(voice: str) -> str:
        if not voice:
            raise ValueError("voice is required.")
        if voice not in PREBUILT_VOICES and not _is_custom_voice(voice):
            raise ValueError(
                f"Unknown voice {voice!r}. Use one of the prebuilt voices {list(PREBUILT_VOICES)} "
                "or a custom 'voice_...' / 'voicekey_...' id."
            )
        return voice

    @staticmethod
    def _response_format(mime_type: str, sample_rate: Optional[int]) -> Dict[str, Any]:
        if mime_type not in AUDIO_MIME_TYPES:
            raise ValueError(f"mime_type must be one of {sorted(AUDIO_MIME_TYPES)} (got {mime_type!r}).")
        fmt: Dict[str, Any] = {"type": "audio"}
        if mime_type != "audio/wav":  # WAV (24 kHz mono 16-bit) is the API default
            fmt["mime_type"] = mime_type
        if sample_rate is not None:
            if int(sample_rate) not in SAMPLE_RATES:
                raise ValueError(f"sample_rate must be one of {sorted(SAMPLE_RATES)} (got {sample_rate}).")
            fmt["sample_rate"] = int(sample_rate)
        return fmt

    @staticmethod
    def _turn(text: str, style: Optional[str], speaker: Optional[str]) -> Dict[str, Any]:
        if not text or not text.strip():
            raise ValueError("text is required for every turn.")
        meta: Dict[str, Any] = {"type": "speech_metadata"}
        if style:
            meta["style"] = style
        if speaker:
            meta["speaker"] = speaker
        item: Dict[str, Any] = {"type": "text", "text": text}
        if len(meta) > 1:
            item["annotations"] = [meta]
        return item

    def _post(self, body: Dict[str, Any]) -> bytes:
        resp = requests.post(
            f"{self.base_url}/v1beta/interactions",
            headers={"x-goog-api-key": self.api_key, "Content-Type": "application/json"},
            json=body,
            timeout=self.timeout,
        )
        if resp.status_code != 200:
            raise RuntimeError(f"Gemini TTS API error ({resp.status_code}): {resp.text[:500]}")
        data = resp.json()
        audio = None
        for step in data.get("steps", []):  # last audio block wins (matches SDK `output_audio`)
            for block in step.get("content", []) or []:
                if block.get("type") == "audio" and block.get("data"):
                    audio = block["data"]
        if audio is None:
            raise RuntimeError(f"Gemini TTS returned no audio. Response: {str(data)[:500]}")
        return base64.b64decode(audio)

    # -- public API ---------------------------------------------------------

    def generate_speech(
        self,
        text: Optional[str] = None,
        voice: str = DEFAULT_VOICE,
        style: Optional[str] = None,
        mime_type: str = "audio/wav",
        sample_rate: Optional[int] = None,
        dialogue: Optional[Any] = None,
        speakers: Optional[Any] = None,
    ) -> bytes:
        """TTS entry point (single speaker, or two speakers when ``dialogue`` is given).
        Returns audio bytes (WAV unless ``mime_type`` says otherwise).

        Args:
            text: verbatim transcript; inline tags like ``<sigh>`` / ``<short pause>`` allowed.
                Required unless ``dialogue`` is given.
            voice: prebuilt voice name (default ``Kore``) or a custom ``voice_...`` id.
            style: delivery direction, e.g. "cheerful and friendly" (not spoken).
            dialogue: two-speaker mode -- a list of ``{"speaker", "text", "style"?}`` turns, a JSON
                string, or a path to a JSON file. Requires ``speakers``.
            speakers: speaker -> voice mapping, or a list of ``"Name=Voice"`` strings (exactly two).
        """
        if dialogue is not None:
            if text:
                raise ValueError("Pass either text (single speaker) or dialogue (two speakers), not both.")
            return self.generate_dialogue(
                _load_turns(dialogue), _parse_speakers(speakers), mime_type=mime_type, sample_rate=sample_rate
            )
        if speakers:
            raise ValueError("speakers is only used with dialogue.")
        body = {
            "model": self.model,
            "input": [{"type": "user_input", "content": [self._turn(text, style, None)]}],
            "response_format": self._response_format(mime_type, sample_rate),
            "generation_config": {"speech_config": [{"voice": self._check_voice(voice)}]},
        }
        return self._post(body)

    def generate_dialogue(
        self,
        turns: List[Mapping[str, Any]],
        speakers: Mapping[str, str],
        mime_type: str = "audio/wav",
        sample_rate: Optional[int] = None,
    ) -> bytes:
        """Two-speaker TTS.

        Args:
            turns: ``[{"speaker": "Joe", "text": "...", "style": "optional"}, ...]``.
            speakers: speaker name -> voice, exactly two entries (prebuilt voices only in one request).
        """
        if len(speakers) != MAX_SPEAKERS:
            raise ValueError(f"Exactly {MAX_SPEAKERS} speakers are required for dialogue (got {len(speakers)}).")
        if any(_is_custom_voice(v) for v in speakers.values()):
            raise ValueError(
                "Custom (voice_... / voicekey_...) voices cannot be combined in one multi-speaker request; "
                "synthesize each speaker's turn separately."
            )
        if not turns:
            raise ValueError("turns must be a non-empty list.")
        content = []
        for i, turn in enumerate(turns):
            speaker = turn.get("speaker")
            if speaker not in speakers:
                raise ValueError(f"turn {i}: speaker {speaker!r} is not in speakers {list(speakers)}.")
            content.append(self._turn(turn.get("text", ""), turn.get("style"), speaker))
        body = {
            "model": self.model,
            "input": [{"type": "user_input", "content": content}],
            "response_format": self._response_format(mime_type, sample_rate),
            "generation_config": {
                "speech_config": {
                    "speakers": [
                        {"speaker": name, "voice": self._check_voice(voice)} for name, voice in speakers.items()
                    ]
                }
            },
        }
        return self._post(body)
