"""
DEPRECATED research entrypoint.

This script is not part of the registry-driven `opentryon` CLI/MCP surface.
It was moved to `examples/legacy/run_ootd.py`.
"""

from __future__ import annotations

import pathlib
import runpy
import sys

_ROOT = pathlib.Path(__file__).resolve().parent
_TARGET = _ROOT / "examples" / "legacy" / "run_ootd.py"

print("[opentryon] WARNING: `run_ootd.py` is legacy; moved to examples/legacy.", file=sys.stderr)

runpy.run_path(str(_TARGET), run_name="__main__")

