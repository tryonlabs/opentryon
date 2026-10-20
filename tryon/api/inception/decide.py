"""
Inception Labs Mercury Decide — structured decisions via POST /v1/decisions.

Evaluate named ``noul``, ``choice``, and ``score`` questions against shared
``state`` (text, JSON, or multimodal content parts with base64 images).

Reference:
https://docs.inceptionlabs.ai/capabilities/decisions
https://docs.inceptionlabs.ai/api-reference/decisions/create-a-decision

Env:
  INCEPTION_API_KEY (required)
  INCEPTION_BASE_URL — default https://api.inceptionlabs.ai/v1 (decisions URL derived)
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Union

import requests

from tryon.d3_media import prepare_images_for_api
from tryon.decision import Questions, load_questions, load_state

DEFAULT_DECISIONS_ROOT = "https://api.inceptionlabs.ai"
VALID_MODELS = {"mercury-decide"}
DEFAULT_MODEL = "mercury-decide"


def _decisions_endpoint(base_url: Optional[str]) -> str:
    """Resolve POST URL for /v1/decisions from INCEPTION_BASE_URL or default."""
    raw = (base_url or os.getenv("INCEPTION_BASE_URL") or f"{DEFAULT_DECISIONS_ROOT}/v1").rstrip("/")
    if raw.endswith("/v1"):
        return f"{raw}/decisions"
    return f"{raw}/v1/decisions"


def _build_state(
    state: Optional[Any],
    image: Optional[Union[str, List[str]]],
) -> Any:
    images: List[str] = []
    if image is not None:
        images = image if isinstance(image, list) else [image]

    if not images:
        if state is None or state == "":
            raise ValueError("Provide --state and/or --image (Mercury Decide is multimodal).")
        return state

    data_urls = prepare_images_for_api(images)
    for url in data_urls:
        if url.startswith(("http://", "https://")):
            raise ValueError(
                "Mercury Decide does not accept remote image URLs — use local paths "
                "(converted to base64 data URLs) or pass a data: URL."
            )

    parts: List[Dict[str, Any]] = []
    st = load_state(state)
    if st not in (None, ""):
        if isinstance(st, (dict, list)):
            parts.append({"type": "text", "text": json.dumps(st, ensure_ascii=False)})
        else:
            parts.append({"type": "text", "text": str(st)})
    for url in data_urls:
        parts.append({"type": "image_url", "image_url": {"url": url}})
    if not parts:
        raise ValueError("Provide --state text and/or --image for Mercury Decide.")
    return parts if len(parts) > 1 or parts[0]["type"] == "image_url" else parts[0]


class MercuryDecideAdapter:
    """Inception Mercury Decide client (classification / routing / scoring)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        base_url: Optional[str] = None,
        timeout: float = 120.0,
    ):
        if model not in VALID_MODELS:
            raise ValueError(f"Invalid model: {model!r}. Supported: {sorted(VALID_MODELS)}")
        self.api_key = api_key or os.getenv("INCEPTION_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Inception API key is required. Set INCEPTION_API_KEY or pass api_key. "
                "Create a key at https://platform.inceptionlabs.ai/"
            )
        self.model = model
        self.base_url = base_url or os.getenv("INCEPTION_BASE_URL")
        self.timeout = timeout
        self._decisions_url = _decisions_endpoint(self.base_url)

    def decide(
        self,
        questions: Questions,
        state: Optional[Any] = None,
        image: Optional[Union[str, List[str]]] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Answer ``questions`` about ``state`` (and optional ``image`` parts)."""
        qs = load_questions(questions)
        payload_state = _build_state(state, image)
        use_model = model or self.model
        if use_model not in VALID_MODELS:
            raise ValueError(f"Invalid model: {use_model!r}. Supported: {sorted(VALID_MODELS)}")

        resp = requests.post(
            self._decisions_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={"model": use_model, "state": payload_state, "questions": qs},
            timeout=self.timeout,
        )
        if resp.status_code != 200:
            raise RuntimeError(f"Mercury Decide API error ({resp.status_code}): {resp.text[:800]}")
        data = resp.json()
        return {
            "model": data.get("model", use_model),
            "answers": data.get("answers", {}),
            "usage": data.get("usage"),
        }
