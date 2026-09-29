"""
Limite 1B - Violetto (Paradigma Inc, open-weight) local model package.

Local Hugging Face Transformers adapter for a math-reasoning-specialized
1B LLM -- no first-party hosted API exists. See
:mod:`tryon.models.limite.adapter` for details.
"""

from .adapter import LimiteAdapter

__all__ = [
    "LimiteAdapter",
]
