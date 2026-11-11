"""
Ricursive Ripple-65B Preview -- open-weight coding / agent LLM (text only).

Ripple-65B Preview (Ricursive Intelligence, Apache-2.0) is a 65B dense Transformer
with a 1M-token context, tuned for agentic coding (Terminal-Bench 2.1 80.5, vendor
reported). It is **text only** -- there is no image or video input -- so in OpenTryOn
it sits in the ``understand`` service as a named-model-only text model, the same way
``flint-*`` and ``beam`` do.

Ricursive has no first-party HTTP API. Two ways to run it:

- ``endpoint="openrouter"``: OpenRouter model ``ricursiveai/ripple-65b-preview``
  (third-party aggregator; Together AI, GMI Cloud and Fireworks also host it).
  Needs ``OPENROUTER_API_KEY``.
- ``endpoint="local"``: any OpenAI-compatible server you run yourself (vLLM, SGLang)
  serving ``ricursiveAI/Ripple-65B-Preview`` (BF16) or the ``-NVFP4`` checkpoint.
  Default ``http://127.0.0.1:8000/v1`` (override with ``RIPPLE_BASE_URL``). The model
  card gives no serve command, so the server setup is up to you.

Docs:
  https://www.ricursive.com/ripple
  https://huggingface.co/ricursiveAI/Ripple-65B-Preview
  https://openrouter.ai/ricursiveai/ripple-65b-preview
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

OPENROUTER_BASE = "https://openrouter.ai/api/v1"
LOCAL_DEFAULT_BASE = "http://127.0.0.1:8000/v1"
OPENROUTER_MODEL = "ricursiveai/ripple-65b-preview"
LOCAL_MODEL = "ricursiveAI/Ripple-65B-Preview"
VALID_ENDPOINTS = {"local", "openrouter"}
DEFAULT_MAX_TOKENS = 8192


class RippleAdapter:
    """OpenAI-compatible chat client for Ricursive Ripple-65B Preview."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        endpoint: str = "local",
        max_tokens: int = DEFAULT_MAX_TOKENS,
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
                raise ValueError("Set OPENROUTER_API_KEY for OpenRouter Ripple.")
            self.base_url = (base_url or OPENROUTER_BASE).rstrip("/")
            self.model = model or OPENROUTER_MODEL
        else:
            self.api_key = api_key or os.getenv("RIPPLE_API_KEY") or "unused"
            self.base_url = (base_url or os.getenv("RIPPLE_BASE_URL") or LOCAL_DEFAULT_BASE).rstrip("/")
            self.model = model or os.getenv("RIPPLE_MODEL") or LOCAL_MODEL
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def understand(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Text in, text out (Ripple has no vision input)."""
        if not (prompt or "").strip():
            raise ValueError("prompt is required.")
        messages: List[Dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "max_tokens": int(max_tokens or self.max_tokens),
        }
        if temperature is not None:
            kwargs["temperature"] = float(temperature)
        response = self.client.chat.completions.create(**kwargs)
        message = response.choices[0].message
        text = message.content or ""
        reasoning = getattr(message, "reasoning_content", None)
        if reasoning:
            text = f"{reasoning}\n\n{text}".strip()
        return {
            "text": text,
            "model": self.model,
            "endpoint": self.endpoint,
            "usage": getattr(response, "usage", None),
        }
