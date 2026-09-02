"""
Tencent Hy4 preview — TokenHub API + self-hosted OpenAI-compatible serving.

Hy4 preview is Tencent Hy Team's 770B MoE flagship LLM (49B active, 1M context).
OpenTryOn exposes it on the ``understand`` service (text in → text out, optional
image as an OpenAI vision part). It is **not** a VTON or video-generation model.

Path A (hosted): Tencent Cloud TokenHub OpenAI Chat Completions.
Path B (weights): serve ``tencent/Hy4-preview`` / ``tencent/Hy4-preview-FP8``
with the official vLLM or SGLang image, then call the same adapter against
``http://127.0.0.1:8000/v1``. Do **not** load 770B in-process.

Reference:
https://hy.tencent.ai/research/hy4-preview
https://www.tencentcloud.com/document/product/1300/80695
https://huggingface.co/tencent/Hy4-preview
https://github.com/Tencent-Hunyuan/Hy4-preview

Model id (API and served-name): ``hy4-preview``

Env (TokenHub):
  TOKENHUB_API_KEY (required for ``--model hy4-preview``)
  TOKENHUB_BASE_URL — default https://tokenhub-intl.tencentcloudmaas.com/v1
  TENCENT_TOKENHUB_API_KEY — alias for TOKENHUB_API_KEY

Env (local vLLM / SGLang):
  HY4_BASE_URL — default http://127.0.0.1:8000/v1
  HY4_API_KEY — optional (official examples use ``EMPTY``)

Examples:
    >>> from tryon.api.hy import Hy4Adapter
    >>> adapter = Hy4Adapter()  # TokenHub
    >>> result = adapter.understand(prompt="Describe a linen trench for a lookbook.")
    >>> print(result["text"])

    >>> local = Hy4Adapter(endpoint="local")  # vLLM/SGLang on localhost
    >>> result = local.understand(prompt="Hello")
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

TOKENHUB_DEFAULT_BASE_URL = "https://tokenhub-intl.tencentcloudmaas.com/v1"
LOCAL_DEFAULT_BASE_URL = "http://127.0.0.1:8000/v1"
LOCAL_DEFAULT_API_KEY = "EMPTY"

VALID_MODELS = {"hy4-preview"}
VALID_ENDPOINTS = {"tokenhub", "local"}
VALID_REASONING_EFFORTS = {"high", "medium", "low"}

DEFAULT_UNDERSTAND_PROMPT = "Describe what is shown in as much relevant detail as possible."
DEFAULT_TEMPERATURE = 0.9
DEFAULT_TOP_P = 1.0

ImageInput = Union[str, Path, io.BytesIO, bytes, Image.Image]


class Hy4Adapter:
    """
    Tencent Hy4 preview via TokenHub or a local OpenAI-compatible server.

    Args:
        api_key: TokenHub key (``TOKENHUB_API_KEY``) or local dummy key.
        model: OpenAI ``model`` field. Defaults to ``hy4-preview``.
        base_url: Chat Completions base URL.
        endpoint: ``tokenhub`` (hosted) or ``local`` (vLLM/SGLang).
        temperature: Official default ``0.9``.
        top_p: Official default ``1.0``.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "hy4-preview",
        base_url: Optional[str] = None,
        endpoint: str = "tokenhub",
        temperature: float = DEFAULT_TEMPERATURE,
        top_p: float = DEFAULT_TOP_P,
    ):
        if not _OPENAI_AVAILABLE:
            raise ImportError(
                "OpenAI SDK is not available. Please install it with 'pip install openai'."
            )
        if model not in VALID_MODELS:
            raise ValueError(
                f"Invalid model: {model!r}. Supported models: {sorted(VALID_MODELS)}"
            )
        serving = (endpoint or "tokenhub").strip().lower()
        if serving not in VALID_ENDPOINTS:
            raise ValueError(
                f"Invalid endpoint: {endpoint!r}. Use one of {sorted(VALID_ENDPOINTS)}"
            )
        self.endpoint = serving
        self.model = model
        self.temperature = float(temperature)
        self.top_p = float(top_p)

        if serving == "local":
            self.api_key = (
                api_key
                or os.getenv("HY4_API_KEY")
                or LOCAL_DEFAULT_API_KEY
            )
            self.base_url = (
                base_url
                or os.getenv("HY4_BASE_URL")
                or LOCAL_DEFAULT_BASE_URL
            ).rstrip("/")
        else:
            self.api_key = (
                api_key
                or os.getenv("TOKENHUB_API_KEY")
                or os.getenv("TENCENT_TOKENHUB_API_KEY")
            )
            if not self.api_key:
                raise ValueError(
                    "Tencent TokenHub API key is required. Set TOKENHUB_API_KEY "
                    "(or TENCENT_TOKENHUB_API_KEY) or pass api_key=."
                )
            self.base_url = (
                base_url
                or os.getenv("TOKENHUB_BASE_URL")
                or TOKENHUB_DEFAULT_BASE_URL
            ).rstrip("/")

        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

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
        if source_str.startswith(("http://", "https://")):
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

    def _image_to_data_uri(self, image: ImageInput) -> str:
        data, ext = self._load_bytes(image, default_ext="png")
        mime = "jpeg" if ext in {"jpg", "jpeg"} else ext
        return f"data:image/{mime};base64,{base64.b64encode(data).decode('utf-8')}"

    def _media_url(self, source: ImageInput) -> str:
        if isinstance(source, (str, Path)):
            source_str = str(source)
            if source_str.startswith(("http://", "https://", "data:")):
                return source_str
        return self._image_to_data_uri(source)

    def _extra_body(
        self,
        enable_thinking: bool,
        reasoning_effort: Optional[str],
    ) -> Dict[str, Any]:
        extra: Dict[str, Any] = {}
        effort = (reasoning_effort or "high").strip().lower()
        if effort not in VALID_REASONING_EFFORTS:
            raise ValueError(
                f"Invalid reasoning_effort: {reasoning_effort!r}. "
                f"Supported values: {sorted(VALID_REASONING_EFFORTS)}"
            )
        if self.endpoint == "local":
            extra["chat_template_kwargs"] = {
                "reasoning_effort": "no_think" if not enable_thinking else effort,
            }
            return extra
        extra["thinking"] = {"type": "enabled" if enable_thinking else "disabled"}
        extra["reasoning_effort"] = effort
        return extra

    def _chat(
        self,
        content: Union[str, List[Dict[str, Any]]],
        model: Optional[str] = None,
        enable_thinking: bool = True,
        reasoning_effort: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
    ) -> Dict[str, Any]:
        model = model or self.model
        if model not in VALID_MODELS:
            raise ValueError(
                f"Invalid model: {model!r}. Supported models: {sorted(VALID_MODELS)}"
            )
        kwargs: Dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": content}],
            "temperature": self.temperature if temperature is None else float(temperature),
            "top_p": self.top_p if top_p is None else float(top_p),
            "extra_body": self._extra_body(enable_thinking, reasoning_effort),
        }
        if max_tokens is not None:
            kwargs["max_tokens"] = int(max_tokens)
        completion = self.client.chat.completions.create(**kwargs)
        message = completion.choices[0].message
        reasoning = getattr(message, "reasoning_content", None)
        if reasoning is None:
            reasoning = getattr(message, "reasoning", None)
        return {
            "text": message.content,
            "reasoning": reasoning,
            "model": completion.model,
            "usage": completion.usage.model_dump() if completion.usage else None,
        }

    def understand_image(
        self,
        image: Union[ImageInput, List[ImageInput]],
        prompt: str = DEFAULT_UNDERSTAND_PROMPT,
        model: Optional[str] = None,
        enable_thinking: bool = True,
        reasoning_effort: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Optional vision part + prompt. Hy4 is a text LLM; image is best-effort."""
        images = image if isinstance(image, list) else [image]
        content: List[Dict[str, Any]] = [
            {"type": "image_url", "image_url": {"url": self._media_url(img)}}
            for img in images
        ]
        content.append({"type": "text", "text": prompt or DEFAULT_UNDERSTAND_PROMPT})
        return self._chat(
            content,
            model=model,
            enable_thinking=enable_thinking,
            reasoning_effort=reasoning_effort,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
        )

    def understand(
        self,
        image: Optional[Union[ImageInput, List[ImageInput]]] = None,
        video: Optional[Any] = None,
        prompt: Optional[str] = None,
        model: Optional[str] = None,
        enable_thinking: bool = True,
        reasoning_effort: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
    ) -> Dict[str, Any]:
        """CLI entry: text prompt (required unless ``image`` is set). No video."""
        if video is not None:
            raise ValueError(
                "Hy4 preview is a text LLM (TokenHub / vLLM). Video understanding "
                "is not in the Hy4 API — use kimi-k2.6, qwen3.8-max, or nemotron-omni."
            )
        text = (prompt or "").strip()
        if image is None and not text:
            raise ValueError(
                "Provide a `prompt` (Hy4 is a text model). `image` is optional."
            )
        if image is not None:
            return self.understand_image(
                image,
                prompt=text or DEFAULT_UNDERSTAND_PROMPT,
                model=model,
                enable_thinking=enable_thinking,
                reasoning_effort=reasoning_effort,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
            )
        return self._chat(
            text,
            model=model,
            enable_thinking=enable_thinking,
            reasoning_effort=reasoning_effort,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
        )

    def chat(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        enable_thinking: bool = True,
        reasoning_effort: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
    ):
        """Multi-turn / tool-calling escape hatch; returns the raw ChatCompletion."""
        model = model or self.model
        kwargs: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": self.temperature if temperature is None else float(temperature),
            "top_p": self.top_p if top_p is None else float(top_p),
            "extra_body": self._extra_body(enable_thinking, reasoning_effort),
        }
        if max_tokens is not None:
            kwargs["max_tokens"] = int(max_tokens)
        if tools is not None:
            kwargs["tools"] = tools
        if tool_choice is not None:
            kwargs["tool_choice"] = tool_choice
        return self.client.chat.completions.create(**kwargs)
