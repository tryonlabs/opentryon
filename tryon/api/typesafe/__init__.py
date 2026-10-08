"""
Typesafe AI Jev ("System One" decision model) API adapter.

Jev returns calibrated, schema-valid answers (choice / score / yes-no) to
developer-defined questions instead of generating text. Useful in OpenTryOn for
routing, moderation, attribute classification and QC gating of text/JSON state.
"""

from .adapter import JevAdapter

__all__ = ["JevAdapter"]
