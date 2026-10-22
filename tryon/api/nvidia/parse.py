"""
NVIDIA Nemotron Parse — document image → markdown (+ optional bounding boxes).

Hosted NIM: ``nvidia/nemotron-parse`` on ``https://integrate.api.nvidia.com/v1``.
Local: Nemotron Parse NIM Docker on ``http://127.0.0.1:8000/v1`` (``NEMOTRON_PARSE_BASE_URL``).

Docs:
  https://docs.api.nvidia.com/nim/reference/nvidia-nemotron-parse-infer
  https://docs.nvidia.com/nim/vision-language-models/1.5.0/examples/nemotron-parse/api.html
"""

from __future__ import annotations

import base64
import io
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import requests
from PIL import Image

try:
    from openai import OpenAI

    _OPENAI_AVAILABLE = True
except ImportError:
    _OPENAI_AVAILABLE = False
    OpenAI = None

from .adapter import _resolve_nvidia_key, DEFAULT_BASE_URL, _pass_or_data_uri

NEMOTRON_PARSE_MODEL = "nvidia/nemotron-parse"
VALID_TOOLS = {"markdown_bbox", "markdown_no_bbox", "detection_only"}
DEFAULT_TOOL = "markdown_bbox"

ImageInput = Union[str, Path, io.BytesIO, bytes, Image.Image]


class NemotronParseAdapter:
    """Parse document/page images to markdown (hosted NIM or local OpenAI-compatible server)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = NEMOTRON_PARSE_MODEL,
        base_url: Optional[str] = None,
        endpoint: str = "nim",
    ):
        if not _OPENAI_AVAILABLE:
            raise ImportError("OpenAI SDK required. Install: pip install openai")
        serving = (endpoint or "nim").strip().lower()
        if serving not in {"nim", "local"}:
            raise ValueError("endpoint must be 'nim' or 'local'.")
        self.endpoint = serving
        if serving == "local":
            self.api_key = api_key or os.getenv("NEMOTRON_PARSE_API_KEY") or "EMPTY"
            self.base_url = (
                base_url or os.getenv("NEMOTRON_PARSE_BASE_URL") or "http://127.0.0.1:8000/v1"
            ).rstrip("/")
        else:
            self.api_key = _resolve_nvidia_key(api_key)
            self.base_url = (
                base_url or os.getenv("NVIDIA_API_BASE_URL") or DEFAULT_BASE_URL
            ).rstrip("/")
        self.model = model or NEMOTRON_PARSE_MODEL
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    @staticmethod
    def _extract_tool_payload(message: Any) -> Dict[str, Any]:
        """Parse tool call arguments from the assistant message."""
        tool_calls = getattr(message, "tool_calls", None) or []
        for call in tool_calls:
            fn = getattr(call, "function", None)
            if fn is None:
                continue
            args = getattr(fn, "arguments", None) or "{}"
            try:
                return json.loads(args)
            except json.JSONDecodeError:
                return {"raw_arguments": args}
        content = getattr(message, "content", None) or ""
        if content.strip():
            return {"markdown": content, "blocks": []}
        return {"markdown": "", "blocks": []}

    def parse_document(
        self,
        image: ImageInput,
        tool: str = DEFAULT_TOOL,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Parse a document image to markdown (and bounding boxes when ``tool=markdown_bbox``).

        Args:
            image: Path, URL, bytes, or PIL image (required).
            tool: ``markdown_bbox`` (default), ``markdown_no_bbox``, or ``detection_only``.
            max_tokens: Optional cap on model output tokens.
        """
        if tool not in VALID_TOOLS:
            raise ValueError(f"tool must be one of {sorted(VALID_TOOLS)}")
        url = _pass_or_data_uri(image, "image", "png", "image", {"jpg": "jpeg"})
        messages = [
            {
                "role": "user",
                "content": [{"type": "image_url", "image_url": {"url": url}}],
            }
        ]
        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "tools": [{"type": "function", "function": {"name": tool}}],
        }
        if max_tokens is not None:
            kwargs["max_tokens"] = int(max_tokens)
        response = self.client.chat.completions.create(**kwargs)
        message = response.choices[0].message
        payload = self._extract_tool_payload(message)
        return {
            "model": self.model,
            "tool": tool,
            "endpoint": self.endpoint,
            "markdown": payload.get("markdown") or payload.get("text") or "",
            "blocks": payload.get("blocks") or payload.get("regions") or [],
            "raw": payload,
        }
