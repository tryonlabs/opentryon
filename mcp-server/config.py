"""Environment configuration for the OpenTryOn MCP server.

Loads the parent repo's ``.env`` (same file the ``opentryon`` CLI and the
adapters themselves read via ``python-dotenv``/``os.getenv``) and derives a
readiness report straight from :data:`tryon.cli.registry.SERVICES`, so this
never drifts out of sync with which models actually need which keys.
"""

from __future__ import annotations

import os
import re
import stat
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from dotenv import load_dotenv

_PARENT_DIR = Path(__file__).resolve().parent.parent
_DEFAULT_ENV_PATH = _PARENT_DIR / ".env"
_ENV_NAME_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")

# Aliases documented in env.template plus planner-only secrets that are not
# always present as a registry ``env_hint``.
_EXTRA_ENV_NAMES = (
    "OPENTRYON_AGENT_LLM_API_KEY",
    "ANTHROPIC_API_KEY",
    "GOOGLE_API_KEY",
    "GOOGLE_CLOUD_LOCATION",
    "GOOGLE_APPLICATION_CREDENTIALS",
    "BYTEPLUS_ARK_API_KEY",
    "WAN_API_KEY",
    "RUNWAY_API_KEY",
    "META_MODEL_API_KEY",
    "MUSE_API_KEY",
)

# Registry env_hint name -> names that also count as configured (adapter aliases).
_VAR_ALIASES: Dict[str, Tuple[str, ...]] = {
    "MODEL_API_KEY": ("MODEL_API_KEY", "META_MODEL_API_KEY", "MUSE_API_KEY"),
}

