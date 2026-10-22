"""
NVIDIA Nemotron 3.5 Embed 1B (hosted NIM + self-hosted OpenAI-compatible server).

Hosted: ``POST https://integrate.api.nvidia.com/v1/embeddings`` with
``nvidia/nemotron-3.5-embed-1b``.

Local: serve ``nvidia/Nemotron-3.5-Embed-1B-BF16`` (or NVFP4) with NeMo Retriever
Embedding NIM / vLLM and point ``NEMOTRON_EMBED_BASE_URL`` at ``http://127.0.0.1:8000/v1``.

Docs:
  https://build.nvidia.com/nvidia/nemotron-3_5-embed-1b
  https://docs.nvidia.com/nim/nemo-retriever/embedding/latest/use-the-api-openai.html
"""

from __future__ import annotations

import base64
import io
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

import numpy as np
import requests
from PIL import Image

try:
    from openai import OpenAI

    _OPENAI_AVAILABLE = True
except ImportError:
    _OPENAI_AVAILABLE = False
    OpenAI = None

from .adapter import _resolve_nvidia_key, DEFAULT_BASE_URL

NEMOTRON_35_EMBED_MODEL = "nvidia/nemotron-3.5-embed-1b"
VALID_MODELS = {NEMOTRON_35_EMBED_MODEL, "nemotron-3.5-embed-1b", "nemotron-3-5-embed-1b"}
VALID_INPUT_TYPES = {"query", "passage"}
VALID_MODALITIES = {"text", "image", "text_image"}

Media = Union[str, Path, io.BytesIO, bytes, Image.Image]


class Nemotron35EmbedAdapter:
    """Nemotron 3.5 Embed 1B — text and document-image embeddings via OpenAI API shape."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = NEMOTRON_35_EMBED_MODEL,
        base_url: Optional[str] = None,
        endpoint: str = "nim",
    ):
        if not _OPENAI_AVAILABLE:
            raise ImportError("OpenAI SDK required. Install: pip install openai")
        serving = (endpoint or "nim").strip().lower()
        if serving not in {"nim", "local"}:
            raise ValueError("endpoint must be 'nim' (hosted) or 'local' (self-hosted NIM/vLLM).")
        self.endpoint = serving
        if serving == "local":
            self.api_key = api_key or os.getenv("NEMOTRON_EMBED_API_KEY") or "EMPTY"
            self.base_url = (
                base_url or os.getenv("NEMOTRON_EMBED_BASE_URL") or "http://127.0.0.1:8000/v1"
            ).rstrip("/")
        else:
            self.api_key = _resolve_nvidia_key(api_key)
            self.base_url = (
                base_url or os.getenv("NVIDIA_API_BASE_URL") or DEFAULT_BASE_URL
            ).rstrip("/")
        key = (model or NEMOTRON_35_EMBED_MODEL).strip()
        self.model = NEMOTRON_35_EMBED_MODEL if key in VALID_MODELS else key
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    @staticmethod
    def _image_data_url(source: Media) -> str:
        if isinstance(source, Image.Image):
            buf = io.BytesIO()
            source.convert("RGB").save(buf, format="JPEG")
            data = buf.getvalue()
            mime = "image/jpeg"
        elif isinstance(source, (bytes, bytearray)):
            data = bytes(source)
            mime = "image/jpeg"
        elif isinstance(source, io.BytesIO):
            source.seek(0)
            data = source.read()
            mime = "image/jpeg"
        else:
            text = str(source)
            if text.startswith(("http://", "https://")):
                return text
            path = Path(text)
            if not path.exists():
                raise FileNotFoundError(f"Image not found: {text}")
            data = path.read_bytes()
            ext = path.suffix.lower()
            mime = "image/png" if ext == ".png" else "image/jpeg"
        b64 = base64.b64encode(data).decode("ascii")
        return f"data:{mime};base64,{b64}"

    def embed(
        self,
        text: Optional[Union[str, Sequence[str]]] = None,
        image: Optional[Union[Media, Sequence[Media]]] = None,
        query: Optional[str] = None,
        query_image: Optional[Media] = None,
        input_type: str = "passage",
        modality: Optional[str] = None,
        dimensions: Optional[int] = None,
        longest_edge: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Embed text and/or images; optional query for cosine scores (like other embed models)."""
        if input_type not in VALID_INPUT_TYPES:
            raise ValueError(f"input_type must be one of {sorted(VALID_INPUT_TYPES)}")
        if modality is not None and modality not in VALID_MODALITIES:
            raise ValueError(f"modality must be one of {sorted(VALID_MODALITIES)}")

        def listify(v):
            if v is None:
                return []
            return v if isinstance(v, (list, tuple)) else [v]

        inputs: List[Any] = []
        labels: List[str] = []
        for t in listify(text):
            inputs.append(str(t))
            labels.append(f"text:{str(t)[:80]}")
        for img in listify(image):
            inputs.append(self._image_data_url(img))
            labels.append("image")

        if not inputs:
            raise ValueError("Provide at least one --text or --image input.")

        body: Dict[str, Any] = {
            "model": self.model,
            "input": inputs if len(inputs) > 1 else inputs[0],
            "input_type": input_type,
        }
        if modality:
            body["modality"] = modality if len(inputs) == 1 else [modality] * len(inputs)
        elif image and not text:
            body["modality"] = "image"
        elif image and text:
            body["modality"] = ["text" if isinstance(x, str) and not x.startswith("data:") else "image" for x in inputs]
        if dimensions is not None:
            body["dimensions"] = int(dimensions)
        if longest_edge is not None:
            body["longest_edge"] = int(longest_edge)

        resp = self.client.embeddings.create(**body)
        vectors = [np.asarray(row.embedding, dtype="float32") for row in resp.data]
        arr = np.stack(vectors, axis=0)
        arr = arr / np.clip(np.linalg.norm(arr, axis=1, keepdims=True), 1e-12, None)

        result: Dict[str, Any] = {
            "model": self.model,
            "kind": "dense",
            "labels": labels,
            "embeddings": arr,
            "endpoint": self.endpoint,
        }

        if query or query_image is not None:
            q_inputs = [query] if query else [self._image_data_url(query_image)]
            q_body = {
                "model": self.model,
                "input": q_inputs[0],
                "input_type": "query",
                "modality": "text" if query else "image",
            }
            q_resp = self.client.embeddings.create(**q_body)
            qv = np.asarray(q_resp.data[0].embedding, dtype="float32")
            qv = qv / max(float(np.linalg.norm(qv)), 1e-12)
            result["scores"] = (arr @ qv).tolist()
        return result
