"""
Local ISO 8559-1 measurements via ``clad-body`` on Anny/MHR parametric meshes.

Requires ``pip install 'clad-body[anny]'`` (or ``[mhr]``) plus PyTorch.
Does not reconstruct a body from a photo — use ``clad-body-photo`` (Clad API) for that.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class CladBodyLocalAdapter:
    """Measure an existing Anny or MHR body from params JSON (Path B)."""

    def __init__(self, body_backend: str = "anny"):
        backend = (body_backend or "anny").strip().lower()
        if backend not in {"anny", "mhr"}:
            raise ValueError("body_backend must be 'anny' or 'mhr'")
        self.body_backend = backend

    def _load_params(self, params: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        if isinstance(params, dict):
            return params
        text = str(params)
        path = Path(text)
        if path.is_file():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return json.loads(text)

    def measure(
        self,
        params: Union[str, Dict[str, Any]],
        preset: Optional[str] = None,
        only: Optional[List[str]] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        try:
            from clad_body.measure import measure as clad_measure
        except ImportError as exc:
            raise ImportError(
                "clad-body is required. Install with:\n"
                "  pip install opentryon[local]\n"
                "  pip install 'clad-body[anny]'   # or clad-body[mhr]\n"
                f"Original error: {exc}"
            ) from exc

        if self.body_backend == "anny":
            try:
                from clad_body.load import load_anny_from_params
            except ImportError as exc:
                raise ImportError(
                    "Anny loader needs pip install 'clad-body[anny]' (torch)."
                ) from exc
            body = load_anny_from_params(self._load_params(params))
        else:
            try:
                from clad_body.load import load_mhr_from_params
            except ImportError as exc:
                raise ImportError(
                    "MHR loader needs pip install 'clad-body[mhr]' (pymomentum)."
                ) from exc
            path = Path(str(params))
            if not path.is_file():
                raise ValueError(
                    "MHR backend expects --params to be a path to a SAM 3D Body params JSON file."
                )
            body = load_mhr_from_params(str(path))

        kwargs: Dict[str, Any] = {}
        if preset:
            kwargs["preset"] = preset
        if only:
            kwargs["only"] = only
        if tags:
            kwargs["tags"] = tags
        measurements = clad_measure(body, **kwargs)
        # clad_measure returns dict-like with float values
        return {
            "measurements": dict(measurements),
            "body_backend": self.body_backend,
            "preset": preset,
            "only": only,
            "tags": tags,
        }
