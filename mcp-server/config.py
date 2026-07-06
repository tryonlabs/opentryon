"""Environment configuration for the OpenTryOn MCP server.

Loads the parent repo's ``.env`` (same file the ``opentryon`` CLI and the
adapters themselves read via ``python-dotenv``/``os.getenv``) and derives a
readiness report straight from :data:`tryon.cli.registry.SERVICES`, so this
never drifts out of sync with which models actually need which keys.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv

_PARENT_DIR = Path(__file__).resolve().parent.parent
_ENV_PATH = _PARENT_DIR / ".env"
if _ENV_PATH.exists():
    load_dotenv(_ENV_PATH)


def is_configured(env_hint: Optional[str]) -> Optional[bool]:
    """Return True/False for whether the env var(s) in ``env_hint`` (e.g.
    ``"AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY"``) are all set, or None if
    the model needs no API key at all (local/open-weight models)."""
    if not env_hint:
        return None
    names = [v.strip() for v in env_hint.split("/")]
    return all(os.getenv(name) for name in names)


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
