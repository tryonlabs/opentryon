"""
Qwen 3.8 (DashScope / Qwen Cloud) Vision API Adapter

Adapter for Alibaba Cloud Model Studio's Qwen3.8 multimodal models via the
DashScope OpenAI-compatible Chat Completions API. Qwen3.8-Max natively
accepts text, images, and video and is general-purpose — useful for garment
photos and lookbook clips as well as documents, UI, and product photography.

Reference:
https://docs.qwencloud.com/developer-guides/multimodal/vision
https://www.alibabacloud.com/help/en/model-studio/vision
https://www.alibabacloud.com/help/en/model-studio/get-api-key

Models:
- qwen3.8-max: Hosted flagship multimodal model (text + image + video).

Env:
  DASHSCOPE_API_KEY (required)
  QWEN_BASE_URL — default https://dashscope-intl.aliyuncs.com/compatible-mode/v1
    China: https://dashscope.aliyuncs.com/compatible-mode/v1
    US: https://dashscope-us.aliyuncs.com/compatible-mode/v1

Examples:
    >>> from tryon.api.qwen import QwenUnderstandAdapter
    >>> adapter = QwenUnderstandAdapter()
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

DEFAULT_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"

VALID_MODELS = {
    "qwen3.8-max",
}
VALID_REASONING_EFFORTS = {"xhigh", "medium", "low"}

VIDEO_MIME_OVERRIDES = {"flv": "x-flv", "3gp": "3gpp"}

DEFAULT_UNDERSTAND_PROMPT = "Describe what is shown in as much relevant detail as possible."

ImageInput = Union[str, Path, io.BytesIO, bytes, Image.Image]
VideoInput = Union[str, Path, io.BytesIO, bytes]


class QwenUnderstandAdapter:
    """
    Adapter for Qwen3.8 multimodal understanding via DashScope's
    OpenAI-compatible API.

    Args:
        api_key: DashScope / Model Studio key. Defaults to ``DASHSCOPE_API_KEY``.
        model: Default model id. Defaults to ``"qwen3.8-max"``.
        base_url: Compatible-mode base URL. Defaults to ``QWEN_BASE_URL`` or
            the international DashScope endpoint.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "qwen3.8-max",
        base_url: Optional[str] = None,
    ):
        if not _OPENAI_AVAILABLE:
            raise ImportError(
                "OpenAI SDK is not available. Please install it with 'pip install openai'."
            )

        if model not in VALID_MODELS:
            raise ValueError(f"Invalid model: {model!r}. Supported models: {sorted(VALID_MODELS)}")

        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "DashScope API key must be provided either as a parameter or "
                "through the DASHSCOPE_API_KEY environment variable."
            )

        self.model = model
        self.base_url = (
            base_url
            or os.getenv("QWEN_BASE_URL")
            or DEFAULT_BASE_URL
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
        enable_thinking: Optional[bool] = None,
        reasoning_effort: Optional[str] = None,
        max_tokens: Optional[int] = None,
        preserve_thinking: Optional[bool] = None,
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

        extra_body: Dict[str, Any] = {}
        if enable_thinking is not None:
            # Qwen Cloud uses top-level enable_thinking (not chat_template_kwargs).
            extra_body["enable_thinking"] = enable_thinking
        if preserve_thinking is not None:
            extra_body["preserve_thinking"] = preserve_thinking
        if extra_body:
            kwargs["extra_body"] = extra_body

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
        enable_thinking: Optional[bool] = None,
        reasoning_effort: Optional[str] = None,
        max_tokens: Optional[int] = None,
        preserve_thinking: Optional[bool] = None,
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
            enable_thinking=enable_thinking,
            reasoning_effort=reasoning_effort,
            max_tokens=max_tokens,
            preserve_thinking=preserve_thinking,
        )

    def understand_video(
        self,
        video: VideoInput,
        prompt: str = "Describe what happens in this video.",
        model: Optional[str] = None,
        enable_thinking: Optional[bool] = None,
        reasoning_effort: Optional[str] = None,
        max_tokens: Optional[int] = None,
        preserve_thinking: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Understand video content with a text prompt/instruction."""
        content = [
            {"type": "video_url", "video_url": {"url": self._media_url(video, "video")}},
            {"type": "text", "text": prompt},
        ]
        return self._chat(
            content,
            model=model,
            enable_thinking=enable_thinking,
            reasoning_effort=reasoning_effort,
            max_tokens=max_tokens,
            preserve_thinking=preserve_thinking,
        )

    def understand(
        self,
        image: Optional[Union[ImageInput, List[ImageInput]]] = None,
        video: Optional[VideoInput] = None,
        prompt: str = DEFAULT_UNDERSTAND_PROMPT,
        model: Optional[str] = None,
        enable_thinking: Optional[bool] = None,
        reasoning_effort: Optional[str] = None,
        max_tokens: Optional[int] = None,
        preserve_thinking: Optional[bool] = None,
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
            enable_thinking=enable_thinking,
            reasoning_effort=reasoning_effort,
            max_tokens=max_tokens,
            preserve_thinking=preserve_thinking,
        )

    def chat(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        enable_thinking: Optional[bool] = None,
        reasoning_effort: Optional[str] = None,
        max_tokens: Optional[int] = None,
        preserve_thinking: Optional[bool] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
    ):
        """Multi-turn / tool-calling escape hatch; returns the raw ChatCompletion."""
        model = model or self.model
        kwargs: Dict[str, Any] = {"model": model, "messages": messages}
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        if tools is not None:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice or "auto"

        extra_body: Dict[str, Any] = {}
        if enable_thinking is not None:
            extra_body["enable_thinking"] = enable_thinking
        if preserve_thinking is not None:
            extra_body["preserve_thinking"] = preserve_thinking
        if extra_body:
            kwargs["extra_body"] = extra_body

        if reasoning_effort is not None:
            if reasoning_effort not in VALID_REASONING_EFFORTS:
                raise ValueError(
                    f"Invalid reasoning_effort: {reasoning_effort!r}. "
                    f"Supported values: {sorted(VALID_REASONING_EFFORTS)}"
                )
            kwargs["reasoning_effort"] = reasoning_effort

        return self.client.chat.completions.create(**kwargs)
