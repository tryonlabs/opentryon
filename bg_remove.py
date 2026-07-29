"""
DEPRECATED legacy entrypoint.

Moved to `examples/legacy/bg_remove.py`. Prefer:
  opentryon bg-remove --model ben2 --image ... [--refine]
"""

from __future__ import annotations

import pathlib
import runpy
import sys

_ROOT = pathlib.Path(__file__).resolve().parent
_TARGET = _ROOT / "examples" / "legacy" / "bg_remove.py"

print(
    "[opentryon] WARNING: `bg_remove.py` is legacy; use `opentryon bg-remove --model ben2 ...` instead.",
    file=sys.stderr,
)

runpy.run_path(str(_TARGET), run_name="__main__")