# (id, label, docs_url, env var names, optional notes). Order is the Connect rail.
_PROVIDER_CATALOG: Tuple[Tuple[str, str, str, Tuple[str, ...], str], ...] = (
    (
        "agent",
        "Studio chat (planner)",
        "https://tryonlabs.github.io/opentryon/docs/agents/planner-agent",
        ("OPENTRYON_AGENT_LLM_API_KEY",),
        "Optional override. Chat uses OPENAI_API_KEY, ANTHROPIC_API_KEY, or "
        "GEMINI_API_KEY based on OPENTRYON_AGENT_LLM_PROVIDER.",
    ),
    (
        "openai",
        "OpenAI",
        "https://platform.openai.com/api-keys",
        ("OPENAI_API_KEY",),
        "Also used by Studio chat when OPENTRYON_AGENT_LLM_PROVIDER=openai.",
    ),
    (
        "anthropic",
        "Anthropic",
        "https://console.anthropic.com/settings/keys",
        ("ANTHROPIC_API_KEY",),
        "Used by Studio chat when OPENTRYON_AGENT_LLM_PROVIDER=anthropic.",
    ),
    (
        "gemini",
        "Google Gemini",
        "https://aistudio.google.com/app/apikey",
        ("GEMINI_API_KEY",),
        "Also used by Studio chat when OPENTRYON_AGENT_LLM_PROVIDER=google. "
        "Does not unlock Vertex Virtual Try-On (google-vton).",
    ),
    (
        "photoroom",
        "Photoroom",
        "https://app.photoroom.com/api",
        ("PHOTOROOM_API_KEY",),
        "Image Editing API Plus. Unlocks photoroom-vton (shopper try-on) and "
        "photoroom-virtual-model (flat-lay → on-model). Prefix the key with "
        "sandbox_ for watermarked tests.",
    ),
    (
        "vertex",
        "Google Vertex Virtual Try-On",
        "https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/imagen/virtual-try-on-001",
        ("GOOGLE_CLOUD_PROJECT",),
        "GCP project id, not GEMINI_API_KEY. Also run "
        "`gcloud auth application-default login` (or set "
        "GOOGLE_APPLICATION_CREDENTIALS). Optional GOOGLE_CLOUD_LOCATION "
        "(default global).",
    ),
    (
        "meta",
        "Muse Image (Meta)",
        "https://dev.meta.ai/docs/authentication",
        ("MODEL_API_KEY",),
        "Official env name for Muse Image (generate, edit, composition VTON). "
        "META_MODEL_API_KEY / MUSE_API_KEY also work. Muse Video has no API yet.",
    ),
    (
        "minimax",
        "MiniMax (Hailuo 2.3 / H3)",
        "https://platform.minimax.io/user-center/basic-information/interface-key",
        ("MINIMAX_API_KEY",),
        "One key for Hailuo 2.3 and MiniMax H3 video. Local H3 needs no key.",
    ),
    (
        "moonshot",
        "Moonshot (Kimi)",
        "https://platform.kimi.ai/console/api-keys",
        ("MOONSHOT_API_KEY",),
        "",
    ),
    (
        "nvidia",
        "NVIDIA NIM (Nemotron / Cosmos)",
        "https://build.nvidia.com",
        ("NVIDIA_API_KEY",),
        "One key for Nemotron Omni understand, Cosmos 3 Reasoner understand, "
        "and Cosmos 3 Generator video. Optional COSMOS3_INFER_URL for a self-hosted Generator NIM.",
    ),
    (
        "bfl",
        "Black Forest Labs",
        "https://docs.bfl.ai/",
        ("BFL_API_KEY",),
        "",
    ),
    (
        "kling",
        "Kling AI",
        "https://kling.ai/document-api/guides/get-started/overview",
        ("KLING_AI_API_KEY", "KLING_AI_SECRET_KEY"),
        "Both values are required.",
    ),
    (
        "dashscope",
        "Alibaba DashScope",
        "https://www.alibabacloud.com/help/en/model-studio/get-api-key",
        ("DASHSCOPE_API_KEY",),
        "Same key for Qwen3.8-Max, Qwen-Image, and Wan. OutfitAnyone-Plus "
        "(outfitanyone-plus / aitryon-plus) needs a China Beijing-region key.",
    ),
    (
        "aws",
        "Amazon Bedrock",
        "https://console.aws.amazon.com/bedrock/",
        ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"),
        "Both values are required.",
    ),
    (
        "fashn",
        "FASHN AI",
        "https://app.fashn.ai/api",
        ("FASHN_API_KEY",),
        "",
    ),
    (
        "pruna",
        "Pruna AI",
        "https://dashboard.pruna.ai/login",
        ("PRUNA_API_KEY",),
        "P-Image, P-Image-Ideogram, P-Image-Edit, try-on, and P-Video family.",
    ),
    (
        "segmind",
        "Segmind",
        "https://www.segmind.com/",
        ("SEGMIND_API_KEY",),
        "",
    ),
    (
        "luma",
        "Luma AI",
        "https://lumalabs.ai/dream-machine/api",
        ("LUMA_AI_API_KEY",),
        "",
    ),
    (
        "luma-agents",
        "Luma Agents",
        "https://platform.lumalabs.ai/",
        ("LUMA_AGENTS_API_KEY",),
        "Preferred for Ray 3.2.",
    ),
    (
        "ark",
        "BytePlus ModelArk",
        "https://console.byteplus.com/",
        ("ARK_API_KEY",),
        "",
    ),
    (
        "xai",
        "xAI",
        "https://console.x.ai/",
        ("XAI_API_KEY",),
        "",
    ),
    (
        "ideogram",
        "Ideogram",
        "https://developer.ideogram.ai/",
        ("IDEOGRAM_API_KEY",),
        "",
    ),
    (
        "ltx",
        "LTX (Lightricks)",
        "https://console.ltx.io",
        ("LTX_API_KEY",),
        "",
    ),
    (
        "runway",
        "Runway",
        "https://dev.runwayml.com/",
        ("RUNWAYML_API_SECRET",),
        "",
    ),
)

if _DEFAULT_ENV_PATH.exists():
    load_dotenv(_DEFAULT_ENV_PATH)


