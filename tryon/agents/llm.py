"""Shared LLM construction for OpenTryOn agents.

Specialist agents (fashion / model-swap / vton) use ``OPENTRYON_AGENT_LLM_*``.
The planner uses a cheaper model via ``OPENTRYON_PLANNER_LLM_MODEL`` so intent
routing does not spend a frontier-model call.
"""

from __future__ import annotations

import os
from typing import Literal, Optional, Tuple

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

Role = Literal["planner", "agent"]

PROVIDERS = ("openai", "anthropic", "google")

_DEFAULT_AGENT_MODEL = {
    "openai": "gpt-4o",
    "anthropic": "claude-sonnet-4-20250514",
    "google": "gemini-2.0-flash",
}

_DEFAULT_PLANNER_MODEL = {
    "openai": "gpt-4o-mini",
    "anthropic": "claude-3-5-haiku-latest",
    "google": "gemini-2.0-flash",
}


def agent_llm_provider() -> str:
    return (os.getenv("OPENTRYON_AGENT_LLM_PROVIDER") or "openai").strip().lower()


def agent_llm_model(role: Role = "agent") -> str:
    provider = agent_llm_provider()
    if role == "planner":
        return (
            os.getenv("OPENTRYON_PLANNER_LLM_MODEL")
            or os.getenv("OPENTRYON_AGENT_LLM_MODEL")
            or _DEFAULT_PLANNER_MODEL.get(provider, "gpt-4o-mini")
        )
    return os.getenv("OPENTRYON_AGENT_LLM_MODEL") or _DEFAULT_AGENT_MODEL.get(provider, "gpt-4o")


def _api_key_for(provider: str, override: Optional[str] = None) -> Optional[str]:
    if override:
        return override
    if provider == "openai":
        return os.getenv("OPENTRYON_AGENT_LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    if provider == "anthropic":
        return os.getenv("ANTHROPIC_API_KEY")
    if provider == "google":
        return os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    return None


def chat_model(
    *,
    role: Role = "agent",
    provider: Optional[str] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    temperature: float = 0.0,
    **kwargs,
) -> Tuple[BaseChatModel, str, str]:
    """Return ``(llm, provider, model_name)`` from args or ``.env``.

    OpenAI-compatible hosts can set ``OPENTRYON_AGENT_LLM_BASE_URL``
    (e.g. Moonshot / DashScope compatible mode) when provider is ``openai``.
    """
    provider = (provider or agent_llm_provider()).strip().lower()
    if provider not in PROVIDERS:
        raise ValueError(
            f"Unsupported LLM provider '{provider}'. "
            f"Set OPENTRYON_AGENT_LLM_PROVIDER to one of: {', '.join(PROVIDERS)}"
        )
    model_name = model or agent_llm_model(role)
    key = _api_key_for(provider, api_key)

    if provider == "openai":
        llm_kwargs = {"model": model_name, "temperature": temperature, **kwargs}
        if key:
            llm_kwargs["api_key"] = key
        base_url = os.getenv("OPENTRYON_AGENT_LLM_BASE_URL")
        if base_url:
            llm_kwargs["base_url"] = base_url
        return ChatOpenAI(**llm_kwargs), provider, model_name

    if provider == "anthropic":
        llm_kwargs = {"model": model_name, "temperature": temperature, **kwargs}
        if key:
            llm_kwargs["api_key"] = key
        return ChatAnthropic(**llm_kwargs), provider, model_name

    llm_kwargs = {"model": model_name, "temperature": temperature, **kwargs}
    if key:
        llm_kwargs["google_api_key"] = key
    return ChatGoogleGenerativeAI(**llm_kwargs), provider, model_name
