"""
Generic System One decision client (``POST /v1/systemone``) plus shared helpers.

TypeSafe's System One contract has become the common wire format for decision models:
send a ``state`` and named, typed ``questions`` (``noul`` / ``choice`` / ``score``) and
get calibrated ``answers`` back in one forward pass. Several open models now serve the
same contract, so one client covers them through presets:

- ``kev-openrouter``     -- Jared Palmer's Kev 4B via OpenRouter (third-party; Kev has no
  first-party API). ``https://openrouter.ai/api/v1/systemone``, ``OPENROUTER_API_KEY``.
- ``kev-local``          -- the Kev repo's own server (``python -m kev.serve``), default
  ``http://127.0.0.1:8008`` (``KEV_BASE_URL``; ``KEV_API_KEY`` only if you set one).
- ``clef-local``         -- Cloudflare Clef served by SGLang, default
  ``http://127.0.0.1:30000`` (``CLEF_BASE_URL``).
- ``pplx-decider-local`` -- Perplexity Decider served by SGLang, default
  ``http://127.0.0.1:30000`` (``PPLX_DECIDER_BASE_URL``).

Hosted Clef (Cloudflare Workers AI) and hosted Decider (Perplexity Decisions API) use
their vendors' own endpoints; see :mod:`tryon.api.cloudflare` and :mod:`tryon.api.perplexity`.

References:
  https://openrouter.ai/docs/guides/community/typesafe-sdk
  https://huggingface.co/jaredpalmer/kev-4b
  https://huggingface.co/Cloudflare/clef
  https://docs.sglang.io/cookbook/autoregressive/Perplexity/pplx-decider-v1-27b
"""

from __future__ import annotations

import base64
import json
import mimetypes
import os
from typing import Any, Dict, List, Optional, Sequence, Union

import requests

from tryon.d3_media import prepare_images_for_api
from tryon.decision import Questions, load_questions, load_state

ImageInput = Union[str, Any]

PRESETS: Dict[str, Dict[str, Any]] = {
    "kev-openrouter": {
        "base_url": "https://openrouter.ai/api",
        "base_env": None,
        "key_env": "OPENROUTER_API_KEY",
        "key_required": True,
        "model": "jaredpalmer/kev-4b",
        "max_images": 0,
    },
    "kev-local": {
        "base_url": "http://127.0.0.1:8008",
        "base_env": "KEV_BASE_URL",
        "key_env": "KEV_API_KEY",
        "key_required": False,
        "model": "kev-latest",
        "max_images": 0,
    },
    "clef-local": {
        "base_url": "http://127.0.0.1:30000",
        "base_env": "CLEF_BASE_URL",
        "key_env": None,
        "key_required": False,
        "model": "Cloudflare/clef",
        "max_images": 4,
    },
    "pplx-decider-local": {
        "base_url": "http://127.0.0.1:30000",
        "base_env": "PPLX_DECIDER_BASE_URL",
        "key_env": None,
        "key_required": False,
        "model": "perplexity-ai/pplx-decider-v1.1-27b",
        "max_images": 8,
    },
}

MAX_CHOICE_OPTIONS = 255


def as_list(value: Optional[Union[Any, Sequence[Any]]]) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def image_data_urls(
    images: Optional[Union[ImageInput, Sequence[ImageInput]]],
    *,
    max_images: Optional[int] = None,
    allowed_mimes: Optional[Sequence[str]] = None,
    max_bytes: Optional[int] = None,
) -> List[str]:
    """Turn paths, URLs, PIL images or data URLs into base64 ``data:`` URLs.

    Remote ``http(s)`` URLs are downloaded and inlined, because several decision APIs
    (Perplexity, Cloudflare) reject remote image URLs.
    """
    items = as_list(images)
    if max_images is not None and len(items) > max_images:
        raise ValueError(f"At most {max_images} image(s) per request (got {len(items)}).")
    out: List[str] = []
    for url in prepare_images_for_api(items):
        if url.startswith(("http://", "https://")):
            resp = requests.get(url, timeout=120)
            resp.raise_for_status()
            mime = (resp.headers.get("Content-Type") or "").split(";")[0].strip()
            if not mime.startswith("image/"):
                mime = mimetypes.guess_type(url.split("?")[0])[0] or "image/jpeg"
            url = f"data:{mime};base64,{base64.b64encode(resp.content).decode('ascii')}"
        header, _, payload = url.partition(",")
        mime = header[5:].split(";")[0] if header.startswith("data:") else ""
        if allowed_mimes is not None and mime not in allowed_mimes:
            raise ValueError(f"Unsupported image type {mime or '(unknown)'!r}; use {sorted(allowed_mimes)}.")
        if max_bytes is not None and len(payload) * 3 // 4 > max_bytes:
            raise ValueError(f"Image larger than {max_bytes // (1024 * 1024)} MiB.")
        out.append(url)
    return out