def env_file_path() -> Path:
    """``.env`` written by ``set_api_keys``. Override with ``OPENTRYON_ENV_PATH``."""
    override = (os.getenv("OPENTRYON_ENV_PATH") or "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return _DEFAULT_ENV_PATH


def env_names_from_hint(env_hint: Optional[str]) -> List[str]:
    if not env_hint:
        return []
    return [part.strip() for part in env_hint.split("/") if part.strip()]


def is_configured(env_hint: Optional[str]) -> Optional[bool]:
    """Return True/False for whether the env var(s) in ``env_hint`` (e.g.
    ``"AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY"``) are all set, or None if
    the model needs no API key at all (local/open-weight models)."""
    names = env_names_from_hint(env_hint)
    if not names:
        return None
    return all(_is_var_configured(name) for name in names)


def _is_var_configured(name: str) -> bool:
    aliases = _VAR_ALIASES.get(name, (name,))
    return any(bool(os.getenv(alias)) for alias in aliases)


def allowed_env_names() -> frozenset[str]:
    """Env vars ``set_api_keys`` may write. Registry hints plus documented aliases."""
    names = set(_EXTRA_ENV_NAMES)
    from tryon.cli.registry import SERVICES

    for models in SERVICES.values():
        for spec in models.values():
            names.update(env_names_from_hint(spec.env_hint))
    return frozenset(names)


def _unlocks_by_var() -> Dict[str, List[Dict[str, str]]]:
    from tryon.cli.registry import SERVICES

    unlocks: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for service, models in SERVICES.items():
        for model_id, spec in models.items():
            for name in env_names_from_hint(spec.env_hint):
                unlocks[name].append({"service": service, "model": model_id})
    unlocks["OPENAI_API_KEY"].append({"service": "agent", "model": "planner_agent"})
    unlocks["ANTHROPIC_API_KEY"].append({"service": "agent", "model": "planner_agent"})
    unlocks["GEMINI_API_KEY"].append({"service": "agent", "model": "planner_agent"})
    unlocks["OPENTRYON_AGENT_LLM_API_KEY"].append({"service": "agent", "model": "planner_agent"})
    return unlocks


def _dedupe_unlocks(items: Sequence[Mapping[str, str]]) -> List[Dict[str, str]]:
    seen = set()
    out: List[Dict[str, str]] = []
    for item in items:
        key = (item.get("service", ""), item.get("model", ""))
        if key in seen:
            continue
        seen.add(key)
        out.append({"service": key[0], "model": key[1]})
    return out


def _provider_payload(
    provider_id: str,
    label: str,
    docs: str,
    var_names: Sequence[str],
    notes: str,
    unlocks_by_var: Mapping[str, Sequence[Mapping[str, str]]],
) -> Dict[str, Any]:
    vars_payload = [
        {"name": name, "configured": _is_var_configured(name)} for name in var_names
    ]
    unlocks: List[Mapping[str, str]] = []
    for name in var_names:
        unlocks.extend(unlocks_by_var.get(name, ()))
    return {
        "id": provider_id,
        "label": label,
        "docs": docs,
        "notes": notes or None,
        "configured": all(item["configured"] for item in vars_payload) if vars_payload else False,
        "vars": vars_payload,
        "unlocks": _dedupe_unlocks(unlocks),
    }


def list_api_keys() -> Dict[str, Any]:
    """Provider-grouped key status. Never includes secret values."""
    unlocks_by_var = _unlocks_by_var()
    catalog_vars = {name for row in _PROVIDER_CATALOG for name in row[3]}
    providers = [
        _provider_payload(pid, label, docs, names, notes, unlocks_by_var)
        for pid, label, docs, names, notes in _PROVIDER_CATALOG
    ]

    leftovers: List[str] = []
    for name in sorted(allowed_env_names()):
        if name in catalog_vars:
            continue
        if name not in unlocks_by_var:
            continue
        leftovers.append(name)
    for name in leftovers:
        providers.append(
            _provider_payload(
                name.lower().replace("_", "-"),
                name,
                "",
                (name,),
                "",
                unlocks_by_var,
            )
        )

    return {
        "success": True,
        "env_path": str(env_file_path()),
        "providers": providers,
    }


def _env_escape(value: str) -> str:
    if any(ch in value for ch in ' \t#\'"\\') or value != value.strip():
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return value


def _parse_env_assignment(line: str) -> Optional[Tuple[str, bool]]:
    """Return ``(key, used_export)`` if this line is a KEY=value assignment."""
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or "=" not in stripped:
        return None
    used_export = stripped.startswith("export ")
    body = stripped[7:] if used_export else stripped
    key = body.split("=", 1)[0].strip()
    if not _ENV_NAME_RE.match(key):
        return None
    return key, used_export


def upsert_env_file(path: Path, updates: Mapping[str, str]) -> None:
    """Replace or append ``KEY=value`` lines. File mode is ``0600``."""
    remaining = dict(updates)
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    lines = existing.splitlines()
    out: List[str] = []
    for line in lines:
        parsed = _parse_env_assignment(line)
        if parsed is None or parsed[0] not in remaining:
            out.append(line)
            continue
        key, used_export = parsed
        prefix = "export " if used_export else ""
        out.append(f"{prefix}{key}={_env_escape(remaining.pop(key))}")
    if remaining:
        if out and out[-1].strip():
            out.append("")
        out.append("# Set from TryOn Studio Connect")
        for key, value in remaining.items():
            out.append(f"{key}={_env_escape(value)}")
    text = "\n".join(out)
    if text and not text.endswith("\n"):
        text += "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)


def _normalize_keys(keys: Any) -> Dict[str, str]:
    if keys is None:
        raise ValueError("keys is required")
    if isinstance(keys, str):
        import json

        keys = json.loads(keys)
    pairs: List[Tuple[Any, Any]] = []
    if isinstance(keys, Mapping):
        pairs = list(keys.items())
    elif isinstance(keys, list):
        for entry in keys:
            if not isinstance(entry, Mapping):
                raise ValueError("each key entry must be an object with name and value")
            pairs.append((entry.get("name"), entry.get("value")))
    else:
        raise ValueError("keys must be an object mapping env names to values")

    normalized: Dict[str, str] = {}
    for name, value in pairs:
        if not isinstance(name, str) or not _ENV_NAME_RE.match(name):
            raise ValueError(f"Invalid env var name: {name!r}")
        if value is None:
            raise ValueError(f"{name} is empty")
        if not isinstance(value, str):
            value = str(value)
        if "\n" in value or "\r" in value:
            raise ValueError(f"{name} must not contain newlines")
        stripped = value.strip()
        if not stripped:
            raise ValueError(f"{name} is empty")
        normalized[name] = stripped
    if not normalized:
        raise ValueError("No keys provided")
    return normalized


def set_api_keys(keys: Any) -> Dict[str, Any]:
    """Upsert allowed env vars into ``.env`` and ``os.environ``. Never echoes values."""
    try:
        updates = _normalize_keys(keys)
    except (ValueError, TypeError) as err:
        return {"success": False, "error": str(err)}

    allowed = allowed_env_names()
    unknown = sorted(name for name in updates if name not in allowed)
    if unknown:
        return {
            "success": False,
            "error": f"Unknown env var(s): {', '.join(unknown)}. Only registry and planner keys can be set.",
        }

    path = env_file_path()
    try:
        upsert_env_file(path, updates)
    except OSError as err:
        return {"success": False, "error": f"Could not write {path}: {err}"}

    for name, value in updates.items():
        os.environ[name] = value

    listed = list_api_keys()
    return {
        "success": True,
        "updated": sorted(updates),
        "env_path": listed["env_path"],
        "providers": listed["providers"],
    }


def status_report() -> Dict[str, Any]:
    """Build a ``{service: {model: {...}}}`` readiness map straight from the
    registry."""
    from tryon.cli.registry import SERVICES

    report: Dict[str, Any] = {}
    for service, models in SERVICES.items():
        report[service] = {}
        for model_id, spec in models.items():
            report[service][model_id] = {
                "label": spec.label,
                "requires_env": spec.env_hint,
                "configured": is_configured(spec.env_hint),
                "runs_locally": spec.extra == "local",
            }
    return report


def status_message() -> str:
    """Human-readable configuration summary, printed to stderr on server
    startup and returned by the ``opentryon_status`` MCP tool."""
    report = status_report()

    lines = ["OpenTryOn MCP Server Configuration Status:", ""]
    ready = 0
    total_api = 0
    local_count = 0

    for service, models in report.items():
        lines.append(f"[{service}]")
        for model_id, info in models.items():
            if info["runs_locally"]:
                local_count += 1
                lines.append(f"  {model_id:<20} local (no API key needed)")
                continue
            total_api += 1
            if info["configured"]:
                ready += 1
                mark = "\u2713 configured"
            else:
                mark = f"\u2717 missing {info['requires_env']}"
            lines.append(f"  {model_id:<20} {mark}")
        lines.append("")

    lines.append(f"API-backed models ready: {ready}/{total_api}")
    lines.append(f"Local models available (need `pip install opentryon[local]` + GPU): {local_count}")
    if ready == 0:
        lines.append("")
        lines.append("\u26a0\ufe0f  No API keys configured yet.")
        lines.append("   Copy env.template to .env in the repo root and add your API keys.")
    return "\n".join(lines)
