"""
DEPRECATED legacy entrypoint.

Moved to `examples/legacy/gpt_image.py`. Prefer:
  - `opentryon generate --model gpt-image ...`
  - `opentryon edit --model gpt-image ...`
"""

from __future__ import annotations

import pathlib
import runpy
import sys

_ROOT = pathlib.Path(__file__).resolve().parent
_TARGET = _ROOT / "examples" / "legacy" / "gpt_image.py"

print(
    "[opentryon] WARNING: `gpt_image.py` is legacy; use `opentryon generate|edit --model gpt-image` instead.",
    file=sys.stderr,
)

runpy.run_path(str(_TARGET), run_name="__main__")

