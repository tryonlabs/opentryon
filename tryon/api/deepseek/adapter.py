"""
DeepSeek-V4.1-Flash (deepseek-flash) Vision API Adapter

Adapter for DeepSeek's multimodal Flash model via the DeepSeek Platform API,
which is fully compatible with the OpenAI SDK/API format. deepseek-flash is
DeepSeek's first Causal Encoder-Decoder (CED) model with native image input
(released as V4-Flash-Vision-Exp, folded into the general-availability
V4.1-Flash on 10 Sep 2026) -- general-purpose, not limited to the fashion
domain, so this adapter can be used to understand garment photos as well as
documents, UI screenshots, product photography, or any other image content.

Unlike Kimi/Qwen3.8/GLM-5.3-FlashX, DeepSeek's API does **not** accept video
input -- images only.

Reference:
https://api-docs.deepseek.com/quick_start/pricing/
https://api-docs.deepseek.com/api/create-chat-completion
https://api-docs.deepseek.com/news/news260821/

Models:
- deepseek-flash: Multimodal (text + image -> text), 1M context, 384K max
  output. Thinking on by default; `reasoning_effort` controls depth
  (`none` disables thinking, `max` is the deepest). The legacy names
  `deepseek-v4-flash` / `deepseek-v4-flash-vision-exp` still work upstream
  but are billed and served as `deepseek-flash` -- this adapter only
  exposes the canonical id.

Env:
  DEEPSEEK_API_KEY (required)
  DEEPSEEK_BASE_URL -- default https://api.deepseek.com

Examples:
    >>> from tryon.api.deepseek import DeepSeekUnderstandAdapter
    >>> adapter = DeepSeekUnderstandAdapter()
    >>> result = adapter.understand_image("garment.jpg", prompt="Describe this outfit.")
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

DEFAULT_BASE_URL = "https://api.deepseek.com"

VALID_MODELS = {
    "deepseek-flash",
}
VALID_REASONING_EFFORTS = {"none", "low", "high", "max"}

DEFAULT_UNDERSTAND_PROMPT = "Describe what is shown in as much relevant detail as possible."

ImageInput = Union[str, Path, io.BytesIO, bytes, Image.Image]


class DeepSeekUnderstandAdapter:
    """
    Adapter for DeepSeek's deepseek-flash vision model via the DeepSeek
    Platform's OpenAI-compatible API.

    Args:
        api_key: DeepSeek Platform key. Defaults to ``DEEPSEEK_API_KEY``.
        model: Default model id. Defaults to ``"deepseek-flash"``.
        base_url: Base URL. Defaults to ``DEEPSEEK_BASE_URL`` or
            ``"https://api.deepseek.com"``.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "deepseek-flash",
        base_url: Optional[str] = None,
    ):
        if not _OPENAI_AVAILABLE:
            raise ImportError(
                "OpenAI SDK is not available. Please install it with 'pip install openai'."
            )

        if model not in VALID_MODELS:
            raise ValueError(f"Invalid model: {model!r}. Supported models: {sorted(VALID_MODELS)}")

        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError(
                "DeepSeek API key must be provided either as a parameter or "
                "through the DEEPSEEK_API_KEY environment variable."
            )

        self.model = model
        self.base_url = (
            base_url or os.getenv("DEEPSEEK_BASE_URL") or DEFAULT_BASE_URL
        ).rstrip("/")
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    # -- input loading --------------------------------------------------

    @staticmethod
    def _load_bytes(source, default_ext: str):
        """Return (raw_bytes, file_extension) for a path/URL/bytes/BytesIO/PIL input."""
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
        """Pass through http(s) URLs; otherwise encode as a base64 data URI."""
        if isinstance(image, (str, Path)):
            image_str = str(image)
            if image_str.startswith("http://") or image_str.startswith("https://"):
                return image_str
        data, ext = self._load_bytes(image, default_ext="png")
        mime = "jpeg" if ext in {"jpg", "jpeg"} else ext
        return f"data:image/{mime};base64,{base64.b64encode(data).decode('utf-8')}"

    # -- core call --------------------------------------------------------

    def _chat(
        self,
        content: List[Dict[str, Any]],
        model: Optional[str] = None,
        reasoning_effort: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        model = model or self.model
        if model not in VALID_MODELS:
            raise ValueError(f"Invalid model: {model!r}. Supported models: {sorted(VALID_MODELS)}")

        kwargs: Dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": content}],
        }
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        if reasoning_effort is not None:
            if reasoning_effort not in VALID_REASONING_EFFORTS:
                raise ValueError(
                    f"Invalid reasoning_effort: {reasoning_effort!r}. "
                    f"Supported values: {sorted(VALID_REASONING_EFFORTS)}"
                )
            kwargs["reasoning_effort"] = reasoning_effort

        completion = self.client.chat.completions.create(**kwargs)
        message = completion.choices[0].message
        reasoning = getattr(message, "reasoning_content", None)
        return {
            "text": message.content,
            "reasoning": reasoning,
            "model": completion.model,
            "usage": completion.usage.model_dump() if completion.usage else None,
        }

    # -- public API ---------------------------------------------------------

    def understand_image(
        self,
        image: Union[ImageInput, List[ImageInput]],
        prompt: str = DEFAULT_UNDERSTAND_PROMPT,
        model: Optional[str] = None,
        reasoning_effort: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Understand one or more images with a text prompt/instruction."""
        images = image if isinstance(image, list) else [image]
        content = [
            {"type": "image_url", "image_url": {"url": self._image_url(img)}}
            for img in images
        ]
        content.append({"type": "text", "text": prompt})
        return self._chat(
            content,
            model=model,
            reasoning_effort=reasoning_effort,
            max_tokens=max_tokens,
        )

    def understand(
        self,
        image: Optional[Union[ImageInput, List[ImageInput]]] = None,
        prompt: str = DEFAULT_UNDERSTAND_PROMPT,
        model: Optional[str] = None,
        reasoning_effort: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """CLI-friendly entry point: pass ``image`` (required -- DeepSeek's
        API does not accept video input, unlike Kimi/Qwen3.8/GLM-5.3-FlashX)."""
        if image is None:
            raise ValueError(
                "image is required. DeepSeek's API does not accept video input."
            )
        return self.understand_image(
            image,
            prompt=prompt,
            model=model,
            reasoning_effort=reasoning_effort,
            max_tokens=max_tokens,
        )
