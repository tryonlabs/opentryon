"""Live capability catalog for planner help answers.

The planner does not use a vector RAG store. Answers are grounded in this
brief, which is built from ``tryon.cli.registry`` so new models show up
after an MCP restart.
"""

from __future__ import annotations

import re

from tryon.cli.registry import SERVICE_HELP, SERVICES

STUDIO_SURFACES = (
    "Connect (MCP status)",
    "Agent chat (this planner)",
    "Image generate / edit",
    "VTON",
    "Understand",
    "Video",
    "BG Remove",
    "Prompt builder",
)

FALLBACK_HELP = (
    "Hi — I'm the OpenTryOn planner in TryOn Studio.\n\n"
    "I can help with:\n"
    "- **Image generate / edit** — describe a look, or attach a photo to edit\n"
    "- **Virtual try-on** — attach a person photo and a garment photo\n"
    "- **Model swap** — attach an outfit photo and describe the new model\n"
    "- **Video** — text or first-frame to video\n"
    "- **Understand** — ask about an image or a video URL\n"
    "- **Background remove** — attach a product or model photo\n\n"
    "Say what you want, and attach files when the task needs them. "
    "API keys stay in `opentryon/.env`, not in this chat."
)


def capabilities_brief(*, models_per_service: int = 14) -> str:
    """Compact, always-current list of services and registry model ids."""
    lines = [
        "You are answering as the OpenTryOn planner inside TryOn Studio.",
        "Studio screens: " + "; ".join(STUDIO_SURFACES) + ".",
        "Never ask the user for API keys; they live in opentryon/.env on the MCP host.",
        "The planner is a super agent over the live registry "
        "(same tools as MCP model tools, filtered by intent). Recipes: "
        "vton (person + garment), model_swap (outfit photo + new-person text), "
        "generate / edit / video / understand / bg-remove.",
        "",
        "Live registry (service → models):",
    ]
    for service, models in SERVICES.items():
        ids = list(models.keys())
        shown = ", ".join(ids[:models_per_service])
        extra = f" (+{len(ids) - models_per_service} more)" if len(ids) > models_per_service else ""
        help_text = SERVICE_HELP.get(service, "")
        lines.append(f"- {service}: {help_text}. Models: {shown}{extra}")
    return "\n".join(lines)


def out_of_scope_message(reason: str = "") -> str:
    """Polite decline that still points at what chat can do."""
    pointer = (
        "I focus on fashion AI: generate and edit images, virtual try-on, "
        "model swap, video, image/video understanding, and background removal. "
        "Ask what I can do, or send a look with what you want changed."
    )
    text = (reason or "").strip()
    if not text:
        return pointer
    lowered = text.lower().rstrip(".")
    if lowered in {
        "no fashion-related inputs",
        "not fashion",
        "out of scope",
        "not a fashion task",
    }:
        return pointer
    return f"{text.rstrip('.')}. {pointer}"


_HYPHEN_BEFORE_LABEL = re.compile(r"(?m)^[ \t]*[-*][ \t]*\n+[ \t]*(?=\*\*)")
_LABEL_THEN_COLON = re.compile(r"(?m)^([ \t]*[-*][ \t]+\*\*[^*]+\*\*)[ \t]*\n+[ \t]*:")
_LABEL_COLON_NL = re.compile(r"(?m)^([ \t]*[-*][ \t]+\*\*[^*]+\*\*[ \t]*:)[ \t]*\n+[ \t]*")
_ORPHAN_HYPHEN = re.compile(r"(?m)^[ \t]*[-*][ \t]*\n+")
_MULTI_NL = re.compile(r"\n{3,}")
_EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001F5FF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U0001F700-\U0001F77F"
    "\U0001F780-\U0001F7FF"
    "\U0001F800-\U0001F8FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FAFF"
    "\U0001FB00-\U0001FBFF"
    "\U0001F1E6-\U0001F1FF"
    "\U00002600-\U000026FF"
    "\U00002700-\U000027BF"
    "\U0000FE0F"
    "\U0000200D"
    "]+"
)
_SPACE_BEFORE_PUNCT = re.compile(r"[ \t]+([,.!?;:])")
_MULTI_SPACE = re.compile(r"[ \t]{2,}")


def strip_emojis(text: str) -> str:
    """Remove emoji / dingbats the chat LLM likes to sprinkle in."""
    raw = _EMOJI_RE.sub("", text or "")
    raw = _MULTI_SPACE.sub(" ", raw)
    return _SPACE_BEFORE_PUNCT.sub(r"\1", raw)


def normalize_help_markdown(text: str) -> str:
    """Collapse list items the chat UI can render as one line each.

    Cheap LLMs often emit a hyphen, a bold label, and a ``: description`` on
    three separate lines. Studio's markdown renderer then shows a dangling ``-``.
    """
    raw = strip_emojis((text or "").replace("\r\n", "\n")).strip()
    raw = _HYPHEN_BEFORE_LABEL.sub("- ", raw)
    raw = _LABEL_THEN_COLON.sub(r"\1:", raw)
    raw = _LABEL_COLON_NL.sub(r"\1 ", raw)
    raw = _ORPHAN_HYPHEN.sub("", raw)
    return _MULTI_NL.sub("\n\n", raw).strip()
