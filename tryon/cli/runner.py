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
from pathlib import Path
from typing import Dict, List

from tryon.cli.registry import Arg, ModelSpec, SERVICE_HELP, get_service


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


def _split_kwargs(spec: ModelSpec, args: argparse.Namespace, using_alt: bool):
    init_kwargs, call_kwargs = {}, {}
    for arg in spec.args:
        if arg.alt_only and not using_alt:
            continue
        value = getattr(args, arg.dest, None)
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


def _check_extra(spec: ModelSpec) -> None:
    if spec.extra != "local":
        return
    if importlib.util.find_spec("torch") is None:
        print(
            f"\n✗ '{spec.label}' requires local ML dependencies that aren't installed.\n"
            f"  Install them with: pip install opentryon[local]\n",
            file=sys.stderr,
        )
        raise SystemExit(1)


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

    using_alt = bool(
        spec.alt_method_on_image and getattr(args, spec.alt_image_dest, None)
    )
    method = spec.alt_method_on_image if using_alt else spec.method
    init_kwargs, call_kwargs = _split_kwargs(spec, args, using_alt)

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

    if spec.output_kind in ("images", "image_bytes"):
        images = result if isinstance(result, (list, tuple)) else [result]
        saved = _save_images(images, output_dir, prefix)
        for path in saved:
            print(f"\u2713 Saved: {path}")
        print(f"\n\u2713 Done: {len(saved)} image(s)")
        return 0

    if spec.output_kind == "video_bytes":
        if isinstance(result, str):
            print(f"\u2713 Video generation ID (not yet downloaded): {result}")
            return 0
        path = _save_video(result, output_dir, prefix)
        print(f"\u2713 Saved: {path}")
        return 0

    if spec.output_kind == "text":
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"{prefix}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, default=str)
        print(json.dumps(result, indent=2, default=str))
        print(f"\n\u2713 Saved: {path}")
        return 0

    print(f"Result: {result!r}")
    return 0
