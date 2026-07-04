"""
Kimi (Moonshot AI) Vision API Adapter

Adapter for Moonshot AI's Kimi K2.6 and K2.7 Code models via the Kimi
Platform API, which is fully compatible with the OpenAI SDK/API format.
These models are natively multimodal (text + image + video) and are
general-purpose -- not limited to the fashion domain -- so this adapter can
be used to understand garment photos and runway/lookbook videos as well as
documents, UI screenshots, product photography, or any other visual content.

Reference:
https://platform.kimi.ai/docs/overview
https://platform.kimi.ai/docs/guide/kimi-k2-6-quickstart
https://platform.kimi.ai/docs/guide/kimi-k2-7-code-quickstart
https://platform.kimi.ai/docs/guide/use-kimi-vision-model

Models:
- kimi-k2.6: General-purpose multimodal model. Supports toggling "thinking"
  mode on/off. 256K context.
- kimi-k2.7-code: Coding-focused multimodal model built on K2.6. Always runs
  with thinking enabled (the API rejects requests that try to disable it).
- kimi-k2.7-code-highspeed: Same capabilities as kimi-k2.7-code with faster
  token throughput.

Notes on sampling parameters:
    K2.5/K2.6/K2.7-code fix `temperature`, `top_p`, `n`, `presence_penalty`,
    and `frequency_penalty` server-side -- passing non-default values raises
    an API error. This adapter therefore does not expose those knobs; only
    `thinking` and `max_tokens` are configurable.

Examples:
    Image understanding:
        >>> from tryon.api.kimi import KimiUnderstandAdapter
        >>> adapter = KimiUnderstandAdapter()  # uses kimi-k2.6 by default
        >>> result = adapter.understand_image("garment.jpg", prompt="Describe this outfit.")
        >>> print(result["text"])

    Video understanding:
        >>> result = adapter.understand_video(
        ...     "runway_clip.mp4",
        ...     prompt="Summarize the styling and garments shown in this video.",
        ... )

    Coding-oriented variant (still multimodal):
        >>> adapter = KimiUnderstandAdapter(model="kimi-k2.7-code")
        >>> result = adapter.understand_image("ui_mockup.png", prompt="Write the HTML/CSS for this design.")
"""

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

DEFAULT_BASE_URL = "https://api.moonshot.ai/v1"

VALID_MODELS = {"kimi-k2.6", "kimi-k2.7-code", "kimi-k2.7-code-highspeed", "kimi-k2.5"}
# These models reject requests that try to disable "thinking" mode.
THINKING_LOCKED_MODELS = {"kimi-k2.7-code", "kimi-k2.7-code-highspeed"}

# Kimi's video_url data URIs use these subtype names (mostly the file
# extension, with a couple of overrides for MIME-incompatible extensions).
VIDEO_MIME_OVERRIDES = {"flv": "x-flv", "3gp": "3gpp"}

DEFAULT_SYSTEM_PROMPT = "You are Kimi, a helpful multimodal assistant."
DEFAULT_UNDERSTAND_PROMPT = "Describe what is shown in as much relevant detail as possible."

ImageInput = Union[str, Path, io.BytesIO, bytes, Image.Image]
VideoInput = Union[str, Path, io.BytesIO, bytes]


