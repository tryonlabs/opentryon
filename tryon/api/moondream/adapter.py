"""
Moondream Cloud (Path A) — query, caption, detect, point, and segment.

First-party REST at https://api.moondream.ai/v1/{skill}. Auth header is
``X-Moondream-Auth``. Model ids: ``moondream3.1-9B-A2B`` and
``moondream3-preview``.

Docs: https://docs.moondream.ai/api
Env: MOONDREAM_API_KEY, optional MOONDREAM_BASE_URL
"""

from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

import requests

DEFAULT_BASE_URL = "https://api.moondream.ai/v1"
CLOUD_MODELS = {
    "moondream-3.1": "moondream3.1-9B-A2B",
    "moondream-3-preview": "moondream3-preview",
}

ImageInput = Union[str, Path, bytes]


def _image_url(image: ImageInput) -> str:
    if isinstance(image, str) and (
        image.startswith("http://")
        or image.startswith("https://")
        or image.startswith("data:")
    ):
        return image
    if isinstance(image, bytes):
        encoded = base64.b64encode(image).decode("ascii")
        return f"data:image/png;base64,{encoded}"
    path = Path(image)
    data = path.read_bytes()
    suffix = path.suffix.lower().lstrip(".") or "png"
    mime = "jpeg" if suffix in {"jpg", "jpeg"} else suffix
    encoded = base64.b64encode(data).decode("ascii")
    return f"data:image/{mime};base64,{encoded}"


class MoondreamAdapter:
    """Hosted Moondream skills. ``understand`` is query/caption; ``detect`` is boxes, points, or an SVG mask."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "moondream3.1-9B-A2B",
        base_url: Optional[str] = None,
        timeout: float = 120.0,
    ):
        self.api_key = api_key or os.getenv("MOONDREAM_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Moondream API key is required. Set MOONDREAM_API_KEY "
                "(https://moondream.ai) or pass api_key."
            )
        self.model = model
        self.base_url = (base_url or os.getenv("MOONDREAM_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.timeout = float(timeout)

    def _post(self, skill: str, body: Dict[str, Any]) -> Dict[str, Any]:
        response = requests.post(
            f"{self.base_url}/{skill}",
            headers={
                "X-Moondream-Auth": self.api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json=body,
            timeout=self.timeout,
        )
        try:
            payload = response.json()
        except ValueError:
            payload = None
        if response.status_code >= 400:
            detail = payload if isinstance(payload, dict) else (response.text or "")[:500]
            raise RuntimeError(f"Moondream {skill} HTTP {response.status_code}: {detail}")
        if not isinstance(payload, dict):
            raise RuntimeError(f"Moondream {skill} returned a non-object response")
        return payload

    def understand(
        self,
        image: ImageInput,
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
        body: Dict[str, Any] = {"model": self.model, "image_url": _image_url(image)}
        if skill == "query":
            body["question"] = prompt
            settings: Dict[str, Any] = {}
            if temperature is not None:
                settings["temperature"] = temperature
            if max_tokens is not None:
                settings["max_tokens"] = max_tokens
            if settings:
                body["settings"] = settings
            payload = self._post("query", body)
            answer = payload.get("answer")
            if not isinstance(answer, str):
                raise RuntimeError(f"Moondream query response missing answer: {payload}")
            return answer
        body["length"] = length or "normal"
        payload = self._post("caption", body)
        caption = payload.get("caption")
        if not isinstance(caption, str):
            raise RuntimeError(f"Moondream caption response missing caption: {payload}")
        return caption

    def detect(
        self,
        image: ImageInput,
        object: str,
        skill: str = "detect",
        threshold: Optional[float] = None,
        max_points: Optional[int] = None,
    ) -> Dict[str, Any]:
        skill = (skill or "detect").strip().lower()
        if skill not in {"detect", "point", "segment"}:
            raise ValueError("detect --skill must be detect, point, or segment")
        if not (object and str(object).strip()):
            raise ValueError("detect requires --object")
        if image is None or image == "":
            raise ValueError("Moondream requires --image")
        body: Dict[str, Any] = {
            "model": self.model,
            "image_url": _image_url(image),
            "object": object,
        }
        if skill == "detect" and threshold is not None:
            body["threshold"] = threshold
        if skill == "point" and max_points is not None:
            body["max_points"] = max_points
        payload = self._post(skill, body)
        if skill == "detect":
            detections = []
            for item in payload.get("objects") or []:
                detections.append({
                    "label": item.get("label") or object,
                    "score": item.get("confidence"),
                    "bbox_xyxy": [
                        item.get("x_min"),
                        item.get("y_min"),
                        item.get("x_max"),
                        item.get("y_max"),
                    ],
                    "normalized": True,
                })
            return {"skill": "detect", "object": object, "detections": detections}
        if skill == "point":
            return {"skill": "point", "object": object, "points": payload.get("points") or []}
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
