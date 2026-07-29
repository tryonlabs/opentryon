"""
DEPRECATED legacy entrypoint.

Moved to `examples/legacy/caption_images.py`.
Prefer using the registry-driven CLI/MCP tools where possible.
"""

from __future__ import annotations

import pathlib
import runpy
import sys

_ROOT = pathlib.Path(__file__).resolve().parent
_TARGET = _ROOT / "examples" / "legacy" / "caption_images.py"

print("[opentryon] WARNING: `caption_images.py` is legacy; moved to examples/legacy.", file=sys.stderr)

runpy.run_path(str(_TARGET), run_name="__main__")

