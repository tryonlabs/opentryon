"""
Anthropic Claude Multimodal Understanding API Adapter

Text and image understanding via Anthropic's Messages API. Currently exposes
Claude Haiku 5.5 (``claude-haiku-5-5``), the fastest/cheapest Claude tier built
for high-volume, latency-sensitive work such as classification, extraction and
routing (e.g. tagging garments, extracting care-label text, QC of try-on
outputs). Images only -- the Messages API does not accept video.

Reference: https://platform.claude.com/docs/en/models/haiku-5-5/overview
"""

from .adapter import ClaudeUnderstandAdapter

__all__ = ["ClaudeUnderstandAdapter"]
