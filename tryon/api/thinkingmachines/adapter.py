"""
Inkling 2 Mini — Thinking Machines Lab multimodal understand.

Path A (hosted): Tinker OpenAI-compatible chat
  https://tinker.thinkingmachines.dev/services/tinker-prod/oai/api/v1
  Model ``thinkingmachines/Inkling-2-Mini`` (optional ``:peft:262144`` for 256K train ctx).
  Auth: ``TINKER_API_KEY``. Tinker accepts image input only on Inkling models; use data-URI
  images (max 2 MiB raw per image).

Path B (local): self-hosted weights (HF ``thinkingmachines/Inkling-2-Mini``, Apache 2.0)
  via vLLM, SGLang, Ollama, or Exo — default ``INKLING_BASE_URL=http://127.0.0.1:8000/v1``.

Docs:
  https://thinkingmachines.ai/model-card/inkling-2-mini/
  https://tinker-docs.thinkingmachines.ai/inference/openai/overview/
"""

from __future__ import annotations

import base64
import io
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import requests
from PIL import Image

try:
    from openai import OpenAI

    _OPENAI_AVAILABLE = True
except ImportError:
    _OPENAI_AVAILABLE = False
    OpenAI = None

TINKER_DEFAULT_BASE = "https://tinker.thinkingmachines.dev/services/tinker-prod/oai/api/v1"
LOCAL_DEFAULT_BASE = "http://127.0.0.1:8000/v1"
LOCAL_DEFAULT_API_KEY = "EMPTY"

DEFAULT_MODEL = "thinkingmachines/Inkling-2-Mini"
EXTENDED_CONTEXT_MODEL = "thinkingmachines/Inkling-2-Mini:peft:262144"
VALID_ENDPOINTS = {"tinker", "local"}
VALID_REASONING = {
    "none",
    "minimal",
    "low",
    "medium",
    "high",
    "xhigh",
    "max",
}
TINKER_IMAGE_MAX_BYTES = 2 * 1024 * 1024

DEFAULT_UNDERSTAND_PROMPT = "Describe what is shown in as much relevant detail as possible."

ImageInput = Union[str, Path, io.BytesIO, bytes, Image.Image]


