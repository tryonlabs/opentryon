"""
Sage-A1.5 — Shanghai AI Laboratory agentic MoE (local SGLang / vLLM only).

Serve ``InternScience/Sage-A1.5`` with OpenAI-compatible ``/v1/chat/completions``.
No first-party hosted Sage-A1.5 HTTP API in OpenTryOn (Friendli and others are third-party).

Docs: https://huggingface.co/InternScience/Sage-A1.5
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

try:
    from openai import OpenAI

    _OPENAI_AVAILABLE = True
except ImportError:
    _OPENAI_AVAILABLE = False
    OpenAI = None

DEFAULT_BASE = "http://127.0.0.1:8000/v1"
DEFAULT_MODEL = "InternScience/Sage-A1.5"


class SageA15Adapter:
    """Local OpenAI-compatible client for Sage-A1.5."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        base_url: Optional[str] = None,
    ):
        if not _OPENAI_AVAILABLE:
            raise ImportError("OpenAI SDK required. Install: pip install openai")
        self.api_key = api_key or os.getenv("SAGE_A15_API_KEY") or "EMPTY"
        self.base_url = (base_url or os.getenv("SAGE_A15_BASE_URL") or DEFAULT_BASE).rstrip("/")
        self.model = model or DEFAULT_MODEL
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def understand(
        self,
        prompt: str,
        system: Optional[str] = None,
        verification: bool = False,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Text agent chat; optional verification mode via ``chat_template_kwargs``."""
        if verification and not (system or "").strip():
            raise ValueError("Sage-A1.5 verification mode requires a non-empty --system message.")
        if not (prompt or "").strip():
            raise ValueError("prompt is required.")
        messages: List[Dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        else:
            messages.append({"role": "system", "content": "You are a helpful assistant."})
        messages.append({"role": "user", "content": prompt})
        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
        }
        if max_tokens is not None:
            kwargs["max_tokens"] = int(max_tokens)
        if verification:
            kwargs["extra_body"] = {"chat_template_kwargs": {"verification": True}}
        response = self.client.chat.completions.create(**kwargs)
        msg = response.choices[0].message
        text = msg.content or ""
        reasoning = getattr(msg, "reasoning_content", None)
        if reasoning:
            text = f"{reasoning}\n\n{text}".strip()
        return {
            "text": text,
            "model": self.model,
            "verification": verification,
            "usage": getattr(response, "usage", None),
        }
