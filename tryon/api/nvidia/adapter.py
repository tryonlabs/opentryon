"""
NVIDIA NIM multimodal understanding (Path A).

Hosted OpenAI-compatible chat on ``https://integrate.api.nvidia.com/v1``.
Same ``NVIDIA_API_KEY`` as Cosmos 3 Generator.

Models:
- ``nvidia/nemotron-3-nano-omni-30b-a3b-reasoning`` — image, video, audio, text
- ``nvidia/cosmos3-nano-reasoner`` — physical-world image/video VLM

Docs:
  https://docs.api.nvidia.com/nim/reference/nvidia-nemotron-3-nano-omni-30b-a3b-reasoning
  https://build.nvidia.com/nvidia/cosmos3-nano-reasoner
  https://build.nvidia.com/models

Examples:
    >>> from tryon.api.nvidia import NemotronOmniUnderstandAdapter
    >>> adapter = NemotronOmniUnderstandAdapter()
    >>> print(adapter.understand(image="garment.jpg", prompt="Describe this outfit.")["text"])
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

DEFAULT_BASE_URL = "https://integrate.api.nvidia.com/v1"

NEMOTRON_OMNI_MODEL = "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning"
COSMOS3_REASONER_MODEL = "nvidia/cosmos3-nano-reasoner"

NEMOTRON_ALIASES = {
    "nemotron-omni": NEMOTRON_OMNI_MODEL,
    "nemotron-3-nano-omni": NEMOTRON_OMNI_MODEL,
    NEMOTRON_OMNI_MODEL: NEMOTRON_OMNI_MODEL,
}
REASONER_ALIASES = {
    "cosmos3-reasoner": COSMOS3_REASONER_MODEL,
    "cosmos3-nano-reasoner": COSMOS3_REASONER_MODEL,
    COSMOS3_REASONER_MODEL: COSMOS3_REASONER_MODEL,
}

VIDEO_MIME_OVERRIDES = {"flv": "x-flv", "3gp": "3gpp"}
AUDIO_MIME_OVERRIDES = {"mp3": "mpeg", "m4a": "mp4", "oga": "ogg"}

DEFAULT_UNDERSTAND_PROMPT = "Describe what is shown in as much relevant detail as possible."
REASONER_THINKING_PREFIX = (
    "Answer the question using the following format: Your reasoning. "
    "Write your final answer immediately after the tag.\n\n"
)

ImageInput = Union[str, Path, io.BytesIO, bytes, Image.Image]
VideoInput = Union[str, Path, io.BytesIO, bytes]
AudioInput = Union[str, Path, io.BytesIO, bytes]


def _resolve_nvidia_key(api_key: Optional[str]) -> str:
    key = api_key or os.getenv("NVIDIA_API_KEY")
    if not key:
        raise ValueError(
            "NVIDIA API key is required. Set NVIDIA_API_KEY "
            "(https://build.nvidia.com)."
        )
    return key


def _load_bytes(source, default_ext: str):
    """Return ``(raw_bytes, file_extension)`` for path/URL/bytes/BytesIO/PIL."""
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


def _pass_or_data_uri(
    source,
    kind: str,
    default_ext: str,
    mime_prefix: str,
    mime_overrides: Optional[Dict[str, str]] = None,
) -> str:
    if isinstance(source, (str, Path)):
        source_str = str(source)
        if source_str.startswith("http://") or source_str.startswith("https://"):
            return source_str
        if source_str.startswith("data:"):
            return source_str
    data, ext = _load_bytes(source, default_ext=default_ext)
    mime = (mime_overrides or {}).get(ext, ext)
    if kind == "image" and ext in {"jpg", "jpeg"}:
        mime = "jpeg"
    return f"data:{mime_prefix}/{mime};base64,{base64.b64encode(data).decode('utf-8')}"


class _NvidiaChatUnderstandAdapter:
    """Shared OpenAI-compatible NIM chat client for understand models."""

    default_model: str = NEMOTRON_OMNI_MODEL
    aliases: Dict[str, str] = NEMOTRON_ALIASES
    supports_audio: bool = False

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        if not _OPENAI_AVAILABLE:
            raise ImportError(
                "OpenAI SDK is not available. Please install it with 'pip install openai'."
            )

        self.api_key = _resolve_nvidia_key(api_key)
        self.model = self._resolve_model(model or self.default_model)
        self.base_url = (
            base_url or os.getenv("NVIDIA_API_BASE_URL") or DEFAULT_BASE_URL
        ).rstrip("/")
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def _resolve_model(self, model: str) -> str:
        key = (model or "").strip()
        resolved = self.aliases.get(key, key)
        if resolved not in self.aliases.values() and resolved not in self.aliases:
            raise ValueError(
                f"Invalid model: {model!r}. Supported: {sorted(set(self.aliases))}"
            )
        return self.aliases.get(resolved, resolved)

    def _chat(
        self,
        content: List[Dict[str, Any]],
        model: Optional[str] = None,
        enable_thinking: Optional[bool] = None,
        reasoning_budget: Optional[int] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
    ) -> Dict[str, Any]:
        resolved = self._resolve_model(model) if model else self.model
        kwargs: Dict[str, Any] = {
            "model": resolved,
            "messages": [{"role": "user", "content": content}],
        }
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        if temperature is not None:
            kwargs["temperature"] = temperature
        if top_p is not None:
            kwargs["top_p"] = top_p

        extra_body: Dict[str, Any] = {}
        if enable_thinking is not None:
            extra_body["chat_template_kwargs"] = {"enable_thinking": bool(enable_thinking)}
        if reasoning_budget is not None:
            extra_body["reasoning_budget"] = reasoning_budget
        if extra_body:
            kwargs["extra_body"] = extra_body

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
        **kwargs: Any,
    ) -> Dict[str, Any]:
        return self.understand(image=image, prompt=prompt, **kwargs)

    def understand_video(
        self,
        video: VideoInput,
        prompt: str = "Describe what happens in this video.",
        **kwargs: Any,
    ) -> Dict[str, Any]:
        return self.understand(video=video, prompt=prompt, **kwargs)

    def understand(
        self,
        image: Optional[Union[ImageInput, List[ImageInput]]] = None,
        video: Optional[VideoInput] = None,
        audio: Optional[AudioInput] = None,
        prompt: str = DEFAULT_UNDERSTAND_PROMPT,
        model: Optional[str] = None,
        enable_thinking: Optional[bool] = None,
        reasoning_budget: Optional[int] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
    ) -> Dict[str, Any]:
        has_media = image is not None or video is not None
        if self.supports_audio:
            has_media = has_media or audio is not None
        elif audio is not None:
            raise ValueError(f"{self.__class__.__name__} does not accept `audio`.")
        if not has_media:
            needed = "`image` or `video`"
            if self.supports_audio:
                needed = "`image`, `video`, or `audio`"
            raise ValueError(f"Provide at least one of {needed}.")

        if enable_thinking is None and self.supports_audio:
            enable_thinking = True

        content: List[Dict[str, Any]] = []
        if image is not None:
            images = image if isinstance(image, list) else [image]
            content.extend(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": _pass_or_data_uri(img, "image", "png", "image"),
                    },
                }
                for img in images
            )
        if video is not None:
            content.append(
                {
                    "type": "video_url",
                    "video_url": {
                        "url": _pass_or_data_uri(
                            video, "video", "mp4", "video", VIDEO_MIME_OVERRIDES
                        ),
                    },
                }
            )
        if audio is not None:
            content.append(
                {
                    "type": "audio_url",
                    "audio_url": {
                        "url": _pass_or_data_uri(
                            audio, "audio", "wav", "audio", AUDIO_MIME_OVERRIDES
                        ),
                    },
                }
            )
        text = prompt
        if enable_thinking and not self.supports_audio:
            # Cosmos Reasoner: hosted UI documents a prompt-side reasoning hint.
            if REASONER_THINKING_PREFIX not in (prompt or ""):
                text = REASONER_THINKING_PREFIX + (prompt or DEFAULT_UNDERSTAND_PROMPT)
        content.append({"type": "text", "text": text})

        think_kw = enable_thinking if self.supports_audio else None
        return self._chat(
            content,
            model=model,
            enable_thinking=think_kw,
            reasoning_budget=reasoning_budget if self.supports_audio else None,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
        )


class NemotronOmniUnderstandAdapter(_NvidiaChatUnderstandAdapter):
    """Nemotron 3 Nano Omni — image / video / audio / text understand via NIM."""

    default_model = NEMOTRON_OMNI_MODEL
    aliases = NEMOTRON_ALIASES
    supports_audio = True


class Cosmos3ReasonerAdapter(_NvidiaChatUnderstandAdapter):
    """Cosmos 3 Reasoner nano — physical-world image/video understand via NIM."""

    default_model = COSMOS3_REASONER_MODEL
    aliases = REASONER_ALIASES
    supports_audio = False
