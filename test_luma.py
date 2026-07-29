"""
DEPRECATED legacy test entrypoint.

Moved to `tests/legacy/test_luma.py`.
Use the registry-driven `opentryon` CLI and MCP tools for capability
testing instead.
"""

from __future__ import annotations

import pathlib
import runpy
import sys

_ROOT = pathlib.Path(__file__).resolve().parent
_TARGET = _ROOT / "tests" / "legacy" / "test_luma.py"

print("[opentryon] WARNING: `test_luma.py` moved to tests/legacy.", file=sys.stderr)

runpy.run_path(str(_TARGET), run_name="__main__")

