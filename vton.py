"""
DEPRECATED legacy entrypoint.

This script was moved to `examples/legacy/vton.py` as OpenTryOn adopted the
registry-driven `opentryon` CLI and MCP server.

Preferred:
  opentryon vton --model <model> --person-image ... --garment-image ...
"""

from __future__ import annotations

import pathlib
import runpy
import sys

_ROOT = pathlib.Path(__file__).resolve().parent
_TARGET = _ROOT / "examples" / "legacy" / "vton.py"

print(
    "[opentryon] WARNING: `vton.py` is a legacy wrapper; use `opentryon vton --model ...` instead.",
    file=sys.stderr,
)

runpy.run_path(str(_TARGET), run_name="__main__")

