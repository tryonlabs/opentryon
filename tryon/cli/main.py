"""
Unified OpenTryOn CLI.

Three levels of control:
    opentryon <service> --model <model> [params...]

Examples:
  opentryon vton --model flux-vto --model-image model.png --garment-image garment.png
  opentryon generate --model nano-banana --prompt "Fashion model in a studio"
  opentryon edit --model gpt-image --images photo.jpg --prompt "Add sunglasses"
  opentryon understand --model llava-next --image outfit.jpg
  opentryon video-generate --model veo --prompt "A model walking a runway"
  opentryon bg-remove --model ben2 --image product.jpg

Run `opentryon <service> --help` to list models for that service, or
`opentryon <service> --model <model> --help` to see that model's parameters.
"""

from __future__ import annotations

import argparse
import sys
import traceback

from tryon.cli.registry import SERVICE_HELP, SERVICES


def _build_top_level_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="opentryon",
        description="OpenTryOn: run image/video generation, editing, virtual try-on, "
        "understanding, and background removal models from the command line.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="service", required=True)
    for service, help_text in SERVICE_HELP.items():
        models = ", ".join(sorted(SERVICES[service]))
        sub.add_parser(service, help=f"{help_text} (models: {models})", add_help=False)
    return parser


def main(argv: list[str] | None = None) -> int:
    from dotenv import load_dotenv

    load_dotenv()

    argv = sys.argv[1:] if argv is None else argv
    parser = _build_top_level_parser()

    if not argv or argv[0] in ("-h", "--help"):
        parser.print_help()
        return 0 if argv else 2

    service, rest = argv[0], argv[1:]
    if service not in SERVICES:
        parser.error(
            f"argument service: invalid choice: {service!r} "
            f"(choose from {', '.join(sorted(SERVICES))})"
        )

    from tryon.cli.runner import run_service

    try:
        return run_service(service, rest)
    except SystemExit as e:
        code = e.code
        return 0 if code is None else (code if isinstance(code, int) else 1)
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"\n\u2717 Error: {e}", file=sys.stderr)
        traceback.print_exc()
        return 1


def cli_entry() -> None:
    """Setuptools console_scripts entrypoint."""
    raise SystemExit(main())


if __name__ == "__main__":
    raise SystemExit(main())
