"""Shared media helpers for vLLM-SR Decision 3.0 (d3) adapters."""

from __future__ import annotations

import base64
import json
import mimetypes
import os
from typing import Any, Dict, List, Optional, Union

import requests
from PIL import Image

MediaInput = Union[str, bytes]


def load_assets(assets: Optional[Union[str, Dict[str, Any]]]) -> Optional[Dict[str, Any]]:
    if assets is None:
        return None
    if isinstance(assets, dict):
        return assets
    if isinstance(assets, str):
        text = assets.strip()
        if os.path.isfile(text):
            with open(text, "r", encoding="utf-8") as f:
                text = f.read()
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "assets must be a JSON object, a JSON string, or a path to a JSON file "
                f"(could not parse: {exc})."
            ) from exc
        if not isinstance(parsed, dict):
            raise ValueError("assets must be a JSON object mapping placeholder names to media specs.")
        return parsed
    raise ValueError("Unsupported assets input.")


def _read_bytes(path_or_url: str) -> bytes:
    if path_or_url.startswith(("http://", "https://")):
        resp = requests.get(path_or_url, timeout=120)
        resp.raise_for_status()
        return resp.content
    if not os.path.exists(path_or_url):
        raise ValueError(f"File does not exist: {path_or_url}")
    with open(path_or_url, "rb") as f:
        return f.read()


def _guess_mime(path: str, default: str) -> str:
    mime, _ = mimetypes.guess_type(path)
    return mime or default


def prepare_images_for_api(images: List[MediaInput]) -> List[str]:
    """URLs pass through; local paths become data URLs for the hosted API."""
    out: List[str] = []
    for item in images:
        if isinstance(item, Image.Image):
            import io

            buf = io.BytesIO()
            item.save(buf, format="JPEG")
            b64 = base64.b64encode(buf.getvalue()).decode("ascii")
            out.append(f"data:image/jpeg;base64,{b64}")
            continue
        if not isinstance(item, str):
            raise ValueError("Each image must be a path, URL, or PIL Image.")
        if item.startswith(("http://", "https://", "data:")):
            out.append(item)
            continue
        raw = _read_bytes(item)
        mime = _guess_mime(item, "image/jpeg")
        b64 = base64.b64encode(raw).decode("ascii")
        out.append(f"data:{mime};base64,{b64}")
    return out


def prepare_videos_for_api(videos: List[MediaInput]) -> List[str]:
    out: List[str] = []
    for item in videos:
        if not isinstance(item, str):
            raise ValueError("Each video must be a path or URL string.")
        if item.startswith(("http://", "https://", "data:")):
            out.append(item)
            continue
        raw = _read_bytes(item)
        mime = _guess_mime(item, "video/mp4")
        b64 = base64.b64encode(raw).decode("ascii")
        out.append(f"data:{mime};base64,{b64}")
    return out


def prepare_images_for_local(images: List[MediaInput]) -> List[Union[str, Image.Image]]:
    """Local ``system_one`` accepts paths, URLs, PIL, or base64 strings."""
    out: List[Union[str, Image.Image]] = []
    for item in images:
        if isinstance(item, Image.Image):
            out.append(item.convert("RGB"))
            continue
        if isinstance(item, str):
            out.append(item)
            continue
        raise ValueError("Unsupported image input for local d3.")
    return out


def prepare_videos_for_local(videos: List[str]) -> List[str]:
    return list(videos)
