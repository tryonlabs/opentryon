"""
Google Gemini 3.8 adapters.

- :class:`GeminiUnderstandAdapter` -- Gemini 3.8 Flash multimodal understanding
  (text, image, video, audio, PDF in; text out).
- :class:`GeminiTTSAdapter` -- Gemini 3.8 Flash / Flash-Lite TTS (text in; WAV
  audio out; 30 prebuilt voices, 130+ languages, single- and two-speaker).
- :class:`GeminiEmbeddingAdapter` -- Gemini Embedding 2 (text, image, audio, video, PDF into
  one embedding space; Matryoshka 128-3072 dims).

Both use ``GEMINI_API_KEY`` (same key as Nano Banana / Veo / Omni).
"""

from .embed import GeminiEmbeddingAdapter
from .tts import GeminiTTSAdapter
from .understand import GeminiUnderstandAdapter

__all__ = ["GeminiUnderstandAdapter", "GeminiTTSAdapter", "GeminiEmbeddingAdapter"]
