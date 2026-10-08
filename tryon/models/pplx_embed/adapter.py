"""
Perplexity pplx-embed-v2-late Local Adapter (open weights, multi-vector)

``pplx-embed-v2-late`` is a pair of multimodal **late-interaction** (ColBERT-
style) retrievers built on Qwen3.5 with bidirectional attention: instead of one
vector per document they emit one 128-d vector per token and score a query
against a document with MaxSim. They retrieve text, images and rendered pages
(no OCR needed) and the 0.6B and 9B variants share an embedding space, so a
0.6B query encoder can search an index built with 9B.

- ``0.6b`` -> ``perplexity-ai/pplx-embed-v2-late-0.6b`` (340M active params)
- ``9b``   -> ``perplexity-ai/pplx-embed-v2-late-9b``   (7.4B active params)

MIT licensed. **No Perplexity-hosted API for v2-late** (Hugging Face lists no
inference provider; Perplexity's hosted Embeddings API serves the v1 /
context-v1 dense models only), so this is a local-only integration. Encode text
and image batches separately -- mixed text+image batches are unsupported.

Reference: https://huggingface.co/perplexity-ai/pplx-embed-v2-late-9b

Requirements:
    pip install opentryon[local]
    pip install "sentence-transformers>=6.0.0" "transformers>=5.4.0"

Examples:
    >>> from tryon.models.pplx_embed import PplxEmbedLateAdapter
    >>> adapter = PplxEmbedLateAdapter(variant="0.6b")
    >>> out = adapter.embed(image=["lookbook_page1.png", "lookbook_page2.png"],
    ...                     query="red wool coat with oversized lapels")
    >>> out["scores"]   # MaxSim per page
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Sequence, Union

VARIANTS = {
    "0.6b": "perplexity-ai/pplx-embed-v2-late-0.6b",
    "9b": "perplexity-ai/pplx-embed-v2-late-9b",
}


def _as_list(value: Optional[Union[Any, Sequence[Any]]]) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def _load_image(item: Any):
    from PIL import Image

    if isinstance(item, Image.Image):
        return item.convert("RGB")
    if isinstance(item, str):
        if item.startswith(("http://", "https://")):
            import io
            import requests

            resp = requests.get(item, timeout=60)
            resp.raise_for_status()
            return Image.open(io.BytesIO(resp.content)).convert("RGB")
        if os.path.exists(item):
            return Image.open(item).convert("RGB")
        raise ValueError(f"Image path does not exist: {item}")
    raise ValueError("Unsupported image input for pplx-embed-v2-late.")


class PplxEmbedLateAdapter:
    """
    Local Sentence-Transformers ``MultiVectorEncoder`` adapter.

    Args:
        variant: ``"0.6b"`` (default) or ``"9b"``.
        model_id: Override the HF repo id / local path. Defaults to
            ``PPLX_EMBED_MODEL_ID`` env or the variant's official repo.
        device: Defaults to ``cuda`` if available, else ``cpu``.
    """

    def __init__(
        self,
        variant: str = "0.6b",
        model_id: Optional[str] = None,
        device: Optional[str] = None,
    ):
        if variant not in VARIANTS:
            raise ValueError(f"Invalid variant: {variant!r}. Supported: {sorted(VARIANTS)}")
        try:
            import torch
            from sentence_transformers import MultiVectorEncoder
        except ImportError as exc:
            raise ImportError(
                "pplx-embed-v2-late needs torch and sentence-transformers>=6.0.0 (MultiVectorEncoder). "
                "Install with:\n"
                "  pip install opentryon[local]\n"
                '  pip install "sentence-transformers>=6.0.0" "transformers>=5.4.0"\n'
                f"Original error: {exc}"
            ) from exc
        self.variant = variant
        self.model_id = model_id or os.getenv("PPLX_EMBED_MODEL_ID") or VARIANTS[variant]
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self._Encoder = MultiVectorEncoder
        self._model = None

    def _load(self):
        if self._model is None:
            self._model = self._Encoder(self.model_id, device=self.device)
        return self._model

    @staticmethod
    def _to_numpy(vecs) -> List[Any]:
        import numpy as np

        out = []
        for v in vecs:
            if hasattr(v, "detach"):
                v = v.detach().float().cpu().numpy()
            out.append(np.asarray(v, dtype="float32"))
        return out

    def embed(
        self,
        text: Optional[Union[str, Sequence[str]]] = None,
        image: Optional[Union[Any, Sequence[Any]]] = None,
        query: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Encode documents as per-token 128-d multi-vectors (one ``(tokens, 128)`` matrix each).

        Args:
            text: passages to index (``encode_document``).
            image: page / photo images to index (paths, URLs or PIL); rendered PDF pages work.
            query: optional text query; if given, ``scores`` holds the MaxSim score of the query
                against every document.
        """
        texts = _as_list(text)
        images = _as_list(image)
        if not texts and not images:
            raise ValueError("Provide at least one text passage or image.")

        model = self._load()
        labels: List[str] = []
        docs: List[Any] = []
        if texts:  # separate batches: mixed text+image is unsupported
            docs += self._to_numpy(model.encode_document(texts))
            labels += [f"text:{t[:60]}" for t in texts]
        if images:
            docs += self._to_numpy(model.encode_document([_load_image(i) for i in images]))
            labels += [f"image:{i if isinstance(i, str) else type(i).__name__}" for i in images]

        result: Dict[str, Any] = {
            "model": self.model_id,
            "kind": "multi_vector",
            "labels": labels,
            "embeddings": docs,
        }
        if query:
            import numpy as np

            q = self._to_numpy(model.encode_query([query]))[0]
            # MaxSim: for each query token take the best document-token match, then sum.
            result["scores"] = [float((q @ d.T).max(axis=1).sum()) for d in docs]
        return result
