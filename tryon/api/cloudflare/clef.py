"""
Cloudflare Clef / Clef-flash -- hosted decision models on Workers AI.

Clef puts a small joint schema head on a frozen Qwen backbone: it routes evidence between
the state, the questions and their options and scores the whole schema together, returning
calibrated ``noul`` / ``choice`` / ``score`` answers. ``clef`` is 27B (Qwen3.8-27B, 65,536-token
context) and ``clef-flash`` is 9B (Qwen3.5-9B, 24,576 tokens). Both read images.

Endpoint (Workers AI REST):
  ``POST https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/@cf/cloudflare/{clef|clef-flash}``
  with ``Authorization: Bearer <API token>``. Body: ``model`` (``clef`` / ``clef-flash``),
  ``state``, ``questions`` (1-64) and optional ``images`` (up to 4 PNG / JPEG / WebP data URLs,
  4 MiB each; remote URLs are not accepted, so this adapter inlines them).

The Apache-2.0 weights (``Cloudflare/clef``) can be self-hosted with SGLang: use
``decide --model clef-local``.

References:
  https://developers.cloudflare.com/workers-ai/models/clef/
  https://developers.cloudflare.com/workers-ai/models/clef-flash/
  https://blog.cloudflare.com/clef-decision-models

Env:
  CLOUDFLARE_API_TOKEN (required; a Workers AI token)
  CLOUDFLARE_ACCOUNT_ID (required)
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

from tryon.api.systemone import as_list, check_choice_limits, image_data_urls, post_json
from tryon.decision import Questions, load_questions, load_state

DEFAULT_BASE_URL = "https://api.cloudflare.com/client/v4"
VALID_MODELS = {"clef", "clef-flash"}
DEFAULT_MODEL = "clef"
MAX_QUESTIONS = 64
MAX_IMAGES = 4
IMAGE_MIMES = ("image/png", "image/jpeg", "image/webp")
MAX_IMAGE_BYTES = 4 * 1024 * 1024


class ClefAdapter:
    """Cloudflare Workers AI client for Clef / Clef-flash."""

    def __init__(
        self,
        api_token: Optional[str] = None,
        account_id: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        base_url: Optional[str] = None,
        timeout: float = 120.0,
    ):
        if model not in VALID_MODELS:
            raise ValueError(f"Invalid model: {model!r}. Supported models: {sorted(VALID_MODELS)}")
        self.api_token = api_token or os.getenv("CLOUDFLARE_API_TOKEN")
        self.account_id = account_id or os.getenv("CLOUDFLARE_ACCOUNT_ID")
        missing = [n for n, v in (("CLOUDFLARE_API_TOKEN", self.api_token), ("CLOUDFLARE_ACCOUNT_ID", self.account_id)) if not v]
        if missing:
            raise ValueError(f"Set {' and '.join(missing)} for Cloudflare Workers AI.")
        self.model = model
        self.base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout

    @property
    def endpoint(self) -> str:
        return f"{self.base_url}/accounts/{self.account_id}/ai/run/@cf/cloudflare/{self.model}"

    def decide(self, questions: Questions, state: Optional[Any] = None, image: Optional[Any] = None) -> Dict[str, Any]:
        """Answer ``questions`` about ``state`` (text / JSON) and up to 4 images."""
        qs = load_questions(questions)
        if len(qs) > MAX_QUESTIONS:
            raise ValueError(f"Clef takes at most {MAX_QUESTIONS} questions per request (got {len(qs)}).")
        check_choice_limits(qs)
        st = load_state(state)
        images = as_list(image)
        if (st is None or st == "") and not images:
            raise ValueError("Provide a state (text or JSON) and/or an image.")
        payload: Dict[str, Any] = {"model": self.model, "state": "" if st is None else st, "questions": qs}
        if images:
            payload["images"] = image_data_urls(images, max_images=MAX_IMAGES, allowed_mimes=IMAGE_MIMES,
                                                max_bytes=MAX_IMAGE_BYTES)
        data = post_json(self.endpoint, payload, api_key=self.api_token, timeout=self.timeout,
                         label="Cloudflare Workers AI (Clef)")
        if isinstance(data.get("result"), dict):  # Workers AI REST envelope
            if data.get("success") is False:
                raise RuntimeError(f"Cloudflare Workers AI error: {data.get('errors')}")
            data = data["result"]
        return {"model": data.get("model", self.model), "answers": data.get("answers", {}), "usage": data.get("usage")}
