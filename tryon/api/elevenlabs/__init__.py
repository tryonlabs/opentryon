"""
ElevenLabs Text-to-Speech API Adapter

Eleven v4 / Eleven v4 Turbo via ElevenLabs' first-party REST API.
OpenTryOn's first ``tts`` service model. See
:mod:`tryon.api.elevenlabs.adapter` for details.
"""

from .adapter import ElevenLabsAdapter

__all__ = [
    "ElevenLabsAdapter",
]
