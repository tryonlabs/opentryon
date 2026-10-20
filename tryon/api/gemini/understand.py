"""
Gemini multimodal understanding (Gemini API ``generate_content`` + optional Interactions).

Models:
- ``gemini-3.8-flash`` — Flash multimodal (image, video, audio, PDF → text).
- ``gemini-4-argon`` — flagship reasoning; unified 1M context, long decode, agentic video.

Env:
  GEMINI_API_KEY (required) — same key as Nano Banana / Veo / Omni / TTS / embeddings.

References:
https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash
https://ai.google.dev/gemini-api/docs/models/gemini-4-argon
https://ai.google.dev/gemini-api/docs/generate-content/latest-model
https://ai.google.dev/gemini-api/docs/long-decode
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

VALID_MODELS = {"gemini-3.8-flash", "gemini-4-argon"}
ARGON_MODEL = "gemini-4-argon"
FLASH_MAX_OUTPUT = 65_536
ARGON_MAX_OUTPUT = 1_048_576
ARGON_HTTP_TIMEOUT_MS = 20 * 60 * 1000  # 20 minutes per Google migration guidance
VALID_THINKING_LEVELS = {"low", "medium", "high"}
VALID_VIDEO_PROCESSING = {"static", "agentic"}
DEFAULT_PROMPT = "Describe what is shown in as much relevant detail as possible."
INLINE_LIMIT_BYTES = 18 * 1024 * 1024
YOUTUBE_HOSTS = ("youtube.com/", "youtu.be/")

Media = Union[str, Path, io.BytesIO, bytes, Image.Image]


def _is_url(value: Any) -> bool:
    return isinstance(value, str) and value.startswith(("http://", "https://"))


def _is_argon(model: str) -> bool:
    return model == ARGON_MODEL


class GeminiUnderstandAdapter:
    """Gemini API multimodal understanding."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-3.8-flash"):
        if not _GENAI_AVAILABLE:
            raise ImportError("Google GenAI SDK is required. Install: pip install 'google-genai>=2.30.1'")
        if model not in VALID_MODELS:
            raise ValueError(f"Invalid model: {model!r}. Supported models: {sorted(VALID_MODELS)}")
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API key is required. Set GEMINI_API_KEY or pass api_key.")
        self.model = model
        http_options = None
        if _is_argon(model):
            http_options = types.HttpOptions(timeout=ARGON_HTTP_TIMEOUT_MS)
        self.client = genai.Client(api_key=self.api_key, http_options=http_options)

    @staticmethod
    def _validate_max_tokens(model: str, max_tokens: Optional[int]) -> None:
        if max_tokens is None:
            return
        mt = int(max_tokens)
        cap = ARGON_MAX_OUTPUT if _is_argon(model) else FLASH_MAX_OUTPUT
        if not 1 <= mt <= cap:
            raise ValueError(f"max_tokens must be between 1 and {cap} for {model}.")

    @staticmethod
    def _read(source: Media, default_mime: str):
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
        while str(getattr(getattr(uploaded, "state", None), "name", getattr(uploaded, "state", ""))).endswith(
            "PROCESSING"
        ):
            if time.time() > deadline:
                raise TimeoutError("Timed out waiting for the uploaded file to become ACTIVE.")
            time.sleep(2)
            uploaded = self.client.files.get(name=uploaded.name)
        return uploaded

    def _part(
        self,
        source: Media,
        kind: str,
        *,
        video_processing: Optional[str] = None,
    ):
        defaults = {"image": "image/png", "video": "video/mp4", "audio": "audio/mpeg", "pdf": "application/pdf"}
        suffixes = {"image": ".png", "video": ".mp4", "audio": ".mp3", "pdf": ".pdf"}
        media_processing = None
        if kind == "video" and video_processing and video_processing != "static":
            if video_processing not in VALID_VIDEO_PROCESSING:
                raise ValueError(
                    f"video_processing must be one of {sorted(VALID_VIDEO_PROCESSING)}; got {video_processing!r}."
                )
            if video_processing == "agentic":
                media_processing = types.MediaProcessing.AGENTIC

        if kind == "video" and isinstance(source, str) and any(h in source for h in YOUTUBE_HOSTS):
            fd = types.FileData(file_uri=source)
            return types.Part(file_data=fd, media_processing=media_processing)
        if isinstance(source, str) and (
            source.startswith("gs://") or (_is_url(source) and "/files/" in source)
        ):
            return types.Part(
                file_data=types.FileData(file_uri=source, mime_type=defaults[kind]),
                media_processing=media_processing,
            )
        data, mime = self._read(source, defaults[kind])
        if kind == "pdf":
            mime = "application/pdf"
        if len(data) > INLINE_LIMIT_BYTES:
            uploaded = self._upload(data, mime, suffixes[kind])
            return types.Part(
                file_data=types.FileData(file_uri=uploaded.uri, mime_type=uploaded.mime_type or mime),
                media_processing=media_processing,
            )
        return types.Part(
            inline_data=types.Blob(data=data, mime_type=mime),
            media_processing=media_processing,
        )

    def _thinking_config(self, thinking_level: Optional[str], model: str) -> Optional[types.ThinkingConfig]:
        level = thinking_level
        if level is None and _is_argon(model):
            level = "medium"
        if level is None:
            return None
        if level not in VALID_THINKING_LEVELS:
            raise ValueError(
                f"thinking_level must be one of {sorted(VALID_THINKING_LEVELS)} "
                f"('minimal' is not supported by {model}); got {level!r}."
            )
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            return types.ThinkingConfig(thinking_level=level.upper())

    @staticmethod
    def _interaction_text(interaction: Any) -> str:
        chunks: List[str] = []
        for step in getattr(interaction, "steps", None) or []:
            if getattr(step, "type", None) != "model_output":
                continue
            for content in getattr(step, "content", None) or []:
                if getattr(content, "type", None) == "text" and getattr(content, "text", None):
                    chunks.append(content.text)
        return "".join(chunks)

    def _understand_interactions(
        self,
        *,
        prompt: str,
        system: Optional[str],
        thinking_level: Optional[str],
        max_tokens: Optional[int],
        poll_interval: float,
    ) -> Dict[str, Any]:
        """Long-running text understanding via Interactions API (Argon background / long decode)."""
        out_limit = int(max_tokens) if max_tokens is not None else 262_144
        if out_limit <= 65_536:
            raise ValueError(
                "background Interactions long decode requires --max-tokens greater than 65536 "
                "(or omit --background and use generateContent with automatic continuation)."
            )
        gen_cfg: Dict[str, Any] = {"max_output_tokens": out_limit}
        level = thinking_level or ("medium" if _is_argon(self.model) else None)
        if level:
            gen_cfg["thinking_level"] = level
        body: Dict[str, Any] = {
            "model": self.model,
            "input": prompt,
            "background": True,
            "store": True,
            "generation_config": gen_cfg,
        }
        if system:
            body["system_instruction"] = system
        interaction = self.client.interactions.create(**body)
        while getattr(interaction, "status", None) in ("in_progress", "queued"):
            time.sleep(poll_interval)
            interaction = self.client.interactions.get(interaction.id)
        status = getattr(interaction, "status", None)
        if status not in ("completed", None):
            raise RuntimeError(
                f"Gemini interaction ended with status {status!r}. "
                "Raise --max-tokens or lower --thinking-level and retry."
            )
        text = self._interaction_text(interaction)
        usage = getattr(interaction, "usage", None)
        return {
            "text": text,
            "model": self.model,
            "usage": usage.model_dump(exclude_none=True) if usage is not None and hasattr(usage, "model_dump") else usage,
            "interaction_id": getattr(interaction, "id", None),
            "status": status,
        }

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
        video_processing: str = "static",
        background: bool = False,
        poll_interval: float = 5.0,
    ) -> Dict[str, Any]:
        """Answer ``prompt`` about images, videos, audio clips and/or PDFs."""
        self._validate_max_tokens(self.model, max_tokens)

        def listify(v):
            return [] if v is None else (v if isinstance(v, list) else [v])

        has_media = any(listify(image) or listify(video) or listify(audio) or listify(pdf))
        if not has_media and not (prompt or "").strip():
            raise ValueError("Provide a prompt and/or at least one image, video, audio or pdf input.")

        if background:
            if not _is_argon(self.model):
                raise ValueError("--background long decode is only supported for gemini-4-argon.")
            if has_media:
                raise ValueError(
                    "Interactions background mode is text-only today. Omit --background for multimodal inputs "
                    "(generateContent uses automatic continuation for long decode)."
                )
            return self._understand_interactions(
                prompt=prompt,
                system=system,
                thinking_level=thinking_level,
                max_tokens=max_tokens,
                poll_interval=poll_interval,
            )

        if video_processing != "static" and not _is_argon(self.model):
            raise ValueError("--video-processing agentic is only supported for gemini-4-argon.")

        parts = (
            [self._part(m, "image") for m in listify(image)]
            + [
                self._part(m, "video", video_processing=video_processing)
                for m in listify(video)
            ]
            + [self._part(m, "audio") for m in listify(audio)]
            + [self._part(m, "pdf") for m in listify(pdf)]
        )
        parts.append(types.Part.from_text(text=prompt))

        config_kwargs: Dict[str, Any] = {}
        if system:
            config_kwargs["system_instruction"] = system
        if max_tokens is not None:
            config_kwargs["max_output_tokens"] = int(max_tokens)
        elif _is_argon(self.model):
            config_kwargs["max_output_tokens"] = 65_536
        thinking = self._thinking_config(thinking_level, self.model)
        if thinking is not None:
            config_kwargs["thinking_config"] = thinking
        if _is_argon(self.model):
            config_kwargs["automatic_continuation"] = True

        response = self.client.models.generate_content(
            model=self.model,
            contents=[types.Content(role="user", parts=parts)],
            config=types.GenerateContentConfig(**config_kwargs) if config_kwargs else None,
        )
        usage = getattr(response, "usage_metadata", None)
        return {
            "text": response.text,
            "model": self.model,
            "usage": usage.model_dump(exclude_none=True) if usage is not None and hasattr(usage, "model_dump") else None,
        }
