"""
DEPRECATED legacy entrypoint.

Moved to `examples/legacy/veo_video.py`. Prefer:
  opentryon video-generate --model veo ...
"""

from __future__ import annotations

import pathlib
import runpy
import sys

_ROOT = pathlib.Path(__file__).resolve().parent
_TARGET = _ROOT / "examples" / "legacy" / "veo_video.py"

print(
    "[opentryon] WARNING: `veo_video.py` is legacy; use `opentryon video-generate --model veo` instead.",
    file=sys.stderr,
)

runpy.run_path(str(_TARGET), run_name="__main__")

