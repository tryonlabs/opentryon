"""Filter the live registry to the models the planner may call this turn.

The planner is allowed to use every registry tool, but never binds the full
catalog at once. Classify first, then this module returns a slice. Named
models in the user prompt (e.g. ``wan-3.0``) pin an exact id inside that slice.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from tryon.cli.registry import SERVICES, ModelSpec, get_service

# Intent -> registry services (planner never dumps all ~66 tools into one step).
INTENT_SERVICES: Dict[str, Tuple[str, ...]] = {
    "vton": ("vton",),
    "model_swap": ("edit", "generate"),
    "fashion": ("generate", "edit", "video-generate"),
    "generate": ("generate",),
    "edit": ("edit",),
    "video": ("video-generate",),
    "understand": ("understand",),
    "bg_remove": ("bg-remove",),
    "multi_step": (
        "bg-remove",
        "vton",
        "generate",
        "edit",
        "video-generate",
        "understand",
    ),
}

# Cloud defaults. Local extras are never the implicit default.
DEFAULT_MODEL: Dict[str, Tuple[str, str]] = {
    "vton": ("vton", "kling-ai"),
    "model_swap": ("edit", "nano-banana-pro"),
    "fashion": ("generate", "nano-banana-pro"),
    "generate": ("generate", "nano-banana-pro"),
    "edit": ("edit", "nano-banana-pro"),
    "video": ("video-generate", "sora"),
    "understand": ("understand", "kimi-k2.6"),
    "bg_remove": ("bg-remove", "ben2"),
    "multi_step": ("generate", "nano-banana-pro"),
}

# Short names that are unique enough inside a slice. Longer needles win.
_ALIASES: Tuple[Tuple[str, str, Optional[str]], ...] = (
    # needle, model_id, optional service constraint
    ("kling ai", "kling-ai", "vton"),
    ("kolors", "kling-ai", "vton"),
    ("fashn", "fashn-tryon-max", "vton"),
    ("flux vto", "flux-vto", "vton"),
    ("nova canvas", "nova-canvas", "vton"),
    ("segmind", "segmind", "vton"),
    ("nano banana pro", "nano-banana-pro", None),
    ("nano banana 2 lite", "nano-banana-2-lite", None),
    ("nano banana 2", "nano-banana-2", None),
    ("nano banana", "nano-banana", None),
    ("flux2 pro", "flux2-pro", None),
    ("flux 2 pro", "flux2-pro", None),
    ("flux2 flex", "flux2-flex", None),
    ("seedream", "seedream", None),
    ("ideogram", "ideogram", None),
    ("hailuo", "hailuo-2.3", "video-generate"),
    ("wan 3.0", "wan-3.0", "video-generate"),
    ("wan-3.0", "wan-3.0", "video-generate"),
    ("wan 3", "wan-3.0", "video-generate"),
    ("runway gen", "runway-gen4.5", "video-generate"),
    ("runway-gen", "runway-gen4.5", "video-generate"),
    ("gen-4.5", "runway-gen4.5", "video-generate"),
    ("gen 4.5", "runway-gen4.5", "video-generate"),
    ("kling 3", "kling-v3", "video-generate"),
    ("kling omni", "kling-v3-omni", "video-generate"),
    ("seedance", "seedance", "video-generate"),
    ("luma ray", "luma-ray-3.2", "video-generate"),
    ("gemini omni", "gemini-omni", "video-generate"),
    ("sora", "sora", "video-generate"),
    ("veo", "veo", "video-generate"),
    ("qwen-image", "qwen-image", None),
    ("ben2", "ben2", "bg-remove"),
    ("kimi", "kimi-k2.6", "understand"),
)


@dataclass(frozen=True)
class BoundModel:
    service: str
    model: str
    spec: ModelSpec


def slice_for_intent(intent: str) -> List[BoundModel]:
    """Registry models the planner may call for this classified intent."""
    services = INTENT_SERVICES.get(intent) or INTENT_SERVICES["fashion"]
    bound: List[BoundModel] = []
    for service in services:
        try:
            models = get_service(service)
        except KeyError:
            continue
        for model_id, spec in models.items():
            bound.append(BoundModel(service=service, model=model_id, spec=spec))
    return bound


def _norm(text: str) -> str:
    return re.sub(r"[\s_]+", "-", (text or "").strip().lower())


def _needles_for(item: BoundModel) -> List[str]:
    needles = {
        item.model.lower(),
        item.model.lower().replace(".", "-"),
        item.model.lower().replace("-", " "),
        (item.spec.label or "").lower(),
    }
    return [n for n in needles if len(n) >= 3]


def _contains(haystack: str, needle: str) -> bool:
    if not needle:
        return False
    pattern = r"(?<![a-z0-9])" + re.escape(needle) + r"(?![a-z0-9])"
    return re.search(pattern, haystack, flags=re.IGNORECASE) is not None


def match_named_model(
    prompt: str,
    slice_: Sequence[BoundModel],
    *,
    hinted: Optional[str] = None,
) -> Optional[BoundModel]:
    """Pin a model id mentioned in ``prompt`` or ``hinted`` (plan.model)."""
    if hinted:
        key = _norm(hinted)
        for item in slice_:
            if _norm(item.model) == key or _norm(item.spec.id) == key:
                return item
        # hinted id might live outside the slice (user named wan during fashion)
        for service, models in SERVICES.items():
            for model_id, spec in models.items():
                if _norm(model_id) == key:
                    return BoundModel(service=service, model=model_id, spec=spec)

    text = prompt or ""
    candidates: List[Tuple[int, BoundModel]] = []
    for item in slice_:
        for needle in _needles_for(item):
            if _contains(text, needle):
                candidates.append((len(needle), item))
                break
    lowered = text.lower()
    for needle, model_id, service in _ALIASES:
        if not _contains(lowered, needle):
            continue
        for item in slice_:
            if item.model == model_id and (service is None or item.service == service):
                candidates.append((len(needle), item))
                break
        else:
            # alias hit a model not in the slice — still allow (named-model chat)
            if service and model_id in SERVICES.get(service, {}):
                spec = SERVICES[service][model_id]
                candidates.append(
                    (len(needle), BoundModel(service=service, model=model_id, spec=spec))
                )
            else:
                for svc, models in SERVICES.items():
                    if model_id in models:
                        spec = models[model_id]
                        candidates.append(
                            (
                                len(needle),
                                BoundModel(service=svc, model=model_id, spec=spec),
                            )
                        )
                        break
    if not candidates:
        return None
    candidates.sort(key=lambda pair: pair[0], reverse=True)
    return candidates[0][1]


def _first_cloud(slice_: Iterable[BoundModel]) -> Optional[BoundModel]:
    items = list(slice_)
    for item in items:
        if item.spec.extra != "local":
            return item
    return items[0] if items else None


def pick_model(
    intent: str,
    prompt: str,
    *,
    hinted: Optional[str] = None,
    has_image: bool = False,
    slice_: Optional[Sequence[BoundModel]] = None,
) -> Optional[BoundModel]:
    """Named model wins; otherwise recipe default; otherwise first cloud model."""
    slice_list = list(slice_ if slice_ is not None else slice_for_intent(intent))
    named = match_named_model(prompt, slice_list, hinted=hinted)
    if named:
        return named

    # fashion catch-all: an attached image without a named model is an edit.
    if intent == "fashion" and has_image:
        edit_default = DEFAULT_MODEL.get("edit")
        if edit_default:
            service, model = edit_default
            if model in SERVICES.get(service, {}):
                return BoundModel(
                    service=service, model=model, spec=SERVICES[service][model]
                )

    default = DEFAULT_MODEL.get(intent)
    if default:
        service, model = default
        if model in SERVICES.get(service, {}):
            spec = SERVICES[service][model]
            if any(item.service == service and item.model == model for item in slice_list):
                return BoundModel(service=service, model=model, spec=spec)
            # default is fine even if classifier used a broader slice
            return BoundModel(service=service, model=model, spec=spec)

    return _first_cloud(slice_list)