class Inkling2MiniAdapter:
    """Inkling 2 Mini via Tinker or a local OpenAI-compatible server."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        base_url: Optional[str] = None,
        endpoint: str = "tinker",
    ):
        if not _OPENAI_AVAILABLE:
            raise ImportError("OpenAI SDK required. Install: pip install openai")
        serving = (endpoint or "tinker").strip().lower()
        if serving not in VALID_ENDPOINTS:
            raise ValueError(f"endpoint must be one of {sorted(VALID_ENDPOINTS)}")
        self.endpoint = serving
        self.model = (model or DEFAULT_MODEL).strip()
        if serving == "local":
            self.api_key = api_key or os.getenv("INKLING_API_KEY") or LOCAL_DEFAULT_API_KEY
            self.base_url = (
                base_url or os.getenv("INKLING_BASE_URL") or LOCAL_DEFAULT_BASE
            ).rstrip("/")
        else:
            self.api_key = api_key or os.getenv("TINKER_API_KEY")
            if not self.api_key:
                raise ValueError(
                    "Tinker API key required. Set TINKER_API_KEY "
                    "(https://tinker-docs.thinkingmachines.ai)."
                )
            self.base_url = (
                base_url or os.getenv("TINKER_BASE_URL") or TINKER_DEFAULT_BASE
            ).rstrip("/")
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    @staticmethod
    def _load_bytes(source: ImageInput, default_ext: str = "png") -> bytes:
        if isinstance(source, Image.Image):
            buf = io.BytesIO()
            source.convert("RGB").save(buf, format="PNG")
            return buf.getvalue()
        if isinstance(source, (bytes, bytearray)):
            return bytes(source)
        if isinstance(source, io.BytesIO):
            source.seek(0)
            return source.read()
        text = str(source)
        if text.startswith(("http://", "https://")):
            resp = requests.get(text, timeout=60)
            resp.raise_for_status()
            return resp.content
        path = Path(text)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {text}")
        return path.read_bytes()

    def _image_data_uri(self, source: ImageInput) -> str:
        data = self._load_bytes(source)
        if self.endpoint == "tinker" and len(data) > TINKER_IMAGE_MAX_BYTES:
            raise ValueError(
                f"Tinker Inkling images must be <= {TINKER_IMAGE_MAX_BYTES} bytes "
                f"before base64 (got {len(data)}). Resize or compress the image."
            )
        ext = "png"
        if isinstance(source, (str, Path)) and not str(source).startswith("http"):
            ext = Path(str(source)).suffix.lower().lstrip(".") or "png"
        mime = "jpeg" if ext in {"jpg", "jpeg"} else ext
        if mime not in {"png", "jpeg", "gif", "webp"}:
            mime = "png"
        b64 = base64.b64encode(data).decode("ascii")
        return f"data:image/{mime};base64,{b64}"

    def _media_url(self, source: ImageInput) -> str:
        if self.endpoint == "tinker":
            return self._image_data_uri(source)
        if isinstance(source, (str, Path)):
            s = str(source)
            if s.startswith(("http://", "https://", "data:")):
                return s
        return self._image_data_uri(source)

    def _chat(
        self,
        content: Union[str, List[Dict[str, Any]]],
        *,
        system: Optional[str] = None,
        model: Optional[str] = None,
        reasoning_effort: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
    ) -> Dict[str, Any]:
        messages: List[Dict[str, Any]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": content})

        kwargs: Dict[str, Any] = {"model": model or self.model, "messages": messages}
        if temperature is not None:
            kwargs["temperature"] = float(temperature)
        if top_p is not None:
            kwargs["top_p"] = float(top_p)
        if max_tokens is not None:
            kwargs["max_completion_tokens"] = int(max_tokens)
        if reasoning_effort is not None:
            effort = str(reasoning_effort).strip().lower()
            if effort not in VALID_REASONING:
                raise ValueError(
                    f"reasoning_effort must be one of {sorted(VALID_REASONING)} "
                    f"(got {reasoning_effort!r})."
                )
            kwargs["reasoning_effort"] = effort

        completion = self.client.chat.completions.create(**kwargs)
        message = completion.choices[0].message
        reasoning = getattr(message, "reasoning_content", None)
        text = message.content or ""
        if reasoning and text:
            pass
        elif reasoning and not text:
            text = reasoning
        return {
            "text": text,
            "reasoning": reasoning,
            "model": completion.model,
            "endpoint": self.endpoint,
            "usage": completion.usage.model_dump() if completion.usage else None,
        }

    def understand(
        self,
        image: Optional[Union[ImageInput, List[ImageInput]]] = None,
        video: Optional[Any] = None,
        prompt: Optional[str] = None,
        system: Optional[str] = None,
        model: Optional[str] = None,
        reasoning_effort: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
    ) -> Dict[str, Any]:
        if video is not None:
            raise ValueError(
                "Inkling 2 Mini is image + text only. For video use nemotron-omni or kimi-k2.6."
            )
        text = (prompt or "").strip()
        if image is None and not text:
            raise ValueError("Provide --prompt and/or --image.")

        if image is not None:
            images = image if isinstance(image, list) else [image]
            parts: List[Dict[str, Any]] = []
            for img in images:
                parts.append(
                    {"type": "image_url", "image_url": {"url": self._media_url(img)}}
                )
            parts.append(
                {"type": "text", "text": text or DEFAULT_UNDERSTAND_PROMPT}
            )
            return self._chat(
                parts,
                system=system,
                model=model,
                reasoning_effort=reasoning_effort,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
            )

        return self._chat(
            text,
            system=system,
            model=model,
            reasoning_effort=reasoning_effort,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
        )