def state_text(state: Any) -> str:
    """Render a text / JSON state as one string (for content parts)."""
    if isinstance(state, (dict, list)):
        return json.dumps(state, ensure_ascii=False)
    return "" if state is None else str(state)


def check_choice_limits(questions: Dict[str, Dict[str, Any]], max_options: int = MAX_CHOICE_OPTIONS) -> None:
    for name, spec in questions.items():
        if spec.get("type") == "choice" and len(spec.get("criteria") or {}) > max_options:
            raise ValueError(f"question {name!r}: at most {max_options} choice options.")


def post_json(url: str, payload: Dict[str, Any], *, api_key: Optional[str], timeout: float, label: str) -> Dict[str, Any]:
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
    if resp.status_code != 200:
        raise RuntimeError(f"{label} API error ({resp.status_code}): {resp.text[:800]}")
    return resp.json()


class SystemOneAdapter:
    """Client for any server that speaks TypeSafe's ``POST /v1/systemone`` contract.

    Args:
        preset: one of :data:`PRESETS` (sets base URL, key env var, default model, image limit).
        api_key: overrides the preset's key env var.
        model: model name the server expects (``--served-model`` on the CLI).
        base_url: server root, without ``/v1/systemone``.
        timeout: HTTP timeout in seconds.
    """

    def __init__(
        self,
        preset: str = "kev-local",
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 120.0,
    ):
        if preset not in PRESETS:
            raise ValueError(f"preset must be one of {sorted(PRESETS)} (got {preset!r}).")
        cfg = PRESETS[preset]
        self.preset = preset
        self.max_images = int(cfg["max_images"])
        env_base = os.getenv(cfg["base_env"]) if cfg["base_env"] else None
        self.base_url = (base_url or env_base or cfg["base_url"]).rstrip("/")
        self.api_key = api_key or (os.getenv(cfg["key_env"]) if cfg["key_env"] else None)
        if cfg["key_required"] and not self.api_key:
            raise ValueError(f"Set {cfg['key_env']} (or pass api_key) for {preset}.")
        self.model = model or cfg["model"]
        self.timeout = timeout

    def decide(
        self,
        questions: Questions,
        state: Optional[Any] = None,
        image: Optional[Union[ImageInput, Sequence[ImageInput]]] = None,
    ) -> Dict[str, Any]:
        """Answer ``questions`` about ``state`` (and ``image`` where the model reads images)."""
        qs = load_questions(questions)
        check_choice_limits(qs)
        st = load_state(state)
        images = as_list(image)
        if images and not self.max_images:
            raise ValueError(f"{self.preset} is text-only; pass the image content as --state text instead.")
        if (st is None or st == "") and not images:
            raise ValueError("Provide a state (text or JSON) and/or an image.")
        payload: Dict[str, Any] = {"model": self.model, "state": "" if st is None else st, "questions": qs}
        if images:
            payload["images"] = image_data_urls(images, max_images=self.max_images)
        data = post_json(f"{self.base_url}/v1/systemone", payload, api_key=self.api_key,
                         timeout=self.timeout, label=f"System One ({self.preset})")
        return {"model": data.get("model", self.model), "answers": data.get("answers", {}), "usage": data.get("usage")}
