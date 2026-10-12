"""
Local THX-01 (Apache-2.0) via the ``thx01`` package and Hugging Face weights.

Model: https://huggingface.co/doofz/THX-01
Install: pip install thx01  (included in opentryon[local] extra)
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from tryon.decision import Questions, load_state, load_thx_questions

DEFAULT_MODEL_ID = "doofz/THX-01"


class Thx01LocalAdapter:
    """Runs THX-01 locally with ``thx01.load(model_id).decide(...)``."""

    def __init__(self, model_id: str = DEFAULT_MODEL_ID, device: Optional[str] = None):
        self.model_id = model_id
        self.device = device
        self._agent = None

    def _load(self):
        if self._agent is not None:
            return self._agent
        try:
            import thx01
        except ImportError as exc:
            raise ImportError(
                "Local THX-01 requires the thx01 package: pip install thx01 "
                "(or pip install opentryon[local])."
            ) from exc
        kwargs = {}
        if self.device:
            kwargs["device"] = self.device
        self._agent = thx01.load(self.model_id, **kwargs)
        return self._agent

    def decide(
        self,
        questions: Questions,
        state: Optional[Any] = None,
    ) -> Dict[str, Any]:
        qs = load_thx_questions(questions)
        st = load_state(state)
        if st is None or st == "":
            raise ValueError("state is required for THX-01.")
        agent = self._load()
        result = agent.decide(st, qs)
        if isinstance(result, dict):
            return {
                "model": self.model_id,
                "answers": result.get("answers", result),
                "usage": result.get("usage"),
            }
        return {"model": self.model_id, "answers": result}
