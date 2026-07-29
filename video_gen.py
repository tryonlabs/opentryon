"""
DEPRECATED legacy entrypoint.

Moved to `examples/legacy/video_gen.py`. Prefer:
  - `opentryon video-generate --model veo|sora|luma-video ...`
  - For Gemini Omni Flash: `opentryon video-generate --model gemini-omni ...`
"""

from __future__ import annotations

import pathlib
import runpy
import sys

_ROOT = pathlib.Path(__file__).resolve().parent
_TARGET = _ROOT / "examples" / "legacy" / "video_gen.py"

print(
    "[opentryon] WARNING: `video_gen.py` is legacy; use `opentryon video-generate --model ...` instead.",
    file=sys.stderr,
)

runpy.run_path(str(_TARGET), run_name="__main__")