class KimiUnderstandAdapter:
    """
    Adapter for Moonshot AI's Kimi vision models (K2.6 / K2.7 Code) via the
    OpenAI-compatible Kimi Platform API.

    Args:
        api_key (str, optional): Moonshot API key. Defaults to the
            `MOONSHOT_API_KEY` environment variable.
        model (str, optional): Default model id used when a call doesn't
            override it. One of `VALID_MODELS`. Defaults to `"kimi-k2.6"`.
        base_url (str, optional): Base URL for the Kimi API. Defaults to the
            `KIMI_BASE_URL` environment variable or
            `"https://api.moonshot.ai/v1"`.

    Examples:
        >>> adapter = KimiUnderstandAdapter()
        >>> adapter = KimiUnderstandAdapter(model="kimi-k2.7-code")
        >>> adapter = KimiUnderstandAdapter(api_key="sk-...", model="kimi-k2.6")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "kimi-k2.6",
        base_url: Optional[str] = None,
    ):
        if not _OPENAI_AVAILABLE:
            raise ImportError(
                "OpenAI SDK is not available. Please install it with 'pip install openai'."
            )

        if model not in VALID_MODELS:
            raise ValueError(f"Invalid model: {model!r}. Supported models: {sorted(VALID_MODELS)}")

        self.api_key = api_key or os.getenv("MOONSHOT_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Moonshot API key must be provided either as a parameter or "
                "through the MOONSHOT_API_KEY environment variable."
            )

        self.model = model
        self.base_url = base_url or os.getenv("KIMI_BASE_URL", DEFAULT_BASE_URL)
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
        return f"data:image/{ext};base64,{base64.b64encode(data).decode('utf-8')}"

    def _video_to_data_uri(self, video: VideoInput) -> str:
        data, ext = self._load_bytes(video, default_ext="mp4")
        mime_ext = VIDEO_MIME_OVERRIDES.get(ext, ext)
        return f"data:video/{mime_ext};base64,{base64.b64encode(data).decode('utf-8')}"

    def _upload_video(self, video: VideoInput) -> str:
        """Upload a video to Moonshot storage and return an `ms://<file_id>` URL.

        Recommended by Kimi's docs for large videos (the inline base64 path
        is limited by the ~100MB total request body size) or videos that will
        be referenced multiple times.
        """
        data, ext = self._load_bytes(video, default_ext="mp4")
        file_obj = self.client.files.create(file=(f"video.{ext}", data), purpose="video")
        return f"ms://{file_obj.id}"

    # -- core call --------------------------------------------------------

    def _chat(
        self,
        content: List[Dict[str, Any]],
        model: Optional[str] = None,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        thinking: Optional[bool] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        model = model or self.model
        if model not in VALID_MODELS:
            raise ValueError(f"Invalid model: {model!r}. Supported models: {sorted(VALID_MODELS)}")

        kwargs: Dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content},
            ],
        }
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens

        if thinking is not None:
            if model in THINKING_LOCKED_MODELS and not thinking:
                raise ValueError(f"{model} does not support disabling thinking mode.")
            kwargs["extra_body"] = {"thinking": {"type": "enabled" if thinking else "disabled"}}

        completion = self.client.chat.completions.create(**kwargs)
        message = completion.choices[0].message
        return {
            "text": message.content,
            "reasoning": getattr(message, "reasoning_content", None),
            "model": completion.model,
            "usage": completion.usage.model_dump() if completion.usage else None,
        }

    # -- public API ---------------------------------------------------------

    def understand_image(
        self,
        image: Union[ImageInput, List[ImageInput]],
        prompt: str = DEFAULT_UNDERSTAND_PROMPT,
        model: Optional[str] = None,
        thinking: Optional[bool] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Understand one or more images with a text prompt/instruction.

        Args:
            image: A single image or list of images. Each may be a file
                path, URL, PIL Image, raw bytes, or BytesIO. Formats:
                png, jpeg, webp, gif.
            prompt: Question/instruction about the image(s).
            model: Override the adapter's default model for this call.
            thinking: Force-enable/disable Kimi's thinking mode (only
                supported by kimi-k2.6; kimi-k2.7-code always thinks).
            max_tokens: Maximum output tokens (server default: 32768).

        Returns:
            dict with keys `text`, `reasoning`, `model`, `usage`.
        """
        images = image if isinstance(image, list) else [image]
        content = [
            {"type": "image_url", "image_url": {"url": self._image_to_data_uri(img)}} for img in images
        ]
        content.append({"type": "text", "text": prompt})
        return self._chat(content, model=model, thinking=thinking, max_tokens=max_tokens)

    def understand_video(
        self,
        video: VideoInput,
        prompt: str = "Describe what happens in this video.",
        model: Optional[str] = None,
        thinking: Optional[bool] = None,
        max_tokens: Optional[int] = None,
        use_file_upload: Optional[bool] = None,
        max_inline_mb: float = 20.0,
    ) -> Dict[str, Any]:
        """
        Understand video content with a text prompt/instruction.

        Args:
            video: File path, URL, raw bytes, or BytesIO. Formats: mp4,
                mpeg, mov, avi, x-flv, mpg, webm, wmv, 3gpp.
            prompt: Question/instruction about the video.
            model: Override the adapter's default model for this call.
            thinking: Force-enable/disable Kimi's thinking mode.
            max_tokens: Maximum output tokens (server default: 32768).
            use_file_upload: Upload the video to Moonshot storage first
                (`ms://` reference) instead of inlining as base64. Defaults
                to auto: enabled for videos larger than `max_inline_mb`.
            max_inline_mb: Size threshold (MB) above which the video is
                uploaded instead of inlined. Ignored if `use_file_upload`
                is explicitly set.

        Returns:
            dict with keys `text`, `reasoning`, `model`, `usage`.
        """
        data, ext = self._load_bytes(video, default_ext="mp4")
        size_mb = len(data) / (1024 * 1024)
        if use_file_upload is None:
            use_file_upload = size_mb > max_inline_mb

        if use_file_upload:
            file_obj = self.client.files.create(file=(f"video.{ext}", data), purpose="video")
            video_url = f"ms://{file_obj.id}"
        else:
            mime_ext = VIDEO_MIME_OVERRIDES.get(ext, ext)
            video_url = f"data:video/{mime_ext};base64,{base64.b64encode(data).decode('utf-8')}"

        content = [
            {"type": "video_url", "video_url": {"url": video_url}},
            {"type": "text", "text": prompt},
        ]
        return self._chat(content, model=model, thinking=thinking, max_tokens=max_tokens)

    def understand(
        self,
        image: Optional[Union[ImageInput, List[ImageInput]]] = None,
        video: Optional[VideoInput] = None,
        prompt: str = DEFAULT_UNDERSTAND_PROMPT,
        model: Optional[str] = None,
        thinking: Optional[bool] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Single entry point for CLI/uniform usage: pass `image` and/or
        `video` (at least one is required). Mirrors `understand_image` /
        `understand_video` but lets both be combined in one call.
        """
        if image is None and video is None:
            raise ValueError("Provide at least one of `image` or `video`.")

        content: List[Dict[str, Any]] = []
        if image is not None:
            images = image if isinstance(image, list) else [image]
            content.extend(
                {"type": "image_url", "image_url": {"url": self._image_to_data_uri(img)}} for img in images
            )
        if video is not None:
            content.append({"type": "video_url", "video_url": {"url": self._video_to_data_uri(video)}})
        content.append({"type": "text", "text": prompt})

        return self._chat(content, model=model, thinking=thinking, max_tokens=max_tokens)

    def chat(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        thinking: Optional[bool] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
    ):
        """
        Escape hatch for full multi-turn conversations / tool calling, e.g.
        the "watch_video_clip" agentic pattern from Kimi's docs. Returns the
        raw OpenAI SDK `ChatCompletion` object (not the simplified dict from
        `understand*`) so callers can inspect `message.tool_calls`, etc.
        """
        model = model or self.model
        kwargs: Dict[str, Any] = {"model": model, "messages": messages}
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        if tools is not None:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice or "auto"
        if thinking is not None:
            if model in THINKING_LOCKED_MODELS and not thinking:
                raise ValueError(f"{model} does not support disabling thinking mode.")
            kwargs["extra_body"] = {"thinking": {"type": "enabled" if thinking else "disabled"}}
        return self.client.chat.completions.create(**kwargs)
