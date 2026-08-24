"""Intent plan produced by the planner LLM."""

from __future__ import annotations

import json
import re
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

Intent = Literal["fashion", "model_swap", "vton", "clarify", "out_of_scope"]

INTENTS = ("fashion", "model_swap", "vton", "clarify", "out_of_scope")

VTON_REQUIRED = ("person_image", "garment_image")
MODEL_SWAP_REQUIRED = ("image",)


class Plan(BaseModel):
    intent: Intent
    reason: str = ""
    task: str = ""
    missing_inputs: List[str] = Field(default_factory=list)


_FENCE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


def parse_plan_json(text: str) -> Plan:
    """Parse a planner LLM reply into a Plan. Accepts raw JSON or fenced JSON."""
    raw = (text or "").strip()
    if not raw:
        raise ValueError("Planner LLM returned an empty intent.")
    fenced = _FENCE.search(raw)
    if fenced:
        raw = fenced.group(1).strip()
    if "{" in raw and "}" in raw:
        raw = raw[raw.find("{") : raw.rfind("}") + 1]
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("Planner LLM did not return a JSON object.")
    intent = str(data.get("intent", "")).strip().lower().replace("-", "_").replace(" ", "_")
    if intent in ("virtual_try_on", "tryon", "try_on"):
        intent = "vton"
    if intent in ("model-swap", "modelswap", "swap_model"):
        intent = "model_swap"
    if intent not in INTENTS:
        raise ValueError(f"Unknown intent '{intent}'. Expected one of {INTENTS}.")
    missing = data.get("missing_inputs") or data.get("missing") or []
    if isinstance(missing, str):
        missing = [missing]
    return Plan(
        intent=intent,  # type: ignore[arg-type]
        reason=str(data.get("reason") or ""),
        task=str(data.get("task") or data.get("prompt") or ""),
        missing_inputs=[str(item) for item in missing if item],
    )


def required_inputs(intent: str) -> tuple[str, ...]:
    if intent == "vton":
        return VTON_REQUIRED
    if intent == "model_swap":
        return MODEL_SWAP_REQUIRED
    return ()


def present_inputs(
    *,
    person_image: Optional[str] = None,
    garment_image: Optional[str] = None,
    image: Optional[str] = None,
    images: Optional[list] = None,
) -> dict[str, bool]:
    has_image = bool(image or person_image or (images and len(images) > 0))
    return {
        "person_image": bool(person_image or image),
        "garment_image": bool(garment_image),
        "image": has_image,
        "images": bool(images),
        "prompt": True,
    }
