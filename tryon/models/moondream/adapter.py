"""
Moondream 3.1 local (Path B) via the official Photon runtime.

``pip install moondream`` then ``md.photon("moondream3.1-9B-A2B")``.
Base weights do not need an API key. NVIDIA Ampere+ or Apple Silicon.

Docs: https://docs.moondream.ai/running-locally
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

from PIL import Image


class MoondreamLocalAdapter:
    """Same ``understand`` / ``detect`` methods as the cloud adapter, on Photon."""

    def __init__(self, model: str = "moondream3.1-9B-A2B"):
        self.model = model or os.getenv("MOONDREAM_LOCAL_MODEL") or "moondream3.1-9B-A2B"
        self._runtime = None

    def _model(self):
        if self._runtime is None:
            try:
                import moondream as md
            except ImportError as exc:
                raise ImportError(
                    "Moondream local inference needs the official client:\n"
                    "  pip install moondream\n"
                    f"Original error: {exc}"
                ) from exc
            self._runtime = md.photon(self.model)
        return self._runtime

    @staticmethod
    def _open(image) -> Image.Image:
        if isinstance(image, Image.Image):
            return image
        return Image.open(image)

    def understand(
        self,
        image,
        prompt: Optional[str] = None,
        skill: str = "query",
        length: str = "normal",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        skill = (skill or "query").strip().lower()
        if skill not in {"query", "caption"}:
            raise ValueError("understand --skill must be query or caption")
        if skill == "query" and not (prompt and prompt.strip()):
            raise ValueError("query requires --prompt")
        if image is None or image == "":
            raise ValueError("Moondream requires --image")
        runtime = self._model()
        picture = self._open(image)
        if skill == "query":
            kwargs: Dict[str, Any] = {}
            if temperature is not None:
                kwargs["temperature"] = temperature
            if max_tokens is not None:
                kwargs["max_tokens"] = max_tokens
            result = runtime.query(picture, prompt, **kwargs) if kwargs else runtime.query(picture, prompt)
            answer = result.get("answer") if isinstance(result, dict) else None
            if not isinstance(answer, str):
                raise RuntimeError(f"Moondream query returned no answer: {result}")
            return answer
        result = runtime.caption(picture, length=length or "normal")
        caption = result.get("caption") if isinstance(result, dict) else None
        if not isinstance(caption, str):
            raise RuntimeError(f"Moondream caption returned no caption: {result}")
        return caption

    def detect(
        self,
        image,
        object: str,
        skill: str = "detect",
        threshold: Optional[float] = None,
        max_points: Optional[int] = None,
    ) -> Dict[str, Any]:
        # Reuse the cloud response shape so CLI/MCP callers see one JSON contract.
        cloud = MoondreamAdapter.detect
        skill = (skill or "detect").strip().lower()
        if skill not in {"detect", "point", "segment"}:
            raise ValueError("detect --skill must be detect, point, or segment")
        if not (object and str(object).strip()):
            raise ValueError("detect requires --object")
        if image is None or image == "":
            raise ValueError("Moondream requires --image")
        runtime = self._model()
        picture = self._open(image)
        if skill == "detect":
            kwargs = {"threshold": threshold} if threshold is not None else {}
            payload = runtime.detect(picture, object, **kwargs)
            return {
                "skill": "detect",
                "object": object,
                "detections": [
                    {
                        "label": item.get("label") or object,
                        "score": item.get("confidence"),
                        "bbox_xyxy": [
                            item.get("x_min"),
                            item.get("y_min"),
                            item.get("x_max"),
                            item.get("y_max"),
                        ],
                        "normalized": True,
                    }
                    for item in (payload.get("objects") or [])
                ],
            }
        if skill == "point":
            kwargs = {"max_points": max_points} if max_points is not None else {}
            payload = runtime.point(picture, object, **kwargs)
            return {"skill": "point", "object": object, "points": payload.get("points") or []}
        payload = runtime.segment(picture, object)
        return {
            "skill": "segment",
            "object": object,
            "path": payload.get("path"),
            "bbox_xyxy": [
                payload.get("x_min"),
                payload.get("y_min"),
                payload.get("x_max"),
                payload.get("y_max"),
            ],
            "normalized": True,
        }
