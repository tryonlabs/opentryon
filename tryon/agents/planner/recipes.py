"""Planner recipes: map chat inputs onto ``invoke_model`` kwargs.

VTON / model-swap keep a little domain logic (which dest names, outfit-preserving
prompt rewrite). They are not LangChain agents and not extra MCP tools.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

from tryon.agents.planner.bind import pick_model, slice_for_intent
from tryon.cli.registry import ModelSpec
from tryon.cli.runner import invoke_model

PERSON_DESTS = {
    "person",
    "person_image",
    "source_image",
    "model_image",
}
GARMENT_DESTS = {
    "garment",
    "garment_image",
    "garment_images",
    "reference_image",
    "cloth_image",
    "product_image",
}
IMAGE_DESTS = {"image", "start_image"}
PROMPT_DESTS = {"prompt", "garment_description"}
VIDEO_DESTS = {"video"}


def swap_prompt(task: str) -> str:
    """Outfit-preserving rewrite used by the old ModelSwapAgent."""
    description = (task or "").strip() or "a professional fashion model"
    lowered = description.lower()
    if "wearing the exact same outfit" in lowered:
        return description
    return (
        f"Professional fashion photography showing {description} wearing the "
        "exact same outfit with all clothing details, patterns, colors, and "
        "styling preserved perfectly. Maintain the original lighting, "
        "background, composition, and camera angle. Photorealistic, "
        "high-end e-commerce quality."
    )


def _dests(spec: ModelSpec) -> Dict[str, Any]:
    return {arg.dest: arg for arg in spec.args}


def invoke_kwargs(
    spec: ModelSpec,
    *,
    prompt: Optional[str] = None,
    person_image: Optional[str] = None,
    garment_image: Optional[str] = None,
    image: Optional[str] = None,
    images: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """Fill registry dests from planner media. Unknown dests stay unset (defaults)."""
    extras = [path for path in (images or []) if path]
    ref = image or person_image or (extras[0] if extras else None)
    kwargs: Dict[str, Any] = {}
    for arg in spec.args:
        dest = arg.dest
        value: Any = None
        if dest in PERSON_DESTS and person_image:
            value = person_image
        elif dest in GARMENT_DESTS and garment_image:
            value = [garment_image] if arg.nargs in ("+", "*") else garment_image
        elif dest in IMAGE_DESTS and ref:
            value = ref
        elif dest in PROMPT_DESTS and prompt:
            value = prompt
        elif dest in VIDEO_DESTS and ref:
            value = ref
        if value is None:
            continue
        kwargs[dest] = value
    return kwargs


@dataclass
class PreparedCall:
    intent: str
    service: str
    model: str
    spec: ModelSpec
    kwargs: Dict[str, Any]
    recipe: str
    task: str
    bound_ids: List[str] = field(default_factory=list)


def prepare_call(
    intent: str,
    task: str,
    *,
    person_image: Optional[str] = None,
    garment_image: Optional[str] = None,
    image: Optional[str] = None,
    images: Optional[Sequence[str]] = None,
    hinted_model: Optional[str] = None,
) -> PreparedCall:
    """Pick a registry model for this intent and build invoke_model kwargs."""
    slice_ = slice_for_intent(intent)
    has_image = bool(image or person_image or images)
    picked = pick_model(
        intent,
        task,
        hinted=hinted_model,
        has_image=has_image,
        slice_=slice_,
    )
    if picked is None:
        raise RuntimeError(f"No registry models available for intent '{intent}'.")

    recipe = "one_shot"
    prompt = task
    if intent == "vton":
        recipe = "vton"
    elif intent == "model_swap":
        recipe = "swap"
        prompt = swap_prompt(task)

    kwargs = invoke_kwargs(
        picked.spec,
        prompt=prompt,
        person_image=person_image,
        garment_image=garment_image,
        image=image or person_image,
        images=images,
    )
    return PreparedCall(
        intent=intent,
        service=picked.service,
        model=picked.model,
        spec=picked.spec,
        kwargs=kwargs,
        recipe=recipe,
        task=task,
        bound_ids=[f"{item.service}/{item.model}" for item in slice_],
    )


def execute_call(prepared: PreparedCall, *, dry_run: bool = False) -> Dict[str, Any]:
    """Run the bound registry tool via the same runner MCP model tools use."""
    return invoke_model(
        prepared.service,
        prepared.model,
        dry_run=dry_run,
        **prepared.kwargs,
    )


def run_recipe(
    intent: str,
    task: str,
    *,
    person_image: Optional[str] = None,
    garment_image: Optional[str] = None,
    image: Optional[str] = None,
    images: Optional[Sequence[str]] = None,
    hinted_model: Optional[str] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Facade used by VTOnAgent / FashionAgent / ModelSwapAgent."""
    prepared = prepare_call(
        intent,
        task,
        person_image=person_image,
        garment_image=garment_image,
        image=image,
        images=images,
        hinted_model=hinted_model,
    )
    result = execute_call(prepared, dry_run=dry_run)
    payload = {
        "status": "success" if result.get("success") else "error",
        "provider": prepared.model,
        "service": prepared.service,
        "model": prepared.model,
        "recipe": prepared.recipe,
        "tool": f"{prepared.service}_{prepared.model}".replace("-", "_").replace(".", "_"),
        **result,
    }
    if payload.get("images_base64") and "images" not in payload:
        payload["images"] = payload["images_base64"]
    if not result.get("success"):
        payload["error"] = result.get("error") or "invoke_model failed"
        payload["message"] = payload["error"]
    return payload
