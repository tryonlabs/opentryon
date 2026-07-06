#!/usr/bin/env python3
"""OpenTryOn MCP Server.

Exposes every ``opentryon <service> --model <model>`` combination as an MCP
tool, built on `FastMCP <https://gofastmcp.com>`_ (>= 3.4).

Tools are generated **dynamically** from :data:`tryon.cli.registry.SERVICES`
-- the same data-driven registry that powers the ``opentryon`` CLI -- rather
than hand-written one at a time. That means every model reachable via
``opentryon <service> --model <model> ...`` (virtual try-on, image
generation/editing, image & video understanding, video generation,
background removal -- including Kimi, FLUX VTO/2, GPT Image, Sora, Veo,
Nano Banana, BEN2, etc.) is automatically exposed here too, and any new
model added to the registry shows up as an MCP tool with zero changes to
this file. See ``docs/docs/advanced/new-model-checklist.md`` in the parent
repo for how to add a new model.

Usage
-----
    # stdio transport (default -- what Claude Desktop / Cursor expect)
    python server.py

    # streamable-http transport, for remote clients
    python server.py --transport http --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import argparse
import inspect
import sys
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

# Allow running this file directly (``python mcp-server/server.py``) without
# having run ``pip install -e ..`` first.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastmcp import FastMCP

import config
from tryon.cli.registry import Arg, ModelSpec, SERVICE_HELP, SERVICES
from tryon.cli.runner import invoke_model

__version__ = "0.1.0"


mcp = FastMCP(
    name="opentryon",
    version=__version__,
    instructions=(
        "OpenTryOn is an open-source AI toolkit for fashion tech, virtual "
        "try-on, and general multimodal understanding. Every tool here maps "
        "1:1 to `opentryon <service> --model <model>` from the opentryon "
        "CLI and is named '<service>_<model>' (dashes/dots become "
        "underscores), e.g. 'vton_flux_vto', 'understand_kimi_k2_6', "
        "'generate_nano_banana_pro', 'video_generate_veo'. "
        "Call `list_opentryon_tools` first to discover every available "
        "service/model combination, which environment variable(s) each one "
        "needs, and whether it is already configured in this environment. "
        "Every generated tool accepts a `dry_run` boolean to preview the "
        "resolved adapter call without spending API credits or GPU time, "
        "and an `output_dir` string (default 'outputs') for where to save "
        "any resulting images/video/JSON."
    ),
)


# --------------------------------------------------------------------------
# Registry Arg -> dynamic Python function signature
# --------------------------------------------------------------------------

def _annotation_for(arg: Arg) -> Any:
    """Map a registry ``Arg`` to a Python type annotation suitable for
    building an MCP JSON schema (enums via ``Literal``, lists via
    ``nargs``, optionality via ``required``)."""
    if arg.action in ("store_true", "store_false"):
        return bool

    base: Any = {int: int, float: float}.get(arg.type, str)

    if arg.nargs in ("+", "*"):
        base = List[base]

    if arg.choices:
        try:
            base = Literal[tuple(arg.choices)]  # type: ignore[valid-type]
        except TypeError:
            pass  # non-hashable choices -- fall back to the plain base type

    if not arg.required:
        base = Optional[base]

    return base


def _default_for(arg: Arg) -> Any:
    if arg.action == "store_true":
        return arg.default if arg.default is not None else False
    if arg.action == "store_false":
        return arg.default if arg.default is not None else True
    return arg.default


def _tool_name(service: str, model_id: str) -> str:
    return f"{service}_{model_id}".replace("-", "_").replace(".", "_")


def _build_docstring(spec: ModelSpec) -> str:
    lines = [f"{spec.label}."]
    if spec.notes:
        lines.append(spec.notes)
    if spec.env_hint:
        lines.append(f"Requires environment variable(s): {spec.env_hint}.")
    if spec.extra == "local":
        lines.append(
            "Runs locally on this machine's GPU/CPU; requires "
            "`pip install opentryon[local]`."
        )
    lines.append("")
    for arg in spec.args:
        if arg.help:
            lines.append(f":param {arg.dest}: {arg.help}")
    lines.append(
        ":param output_dir: Directory to save output artifacts "
        "(images/video/json) to. Default: 'outputs'."
    )
    lines.append(
        ":param dry_run: If true, return the resolved adapter call without "
        "invoking the API/GPU/network. Default: false."
    )
    return "\n".join(lines)


def _build_tool_fn(service: str, model_id: str, spec: ModelSpec):
    """Build a function whose *real* ``inspect.signature()`` has one
    keyword-only parameter per registry ``Arg`` (plus ``output_dir`` /
    ``dry_run``), so FastMCP generates an accurate, flat JSON schema
    straight from introspection -- no per-model wrapper needed.
    """
    params: List[inspect.Parameter] = []
    for arg in spec.args:
        annotation = _annotation_for(arg)
        if arg.required:
            params.append(
                inspect.Parameter(arg.dest, inspect.Parameter.KEYWORD_ONLY, annotation=annotation)
            )
        else:
            params.append(
                inspect.Parameter(
                    arg.dest,
                    inspect.Parameter.KEYWORD_ONLY,
                    annotation=annotation,
                    default=_default_for(arg),
                )
            )

    params.append(
        inspect.Parameter("output_dir", inspect.Parameter.KEYWORD_ONLY, annotation=str, default="outputs")
    )
    params.append(
        inspect.Parameter("dry_run", inspect.Parameter.KEYWORD_ONLY, annotation=bool, default=False)
    )

    signature = inspect.Signature(params, return_annotation=Dict[str, Any])

    async def _tool(**kwargs: Any) -> Dict[str, Any]:
        return invoke_model(service, model_id, **kwargs)

    _tool.__signature__ = signature  # type: ignore[attr-defined]
    _tool.__name__ = _tool_name(service, model_id)
    _tool.__annotations__ = {p.name: p.annotation for p in params}
    _tool.__annotations__["return"] = Dict[str, Any]
    _tool.__doc__ = _build_docstring(spec)
    return _tool


def register_model_tools(app: FastMCP) -> int:
    """Register one MCP tool per (service, model) in the registry. Returns
    the number of tools registered."""
    count = 0
    for service, models in SERVICES.items():
        for model_id, spec in models.items():
            fn = _build_tool_fn(service, model_id, spec)
            app.tool(name=_tool_name(service, model_id))(fn)
            count += 1
    return count


# --------------------------------------------------------------------------
# Discovery / meta tools
# --------------------------------------------------------------------------

@mcp.tool
def list_opentryon_tools(service: Optional[str] = None) -> Dict[str, Any]:
    """List every OpenTryOn service/model combination available as an MCP
    tool, along with which environment variable(s) each one needs and
    whether it is currently configured in this server's environment.

    Call this first to decide which tool to use for a task, and to check
    readiness before attempting a real (non dry-run) call.

    :param service: Optional filter, one of: vton, generate, edit,
        understand, video-generate, bg-remove. Omit to list all services.
    """
    if service and service not in SERVICES:
        return {
            "success": False,
            "error": f"Unknown service '{service}'. Available: {', '.join(SERVICES)}",
        }
    services = {service: SERVICES[service]} if service else SERVICES

    result: Dict[str, Any] = {"services": {}}
    for svc, models in services.items():
        result["services"][svc] = {
            "description": SERVICE_HELP.get(svc, ""),
            "models": {
                model_id: {
                    "tool_name": _tool_name(svc, model_id),
                    "label": spec.label,
                    "notes": spec.notes,
                    "requires_env": spec.env_hint,
                    "configured": config.is_configured(spec.env_hint),
                    "runs_locally": spec.extra == "local",
                }
                for model_id, spec in models.items()
            },
        }
    return result


@mcp.tool
def opentryon_status() -> str:
    """Human-readable configuration status: which API keys are set, which
    services/models are ready to use, and setup hints for anything missing.
    """
    return config.status_message()


TOOL_COUNT = register_model_tools(mcp)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="OpenTryOn MCP server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http", "sse"],
        default="stdio",
        help="MCP transport to serve on. Default: stdio (for Claude Desktop / Cursor).",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to (http/sse transports only)")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to (http/sse transports only)")
    return parser


def main() -> None:
    args = _build_arg_parser().parse_args()

    print(config.status_message(), file=sys.stderr)
    print(f"\nStarting OpenTryOn MCP Server ({TOOL_COUNT} model tools + 2 discovery tools)...", file=sys.stderr)

    if args.transport == "stdio":
        mcp.run()
    else:
        mcp.run(transport=args.transport, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
