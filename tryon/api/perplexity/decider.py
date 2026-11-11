"""
Perplexity Decider -- hosted decision model (Perplexity Decisions API).

Decider swaps a Qwen3.8-27B language head for a 255-way answer-code readout (with
non-causal attention in its full-attention layers), so it returns calibrated
``noul`` / ``choice`` / ``score`` answers instead of text.

Endpoint: ``POST https://api.perplexity.ai/v1/decisions`` (``Authorization: Bearer``).
Models: ``pplx-decider-v1.2`` (27B) and ``pplx-decider-flash-v1.2`` (4B), plus the
``pplx-decider-latest`` / ``pplx-decider-flash-latest`` aliases. Images go inside
``state`` as OpenAI-style ``image_url`` parts (PNG / JPEG / WebP data URLs, up to 8;
remote URLs are rejected, so this adapter inlines them). Optional
``mode="web_grounding"`` lets the model search the web first (billed per search).

The open weights (``perplexity-ai/pplx-decider-v1.1-27b``) can also be self-hosted
with SGLang: use ``decide --model pplx-decider-local``.

References:
  https://docs.perplexity.ai/docs/decisions/quickstart
  https://docs.perplexity.ai/api-reference/decisions-post
  https://huggingface.co/perplexity-ai/pplx-decider-v1.1-27b

Env:
  PERPLEXITY_API_KEY (required)
  PERPLEXITY_BASE_URL (optional, default https://api.perplexity.ai)
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Sequence

from tryon.api.systemone import as_list, check_choice_limits, image_data_urls, post_json, state_text
from tryon.decision import Questions, load_questions, load_state

DEFAULT_BASE_URL = "https://api.perplexity.ai"
VALID_MODELS = {
    "pplx-decider-v1.2",
    "pplx-decider-flash-v1.2",
    "pplx-decider-latest",
    "pplx-decider-flash-latest",
}
DEFAULT_MODEL = "pplx-decider-v1.2"
MAX_IMAGES = 8
IMAGE_MIMES = ("image/png", "image/jpeg", "image/webp")


class PerplexityDeciderAdapter:
    """Perplexity Decisions API client."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        base_url: Optional[str] = None,
        timeout: float = 120.0,
    ):
        if model not in VALID_MODELS:
            raise ValueError(f"Invalid model: {model!r}. Supported models: {sorted(VALID_MODELS)}")
        self.api_key = api_key or os.getenv("PERPLEXITY_API_KEY")
        if not self.api_key:
            raise ValueError("Set PERPLEXITY_API_KEY (or pass api_key) for the Perplexity Decisions API.")
        self.model = model
        self.base_url = (base_url or os.getenv("PERPLEXITY_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout

    def decide(
        self,
        questions: Questions,
        state: Optional[Any] = None,
        image: Optional[Any] = None,
        web_grounding: bool = False,
        max_staleness: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Answer ``questions`` about ``state`` (text / JSON) and optional ``image`` inputs.

        Args:
            web_grounding: let Decider search the web before answering (``mode="web_grounding"``).
            max_staleness: with web grounding, the oldest acceptable cached result, in seconds.
        """
        qs = load_questions(questions)
        check_choice_limits(qs)
        st = load_state(state)
        images = as_list(image)
        if (st is None or st == "") and not images:
            raise ValueError("Provide a state (text or JSON) and/or an image.")
        if max_staleness is not None and not web_grounding:
            raise ValueError("max_staleness only applies with web_grounding.")

        payload_state: Any = st
        if images:
            parts: List[Dict[str, Any]] = []
            if st not in (None, ""):
                parts.append({"type": "text", "text": state_text(st)})
            for url in image_data_urls(images, max_images=MAX_IMAGES, allowed_mimes=IMAGE_MIMES):
                parts.append({"type": "image_url", "image_url": {"url": url}})
            payload_state = parts

        payload: Dict[str, Any] = {"model": self.model, "state": payload_state, "questions": qs}
        if web_grounding:
            payload["mode"] = "web_grounding"
            if max_staleness is not None:
                payload["max_staleness"] = int(max_staleness)
        data = post_json(f"{self.base_url}/v1/decisions", payload, api_key=self.api_key,
                         timeout=self.timeout, label="Perplexity Decisions")
        out = {"model": data.get("model", self.model), "answers": data.get("answers", {}), "usage": data.get("usage")}
        for key in ("search_results", "fetched_results"):
            if key in data:
                out[key] = data[key]
        return out
