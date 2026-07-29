"""
DEPRECATED legacy test entrypoint.

Moved to `tests/legacy/test_gpt_image.py`.
Use `opentryon generate/edit --model gpt-image ...` or MCP tools instead.
"""

from __future__ import annotations

import pathlib
import runpy
import sys

_ROOT = pathlib.Path(__file__).resolve().parent
_TARGET = _ROOT / "tests" / "legacy" / "test_gpt_image.py"

print("[opentryon] WARNING: `test_gpt_image.py` moved to tests/legacy.", file=sys.stderr)

runpy.run_path(str(_TARGET), run_name="__main__")

