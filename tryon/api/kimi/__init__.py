"""
Kimi (Moonshot AI) Multimodal Understanding API Adapter

This module provides an adapter for Moonshot AI's Kimi vision models:
- Kimi K2.6 (kimi-k2.6): General-purpose multimodal model. Text, image, and
  video understanding with optional "thinking" mode and 256K context.
- Kimi K2.7 Code (kimi-k2.7-code / kimi-k2.7-code-highspeed): Coding-focused
  multimodal model built on K2.6 with the same vision/video understanding
  capabilities, tuned for long-horizon agentic coding and tool use.

Unlike most other adapters in this repo, Kimi's understanding capabilities
are general-purpose -- useful for the fashion domain (describing garments,
outfits, lookbook videos) as well as any other domain (documents, UI
screenshots, product photography, etc.).

Reference: https://platform.kimi.ai/docs/overview
"""

from .adapter import KimiUnderstandAdapter

__all__ = [
    "KimiUnderstandAdapter",
]
