"""Filter the live registry to the models the planner may call this turn.

Classify first, then bind a capability slice. A model the user names (for
example ``wan-3.0``) pins that registry id from the **full** catalog — not
only the slice. If they do not name one, use the capability default.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from tryon.cli.registry import SERVICES, ModelSpec, get_service
from tryon.agents.planner.plan import current_utterance

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

# Cloud defaults when the user does not name a model. Local extras are never
# the implicit default except bg-remove (ben2 is the only registered model).
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

# Short names that are unique enough. Longer needles win.
_ALIASES: Tuple[Tuple[str, str, Optional[str]], ...] = (
    # needle, model_id, optional service constraint
    ("kling ai", "kling-ai", "vton"),
    ("kolors", "kling-ai", "vton"),
    ("virtual-try-on-001", "google-vton", "vton"),
    ("imagen virtual try-on", "google-vton", "vton"),
    ("vertex try-on", "google-vton", "vton"),
    ("vertex vton", "google-vton", "vton"),
    ("google vton", "google-vton", "vton"),
    ("google-vton", "google-vton", "vton"),
    ("fashn", "fashn-tryon-max", "vton"),
    ("flux vto", "flux-vto", "vton"),
    ("nova canvas", "nova-canvas", "vton"),
    ("segmind", "segmind", "vton"),
    ("nano banana pro", "nano-banana-pro", None),
    ("nano banana 2 lite", "nano-banana-2-lite", None),
    ("nano banana 2", "nano-banana-2", None),
    ("nano banana", "nano-banana", None),
    ("gemini 3 pro", "nano-banana-pro", None),
    ("gemini-3-pro", "nano-banana-pro", None),
    ("flux2 pro", "flux2-pro", None),
    ("flux 2 pro", "flux2-pro", None),
    ("flux2 flex", "flux2-flex", None),
    ("flux2 turbo", "flux2-turbo", None),
    ("flux 2 turbo", "flux2-turbo", None),
    ("gpt-image", "gpt-image", None),
    ("gpt image", "gpt-image", None),
    ("gpt-image-1", "gpt-image", None),
    ("seedream", "seedream", None),
    ("p-image-ideogram", "p-image-ideogram", "generate"),
    ("p image ideogram", "p-image-ideogram", "generate"),
    ("p-image ideogram", "p-image-ideogram", "generate"),
    ("pruna ideogram", "p-image-ideogram", "generate"),
    ("ideogram", "ideogram", None),
    ("muse-image", "muse-image", None),
    ("muse image", "muse-image", None),
    ("meta muse", "muse-image", None),
    ("minimax-h3-local", "minimax-h3-local", "video-generate"),
    ("minimax h3 local", "minimax-h3-local", "video-generate"),
    ("minimax-h3", "minimax-h3", "video-generate"),
    ("minimax h3", "minimax-h3", "video-generate"),
    ("hailuo-h3", "minimax-h3", "video-generate"),
    ("hailuo h3", "minimax-h3", "video-generate"),
    ("hailuo 3", "minimax-h3", "video-generate"),
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
    ("cosmos 3 reasoner", "cosmos3-reasoner", "understand"),
    ("cosmos3-reasoner", "cosmos3-reasoner", "understand"),
    ("cosmos3-nano-reasoner", "cosmos3-reasoner", "understand"),
    ("cosmos 3 generator", "cosmos3", "video-generate"),
    ("cosmos3-nano", "cosmos3", "video-generate"),
    ("cosmos3", "cosmos3", "video-generate"),
    ("nemotron 3 nano omni", "nemotron-omni", "understand"),
    ("nemotron-omni", "nemotron-omni", "understand"),
    ("nemotron omni", "nemotron-omni", "understand"),
    ("qwen3.8-max", "qwen3.8-max", "understand"),
    ("qwen 3.8 max", "qwen3.8-max", "understand"),
    ("qwen3.8", "qwen3.8", "understand"),
    ("llava", "llava-next", "understand"),
    ("kimi k2.6", "kimi-k2.6", "understand"),
    ("kimi-k2.6", "kimi-k2.6", "understand"),
    ("kimi k3", "kimi-k3", "understand"),
    ("ben2", "ben2", "bg-remove"),
    ("kimi", "kimi-k2.6", "understand"),
)


class NamedModelUnknown(ValueError):
    """The user named a model that is not in the live registry."""

    def __init__(self, name: str, intent: str, available: Sequence[str]):
        self.name = name
        self.intent = intent
        self.available = list(available)
        super().__init__(f"Unknown model {name!r} for intent {intent!r}")


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


def all_bound_models() -> List[BoundModel]:
    """Every registry model — used when the user names an id outside the slice."""
    bound: List[BoundModel] = []
    for service, models in SERVICES.items():
        for model_id, spec in models.items():
            bound.append(BoundModel(service=service, model=model_id, spec=spec))
    return bound


def _universe(slice_: Sequence[BoundModel]) -> List[BoundModel]:
    """Slice first, then the rest of the catalog (named models can cross capability)."""
    items = list(slice_)
    seen = {(item.service, item.model) for item in items}
    for item in all_bound_models():
        key = (item.service, item.model)
        if key not in seen:
            items.append(item)
            seen.add(key)
    return items


def _norm(text: str) -> str:
    return re.sub(r"[\s_]+", "-", (text or "").strip().lower())


def _needles_for(item: BoundModel) -> List[str]:
    # Ids and spaced variants only. Marketing labels are too long and collide
    # with chat history ("Completed via generate/nano-banana-pro").
    needles = {
        item.model.lower(),
        item.model.lower().replace(".", "-"),
        item.model.lower().replace("-", " "),
    }
    return [n for n in needles if len(n) >= 3]


_PIN = re.compile(
    r"\b(?:using|use|via)\s+(?:the\s+)?(?:model\s+)?"
    r"([a-z0-9](?:[a-z0-9.\-]*[a-z0-9])?)",
    re.I,
)


def _contains(haystack: str, needle: str) -> bool:
    if not needle:
        return False
    pattern = r"(?<![a-z0-9])" + re.escape(needle) + r"(?![a-z0-9])"
    return re.search(pattern, haystack, flags=re.IGNORECASE) is not None


def _lookup_id(
    model_id: str,
    service: Optional[str],
    slice_: Sequence[BoundModel],
    universe: Sequence[BoundModel],
) -> Optional[BoundModel]:
    if service:
        for item in slice_:
            if item.model == model_id and item.service == service:
                return item
        for item in universe:
            if item.model == model_id and item.service == service:
                return item
    for item in slice_:
        if item.model == model_id:
            return item
    for item in universe:
        if item.model == model_id:
            return item
    return None


def match_named_model(
    prompt: str,
    slice_: Sequence[BoundModel],
    *,
    hinted: Optional[str] = None,
) -> Optional[BoundModel]:
    """Pin a model id mentioned in ``prompt`` or ``hinted`` (plan.model).

    Searches the capability slice first, then the full registry so a named
    model (e.g. ``wan-3.0`` during a generate/fashion turn) still binds.
    """
    slice_list = list(slice_)
    universe = _universe(slice_list)
    slice_keys = {(item.service, item.model) for item in slice_list}

    if hinted:
        key = _norm(hinted)
        hit = _lookup_id(hinted.strip(), None, slice_list, universe)
        if hit is None:
            for item in universe:
                if _norm(item.model) == key or _norm(item.spec.id) == key:
                    hit = item
                    break
        if hit is None:
            for needle, model_id, service in _ALIASES:
                if _norm(needle) == key or _norm(model_id) == key:
                    hit = _lookup_id(model_id, service, slice_list, universe)
                    if hit:
                        break
        if hit:
            return hit

    text = prompt or ""
    candidates: List[Tuple[int, int, BoundModel]] = []
    for item in universe:
        for needle in _needles_for(item):
            if _contains(text, needle):
                bonus = 1 if (item.service, item.model) in slice_keys else 0
                candidates.append((len(needle), bonus, item))
                break
    lowered = text.lower()
    for needle, model_id, service in _ALIASES:
        if not _contains(lowered, needle):
            continue
        item = _lookup_id(model_id, service, slice_list, universe)
        if item is None:
            continue
        bonus = 1 if (item.service, item.model) in slice_keys else 0
        candidates.append((len(needle), bonus, item))
    if not candidates:
        return None
    candidates.sort(key=lambda row: (row[0], row[1]), reverse=True)
    return candidates[0][2]


def _hint_mentioned(hinted: str, prompt: str) -> bool:
    """True when the classifier's model id (or an alias) actually appears in the user text."""
    if not hinted or not prompt:
        return False
    raw = hinted.strip()
    if _contains(prompt, raw) or _contains(prompt, raw.replace("-", " ")):
        return True
    key = _norm(raw)
    for needle, model_id, _service in _ALIASES:
        if _norm(model_id) == key and _contains(prompt, needle):
            return True
        if _norm(needle) == key and _contains(prompt, needle):
            return True
    return False


