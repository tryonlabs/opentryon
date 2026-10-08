"""
Anthropic Claude (Haiku 5.5) Vision API Adapter

Adapter for Claude Haiku 5.5 through Anthropic's first-party Messages API
(``anthropic`` SDK). Text + image input, text output, 1M context, 128K max
output. General purpose -- useful for fashion tasks (garment attribute
extraction, care-label OCR, outfit descriptions, QC of generated images) as
well as any other image understanding.

Reference:
https://platform.claude.com/docs/en/models/haiku-5-5/overview
https://platform.claude.com/docs/en/build-with-claude/effort

Models:
- claude-haiku-5-5: Released 2026-10-07. Adaptive thinking on by default;
  ``effort`` (low / medium / high / xhigh / max, default medium) controls depth.
  ``thinking={"type": "disabled"}`` is accepted at ``high`` effort or below
  (400 at xhigh/max). ``temperature`` / ``top_p`` / ``top_k`` must be omitted
  (a non-default value returns 400), so this adapter does not expose them.
  Images only -- no video input.

Env:
  ANTHROPIC_API_KEY (required)
  ANTHROPIC_BASE_URL (optional, SDK-native override)

Examples:
    >>> from tryon.api.claude import ClaudeUnderstandAdapter
    >>> adapter = ClaudeUnderstandAdapter()
    >>> result = adapter.understand("garment.jpg", prompt="List the fabric, colour and fit.")
    >>> print(result["text"])
"""

from __future__ import annotations

import base64
import io
import mimetypes
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import requests
from PIL import Image

try:
    import anthropic

    _ANTHROPIC_AVAILABLE = True
except ImportError:
    _ANTHROPIC_AVAILABLE = False
    anthropic = None

VALID_MODELS = {"claude-haiku-5-5"}
VALID_EFFORTS = {"low", "medium", "high", "xhigh", "max"}
DEFAULT_MAX_TOKENS = 4096
DEFAULT_UNDERSTAND_PROMPT = "Describe what is shown in as much relevant detail as possible."

ImageInput = Union[str, Path, io.BytesIO, bytes, Image.Image]


class ClaudeUnderstandAdapter:
    """
    Adapter for Claude Haiku 5.5 via the Anthropic Messages API.

    Args:
        api_key: Anthropic API key. Defaults to ``ANTHROPIC_API_KEY``.
        model: Model id. Defaults to ``"claude-haiku-5-5"``.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-haiku-5-5"):
        if not _ANTHROPIC_AVAILABLE:
            raise ImportError(
                "Anthropic SDK is not available. Please install it with 'pip install anthropic'."
            )
        if model not in VALID_MODELS:
            raise ValueError(f"Invalid model: {model!r}. Supported models: {sorted(VALID_MODELS)}")

        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Anthropic API key must be provided either as a parameter or "
                "through the ANTHROPIC_API_KEY environment variable."
            )
        self.model = model
        self.client = anthropic.Anthropic(api_key=self.api_key)

    # -- input loading --------------------------------------------------

    @staticmethod
    def _image_block(image: ImageInput) -> Dict[str, Any]:
        """Build an Anthropic image content block (URL passthrough or base64)."""
        if isinstance(image, (str, Path)):
            image_str = str(image)
            if image_str.startswith(("http://", "https://")):
                return {"type": "image", "source": {"type": "url", "url": image_str}}

        if isinstance(image, Image.Image):
            buf = io.BytesIO()
            image.convert("RGB").save(buf, format="JPEG", quality=92)
            raw, media_type = buf.getvalue(), "image/jpeg"
        elif isinstance(image, (bytes, bytearray)):
            raw, media_type = bytes(image), "image/png"
        elif isinstance(image, io.BytesIO):
            image.seek(0)
            raw, media_type = image.read(), "image/png"
        else:
            path = Path(str(image))
            if not path.exists():
                raise FileNotFoundError(f"File not found: {path}")
            raw = path.read_bytes()
            media_type = mimetypes.guess_type(str(path))[0] or "image/png"

        if media_type not in {"image/jpeg", "image/png", "image/gif", "image/webp"}:
            # Re-encode anything exotic (bmp/tiff/...) so the API accepts it.
            buf = io.BytesIO()
            Image.open(io.BytesIO(raw)).convert("RGB").save(buf, format="PNG")
            raw, media_type = buf.getvalue(), "image/png"
        return {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": base64.b64encode(raw).decode("utf-8"),
            },
        }

    # -- core call --------------------------------------------------------

    def _chat(
        self,
        content: List[Dict[str, Any]],
        system: Optional[str],
        effort: Optional[str],
        thinking: bool,
        max_tokens: int,
    ) -> Dict[str, Any]:
        if effort is not None and effort not in VALID_EFFORTS:
            raise ValueError(f"Invalid effort: {effort!r}. Supported values: {sorted(VALID_EFFORTS)}")
        if not thinking and effort in {"xhigh", "max"}:
            raise ValueError(
                "thinking cannot be disabled at xhigh/max effort (API returns 400); "
                "lower the effort to high or below."
            )

        kwargs: Dict[str, Any] = {
            "model": self.model,
            "max_tokens": int(max_tokens),
            "messages": [{"role": "user", "content": content}],
        }
        if system:
            kwargs["system"] = system
        if not thinking:
            kwargs["thinking"] = {"type": "disabled"}
        if effort is not None:
            # Sent via extra_body so older SDKs without `output_config` still work.
            kwargs["extra_body"] = {"output_config": {"effort": effort}}

        message = self.client.messages.create(**kwargs)
        text = "".join(b.text for b in message.content if getattr(b, "type", None) == "text")
        thinking_text = "".join(
            getattr(b, "thinking", "") or "" for b in message.content if getattr(b, "type", None) == "thinking"
        )
        usage = getattr(message, "usage", None)
        return {
            "text": text,
            "reasoning": thinking_text or None,
            "model": message.model,
            "stop_reason": message.stop_reason,
            "usage": usage.model_dump() if usage is not None and hasattr(usage, "model_dump") else None,
        }

    # -- public API ---------------------------------------------------------

    def understand_image(
        self,
        image: Union[ImageInput, List[ImageInput]],
        prompt: str = DEFAULT_UNDERSTAND_PROMPT,
        system: Optional[str] = None,
        effort: Optional[str] = None,
        thinking: bool = True,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> Dict[str, Any]:
        """Understand one or more images with a text prompt/instruction."""
        images = image if isinstance(image, list) else [image]
        content: List[Dict[str, Any]] = [self._image_block(img) for img in images]
        content.append({"type": "text", "text": prompt})
        return self._chat(content, system, effort, thinking, max_tokens)

    def understand(
        self,
        image: Optional[Union[ImageInput, List[ImageInput]]] = None,
        prompt: str = DEFAULT_UNDERSTAND_PROMPT,
        system: Optional[str] = None,
        effort: Optional[str] = None,
        thinking: bool = True,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> Dict[str, Any]:
        """CLI-friendly entry point. ``image`` is optional (text-only works);
        video is not supported by the Messages API."""
        if image is None:
            if not prompt:
                raise ValueError("Provide a prompt and/or an image.")
            return self._chat([{"type": "text", "text": prompt}], system, effort, thinking, max_tokens)
        return self.understand_image(
            image, prompt=prompt, system=system, effort=effort, thinking=thinking, max_tokens=max_tokens
        )
