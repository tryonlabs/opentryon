"""
Poolside Laguna — first-party OpenAI-compatible chat.

Laguna XS.2 / XS 2.1 (33B / 3B-active) and Laguna M.1 (225B / 23B-active)
are text-in, text-out coding models. OpenTryOn calls the hosted inference
API. Self-host (vLLM / SGLang / Ollama) is a separate stack and is not
registered here.

Thinking is **on by default**. Send ``chat_template_kwargs.enable_thinking:
false`` to turn it off.

Reference:
https://docs.poolside.ai/api/overview
https://docs.poolside.ai/api/openai-api-examples
https://docs.poolside.ai/get-started/supported-models
https://poolside.ai/blog/introducing-laguna-xs2-m1

Env:
  POOLSIDE_API_KEY (required)
  POOLSIDE_BASE_URL — default https://inference.poolside.ai/v1

Examples:
    >>> from tryon.api.poolside import LagunaAdapter
    >>> adapter = LagunaAdapter(model="poolside/laguna-m.1")
    >>> result = adapter.understand(prompt="Write a lookbook caption for a linen trench.")
    >>> print(result["text"])
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

DEFAULT_BASE_URL = "https://inference.poolside.ai/v1"
DEFAULT_MODEL = "poolside/laguna-m.1"
VALID_MODELS = {
    "poolside/laguna-xs.2",
    "poolside/laguna-xs.2.1",
    "poolside/laguna-xs-2.1",
    "poolside/laguna-m.1",
}
_MODEL_ALIASES = {
    "poolside/laguna-xs-2.1": "poolside/laguna-xs.2.1",
}


class LagunaAdapter:
    """Poolside Laguna via ``https://inference.poolside.ai/v1/chat/completions``."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        base_url: Optional[str] = None,
    ):
        if not _OPENAI_AVAILABLE:
            raise ImportError(
                "OpenAI SDK is not available. Please install it with 'pip install openai'."
            )
        resolved = _MODEL_ALIASES.get(model, model)
        if resolved not in VALID_MODELS:
            raise ValueError(
                f"Invalid model: {model!r}. Supported models: {sorted(VALID_MODELS)}"
            )

        self.api_key = api_key or os.getenv("POOLSIDE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Poolside API key must be provided either as a parameter or "
                "through the POOLSIDE_API_KEY environment variable."
            )

        self.model = resolved
        self.base_url = (
            base_url or os.getenv("POOLSIDE_BASE_URL") or DEFAULT_BASE_URL
        ).rstrip("/")
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def understand(
        self,
        prompt: Optional[str] = None,
        system: Optional[str] = None,
        model: Optional[str] = None,
        enable_thinking: bool = True,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        min_p: Optional[float] = None,
        image: Any = None,
        video: Any = None,
    ) -> Dict[str, Any]:
        """Text chat. Laguna does not accept images or video."""
        if image is not None or video is not None:
            raise ValueError(
                "Laguna is text-only. Image and video understanding are not in "
                "the Poolside chat API — use kimi-k2.6, moondream-3.1, or nemotron-omni."
            )
        text = (prompt or "").strip()
        if not text:
            raise ValueError("prompt is required. Laguna is a text chat model.")

        upstream = _MODEL_ALIASES.get(model or self.model, model or self.model)
        if upstream not in VALID_MODELS:
            raise ValueError(
                f"Invalid model: {upstream!r}. Supported models: {sorted(VALID_MODELS)}"
            )

        messages: List[Dict[str, str]] = []
        system_text = (system or "").strip()
        if system_text:
            messages.append({"role": "system", "content": system_text})
        messages.append({"role": "user", "content": text})

        kwargs: Dict[str, Any] = {"model": upstream, "messages": messages}
        if max_tokens is not None:
            kwargs["max_tokens"] = int(max_tokens)
        if temperature is not None:
            kwargs["temperature"] = float(temperature)
        if top_p is not None:
            kwargs["top_p"] = float(top_p)
        extra_body: Dict[str, Any] = {}
        if not enable_thinking:
            extra_body["chat_template_kwargs"] = {"enable_thinking": False}
        if top_k is not None:
            extra_body["top_k"] = int(top_k)
        if min_p is not None:
            extra_body["min_p"] = float(min_p)
        if extra_body:
            kwargs["extra_body"] = extra_body

        completion = self.client.chat.completions.create(**kwargs)
        message = completion.choices[0].message
        reasoning = getattr(message, "reasoning_content", None)
        return {
            "text": message.content,
            "reasoning": reasoning,
            "model": completion.model,
            "usage": completion.usage.model_dump() if completion.usage else None,
        }
