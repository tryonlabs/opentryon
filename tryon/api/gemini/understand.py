"""
Gemini 3.8 Flash Understanding Adapter

Adapter for ``gemini-3.8-flash`` ("our most intelligent Flash model", stable
since 2 Sep 2026) through the Gemini API ``generate_content`` surface.
Inputs: text, **images, video, audio and PDF**; output: text. 1,048,576-token
context, 65,536 max output tokens. Thinking is controlled with
``thinking_level`` (``low`` / ``medium`` / ``high``); ``minimal`` is not
supported on this model and returns an error.

Fashion uses: garment attribute extraction, lookbook/video review, reading
care labels and size charts from PDFs/photos, voice-note briefs (audio).

Reference:
https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash
https://ai.google.dev/gemini-api/docs/thinking

Env:
  GEMINI_API_KEY (required) -- same key as Nano Banana / Veo / Omni.

Examples:
    >>> from tryon.api.gemini import GeminiUnderstandAdapter
    >>> adapter = GeminiUnderstandAdapter()
    >>> out = adapter.understand(image="look.jpg", prompt="List garments, colours and fabrics.")
    >>> print(out["text"])
    >>> adapter.understand(video="runway.mp4", prompt="Summarise the collection shown.", thinking_level="low")
"""

from __future__ import annotations

import io
import mimetypes
import os
import tempfile
import time
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from PIL import Image

try:
    from google import genai
    from google.genai import types

    _GENAI_AVAILABLE = True
except ImportError:
    _GENAI_AVAILABLE = False
    genai = None
    types = None

VALID_MODELS = {"gemini-3.8-flash"}
VALID_THINKING_LEVELS = {"low", "medium", "high"}  # "minimal" is rejected by the API
DEFAULT_PROMPT = "Describe what is shown in as much relevant detail as possible."
INLINE_LIMIT_BYTES = 18 * 1024 * 1024  # stay under the ~20MB request cap; larger media goes through the Files API
YOUTUBE_HOSTS = ("youtube.com/", "youtu.be/")

Media = Union[str, Path, io.BytesIO, bytes, Image.Image]


def _is_url(value: Any) -> bool:
    return isinstance(value, str) and value.startswith(("http://", "https://"))


