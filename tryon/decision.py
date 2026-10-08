"""
Shared helpers for OpenTryOn's ``decide`` service.

"System One" decision models (Liquid AI ``d1-3B`` / ``d1-omni-600M``, Typesafe
``jev``) do not write text. They take a *state* (text, JSON, optionally an
image or audio clip) plus a named set of *questions* and return typed,
calibrated answers in a single forward pass:

* ``noul``   -- yes/no; returns P(yes)
* ``choice`` -- pick one of the named options; returns the choice + probabilities
* ``score``  -- place the state on an ordered scale of 2-10 levels

Question schema (identical across the supported models)::

    {
      "refund":  {"type": "noul", "instructions": "Does the customer want a refund?"},
      "team":    {"type": "choice", "instructions": "Which team owns this?",
                  "criteria": {"billing": "payment issues", "technical": "bugs"}},
      "urgency": {"type": "score", "instructions": "How urgent is this?",
                  "criteria": ["Can wait", "Soon", "Blocking now"]},
    }
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional, Union

VALID_QUESTION_TYPES = {"noul", "choice", "score"}

Questions = Union[Dict[str, Dict[str, Any]], str]


def load_questions(questions: Questions) -> Dict[str, Dict[str, Any]]:
    """Accept a dict, a JSON string, or a path to a JSON file; validate shape."""
    if isinstance(questions, str):
        text = questions.strip()
        if os.path.isfile(text):
            with open(text, "r", encoding="utf-8") as f:
                text = f.read()
        try:
            questions = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "questions must be a dict, a JSON string, or a path to a JSON file "
                f"(could not parse JSON: {exc})."
            ) from exc
    if not isinstance(questions, dict) or not questions:
        raise ValueError("questions must be a non-empty object mapping question name -> spec.")

    for name, spec in questions.items():
        if not isinstance(spec, dict):
            raise ValueError(f"question {name!r} must be an object with 'type' and 'instructions'.")
        qtype = spec.get("type")
        if qtype not in VALID_QUESTION_TYPES:
            raise ValueError(
                f"question {name!r}: type must be one of {sorted(VALID_QUESTION_TYPES)} (got {qtype!r})."
            )
        if not spec.get("instructions"):
            raise ValueError(f"question {name!r}: 'instructions' is required.")
        criteria = spec.get("criteria")
        if qtype == "choice" and not (isinstance(criteria, dict) and len(criteria) >= 2):
            raise ValueError(f"question {name!r}: 'choice' needs a criteria object with >= 2 options.")
        if qtype == "score" and not (isinstance(criteria, list) and 2 <= len(criteria) <= 10):
            raise ValueError(f"question {name!r}: 'score' needs an ordered criteria list of 2-10 levels.")
    return questions


def load_state(state: Optional[Any]) -> Optional[Any]:
    """Return the state as text / JSON value. A path to an existing file is read;
    strings that look like a JSON object/array are parsed."""
    if state is None or not isinstance(state, str):
        return state
    text = state
    if os.path.isfile(text):
        with open(text, "r", encoding="utf-8") as f:
            text = f.read()
    stripped = text.strip()
    if stripped[:1] in ("{", "["):
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            pass
    return text
