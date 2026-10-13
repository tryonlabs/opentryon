"""
Gemini Embedding 2 Adapter (hosted)

``gemini-embedding-2`` (stable, April 2026) is Google's first multimodal embedding
model in the Gemini API: text, images, video, audio and PDF documents are mapped
into **one** embedding space (100+ languages), so you can search a fashion
catalogue by text, by photo, or by a short video / audio clip. Matryoshka output
(128-3072 dims; 768 / 1536 / 3072 recommended, default 3072), automatically
re-normalised when truncated. Same ``GEMINI_API_KEY`` as Nano Banana / Veo / Gemini
understanding. (The older text-only ``gemini-embedding-001`` is a different, incompatible
space and is not exposed here.)

Input limits (per Google's docs): text 8,192 tokens; images up to 6 per request
(PNG / JPEG); audio up to 180 s (MP3 / WAV); video up to 120 s (MP4 / MOV, max 32
frames sampled, audio track ignored); one PDF of up to 6 pages.

Semantics worth knowing:

- **Separate vs aggregated.** Several inputs in one ``contents`` list collapse into ONE
  embedding; wrapping each in its own ``Content`` returns one embedding per input. This
  adapter returns one vector per input by default (matching the other ``embed`` models)
  and offers ``aggregate=True`` for a single combined vector (e.g. title + product photo).
- **No ``task_type``.** Gemini Embedding 2 ignores task types; for **text** you put the task
  in the prompt. This adapter formats it for you: retrieval tasks use
  ``task: search result | query: {q}`` for queries and ``title: none | text: {doc}`` for
  documents; symmetric tasks (classification, clustering, sentence similarity) use
  ``task: {task} | query: {text}`` for everything. Image / audio / video / PDF inputs are
  never prefixed, and text inside an aggregated multimodal embedding is left unprefixed
  (Google advises against prefixing it).
- Embeddings from different models / dims are not comparable; re-embed if you switch.

Reference:
https://ai.google.dev/gemini-api/docs/embeddings

Env:
  GEMINI_API_KEY (required)

Examples:
    >>> from tryon.api.gemini import GeminiEmbeddingAdapter
    >>> adapter = GeminiEmbeddingAdapter()
    >>> out = adapter.embed(image=["boot1.jpg", "boot2.jpg"], query="black leather ankle boots")
    >>> out["scores"]
    >>> adapter.embed(text="Linen shirt", image="shirt.jpg", aggregate=True, output_dimensionality=768)
"""

from __future__ import annotations

import io
import mimetypes
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

from PIL import Image

try:
    from google import genai
    from google.genai import types

    _GENAI_AVAILABLE = True
except ImportError:
    _GENAI_AVAILABLE = False
    genai = None
    types = None

VALID_MODELS = {"gemini-embedding-2"}
DEFAULT_MODEL = "gemini-embedding-2"
MIN_DIM, MAX_DIM = 128, 3072
INLINE_LIMIT_BYTES = 18 * 1024 * 1024
MAX_IMAGES_PER_REQUEST = 6
DEFAULT_BATCH_SIZE = 8

RETRIEVAL_TASKS = {"search result", "question answering", "fact checking", "code retrieval"}
SYMMETRIC_TASKS = {"classification", "clustering", "sentence similarity"}
TASKS = tuple(sorted(RETRIEVAL_TASKS | SYMMETRIC_TASKS))
ROLES = ("document", "query")