def _bound_default(intent: str) -> Optional[BoundModel]:
    default = DEFAULT_MODEL.get(intent)
    if not default:
        return None
    service, model = default
    spec = SERVICES.get(service, {}).get(model)
    if spec is None:
        return None
    return BoundModel(service=service, model=model, spec=spec)


def _first_cloud(slice_: Iterable[BoundModel]) -> Optional[BoundModel]:
    items = list(slice_)
    for item in items:
        if item.spec.extra != "local":
            return item
    return items[0] if items else None


def _explicit_named(
    prompt: str,
    slice_: Sequence[BoundModel],
) -> Optional[BoundModel]:
    """Last 'using/use/via <id>' in the current utterance that resolves to a model."""
    hits: List[BoundModel] = []
    for match in _PIN.finditer(prompt or ""):
        token = match.group(1)
        item = match_named_model(token, slice_, hinted=token)
        if item is not None:
            hits.append(item)
    return hits[-1] if hits else None


def pick_model(
    intent: str,
    prompt: str,
    *,
    hinted: Optional[str] = None,
    has_image: bool = False,
    slice_: Optional[Sequence[BoundModel]] = None,
) -> Optional[BoundModel]:
    """User-named model wins exclusively; otherwise the capability default.

    Only the current user utterance is scanned (Studio history wrappers are
    stripped). ``using gpt-image`` pins that id even if an earlier turn named
    another model. A classifier ``hinted`` id is used only when that name also
    appears in the current utterance.
    """
    prompt = current_utterance(prompt)
    slice_list = list(slice_ if slice_ is not None else slice_for_intent(intent))

    pinned = _explicit_named(prompt, slice_list)
    if pinned:
        return pinned

    named = match_named_model(prompt, slice_list, hinted=None)
    if named:
        return named

    hinted_id = (hinted or "").strip()
    if hinted_id:
        mentioned = _hint_mentioned(hinted_id, prompt)
        hinted_hit = match_named_model(prompt, slice_list, hinted=hinted_id)
        if hinted_hit and mentioned:
            return hinted_hit
        if mentioned and hinted_hit is None:
            raise NamedModelUnknown(
                hinted_id,
                intent,
                [f"{item.service}/{item.model}" for item in slice_list],
            )

    if intent == "fashion" and has_image:
        edit_default = _bound_default("edit")
        if edit_default:
            return edit_default

    default = _bound_default(intent)
    if default:
        return default
    return _first_cloud(slice_list)


def unknown_model_message(name: str, intent: str, available: Sequence[str]) -> str:
    """Human reply when the user named a model that is not in the registry."""
    ids = [item.split("/", 1)[-1] for item in available[:18]]
    shown = ", ".join(ids) if ids else "the models listed on Connect"
    extra = " (+more)" if len(available) > 18 else ""
    default = _bound_default(intent)
    default_s = f"{default.service}/{default.model}" if default else "the capability default"
    return (
        f"I don't have a model called '{name}'. "
        f"For this task I can use: {shown}{extra}. "
        "You can also name any other registry model (for example wan-3.0, "
        "flux2-pro, kimi-k2.6). "
        f"If you don't pick one, I use {default_s}."
    )
