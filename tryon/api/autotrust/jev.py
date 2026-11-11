"""
AutoTrust AI JEV -- client for a self-hosted JEV ``/v1/decide`` server.

JEV (Apache-2.0) wraps a frozen Qwen backbone with a learned decision block -- a LoRA plus a
small decision head -- and returns calibrated probabilities. Not affiliated with TypeSafe
AI's Jev (``decide --model jev``). Checkpoints: ``autotrust/JEV-35B`` (Qwen3.5-35B-A3B MoE,
up to 256 options, images), ``autotrust/JEV-35B-NVFP4`` (fits a 32 GB GPU),
``autotrust/JEV-27B-VL`` (Qwen3.8-27B with vision).

AutoTrust runs no hosted API and no third-party host serves JEV, so this adapter talks to
the server you start with the repo's ``serve.sh`` (vLLM plus a ``POST /v1/decide`` route,
port 8000 by default)::

    hf download autotrust/JEV-35B --local-dir JEV-35B
    bash JEV-35B/serve.sh

``/v1/decide`` answers ONE question per request (``kind`` / ``state`` / ``question`` /
``options``), so this adapter sends one request per question and maps the replies onto the
shared ``decide`` answer shape:

- ``noul``   -> ``{"type": "noul", "noul": P(true)}`` (the server scores ``false`` / ``true``).
- ``choice`` -> criteria keys become ``options``; descriptions are appended to the question.
- ``score``  -> JEV's native score is a fixed 0-5 scale, so ordered criteria levels are asked
  as a ``choice`` over the levels and ``score`` is the probability-weighted level index.

Env:
  AUTOTRUST_JEV_BASE_URL (default http://127.0.0.1:8000)
  AUTOTRUST_JEV_API_KEY (optional; sent as a bearer token if your proxy needs one)

References:
  https://huggingface.co/autotrust/JEV-35B
  https://huggingface.co/autotrust/JEV-27B-VL
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from tryon.api.systemone import as_list, image_data_urls, post_json, state_text
from tryon.decision import Questions, load_questions, load_state

DEFAULT_BASE_URL = "http://127.0.0.1:8000"
MAX_OPTIONS = 256
MAX_IMAGES = 8


def _choice_question(instructions: str, criteria: Dict[str, Any]) -> str:
    described = [(k, v) for k, v in criteria.items() if v not in (None, "")]
    if not described:
        return instructions
    lines = "\n".join(f"- {k}: {v}" for k, v in criteria.items())
    return f"{instructions}\nOptions:\n{lines}"


def _probabilities(reply: Dict[str, Any], options: List[str]) -> Dict[str, float]:
    probs = reply.get("probabilities") or []
    names = reply.get("options") or options
    if isinstance(probs, dict):
        return {str(k): float(v) for k, v in probs.items()}
    return {str(name): float(p) for name, p in zip(names, probs)}


class AutoTrustJevAdapter:
    """Client for AutoTrust JEV's self-hosted ``/v1/decide`` route."""

    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None, timeout: float = 120.0):
        self.base_url = (base_url or os.getenv("AUTOTRUST_JEV_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.api_key = api_key or os.getenv("AUTOTRUST_JEV_API_KEY")
        self.timeout = timeout

    def _state(self, st: Any, images: List[Any]) -> Any:
        if not images:
            return "" if st is None else st
        parts: List[Any] = []
        if st not in (None, ""):
            parts.append(state_text(st))
        parts.extend({"image": url} for url in image_data_urls(images, max_images=MAX_IMAGES))
        return parts

    def _ask(self, body: Dict[str, Any]) -> Dict[str, Any]:
        return post_json(f"{self.base_url}/v1/decide", body, api_key=self.api_key, timeout=self.timeout,
                         label="AutoTrust JEV /v1/decide")

    def decide(self, questions: Questions, state: Optional[Any] = None, image: Optional[Any] = None) -> Dict[str, Any]:
        """Answer every question about ``state`` (text / JSON) and optional images."""
        qs = load_questions(questions)
        st = load_state(state)
        images = as_list(image)
        if (st is None or st == "") and not images:
            raise ValueError("Provide a state (text or JSON) and/or an image.")
        for name, spec in qs.items():
            n = len(spec.get("criteria") or [])
            if spec["type"] in ("choice", "score") and n > MAX_OPTIONS:
                raise ValueError(f"question {name!r}: JEV takes at most {MAX_OPTIONS} options.")
        payload_state = self._state(st, images)

        answers: Dict[str, Any] = {}
        model = None
        input_tokens = 0
        for name, spec in qs.items():
            qtype, text = spec["type"], spec["instructions"]
            if qtype == "noul":
                hints = spec.get("criteria") or {}
                if isinstance(hints, dict) and hints:
                    text = f"{text}\n" + "\n".join(f"{k}: {v}" for k, v in hints.items())
                reply = self._ask({"kind": "noul", "state": payload_state, "question": text})
                probs = _probabilities(reply, ["false", "true"])
                answers[name] = {"type": "noul", "noul": probs.get("true", 0.0)}
            elif qtype == "choice":
                options = [str(k) for k in spec["criteria"]]
                reply = self._ask({"kind": "choice", "state": payload_state,
                                   "question": _choice_question(text, spec["criteria"]), "options": options})
                probs = _probabilities(reply, options)
                best = max(probs, key=probs.get)
                answers[name] = {"type": "choice", "choice": reply.get("choice", best),
                                 "confidence": probs[best], "probabilities": probs}
            else:  # score: ordered levels asked as a choice over the levels
                levels = [str(level) for level in spec["criteria"]]
                reply = self._ask({"kind": "choice", "state": payload_state, "question": text, "options": levels})
                by_level = _probabilities(reply, levels)
                probs = {str(i): by_level.get(level, 0.0) for i, level in enumerate(levels)}
                best = max(probs, key=probs.get)
                answers[name] = {"type": "score", "score": sum(int(i) * p for i, p in probs.items()),
                                 "confidence": probs[best], "legend": {str(i): lv for i, lv in enumerate(levels)},
                                 "probabilities": probs}
            model = reply.get("model", model)
            input_tokens += int((reply.get("usage") or {}).get("prompt_tokens") or 0)
        return {"model": model or "autotrust/JEV", "answers": answers,
                "usage": {"input_tokens": input_tokens, "output_tokens": 0, "requests": len(qs)}}
