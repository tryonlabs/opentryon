"""
Ternary Bonsai 2 27B (PrismML) — local open-weight multimodal understanding.

Ternary-Bonsai-2-27B is a 27B-parameter model (Apache 2.0) built on
Qwen3.8-27B whose weights are quantized to {-1, 0, +1} ("ternary"),
retaining ~98% of full-precision benchmark performance at a fraction of the
footprint (5.9-8.5GB on disk depending on quant). It ships as GGUF
(requires the PrismML llama.cpp fork, ``prism-b10658`` or newer -- a stock
llama.cpp build silently produces gibberish) and as MLX weights for Apple
Silicon.

This adapter does **not** load the model in-process (no rotated-weight
ternary kernel exists in transformers/diffusers). Instead it is a thin
OpenAI-compatible HTTP client for the server the model ships with --
same shape as an LM Studio / Ollama client. Start the server yourself, e.g.:

    ./scripts/start_llama_server.sh   # OpenAI-compatible HTTP on :8080

then point this adapter at it (default ``http://127.0.0.1:8080/v1``, no
API key needed for a local server).

Docs: https://docs.prismml.com/bonsai-2-27b
HF:
  https://huggingface.co/prism-ml/Ternary-Bonsai-2-27B-gguf
  https://huggingface.co/prism-ml/Ternary-Bonsai-2-27B-mlx-2bit

Env:
  BONSAI_BASE_URL -- default http://127.0.0.1:8080/v1
  BONSAI_API_KEY  -- optional; only needed if the server is behind auth

Examples:
    >>> from tryon.models.ternary_bonsai import TernaryBonsaiAdapter
    >>> adapter = TernaryBonsaiAdapter()
    >>> result = adapter.understand(prompt="Explain ternary quantization in two sentences.")
    >>> print(result["text"])
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

DEFAULT_BASE_URL = "http://127.0.0.1:8080/v1"
DEFAULT_MODEL = "Ternary-Bonsai-2-27B"

DEFAULT_UNDERSTAND_PROMPT = "Describe what is shown in as much relevant detail as possible."

ImageInput = Union[str, Path, io.BytesIO, bytes, Image.Image]


class TernaryBonsaiAdapter:
    """
    Thin OpenAI-compatible client for a locally-served Ternary Bonsai 2 27B
    (llama.cpp server / MLX server started by the user).

    Args:
        api_key: Optional bearer token, only if the local server enforces one.
            Defaults to ``BONSAI_API_KEY`` (a placeholder is used if unset,
            since most local servers don't check it).
        model: Model id reported by the server. Defaults to
            ``"Ternary-Bonsai-2-27B"``; most llama.cpp servers ignore this
            and just serve whichever GGUF was loaded.
        base_url: OpenAI-compatible base URL. Defaults to ``BONSAI_BASE_URL``
            or ``http://127.0.0.1:8080/v1``.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        base_url: Optional[str] = None,
    ):
        if not _OPENAI_AVAILABLE:
            raise ImportError(
                "OpenAI SDK is not available. Please install it with 'pip install openai'."
            )

        self.api_key = api_key or os.getenv("BONSAI_API_KEY") or "not-needed"
        self.model = model
        self.base_url = (
            base_url or os.getenv("BONSAI_BASE_URL") or DEFAULT_BASE_URL
        ).rstrip("/")
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    # -- input loading --------------------------------------------------

    @staticmethod
    def _load_bytes(source, default_ext: str):
        if isinstance(source, Image.Image):
            buf = io.BytesIO()
            source.save(buf, format="PNG")
            return buf.getvalue(), "png"

        if isinstance(source, (bytes, bytearray)):
            return bytes(source), default_ext

        if isinstance(source, io.BytesIO):
            source.seek(0)
            return source.read(), default_ext

        source_str = str(source)
        if source_str.startswith("http://") or source_str.startswith("https://"):
            resp = requests.get(source_str, timeout=60)
            resp.raise_for_status()
            ext = Path(source_str.split("?")[0]).suffix.lstrip(".").lower() or default_ext
            return resp.content, ext

        path = Path(source_str)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {source_str}")
        ext = path.suffix.lstrip(".").lower() or default_ext
        with open(path, "rb") as f:
            return f.read(), ext

    def _image_url(self, image: ImageInput) -> str:
        if isinstance(image, (str, Path)):
            image_str = str(image)
            if image_str.startswith("http://") or image_str.startswith("https://"):
                return image_str
        data, ext = self._load_bytes(image, default_ext="png")
        mime = "jpeg" if ext in {"jpg", "jpeg"} else ext
        return f"data:image/{mime};base64,{base64.b64encode(data).decode('utf-8')}"

    # -- public API ---------------------------------------------------------

    def understand(
        self,
        image: Optional[Union[ImageInput, List[ImageInput]]] = None,
        prompt: str = DEFAULT_UNDERSTAND_PROMPT,
        model: Optional[str] = None,
        thinking_budget_tokens: Optional[int] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Text and/or image understanding against the local server.

        ``thinking_budget_tokens`` maps to the server's per-request thinking
        budget (``--reasoning-budget`` is the server-wide equivalent flag).
        """
        content: List[Dict[str, Any]] = []
        if image is not None:
            images = image if isinstance(image, list) else [image]
            content.extend(
                {"type": "image_url", "image_url": {"url": self._image_url(img)}}
                for img in images
            )
        content.append({"type": "text", "text": prompt})

        kwargs: Dict[str, Any] = {
            "model": model or self.model,
            "messages": [{"role": "user", "content": content}],
        }
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        if temperature is not None:
            kwargs["temperature"] = temperature
        if thinking_budget_tokens is not None:
            kwargs["extra_body"] = {"thinking_budget_tokens": int(thinking_budget_tokens)}

        try:
            completion = self.client.chat.completions.create(**kwargs)
        except Exception as exc:  # connection refused, etc.
            raise RuntimeError(
                f"Could not reach the local Ternary Bonsai server at "
                f"{self.base_url!r}. Start it first (see "
                f"https://docs.prismml.com/bonsai-2-27b), or point "
                f"BONSAI_BASE_URL at a running instance. Original error: {exc}"
            ) from exc

        message = completion.choices[0].message
        reasoning = getattr(message, "reasoning_content", None)
        return {
            "text": message.content,
            "reasoning": reasoning,
            "model": completion.model,
            "usage": completion.usage.model_dump() if completion.usage else None,
        }
