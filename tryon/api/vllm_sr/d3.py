"""
vLLM Semantic Router Decision 3.0 — hosted API adapter.

Free tier: https://decision.vllm-sr.ai (``DECISION_API_KEY`` from the home page).
Endpoint: POST {base}/v1/systemone

Models: ``vllm-sr/d3-turbo``, ``d3-flash``, ``d3-mini``, ``d3-nano``, ``d3-lite``,
``d3-edge`` (``vllm-sr/d3`` aliases turbo on the API).

Reference: https://huggingface.co/vllm-sr/d3-turbo
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Union

import requests

from tryon.d3_media import (
    load_assets,
    prepare_images_for_api,
    prepare_videos_for_api,
)
from tryon.decision import Questions, load_d3_questions, load_state

DEFAULT_BASE_URL = "https://decision.vllm-sr.ai"
DEFAULT_MODEL_ID = "vllm-sr/d3-turbo"

D3_MODEL_IDS = frozenset(
    {
        "vllm-sr/d3-turbo",
        "vllm-sr/d3",
        "vllm-sr/d3-flash",
        "vllm-sr/d3-mini",
        "vllm-sr/d3-nano",
        "vllm-sr/d3-lite",
        "vllm-sr/d3-edge",
    }
)


class D3ApiAdapter:
    """Hosted Decision 3.0 client (multimodal System One)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_id: str = DEFAULT_MODEL_ID,
        base_url: Optional[str] = None,
        timeout: float = 120.0,
    ):
        if model_id not in D3_MODEL_IDS:
            raise ValueError(f"Invalid model_id {model_id!r}. Supported: {sorted(D3_MODEL_IDS)}")
        self.api_key = api_key or os.getenv("DECISION_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Decision API key is required. Set DECISION_API_KEY (free key from "
                "https://decision.vllm-sr.ai) or pass api_key."
            )
        self.model_id = model_id
        self.base_url = (base_url or os.getenv("DECISION_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout

    def decide(
        self,
        questions: Questions,
        state: Optional[Any] = None,
        image: Optional[Union[str, List[str]]] = None,
        video: Optional[Union[str, List[str]]] = None,
        assets: Optional[Union[str, Dict[str, Any]]] = None,
        long_context: bool = False,
        model_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        qs = load_d3_questions(questions)
        st = load_state(state)
        images_list: List[str] = []
        if image is not None:
            images_list = image if isinstance(image, list) else [image]
        videos_list: List[str] = []
        if video is not None:
            videos_list = video if isinstance(video, list) else [video]
        asset_map = load_assets(assets)

        if (st is None or st == "") and not images_list and not videos_list:
            raise ValueError(
                "Provide --state and/or --image / --video (Decision 3.0 is multimodal)."
            )

        use_model = model_id or self.model_id
        if use_model not in D3_MODEL_IDS:
            raise ValueError(f"Invalid model_id {use_model!r}. Supported: {sorted(D3_MODEL_IDS)}")

        payload: Dict[str, Any] = {"model": use_model, "questions": qs}
        if st not in (None, ""):
            payload["state"] = st
        if images_list:
            payload["images"] = prepare_images_for_api(images_list)
        if videos_list:
            payload["videos"] = prepare_videos_for_api(videos_list)
        if asset_map:
            payload["assets"] = asset_map
        if long_context:
            payload["long_context"] = True

        resp = requests.post(
            f"{self.base_url}/v1/systemone",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=self.timeout,
        )
        if resp.status_code != 200:
            raise RuntimeError(f"Decision 3.0 API error ({resp.status_code}): {resp.text[:800]}")
        data = resp.json()
        return {
            "model": data.get("model", use_model),
            "answers": data.get("answers", {}),
            "usage": data.get("usage"),
            "latency_ms": data.get("latency_ms"),
        }
