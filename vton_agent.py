"""
DEPRECATED legacy entrypoint.

Moved to `examples/agents/vton_agent.py`.

Prefer: use the registry-driven `opentryon` CLI or MCP tools for
capability testing; keep this for the older LLM orchestration workflow.
"""

from __future__ import annotations

import pathlib
import runpy
import sys

_ROOT = pathlib.Path(__file__).resolve().parent
_TARGET = _ROOT / "examples" / "agents" / "vton_agent.py"

print("[opentryon] WARNING: `vton_agent.py` is legacy; moved to examples/agents.", file=sys.stderr)

runpy.run_path(str(_TARGET), run_name="__main__")

