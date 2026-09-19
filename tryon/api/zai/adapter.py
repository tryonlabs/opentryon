"""
GLM-5.3-FlashX (Z.ai / Zhipu) Vision API Adapter

Adapter for Zhipu's GLM-5.3-FlashX, the high-speed serving tier of
GLM-5.3-Flash (launched 18 Sep 2026, up to 200 tokens/s) via the Z.ai
OpenAI-compatible Chat Completions API. Natively multimodal (text + image +
video) and general-purpose -- useful for garment photos and lookbook clips
as well as documents, UI, and product photography.

Unlike the text-only GLM-5.3 flagship, the Flash/FlashX branch is a VLM and
always runs with thinking enabled (GLM-5.3-FlashX rejects requests that try
to disable it; use ``reasoning_effort`` to control depth instead).

Reference:
https://docs.z.ai/guides/vlm/glm-5.3-flash
https://docs.z.ai/api-reference/introduction

Models:
- glm-5.3-flashx: High-speed serving tier of GLM-5.3-Flash. Same weights,
  faster inference. 1M context, 320B total / 18B activated parameters.

Env:
  ZAI_API_KEY (required)
  ZAI_BASE_URL -- default https://api.z.ai/api/paas/v4

Examples:
    >>> from tryon.api.zai import GLMUnderstandAdapter
    >>> adapter = GLMUnderstandAdapter()
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

DEFAULT_BASE_URL = "https://api.z.ai/api/paas/v4"

VALID_MODELS = {
    "glm-5.3-flashx",
}
VALID_REASONING_EFFORTS = {"low", "high", "max"}

VIDEO_MIME_OVERRIDES = {"flv": "x-flv", "3gp": "3gpp"}

DEFAULT_UNDERSTAND_PROMPT = "Describe what is shown in as much relevant detail as possible."

ImageInput = Union[str, Path, io.BytesIO, bytes, Image.Image]
VideoInput = Union[str, Path, io.BytesIO, bytes]


class GLMUnderstandAdapter:
    """
    Adapter for Zhipu's GLM-5.3-FlashX vision model via the Z.ai
    OpenAI-compatible API.

    Args:
        api_key: Z.ai / Zhipu key. Defaults to ``ZAI_API_KEY``.
        model: Default model id. Defaults to ``"glm-5.3-flashx"``.
        base_url: Compatible-mode base URL. Defaults to ``ZAI_BASE_URL`` or
            the official Z.ai endpoint.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "glm-5.3-flashx",
        base_url: Optional[str] = None,
    ):
        if not _OPENAI_AVAILABLE:
            raise ImportError(
                "OpenAI SDK is not available. Please install it with 'pip install openai'."
            )

        if model not in VALID_MODELS:
            raise ValueError(f"Invalid model: {model!r}. Supported models: {sorted(VALID_MODELS)}")

        self.api_key = api_key or os.getenv("ZAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Z.ai API key must be provided either as a parameter or "
                "through the ZAI_API_KEY environment variable."
            )

        self.model = model
        self.base_url = (
            base_url or os.getenv("ZAI_BASE_URL") or DEFAULT_BASE_URL
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

    def _image_to_data_uri(self, image: ImageInput) -> str:
        data, ext = self._load_bytes(image, default_ext="png")
        mime = "jpeg" if ext in {"jpg", "jpeg"} else ext
        return f"data:image/{mime};base64,{base64.b64encode(data).decode('utf-8')}"

    def _video_to_data_uri(self, video: VideoInput) -> str:
        data, ext = self._load_bytes(video, default_ext="mp4")
        mime_ext = VIDEO_MIME_OVERRIDES.get(ext, ext)
        return f"data:video/{mime_ext};base64,{base64.b64encode(data).decode('utf-8')}"

    def _media_url(self, source: Union[ImageInput, VideoInput], kind: str) -> str:
        """Pass through http(s) URLs; otherwise encode as a data URI."""
        if isinstance(source, (str, Path)):
            source_str = str(source)
            if source_str.startswith("http://") or source_str.startswith("https://"):
                return source_str
        if kind == "image":
            return self._image_to_data_uri(source)  # type: ignore[arg-type]
        return self._video_to_data_uri(source)  # type: ignore[arg-type]

    # -- core call --------------------------------------------------------

    def _chat(
        self,
        content: List[Dict[str, Any]],
        model: Optional[str] = None,
        reasoning_effort: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
    ) -> Dict[str, Any]:
        model = model or self.model
        if model not in VALID_MODELS:
            raise ValueError(f"Invalid model: {model!r}. Supported models: {sorted(VALID_MODELS)}")

        kwargs: Dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": content}],
            # GLM-5.3-FlashX rejects thinking.type: disabled; only "enabled" is valid.
            "extra_body": {"thinking": {"type": "enabled"}},
        }
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        if temperature is not None:
            kwargs["temperature"] = temperature
        if top_p is not None:
            kwargs["top_p"] = top_p
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
        if reasoning is None:
            reasoning = getattr(message, "reasoning", None)
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
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Understand one or more images with a text prompt/instruction."""
        images = image if isinstance(image, list) else [image]
        content = [
            {"type": "image_url", "image_url": {"url": self._media_url(img, "image")}}
            for img in images
        ]
        content.append({"type": "text", "text": prompt})
        return self._chat(
            content,
            model=model,
            reasoning_effort=reasoning_effort,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
        )

    def understand_video(
        self,
        video: VideoInput,
        prompt: str = "Describe what happens in this video.",
        model: Optional[str] = None,
        reasoning_effort: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Understand video content with a text prompt/instruction."""
        content = [
            {"type": "video_url", "video_url": {"url": self._media_url(video, "video")}},
            {"type": "text", "text": prompt},
        ]
        return self._chat(
            content,
            model=model,
            reasoning_effort=reasoning_effort,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
        )

    def understand(
        self,
        image: Optional[Union[ImageInput, List[ImageInput]]] = None,
        video: Optional[VideoInput] = None,
        prompt: str = DEFAULT_UNDERSTAND_PROMPT,
        model: Optional[str] = None,
        reasoning_effort: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
    ) -> Dict[str, Any]:
        """CLI-friendly entry point: pass ``image`` and/or ``video``."""
        if image is None and video is None:
            raise ValueError("Provide at least one of `image` or `video`.")

        content: List[Dict[str, Any]] = []
        if image is not None:
            images = image if isinstance(image, list) else [image]
            content.extend(
                {"type": "image_url", "image_url": {"url": self._media_url(img, "image")}}
                for img in images
            )
        if video is not None:
            content.append(
                {"type": "video_url", "video_url": {"url": self._media_url(video, "video")}}
            )
        content.append({"type": "text", "text": prompt})

        return self._chat(
            content,
            model=model,
            reasoning_effort=reasoning_effort,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
        )
