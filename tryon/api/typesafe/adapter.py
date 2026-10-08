"""
Typesafe AI Jev (System One decision model) API Adapter

Jev is TypeSafe AI's first "System One" model: it does not generate text.
Instead you send a *state* (text, JSON object or array) and a set of named,
typed *questions*; it returns calibrated answers for all of them in one call
(70-500 ms, output tokens free). Text/JSON only -- no image, audio or video
input, no streaming.

Reference:
https://docs.typesafe.ai (System One API)
Endpoint: POST {base}/v1/systemone   (Authorization: Bearer <TYPESAFE_API_KEY>)

Models (first-party aliases): ``jev-latest`` and ``jev-preview`` currently
resolve to ``jev-1.13.0``.

Access: early access / waitlist -- TypeSafe paused new sign-ups on 2026-09-22
(re-check console.typesafe.ai). The same model is also served by third-party
gateways (OpenRouter ``typesafe/jev-1.13``, Vercel AI Gateway, DigitalOcean
Inference); point ``TYPESAFE_BASE_URL`` at a compatible gateway if you use one.

Env:
  TYPESAFE_API_KEY (required)
  TYPESAFE_BASE_URL -- default https://api.typesafe.ai

Examples:
    >>> from tryon.api.typesafe import JevAdapter
    >>> adapter = JevAdapter()
    >>> out = adapter.decide(
    ...     state="Product photo caption: red satin evening gown, size 6, model wearing heels",
    ...     questions={
    ...         "category": {"type": "choice", "instructions": "Garment category?",
    ...                      "criteria": {"dress": "one-piece gowns/dresses", "top": "shirts/blouses"}},
    ...         "formal": {"type": "noul", "instructions": "Is this formal wear?"},
    ...     },
    ... )
    >>> out["answers"]["category"]["choice"]
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

import requests

from tryon.decision import Questions, load_questions, load_state

DEFAULT_BASE_URL = "https://api.typesafe.ai"
VALID_MODELS = {"jev-latest", "jev-preview", "jev-1.13.0"}
DEFAULT_MODEL = "jev-latest"


class JevAdapter:
    """
    Typesafe AI Jev decision-model client.

    Args:
        api_key: Defaults to ``TYPESAFE_API_KEY``.
        model: ``jev-latest`` (default), ``jev-preview`` or ``jev-1.13.0``.
        base_url: Defaults to ``TYPESAFE_BASE_URL`` or ``https://api.typesafe.ai``.
        timeout: HTTP timeout in seconds.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        base_url: Optional[str] = None,
        timeout: float = 60.0,
    ):
        if model not in VALID_MODELS:
            raise ValueError(f"Invalid model: {model!r}. Supported models: {sorted(VALID_MODELS)}")
        self.api_key = api_key or os.getenv("TYPESAFE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Typesafe API key must be provided either as a parameter or "
                "through the TYPESAFE_API_KEY environment variable."
            )
        self.model = model
        self.base_url = (base_url or os.getenv("TYPESAFE_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout

    def decide(
        self,
        questions: Questions,
        state: Optional[Any] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Answer ``questions`` about ``state``. Returns ``{"model","answers","usage"}``.

        Args:
            questions: dict / JSON string / path to a JSON file (see :mod:`tryon.decision`).
            state: text, JSON-able value, or a path to a text/JSON file. Required: Jev has
                no image/audio input.
        """
        qs = load_questions(questions)
        st = load_state(state)
        if st is None or st == "":
            raise ValueError("state is required for Jev (text or JSON; it has no image/audio input).")
        use_model = model or self.model
        if use_model not in VALID_MODELS:
            raise ValueError(f"Invalid model: {use_model!r}. Supported models: {sorted(VALID_MODELS)}")

        resp = requests.post(
            f"{self.base_url}/v1/systemone",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json={"model": use_model, "state": st, "questions": qs},
            timeout=self.timeout,
        )
        if resp.status_code != 200:
            raise RuntimeError(f"Jev API error ({resp.status_code}): {resp.text[:500]}")
        data = resp.json()
        return {
            "model": data.get("model", use_model),
            "answers": data.get("answers", {}),
            "usage": data.get("usage"),
        }
