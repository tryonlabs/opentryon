"""
Reflection Beam — first-party OpenAI-compatible chat.

Beam 1.0 is a 501B / 23B-active MoE (text in, text out, 1M context, Apache-2.0
weights). OpenTryOn calls the hosted API. Self-host is a separate stack
(NVFP4 on four B300s via vLLM/SGLang) and is not registered here.

Reference:
https://developers.reflection.ai/openai-compatibility
https://developers.reflection.ai/api-reference/chat/create-a-chat-completion
https://huggingface.co/reflection/Beam-1.0-501B-A23B

Model id: ``Beam-1.0-501B-A23B``

Env:
  REFLECTION_API_KEY (required)
  REFLECTION_BASE_URL — default https://api.reflection.ai/openai/v1

Examples:
    >>> from tryon.api.reflection import BeamAdapter
    >>> adapter = BeamAdapter()
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

DEFAULT_BASE_URL = "https://api.reflection.ai/openai/v1"
DEFAULT_MODEL = "Beam-1.0-501B-A23B"
VALID_MODELS = {DEFAULT_MODEL}
VALID_REASONING_EFFORTS = {"low", "medium", "high", "xhigh", "max"}


class BeamAdapter:
    """
    Reflection Beam via ``https://api.reflection.ai/openai/v1/chat/completions``.

    Args:
        api_key: Reflection key. Defaults to ``REFLECTION_API_KEY``.
        model: Upstream model id. Defaults to ``Beam-1.0-501B-A23B``.
        base_url: Chat Completions base URL.
    """

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
        if model not in VALID_MODELS:
            raise ValueError(
                f"Invalid model: {model!r}. Supported models: {sorted(VALID_MODELS)}"
            )

        self.api_key = api_key or os.getenv("REFLECTION_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Reflection API key must be provided either as a parameter or "
                "through the REFLECTION_API_KEY environment variable."
            )

        self.model = model
        self.base_url = (
            base_url or os.getenv("REFLECTION_BASE_URL") or DEFAULT_BASE_URL
        ).rstrip("/")
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def understand(
        self,
        prompt: Optional[str] = None,
        system: Optional[str] = None,
        model: Optional[str] = None,
        reasoning_effort: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        image: Any = None,
        video: Any = None,
    ) -> Dict[str, Any]:
        """Text chat. Beam does not accept images or video."""
        if image is not None or video is not None:
            raise ValueError(
                "Beam is text-only. Image and video understanding are not in "
                "the Beam API — use kimi-k2.6, moondream-3.1, or nemotron-omni."
            )
        text = (prompt or "").strip()
        if not text:
            raise ValueError("prompt is required. Beam is a text chat model.")

        upstream = model or self.model
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
        if reasoning_effort is not None:
            effort = reasoning_effort.strip().lower()
            if effort not in VALID_REASONING_EFFORTS:
                raise ValueError(
                    f"Invalid reasoning_effort: {reasoning_effort!r}. "
                    f"Supported values: {sorted(VALID_REASONING_EFFORTS)}"
                )
            kwargs["reasoning_effort"] = effort
        if max_tokens is not None:
            kwargs["max_tokens"] = int(max_tokens)
        if temperature is not None:
            kwargs["temperature"] = float(temperature)

        completion = self.client.chat.completions.create(**kwargs)
        message = completion.choices[0].message
        reasoning = getattr(message, "reasoning_content", None)
        return {
            "text": message.content,
            "reasoning": reasoning,
            "model": completion.model,
            "usage": completion.usage.model_dump() if completion.usage else None,
        }
