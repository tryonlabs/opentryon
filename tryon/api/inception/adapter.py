"""
Inception Labs Mercury 3 — diffusion LLM via OpenAI-compatible Chat Completions.

Mercury 3 is a fast text model (1M context, up to 131K output tokens). The public
API is **text in / text out** on ``v1/chat/completions`` (no image input on
``mercury-3`` per Inception's model table).

Reference:
https://www.inceptionlabs.ai/blog/introducing-mercury-3
https://docs.inceptionlabs.ai/get-started/models

Env:
  INCEPTION_API_KEY (required)
  INCEPTION_BASE_URL — default https://api.inceptionlabs.ai/v1
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

DEFAULT_BASE_URL = "https://api.inceptionlabs.ai/v1"

VALID_MODELS = {
    "mercury-3",
    "mercury-2.5",
    "mercury-2",
    "mercury-voice",
}
DEFAULT_MODEL = "mercury-3"
VALID_REASONING_EFFORTS = {"instant", "low", "medium", "high"}
DEFAULT_UNDERSTAND_PROMPT = "Answer the user's question clearly and concisely."


class InceptionUnderstandAdapter:
    """OpenAI-compatible client for Inception Mercury chat models."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        base_url: Optional[str] = None,
    ):
        if not _OPENAI_AVAILABLE:
            raise ImportError(
                "OpenAI SDK is required for Inception Mercury. Install with: pip install openai"
            )
        if model not in VALID_MODELS:
            raise ValueError(f"Invalid model: {model!r}. Supported: {sorted(VALID_MODELS)}")

        self.api_key = api_key or os.getenv("INCEPTION_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Inception API key is required. Set INCEPTION_API_KEY or pass api_key. "
                "Create a key at https://platform.inceptionlabs.ai/"
            )
        self.model = model
        base = base_url or os.getenv("INCEPTION_BASE_URL") or DEFAULT_BASE_URL
        self.client = OpenAI(api_key=self.api_key, base_url=base.rstrip("/"))

    def _chat(
        self,
        messages: List[Dict[str, str]],
        *,
        model: Optional[str] = None,
        reasoning_effort: Optional[str] = None,
        max_completion_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        system: Optional[str] = None,
    ) -> Dict[str, Any]:
        use_model = model or self.model
        if use_model not in VALID_MODELS:
            raise ValueError(f"Invalid model: {use_model!r}. Supported: {sorted(VALID_MODELS)}")

        payload_messages: List[Dict[str, str]] = []
        if system:
            payload_messages.append({"role": "system", "content": system})
        payload_messages.extend(messages)

        kwargs: Dict[str, Any] = {"model": use_model, "messages": payload_messages}
        if reasoning_effort is not None:
            if reasoning_effort not in VALID_REASONING_EFFORTS:
                raise ValueError(
                    f"Invalid reasoning_effort: {reasoning_effort!r}. "
                    f"Supported: {sorted(VALID_REASONING_EFFORTS)}"
                )
            kwargs["reasoning_effort"] = reasoning_effort
        if max_completion_tokens is not None:
            kwargs["max_completion_tokens"] = max_completion_tokens
        if temperature is not None:
            if not (0.5 <= temperature <= 1.0):
                raise ValueError("temperature must be between 0.5 and 1.0 for Mercury models.")
            kwargs["temperature"] = temperature

        completion = self.client.chat.completions.create(**kwargs)
        message = completion.choices[0].message
        reasoning = getattr(message, "reasoning_content", None) or getattr(message, "reasoning", None)
        return {
            "text": message.content,
            "reasoning": reasoning,
            "model": completion.model,
            "usage": completion.usage.model_dump() if completion.usage else None,
        }

    def understand(
        self,
        prompt: Optional[str] = None,
        model: Optional[str] = None,
        reasoning_effort: Optional[str] = None,
        max_tokens: Optional[int] = None,
        max_completion_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        system: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Text understanding / Q&A (Mercury 3 has no image input on the chat endpoint)."""
        if kwargs.get("image") is not None:
            raise ValueError(
                "mercury-3 is text-only on v1/chat/completions. "
                "For image classification see Mercury Decide (v1/decisions) — not wired here."
            )
        text = (prompt or "").strip()
        if not text:
            raise ValueError("Provide --prompt (Mercury 3 is a text model).")
        out_limit = max_completion_tokens if max_completion_tokens is not None else max_tokens
        return self._chat(
            [{"role": "user", "content": text}],
            model=model,
            reasoning_effort=reasoning_effort,
            max_completion_tokens=out_limit,
            temperature=temperature,
            system=system,
        )
