"""
Arcee Trinity — first-party OpenAI-compatible chat.

Trinity Large Preview / Thinking are 400B / 13B-active MoE models. Trinity Mini
(26B / 3B-active) is also served on the Arcee Platform. Trinity Nano (6B /
1B-active) is **not hosted** — register ``trinity-nano`` against a local
vLLM/SGLang server.

Text in, text out. Apache-2.0 weights exist; Large needs multi-GPU self-host,
so there is no in-process GPU registry id.

Reference:
https://docs.arcee.ai/api-reference/your-first-api-call
https://docs.arcee.ai/arcee-language-models/trinity-family
https://www.arcee.ai/trinity

Env:
  ARCEE_API_KEY (required for hosted ids; ARCEEAI_API_KEY is an alias)
  ARCEE_BASE_URL — default https://api.arcee.ai/api/v1
  TRINITY_BASE_URL — local OpenAI-compatible server (trinity-nano)

Examples:
    >>> from tryon.api.arcee import TrinityAdapter
    >>> adapter = TrinityAdapter(model="Trinity-Large-Preview")
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

DEFAULT_ARCEE_BASE_URL = "https://api.arcee.ai/api/v1"
DEFAULT_LOCAL_BASE_URL = "http://127.0.0.1:8000/v1"
DEFAULT_MODEL = "Trinity-Large-Preview"
VALID_ENDPOINTS = {"arcee", "local"}

# Canonical hosted / served ids. Aliases collapse onto these.
CANONICAL_MODELS = {
    "Trinity-Large-Preview",
    "Trinity-Large-Thinking",
    "trinity-mini",
    "Trinity-Nano",
}
_MODEL_ALIASES = {
    "trinity-large-preview": "Trinity-Large-Preview",
    "trinity-large": "Trinity-Large-Preview",
    "arcee-ai/trinity-large-preview": "Trinity-Large-Preview",
    "arcee-ai/Trinity-Large-Preview": "Trinity-Large-Preview",
    "arcee/trinity-large-preview": "Trinity-Large-Preview",
    "trinity-large-thinking": "Trinity-Large-Thinking",
    "arcee-ai/trinity-large-thinking": "Trinity-Large-Thinking",
    "arcee-ai/Trinity-Large-Thinking": "Trinity-Large-Thinking",
    "arcee/trinity-large-thinking": "Trinity-Large-Thinking",
    "Trinity-Mini": "trinity-mini",
    "Trinity-Mini-26B": "trinity-mini",
    "arcee-ai/trinity-mini": "trinity-mini",
    "arcee-ai/Trinity-Mini": "trinity-mini",
    "arcee/trinity-mini": "trinity-mini",
    "trinity-nano": "Trinity-Nano",
    "Trinity-Nano-6B": "Trinity-Nano",
    "arcee-ai/trinity-nano": "Trinity-Nano",
    "arcee-ai/Trinity-Nano": "Trinity-Nano",
    "arcee-ai/Trinity-Nano-6B": "Trinity-Nano",
}
HOSTED_MODELS = {
    "Trinity-Large-Preview",
    "Trinity-Large-Thinking",
    "trinity-mini",
}


def _canonical_model(model: str) -> str:
    return _MODEL_ALIASES.get(model, model)


class TrinityAdapter:
    """Arcee Trinity via ``https://api.arcee.ai/api/v1/chat/completions`` (or a local server)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        base_url: Optional[str] = None,
        endpoint: str = "arcee",
    ):
        if not _OPENAI_AVAILABLE:
            raise ImportError(
                "OpenAI SDK is not available. Please install it with 'pip install openai'."
            )
        if endpoint not in VALID_ENDPOINTS:
            raise ValueError(
                f"Invalid endpoint: {endpoint!r}. Supported: {sorted(VALID_ENDPOINTS)}"
            )
        resolved = _canonical_model(model)
        if resolved not in CANONICAL_MODELS:
            raise ValueError(
                f"Invalid model: {model!r}. Supported models: {sorted(CANONICAL_MODELS)}"
            )
        if endpoint == "arcee" and resolved not in HOSTED_MODELS:
            raise ValueError(
                f"{resolved} is not hosted on the Arcee Platform. "
                "Serve it locally and use --model trinity-nano (or endpoint=local)."
            )

        self.endpoint = endpoint
        self.model = resolved
        if endpoint == "local":
            self.api_key = api_key or os.getenv("TRINITY_API_KEY") or "EMPTY"
            self.base_url = (
                base_url
                or os.getenv("TRINITY_BASE_URL")
                or DEFAULT_LOCAL_BASE_URL
            ).rstrip("/")
        else:
            self.api_key = (
                api_key
                or os.getenv("ARCEE_API_KEY")
                or os.getenv("ARCEEAI_API_KEY")
            )
            if not self.api_key:
                raise ValueError(
                    "Arcee API key must be provided either as a parameter or "
                    "through the ARCEE_API_KEY environment variable."
                )
            self.base_url = (
                base_url or os.getenv("ARCEE_BASE_URL") or DEFAULT_ARCEE_BASE_URL
            ).rstrip("/")
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def understand(
        self,
        prompt: Optional[str] = None,
        system: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        image: Any = None,
        video: Any = None,
    ) -> Dict[str, Any]:
        """Text chat. Trinity does not accept images or video."""
        if image is not None or video is not None:
            raise ValueError(
                "Trinity is text-only. Image and video understanding are not in "
                "the Arcee chat API — use kimi-k2.6, moondream-3.1, or nemotron-omni."
            )
        text = (prompt or "").strip()
        if not text:
            raise ValueError("prompt is required. Trinity is a text chat model.")

        upstream = _canonical_model(model or self.model)
        if upstream not in CANONICAL_MODELS:
            raise ValueError(
                f"Invalid model: {upstream!r}. Supported models: {sorted(CANONICAL_MODELS)}"
            )
        if self.endpoint == "arcee" and upstream not in HOSTED_MODELS:
            raise ValueError(
                f"{upstream} is not hosted on the Arcee Platform. Use endpoint=local."
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

        completion = self.client.chat.completions.create(**kwargs)
        message = completion.choices[0].message
        reasoning = getattr(message, "reasoning_content", None)
        if reasoning is None:
            reasoning = getattr(message, "reasoning", None)
        return {
            "text": message.content,
            "reasoning": reasoning,
            "model": completion.model,
            "usage": completion.usage.model_dump() if completion.usage else None,
        }
