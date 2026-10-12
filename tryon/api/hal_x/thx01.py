"""
HAL-X THX-01 hosted decision model (TypeSafe System One compatible).

Reference: https://api.hal-x.ai/docs/thx-01/
Endpoint: POST https://api.hal-x.ai/v1/systemone

Env:
    HALX_API_KEY (required for production; create at HAL-X console)
    HALX_BASE_URL — default https://api.hal-x.ai
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

import requests

from tryon.decision import Questions, load_questions, load_state, load_thx_questions

DEFAULT_BASE_URL = "https://api.hal-x.ai"
DEFAULT_MODEL = "thx-01"


class Thx01Adapter:
    """Hosted THX-01 client (calibrated choice / noul / score / number / excerpt)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        base_url: Optional[str] = None,
        timeout: float = 120.0,
    ):
        self.api_key = api_key or os.getenv("HALX_API_KEY")
        if not self.api_key:
            raise ValueError(
                "HAL-X API key is required. Set HALX_API_KEY or pass api_key. "
                "See https://api.hal-x.ai/docs/thx-01/"
            )
        self.model = model or DEFAULT_MODEL
        self.base_url = (base_url or os.getenv("HALX_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout

    def decide(
        self,
        questions: Questions,
        state: Optional[Any] = None,
        model: Optional[str] = None,
        *,
        use_thx_schema: bool = True,
    ) -> Dict[str, Any]:
        """Answer ``questions`` about ``state`` in one forward pass."""
        loader = load_thx_questions if use_thx_schema else load_questions
        qs = loader(questions)
        st = load_state(state)
        if st is None or st == "":
            raise ValueError("state is required for THX-01.")
        use_model = model or self.model

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        resp = requests.post(
            f"{self.base_url}/v1/systemone",
            headers=headers,
            json={"model": use_model, "state": st, "questions": qs},
            timeout=self.timeout,
        )
        if resp.status_code != 200:
            raise RuntimeError(f"THX-01 API error ({resp.status_code}): {resp.text[:500]}")
        data = resp.json()
        return {
            "model": data.get("model", use_model),
            "answers": data.get("answers", {}),
            "usage": data.get("usage"),
            "detected": data.get("detected"),
            "latency_ms": data.get("latency_ms"),
        }
