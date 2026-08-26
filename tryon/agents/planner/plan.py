"""Intent plan produced by the planner LLM."""

from __future__ import annotations

import json
import re
from typing import List, Literal, Optional, Sequence

from pydantic import BaseModel, Field

Intent = Literal[
    "fashion",
    "model_swap",
    "vton",
    "generate",
    "edit",
    "video",
    "understand",
    "bg_remove",
    "multi_step",
    "clarify",
    "help",
    "out_of_scope",
]

INTENTS = (
    "fashion",
    "model_swap",
    "vton",
    "generate",
    "edit",
    "video",
    "understand",
    "bg_remove",
    "multi_step",
    "clarify",
    "help",
    "out_of_scope",
)

ACTION_INTENTS = (
    "fashion",
    "model_swap",
    "vton",
    "generate",
    "edit",
    "video",
    "understand",
    "bg_remove",
    "multi_step",
)

VTON_REQUIRED = ("person_image", "garment_image")
MODEL_SWAP_REQUIRED = ("image",)
EDIT_REQUIRED = ("image",)
BG_REMOVE_REQUIRED = ("image",)


class Plan(BaseModel):
    intent: Intent
    reason: str = ""
    task: str = ""
    model: str = ""
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
    if intent in ("qa", "chat", "capabilities", "capability", "greeting", "greet"):
        intent = "help"
    if intent in ("video_generate", "video-generate", "t2v", "i2v"):
        intent = "video"
    if intent in ("t2i", "text_to_image", "image_generate"):
        intent = "generate"
    if intent in ("image_edit", "i2i"):
        intent = "edit"
    if intent in ("bg-remove", "background", "background_remove", "bgremove"):
        intent = "bg_remove"
    if intent in ("multistep", "multi-step", "chain"):
        intent = "multi_step"
    if intent not in INTENTS:
        raise ValueError(f"Unknown intent '{intent}'. Expected one of {INTENTS}.")
    missing = data.get("missing_inputs") or data.get("missing") or []
    if isinstance(missing, str):
        missing = [missing]
    return Plan(
        intent=intent,  # type: ignore[arg-type]
        reason=str(data.get("reason") or ""),
        task=str(data.get("task") or data.get("prompt") or ""),
        model=str(data.get("model") or data.get("model_id") or ""),
        missing_inputs=[str(item) for item in missing if item],
    )


def required_inputs(intent: str) -> tuple[str, ...]:
    if intent == "vton":
        return VTON_REQUIRED
    if intent == "model_swap":
        return MODEL_SWAP_REQUIRED
    if intent == "edit":
        return EDIT_REQUIRED
    if intent == "bg_remove":
        return BG_REMOVE_REQUIRED
    if intent == "understand":
        return ("image",)
    return ()


_CAPABILITY_ABOUT = re.compile(
    r"\b(what models|which models|tell me more|how (do|can) (i|we)|how does|"
    r"what can you|do you support|are you able)\b",
    re.I,
)
_CAN_YOU_TASK = re.compile(
    r"^\s*(can|could) you (please )?(perform |do |run )?"
    r"(image )?(understanding|understand|edit(?:ing)?|try-?on|virtual try-?on|"
    r"generate|generation|remove (the )?background|bg remove)\b",
    re.I,
)
_RUN_NOW = re.compile(
    r"\b(this|attached|these|here|make it|change|into |so that)\b",
    re.I,
)
_UNSUPPORTED = re.compile(
    r"\b("
    r"3d|3-d|three[\s-]?dimensional|"
    r"3d\s+world|open world|game world|virtual world|"
    r"cad|mesh|voxel|blender|unity|unreal|"
    r"video game|game engine|"
    r"website|web ?app|source code|python script|"
    r"\baudio\b|\bmusic\b|podcast|\bsong\b"
    r")\b",
    re.I,
)


def current_utterance(prompt: str) -> str:
    """Strip Studio history wrappers so gates see only the latest user line."""
    text = prompt or ""
    lowered = text.lower()
    start = lowered.find("current request:")
    if start != -1:
        text = text[start + len("current request:") :]
        lowered = text.lower()
    for marker in ("previous turns", "quick action:"):
        cut = lowered.find(marker)
        if cut != -1:
            text = text[:cut]
            lowered = text.lower()
    return text.strip()


def is_capability_question(prompt: str) -> bool:
    """True when the user is asking *about* a skill, not asking to run it now."""
    text = current_utterance(prompt)
    if not text:
        return False
    if _CAPABILITY_ABOUT.search(text):
        return True
    if _CAN_YOU_TASK.search(text) and not _RUN_NOW.search(text):
        return True
    return False


def is_unsupported_request(prompt: str) -> bool:
    """True when the user asked for a job this product cannot run (3D, games, …)."""
    text = current_utterance(prompt)
    return bool(text and _UNSUPPORTED.search(text))


def clarify_message(intent: str, missing: Sequence[str]) -> str:
    """User-facing ask for files. Never return a bare 'missing inputs'."""
    needed = [item for item in missing if item]
    names = set(needed)
    if "person_image" in names and "garment_image" in names:
        return "Attach a person photo and a garment photo, then ask me to try the garment on."
    if names == {"garment_image"}:
        return "Attach a garment photo as well, then send again."
    if names == {"person_image"}:
        return "Attach a person photo as well, then send again."
    if "image" in names:
        if intent == "edit":
            return "Attach the photo you want to edit and tell me what to change."
        if intent == "understand":
            return "Attach a photo (or paste a video URL) and ask what you want to know about it."
        if intent == "bg_remove":
            return "Attach a photo and I'll remove the background."
        if intent == "model_swap":
            return "Attach an outfit photo and describe the new person."
        return "Attach a photo so I can continue."
    if needed:
        return f"I need {', '.join(needed)} before I can run this. Attach the file(s) and send again."
    return "I need a bit more before I can run this. Attach the relevant photo(s) and send again."


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
    }
