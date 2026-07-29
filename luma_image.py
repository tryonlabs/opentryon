"""
DEPRECATED legacy entrypoint.

Moved to `examples/legacy/luma_image.py`. Prefer:
  - `opentryon generate --model luma-image ...`
"""

from __future__ import annotations

import pathlib
import runpy
import sys

_ROOT = pathlib.Path(__file__).resolve().parent
_TARGET = _ROOT / "examples" / "legacy" / "luma_image.py"

print(
    "[opentryon] WARNING: `luma_image.py` is legacy; use `opentryon generate --model luma-image ...` instead.",
    file=sys.stderr,
)

runpy.run_path(str(_TARGET), run_name="__main__")

