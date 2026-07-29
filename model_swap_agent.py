"""
DEPRECATED legacy entrypoint.

Moved to `examples/agents/model_swap_agent.py`.
"""

from __future__ import annotations

import pathlib
import runpy
import sys

_ROOT = pathlib.Path(__file__).resolve().parent
_TARGET = _ROOT / "examples" / "agents" / "model_swap_agent.py"

print(
    "[opentryon] WARNING: `model_swap_agent.py` is legacy; moved to examples/agents.",
    file=sys.stderr,
)

runpy.run_path(str(_TARGET), run_name="__main__")

