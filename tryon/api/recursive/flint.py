"""
Recursive Flint — coding agent LLM (local SGLang or OpenRouter).

Path B (local): serve ``RecursiveSI/flint`` with the repo SGLang kit
(``http://127.0.0.1:30000/v1``, model id ``flint``).

Path A (hosted): OpenRouter ``recursive/flint-v1.0:free`` (third-party aggregator;
no first-party Flint HTTP API).

Docs: https://huggingface.co/RecursiveSI/flint
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

LOCAL_DEFAULT_BASE = "http://127.0.0.1:30000/v1"
OPENROUTER_BASE = "https://openrouter.ai/api/v1"
LOCAL_MODEL = "flint"
OPENROUTER_MODEL = "recursive/flint-v1.0:free"
VALID_ENDPOINTS = {"local", "openrouter"}


class FlintAdapter:
    """OpenAI-compatible chat client for Recursive Flint."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        endpoint: str = "local",
        max_tokens: int = 8192,
    ):
        if not _OPENAI_AVAILABLE:
            raise ImportError("OpenAI SDK required. Install: pip install openai")
        serving = (endpoint or "local").strip().lower()
        if serving not in VALID_ENDPOINTS:
            raise ValueError(f"endpoint must be one of {sorted(VALID_ENDPOINTS)}")
        self.endpoint = serving
        self.max_tokens = int(max_tokens)
        if serving == "openrouter":
            self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
            if not self.api_key:
                raise ValueError("Set OPENROUTER_API_KEY for OpenRouter Flint.")
            self.base_url = (base_url or OPENROUTER_BASE).rstrip("/")
            self.model = model or OPENROUTER_MODEL
        else:
            self.api_key = api_key or os.getenv("FLINT_API_KEY") or "unused"
            self.base_url = (base_url or os.getenv("FLINT_BASE_URL") or LOCAL_DEFAULT_BASE).rstrip("/")
            self.model = model or LOCAL_MODEL
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def understand(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Text-in → text-out (Flint is not a vision model)."""
        if not (prompt or "").strip():
            raise ValueError("prompt is required.")
        messages: List[Dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens or self.max_tokens,
        )
        msg = response.choices[0].message
        text = msg.content or ""
        reasoning = getattr(msg, "reasoning_content", None)
        if reasoning:
            text = f"{reasoning}\n\n{text}".strip()
        return {
            "text": text,
            "model": self.model,
            "endpoint": self.endpoint,
            "usage": getattr(response, "usage", None),
        }