class GeminiUnderstandAdapter:
    """
    Gemini 3.8 Flash multimodal understanding.

    Args:
        api_key: Defaults to ``GEMINI_API_KEY``.
        model: ``gemini-3.8-flash`` (default).
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-3.8-flash"):
        if not _GENAI_AVAILABLE:
            raise ImportError("Google GenAI SDK is required. Install it with: pip install google-genai")
        if model not in VALID_MODELS:
            raise ValueError(f"Invalid model: {model!r}. Supported models: {sorted(VALID_MODELS)}")
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Gemini API key is required. Set GEMINI_API_KEY or pass api_key."
            )
        self.model = model
        self.client = genai.Client(api_key=self.api_key)

    # -- input loading --------------------------------------------------

    @staticmethod
    def _read(source: Media, default_mime: str):
        """Return ``(bytes, mime)`` for a path / URL / bytes / BytesIO / PIL input."""
        if isinstance(source, Image.Image):
            buf = io.BytesIO()
            source.convert("RGB").save(buf, format="PNG")
            return buf.getvalue(), "image/png"
        if isinstance(source, (bytes, bytearray)):
            return bytes(source), default_mime
        if isinstance(source, io.BytesIO):
            source.seek(0)
            return source.read(), default_mime
        text = str(source)
        if _is_url(text):
            import requests

            resp = requests.get(text, timeout=120)
            resp.raise_for_status()
            mime = resp.headers.get("Content-Type", "").split(";")[0].strip()
            return resp.content, mime or mimetypes.guess_type(text.split("?")[0])[0] or default_mime
        path = Path(text)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {text}")
        return path.read_bytes(), mimetypes.guess_type(str(path))[0] or default_mime

    def _upload(self, data: bytes, mime: str, suffix: str):
        """Upload through the Files API and wait until it is ACTIVE; returns a file Part."""
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(data)
            path = tmp.name
        try:
            uploaded = self.client.files.upload(file=path, config={"mime_type": mime})
        finally:
            try:
                os.remove(path)
            except OSError:
                pass
        deadline = time.time() + 600
        while str(getattr(getattr(uploaded, "state", None), "name", getattr(uploaded, "state", ""))).endswith("PROCESSING"):
            if time.time() > deadline:
                raise TimeoutError("Timed out waiting for the uploaded file to become ACTIVE.")
            time.sleep(2)
            uploaded = self.client.files.get(name=uploaded.name)
        return types.Part.from_uri(file_uri=uploaded.uri, mime_type=uploaded.mime_type or mime)

    def _part(self, source: Media, kind: str):
        defaults = {"image": "image/png", "video": "video/mp4", "audio": "audio/mpeg", "pdf": "application/pdf"}
        suffixes = {"image": ".png", "video": ".mp4", "audio": ".mp3", "pdf": ".pdf"}
        if kind == "video" and isinstance(source, str) and any(h in source for h in YOUTUBE_HOSTS):
            return types.Part(file_data=types.FileData(file_uri=source))  # YouTube URLs are read server-side
        if isinstance(source, str) and (
            source.startswith("gs://") or (_is_url(source) and "/files/" in source)
        ):  # already a Cloud Storage / Gemini Files API reference
            return types.Part.from_uri(file_uri=source, mime_type=defaults[kind])
        data, mime = self._read(source, defaults[kind])
        if kind == "pdf":
            mime = "application/pdf"
        if len(data) > INLINE_LIMIT_BYTES:
            return self._upload(data, mime, suffixes[kind])
        return types.Part.from_bytes(data=data, mime_type=mime)

    # -- core call --------------------------------------------------------

    def understand(
        self,
        image: Optional[Union[Media, List[Media]]] = None,
        video: Optional[Union[Media, List[Media]]] = None,
        audio: Optional[Union[Media, List[Media]]] = None,
        pdf: Optional[Union[Media, List[Media]]] = None,
        prompt: str = DEFAULT_PROMPT,
        system: Optional[str] = None,
        thinking_level: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Answer ``prompt`` about any mix of images, videos, audio clips and PDFs.

        Args:
            image / video / audio / pdf: a single input or a list. Paths and URLs are
                read; media over ~18MB goes through the Files API; YouTube URLs are
                passed straight to Gemini.
            thinking_level: ``low`` / ``medium`` / ``high`` (``minimal`` is not supported).
            max_tokens: output cap (model maximum 65,536).

        Returns: ``{"text", "model", "usage"}``.
        """
        if thinking_level is not None and thinking_level not in VALID_THINKING_LEVELS:
            raise ValueError(
                f"thinking_level must be one of {sorted(VALID_THINKING_LEVELS)} "
                f"('minimal' is not supported by {self.model}); got {thinking_level!r}."
            )
        if max_tokens is not None and not 1 <= int(max_tokens) <= 65536:
            raise ValueError("max_tokens must be between 1 and 65536.")

        def listify(v):
            return [] if v is None else (v if isinstance(v, list) else [v])

        parts = (
            [self._part(m, "image") for m in listify(image)]
            + [self._part(m, "video") for m in listify(video)]
            + [self._part(m, "audio") for m in listify(audio)]
            + [self._part(m, "pdf") for m in listify(pdf)]
        )
        if not parts and not prompt:
            raise ValueError("Provide a prompt and/or at least one image, video, audio or pdf input.")
        parts.append(types.Part.from_text(text=prompt))

        config: Dict[str, Any] = {}
        if system:
            config["system_instruction"] = system
        if max_tokens is not None:
            config["max_output_tokens"] = int(max_tokens)
        if thinking_level is not None:
            with warnings.catch_warnings():
                # Older google-genai releases do not list MEDIUM in their ThinkingLevel enum; the value is
                # still sent as-is, so silence the cosmetic "not a valid ThinkingLevel" warning.
                warnings.simplefilter("ignore", UserWarning)
                config["thinking_config"] = types.ThinkingConfig(thinking_level=thinking_level.upper())

        response = self.client.models.generate_content(
            model=self.model,
            contents=[types.Content(role="user", parts=parts)],
            config=types.GenerateContentConfig(**config) if config else None,
        )
        usage = getattr(response, "usage_metadata", None)
        return {
            "text": response.text,
            "model": self.model,
            "usage": usage.model_dump(exclude_none=True) if usage is not None and hasattr(usage, "model_dump") else None,
        }
