"""
Generic execution engine shared by every ``opentryon <service>`` subcommand.

Argument parsing happens in two stages so that ``--model`` determines which
further flags are valid (mirrors how e.g. ``git <subcommand>`` or
``docker <object> <verb>`` work):

    1. A first, permissive pass extracts just ``--model`` (and ``-h``).
    2. A second pass builds the full parser for that model's args (from the
       registry) and parses the remaining argv against it.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import io
import json
import os
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

from tryon.cli.registry import Arg, ModelSpec, SERVICE_HELP, get_model, get_service


def add_model_selector(parser: argparse.ArgumentParser, service: str) -> None:
    """Add the level-2 ``--model`` flag (with choices) plus a couple of
    service-wide flags that apply regardless of which model is chosen."""
    models = get_service(service)
    parser.description = SERVICE_HELP.get(service, "")
    parser.add_argument(
        "--model",
        required=True,
        choices=sorted(models),
        help="Model/provider to use for this service. Run with just --model "
        "NAME --help to see that model's parameters.",
    )
    parser.add_argument("-o", "--output-dir", default="outputs", help="Directory to write results to. Default: outputs")
    parser.add_argument("--dry-run", action="store_true", help="Print the resolved call without invoking the API/model")


def _add_arg(parser: argparse.ArgumentParser, arg: Arg) -> None:
    kwargs = {"dest": arg.dest, "help": arg.help}
    if arg.action:
        kwargs["action"] = arg.action
        if arg.default is not None:
            kwargs["default"] = arg.default
    else:
        kwargs["type"] = arg.type
        if arg.default is not None:
            kwargs["default"] = arg.default
        if arg.choices:
            kwargs["choices"] = arg.choices
        if arg.nargs:
            kwargs["nargs"] = arg.nargs
        if arg.required:
            kwargs["required"] = True
    parser.add_argument(*arg.flags, **kwargs)


def build_model_parser(service: str, model: str, spec: ModelSpec) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=f"opentryon {service} --model {model}",
        description=f"{spec.label}" + (f"  [{spec.notes}]" if spec.notes else ""),
    )
    add_model_selector(parser, service)
    for arg in spec.args:
        _add_arg(parser, arg)
    return parser


def parse_service_args(service: str, argv: List[str]) -> argparse.Namespace:
    """Two-stage parse: first find --model, then parse fully against that
    model's spec."""
    probe = argparse.ArgumentParser(add_help=False)
    probe.add_argument("--model", choices=sorted(get_service(service)))
    probe_ns, _ = probe.parse_known_args(argv)

    if probe_ns.model is None:
        # No --model yet (or user asked for bare --help): show the
        # service-level help listing available models.
        top = argparse.ArgumentParser(prog=f"opentryon {service}")
        add_model_selector(top, service)
        return top.parse_args(argv)  # will error/help out appropriately

    spec = get_service(service)[probe_ns.model]
    parser = build_model_parser(service, probe_ns.model, spec)
    return parser.parse_args(argv)


def _split_kwargs(spec: ModelSpec, values: Mapping[str, Any], using_alt: bool):
    """Split a flat mapping of ``dest -> value`` (an argparse ``Namespace``
    via ``vars()``, or a plain kwargs dict from a non-CLI caller like the MCP
    server) into constructor kwargs and method-call kwargs."""
    init_kwargs, call_kwargs = {}, {}
    for arg in spec.args:
        if arg.alt_only and not using_alt:
            continue
        value = values.get(arg.dest)
        if value is None:
            continue
        name = arg.call_name or arg.dest
        if arg.target == "init":
            init_kwargs[name] = value
        else:
            call_kwargs[name] = value
    return init_kwargs, call_kwargs


def _load_class(spec: ModelSpec):
    module = importlib.import_module(spec.import_path)
    return getattr(module, spec.class_name)


def _extra_missing(spec: ModelSpec) -> Optional[str]:
    """Return a human-readable error message if ``spec`` needs the `local`
    extra and it isn't installed, else ``None``."""
    if spec.extra != "local":
        return None
    if importlib.util.find_spec("torch") is None:
        return (
            f"'{spec.label}' requires local ML dependencies that aren't installed. "
            "Install them with: pip install opentryon[local]"
        )
    return None


def _check_extra(spec: ModelSpec) -> None:
    msg = _extra_missing(spec)
    if msg:
        print(f"\n\u2717 {msg}\n", file=sys.stderr)
        raise SystemExit(1)


