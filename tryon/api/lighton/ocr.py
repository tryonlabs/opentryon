"""
LightOnOCR-3 -- client for an OpenAI-compatible server you run (vLLM or SGLang).

LightOn publishes no hosted API for LightOnOCR-3, so this adapter talks to your own server.
It needs no torch: pages are rendered locally and sent as base64 images. Start one with::

    vllm serve lightonai/LightOnOCR-3-0.8B --trust-remote-code \
      --default-chat-template-kwargs '{"enable_thinking": false}'

Each page is a ``/v1/chat/completions`` call: an image part followed by the prompt
(``""`` for markdown, ``"grounding"`` for labelled blocks with 0-1000 boxes), with
LightOn's settings ``temperature=0.2``, ``top_p=0.9``.

Env:
  LIGHTONOCR_BASE_URL (default http://127.0.0.1:8000/v1)
  LIGHTONOCR_MODEL    (default lightonai/LightOnOCR-3-0.8B; the name your server exposes)
  LIGHTONOCR_API_KEY  (optional; only if your server requires one)

For in-process Transformers inference use :class:`tryon.models.lightonocr.LightOnOCRLocalAdapter`.

References:
  https://huggingface.co/lightonai/LightOnOCR-3-0.8B
  https://github.com/lightonai/LightOnOCR
"""

from __future__ import annotations

import base64
import io
import os
from typing import Any, Dict, Optional, Sequence, Union

from tryon.ocr import PageInput, load_pages, package_pages

try:
    from openai import OpenAI

    _OPENAI_AVAILABLE = True
except ImportError:
    _OPENAI_AVAILABLE = False
    OpenAI = None

DEFAULT_BASE_URL = "http://127.0.0.1:8000/v1"
DEFAULT_MODEL = "lightonai/LightOnOCR-3-0.8B"
GROUNDING_PROMPT = "grounding"
DEFAULT_MAX_TOKENS = 4096


class LightOnOCRServerAdapter:
    """OpenAI-compatible client for a LightOnOCR-3 server."""

    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None, api_key: Optional[str] = None):
        if not _OPENAI_AVAILABLE:
            raise ImportError("OpenAI SDK required. Install: pip install openai")
        self.base_url = (base_url or os.getenv("LIGHTONOCR_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.model = model or os.getenv("LIGHTONOCR_MODEL") or DEFAULT_MODEL
        self.api_key = api_key or os.getenv("LIGHTONOCR_API_KEY") or "EMPTY"
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    @staticmethod
    def _data_url(page) -> str:
        buf = io.BytesIO()
        page.save(buf, format="PNG")
        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")

    def parse_document(
        self,
        image: PageInput,
        grounding: bool = False,
        pages: Optional[Union[str, Sequence[int]]] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """OCR an image or PDF into markdown (see :meth:`LightOnOCRLocalAdapter.parse_document`)."""
        prompt = GROUNDING_PROMPT if grounding else ""
        limit = int(max_tokens or DEFAULT_MAX_TOKENS)
        raw_pages = []
        for page in load_pages(image, pages):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": [
                    {"type": "image_url", "image_url": {"url": self._data_url(page)}},
                    {"type": "text", "text": prompt},
                ]}],
                max_tokens=limit,
                temperature=0.2,
                top_p=0.9,
            )
            raw_pages.append(response.choices[0].message.content or "")
        return package_pages(self.model, "server", grounding, raw_pages)