_MEDIA_MIME = {
    "image": {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"},
    "audio": {".mp3": "audio/mpeg", ".wav": "audio/wav"},
    "video": {".mp4": "video/mp4", ".mov": "video/quicktime"},
    "pdf": {".pdf": "application/pdf"},
}

Media = Union[str, Path, io.BytesIO, bytes, Image.Image]


def _as_list(value: Optional[Union[Any, Sequence[Any]]]) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def format_text(text: str, task: str, role: str) -> str:
    """Task-prefix ``text`` the way Gemini Embedding 2 expects (text-only inputs)."""
    if task not in TASKS:
        raise ValueError(f"task must be one of {list(TASKS)} (got {task!r}).")
    if role not in ROLES:
        raise ValueError(f"role must be one of {list(ROLES)} (got {role!r}).")
    if task in SYMMETRIC_TASKS:
        return f"task: {task} | query: {text}"
    return f"task: {task} | query: {text}" if role == "query" else f"title: none | text: {text}"


class GeminiEmbeddingAdapter:
    """
    Gemini Embedding 2 (hosted, multimodal).

    Args:
        api_key: Defaults to ``GEMINI_API_KEY``.
        model: ``gemini-embedding-2`` (default).
    """

    def __init__(self, api_key: Optional[str] = None, model: str = DEFAULT_MODEL):
        if not _GENAI_AVAILABLE:
            raise ImportError("Google GenAI SDK is required. Install it with: pip install google-genai")
        if model not in VALID_MODELS:
            raise ValueError(f"Invalid model: {model!r}. Supported models: {sorted(VALID_MODELS)}")
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API key is required. Set GEMINI_API_KEY or pass api_key.")
        self.model = model
        self.client = genai.Client(api_key=self.api_key)

    # -- inputs -----------------------------------------------------------

    @staticmethod
    def _read(source: Media, kind: str):
        """(bytes, mime) for a path / URL / bytes / BytesIO / PIL input, validating the format."""
        mimes = _MEDIA_MIME[kind]
        default = next(iter(mimes.values()))
        if isinstance(source, Image.Image):
            if kind != "image":
                raise ValueError("A PIL image can only be used as an image input.")
            buf = io.BytesIO()
            source.convert("RGB").save(buf, format="PNG")
            return buf.getvalue(), "image/png"
        if isinstance(source, (bytes, bytearray)):
            return bytes(source), default
        if isinstance(source, io.BytesIO):
            source.seek(0)
            return source.read(), default
        text = str(source)
        if text.startswith(("http://", "https://")):
            import requests

            resp = requests.get(text, timeout=120)
            resp.raise_for_status()
            data = resp.content
            ext = Path(text.split("?")[0]).suffix.lower()
        else:
            path = Path(text)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {text}")
            data = path.read_bytes()
            ext = path.suffix.lower()
        if ext not in mimes:
            raise ValueError(f"Unsupported {kind} format {ext or '(none)'!r}; supported: {sorted(mimes)}.")
        return data, mimes[ext]

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
        while str(getattr(getattr(uploaded, "state", None), "name", getattr(uploaded, "state", ""))).endswith("PROCESSING"):
            if time.time() > deadline:
                raise TimeoutError("Timed out waiting for the uploaded file to become ACTIVE.")
            time.sleep(2)
            uploaded = self.client.files.get(name=uploaded.name)
        return types.Part.from_uri(file_uri=uploaded.uri, mime_type=uploaded.mime_type or mime)

    def _media_part(self, source: Media, kind: str):
        data, mime = self._read(source, kind)
        if len(data) > INLINE_LIMIT_BYTES:
            return self._upload(data, mime, mimetypes.guess_extension(mime) or "")
        return types.Part.from_bytes(data=data, mime_type=mime)

    # -- public API ---------------------------------------------------------

    def embed(
        self,
        text: Optional[Union[str, Sequence[str]]] = None,
        image: Optional[Union[Media, Sequence[Media]]] = None,
        audio: Optional[Union[Media, Sequence[Media]]] = None,
        video: Optional[Union[Media, Sequence[Media]]] = None,
        pdf: Optional[Union[Media, Sequence[Media]]] = None,
        query: Optional[str] = None,
        query_image: Optional[Media] = None,
        task: str = "search result",
        role: str = "document",
        output_dimensionality: Optional[int] = None,
        aggregate: bool = False,
        batch_size: int = DEFAULT_BATCH_SIZE,
    ) -> Dict[str, Any]:
        """Embed each input (text -> image -> audio -> video -> pdf), or all together with ``aggregate``.

        Args:
            text: strings; task-prefixed as ``role`` (``document`` / ``query``) for ``task`` -- except when
                ``aggregate`` is combined with media, where text is left unprefixed.
            image / audio / video / pdf: paths, URLs, bytes or PIL (images). Formats: PNG/JPEG, MP3/WAV,
                MP4/MOV, PDF. Large media goes through the Files API automatically.
            query: optional text query; ``scores`` = cosine similarity to every output vector.
            query_image: optional image query (mutually exclusive with ``query``).
            output_dimensionality: 128-3072 (768 / 1536 / 3072 recommended; default 3072).
            aggregate: return ONE embedding for all inputs combined (e.g. title + product photo).
        """
        import numpy as np

        texts = [str(t) for t in _as_list(text)]
        media = (
            [("image", m) for m in _as_list(image)] + [("audio", m) for m in _as_list(audio)]
            + [("video", m) for m in _as_list(video)] + [("pdf", m) for m in _as_list(pdf)]
        )
        if not texts and not media:
            raise ValueError("Provide at least one of text / image / audio / video / pdf.")
        if query and query_image is not None:
            raise ValueError("Pass either query (text) or query_image, not both.")
        if output_dimensionality is not None and not MIN_DIM <= int(output_dimensionality) <= MAX_DIM:
            raise ValueError(f"output_dimensionality must be between {MIN_DIM} and {MAX_DIM}.")
        if int(batch_size) < 1:
            raise ValueError("batch_size must be >= 1.")
        if sum(1 for k, _ in media if k == "image") > MAX_IMAGES_PER_REQUEST and aggregate:
            raise ValueError(f"At most {MAX_IMAGES_PER_REQUEST} images fit in one aggregated embedding.")
        if sum(1 for k, _ in media if k == "pdf") > 1 and aggregate:
            raise ValueError("Only one PDF (up to 6 pages) fits in one aggregated embedding.")
        prefix_text = not (aggregate and media)  # Google: don't task-prefix text inside multimodal embeddings

        text_values = [format_text(t, task, role) if prefix_text else t for t in texts]
        labels = [f"text:{t[:60]}" for t in texts] + [
            f"{k}:{m if isinstance(m, (str, Path)) else '<' + type(m).__name__ + '>'}" for k, m in media
        ]
        config = (
            types.EmbedContentConfig(output_dimensionality=int(output_dimensionality))
            if output_dimensionality is not None else None
        )

        def run(contents: List[Any], expect: int) -> List[List[float]]:
            resp = self.client.models.embed_content(model=self.model, contents=contents, config=config)
            vectors = [list(e.values) for e in (resp.embeddings or [])]
            if len(vectors) != expect:
                raise RuntimeError(f"Expected {expect} embedding(s) from Gemini, got {len(vectors)}.")
            return vectors

        parts_text = [types.Part.from_text(text=t) for t in text_values]
        parts_media = [self._media_part(m, k) for k, m in media]
        if aggregate:
            matrix = run(parts_text + parts_media, 1)
            labels = ["aggregate:" + " + ".join(labels)[:200]]
        else:
            items = [types.Content(parts=[p]) for p in parts_text + parts_media]
            matrix = []
            for i in range(0, len(items), int(batch_size)):
                chunk = items[i:i + int(batch_size)]
                matrix.extend(run(chunk, len(chunk)))
        arr = np.asarray(matrix, dtype="float32")
        arr = arr / np.clip(np.linalg.norm(arr, axis=1, keepdims=True), 1e-12, None)

        result: Dict[str, Any] = {"model": self.model, "kind": "dense", "labels": labels, "embeddings": arr}
        if query or query_image is not None:
            if query:
                q_content = [types.Content(parts=[types.Part.from_text(text=format_text(query, task, "query"))])]
            else:
                q_content = [types.Content(parts=[self._media_part(query_image, "image")])]
            qv = np.asarray(run(q_content, 1), dtype="float32")[0]
            qv = qv / max(float(np.linalg.norm(qv)), 1e-12)
            result["scores"] = (arr @ qv).tolist()
        return result
