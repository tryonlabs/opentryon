"""
Google Gemini 3.8 adapters.

- :class:`GeminiUnderstandAdapter` -- Gemini 3.8 Flash multimodal understanding
  (text, image, video, audio, PDF in; text out).
- :class:`GeminiTTSAdapter` -- Gemini 3.8 Flash / Flash-Lite TTS (text in; WAV
  audio out; 30 prebuilt voices, 130+ languages, single- and two-speaker).

Both use ``GEMINI_API_KEY`` (same key as Nano Banana / Veo / Omni).
"""

from .tts import GeminiTTSAdapter
from .understand import GeminiUnderstandAdapter

__all__ = ["GeminiUnderstandAdapter", "GeminiTTSAdapter"]
