"""
DEPRECATED legacy test entrypoint.

Moved to `tests/legacy/luma_video_test.py`.
Use `opentryon video-generate ... --dry-run` for registry-driven testing.
"""

from __future__ import annotations

import pathlib
import runpy
import sys

_ROOT = pathlib.Path(__file__).resolve().parent
_TARGET = _ROOT / "tests" / "legacy" / "luma_video_test.py"

print("[opentryon] WARNING: `luma_video_test.py` moved to tests/legacy.", file=sys.stderr)

runpy.run_path(str(_TARGET), run_name="__main__")

