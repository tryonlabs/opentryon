"""
DEPRECATED legacy entrypoint.

Moved to `examples/agents/fashion_agent.py`.

This is an LLM orchestration demo (not the registry-driven `opentryon` CLI).
"""

from __future__ import annotations

import pathlib
import runpy
import sys

_ROOT = pathlib.Path(__file__).resolve().parent
_TARGET = _ROOT / "examples" / "agents" / "fashion_agent.py"

print("[opentryon] WARNING: `fashion_agent.py` is legacy; moved to examples/agents.", file=sys.stderr)

runpy.run_path(str(_TARGET), run_name="__main__")