def _package_result(spec: ModelSpec, result: Any, output_dir: Path, prefix: str) -> Dict[str, Any]:
    """Turn a raw adapter return value into a structured, JSON-serializable
    dict, saving any images/video/text artifacts to ``output_dir`` along the
    way. Shared by the CLI (`run_service`) and the MCP server
    (`invoke_model`) so both surfaces produce identical output shapes."""
    if spec.output_kind in ("images", "image_bytes"):
        images = result if isinstance(result, (list, tuple)) else [result]
        saved = _save_images(images, output_dir, prefix)
        return {
            "output_kind": spec.output_kind,
            "output_paths": [str(p) for p in saved],
            "count": len(saved),
        }

    if spec.output_kind == "video_bytes":
        if isinstance(result, str):
            return {"output_kind": "video_bytes", "video_id": result, "downloaded": False}
        path = _save_video(result, output_dir, prefix)
        return {"output_kind": "video_bytes", "output_path": str(path), "downloaded": True}

    if spec.output_kind == "text":
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"{prefix}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, default=str)
        return {"output_kind": "text", "result": result, "output_path": str(path)}

    return {"output_kind": "raw", "result": repr(result)}


def _save_images(images, output_dir: Path, prefix: str) -> List[Path]:
    from PIL import Image

    output_dir.mkdir(parents=True, exist_ok=True)
    saved = []
    for idx, img in enumerate(images):
        if isinstance(img, (bytes, bytearray)):
            img = Image.open(io.BytesIO(img))
        path = output_dir / f"{prefix}_{idx}.png"
        img.save(path)
        saved.append(path)
    return saved


def _save_video(video_bytes: bytes, output_dir: Path, prefix: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{prefix}.mp4"
    with open(path, "wb") as f:
        f.write(video_bytes)
    return path


def run_service(service: str, argv: List[str]) -> int:
    args = parse_service_args(service, argv)
    spec = get_service(service)[args.model]
    _check_extra(spec)

    values = vars(args)
    using_alt = bool(spec.alt_method_on_image and values.get(spec.alt_image_dest))
    method = spec.alt_method_on_image if using_alt else spec.method
    init_kwargs, call_kwargs = _split_kwargs(spec, values, using_alt)

    if args.dry_run:
        print(f"[dry-run] {spec.class_name}(**{init_kwargs}).{method}(**{call_kwargs})")
        return 0

    if spec.env_hint:
        print(f"Using {spec.label} (env: {spec.env_hint})")
    else:
        print(f"Using {spec.label}")

    cls = _load_class(spec)
    adapter = cls(**init_kwargs)
    result = getattr(adapter, method)(**call_kwargs)

    output_dir = Path(args.output_dir)
    prefix = f"{service}_{args.model}"
    packaged = _package_result(spec, result, output_dir, prefix)

    if packaged["output_kind"] in ("images", "image_bytes"):
        for path in packaged["output_paths"]:
            print(f"\u2713 Saved: {path}")
        print(f"\n\u2713 Done: {packaged['count']} image(s)")
        return 0

    if packaged["output_kind"] == "video_bytes":
        if not packaged["downloaded"]:
            print(f"\u2713 Video generation ID (not yet downloaded): {packaged['video_id']}")
        else:
            print(f"\u2713 Saved: {packaged['output_path']}")
        return 0

    if packaged["output_kind"] == "text":
        print(json.dumps(packaged["result"], indent=2, default=str))
        print(f"\n\u2713 Saved: {packaged['output_path']}")
        return 0

    print(f"Result: {packaged['result']}")
    return 0


def invoke_model(
    service: str,
    model: str,
    output_dir: str = "outputs",
    dry_run: bool = False,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Programmatic (non-argv) equivalent of ``run_service``, used by
    non-CLI callers -- currently the MCP server (``mcp-server/server.py``),
    which builds one FastMCP tool per (service, model) directly from this
    same registry and calls straight into this function.

    Unlike ``run_service`` this never raises for expected failure modes
    (missing extra, unknown model, adapter errors): it always returns a
    dict with a ``success`` key so callers (in particular LLM tool-calling
    clients) get a structured result instead of a stack trace.
    """
    try:
        spec = get_model(service, model)
    except KeyError as e:
        return {"success": False, "error": e.args[0] if e.args else str(e)}

    extra_error = _extra_missing(spec)
    if extra_error:
        return {"success": False, "error": extra_error}

    using_alt = bool(spec.alt_method_on_image and kwargs.get(spec.alt_image_dest))
    method = spec.alt_method_on_image if using_alt else spec.method
    init_kwargs, call_kwargs = _split_kwargs(spec, kwargs, using_alt)

    if dry_run:
        return {
            "success": True,
            "dry_run": True,
            "call": f"{spec.class_name}(**{init_kwargs}).{method}(**{call_kwargs})",
        }

    try:
        cls = _load_class(spec)
        adapter = cls(**init_kwargs)
        result = getattr(adapter, method)(**call_kwargs)
        packaged = _package_result(spec, result, Path(output_dir), f"{service}_{model}")
        return {"success": True, **packaged}
    except Exception as e:  # noqa: BLE001 - surfaced to the caller, not raised
        return {
            "success": False,
            "error": f"{type(e).__name__}: {e}",
            "traceback": traceback.format_exc(),
        }
