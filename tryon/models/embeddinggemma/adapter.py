"""
Google EmbeddingGemma 2 Local Adapter (open weights, multimodal embeddings)

EmbeddingGemma 2 (``google/embeddinggemma-2``, 740M params, Apache-2.0 tag --
the card also links the Gemma terms, so review before commercial use) maps
text, code, images, video and audio into a single shared 768-d space
(Matryoshka-truncatable to 512 / 256 / 128). 8,192-token shared context.

Useful in OpenTryOn for fashion retrieval: embed catalogue photos and garment
descriptions in one space, then search by text *or* by image.

Modality configurations are load options, not separate checkpoints
(``modalities``): text-only 270M, text+image 440M, text+audio 570M, full 740M.
Prompt prefixes (``SearchQuery``, ``Document``, ``Classification``, ...) apply to
text only. Use bfloat16 or float32 -- float16 is not recommended upstream.

Reference: https://huggingface.co/google/embeddinggemma-2

Requirements:
    pip install opentryon[local]
    pip install -U sentence-transformers transformers

Examples:
    >>> from tryon.models.embeddinggemma import EmbeddingGemma2Adapter
    >>> adapter = EmbeddingGemma2Adapter(modalities="text+image")
    >>> out = adapter.embed(text=["red satin evening gown"], image=["dress.jpg"],
    ...                     query="formal red dress")
    >>> out["scores"]   # cosine similarity of the query vs each input
"""

from __future__ import annotations

import io
import os
from typing import Any, Dict, List, Optional, Sequence, Union

DEFAULT_MODEL_ID = "google/embeddinggemma-2"
VALID_DIMS = (768, 512, 256, 128)
MODALITIES = {
    "text": {"vision_config": None, "audio_config": None},
    "text+image": {"audio_config": None},
    "text+audio": {"vision_config": None},
    "full": {},
}
VALID_TASKS = (
    "SearchQuery", "Document", "QuestionAnswering", "FactChecking",
    "CodeRetrieval", "Classification", "Clustering", "SentenceSimilarity",
)


def _as_list(value: Optional[Union[Any, Sequence[Any]]]) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


class EmbeddingGemma2Adapter:
    """
    Local Sentence-Transformers adapter for EmbeddingGemma 2.

    Args:
        model_id: HF repo id / local path. Defaults to ``EMBEDDINGGEMMA_MODEL_ID``
            env or ``google/embeddinggemma-2``.
        modalities: ``"text"``, ``"text+image"``, ``"text+audio"`` or ``"full"``
            (default) -- loads only the encoders you need.
        device: Defaults to best available.
    """

    def __init__(
        self,
        model_id: Optional[str] = None,
        modalities: str = "full",
        device: Optional[str] = None,
    ):
        if modalities not in MODALITIES:
            raise ValueError(f"Invalid modalities: {modalities!r}. Supported: {sorted(MODALITIES)}")
        try:
            import torch  # noqa: F401
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise ImportError(
                "EmbeddingGemma 2 needs torch and sentence-transformers. Install with:\n"
                "  pip install opentryon[local]\n"
                "  pip install -U sentence-transformers transformers\n"
                f"Original error: {exc}"
            ) from exc
        self._ST = SentenceTransformer
        self.model_id = model_id or os.getenv("EMBEDDINGGEMMA_MODEL_ID") or DEFAULT_MODEL_ID
        self.modalities = modalities
        self.device = device
        self._model = None

    def _load(self):
        if self._model is None:
            kwargs: Dict[str, Any] = {"config_kwargs": MODALITIES[self.modalities]}
            if self.device:
                kwargs["device"] = self.device
            self._model = self._ST(self.model_id, **kwargs)
        return self._model

    @staticmethod
    def _truncate(vecs, dim: Optional[int]):
        import numpy as np

        arr = np.asarray(vecs, dtype="float32")
        if dim is not None:
            if dim not in VALID_DIMS:
                raise ValueError(f"dim must be one of {list(VALID_DIMS)} (got {dim}).")
            arr = arr[:, :dim]
            norms = np.linalg.norm(arr, axis=1, keepdims=True)
            arr = arr / np.clip(norms, 1e-12, None)  # re-normalise after truncation
        return arr

    def embed(
        self,
        text: Optional[Union[str, Sequence[str]]] = None,
        image: Optional[Union[Any, Sequence[Any]]] = None,
        audio: Optional[Union[str, Sequence[str]]] = None,
        video: Optional[Union[str, Sequence[str]]] = None,
        query: Optional[str] = None,
        task: str = "Document",
        dim: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Embed each given input (one vector per item, in text -> image -> audio -> video order).

        Args:
            text: strings (prompted with ``task``).
            image / audio / video: file paths or URLs (audio: mono 16 kHz; video sampled at 1 fps).
            query: optional search query; if given, ``scores`` holds the cosine similarity of
                the query (``SearchQuery`` prompt) against every input.
            task: text prompt name (default ``Document``).
            dim: Matryoshka truncation (768 / 512 / 256 / 128), re-normalised.
        """
        if task not in VALID_TASKS:
            raise ValueError(f"task must be one of {list(VALID_TASKS)} (got {task!r}).")
        texts = _as_list(text)
        media = (
            [("image", i) for i in _as_list(image)]
            + [("audio", a) for a in _as_list(audio)]
            + [("video", v) for v in _as_list(video)]
        )
        if not texts and not media:
            raise ValueError("Provide at least one of text / image / audio / video.")
        need = {"image": "text+image", "audio": "text+audio"}
        for kind, _ in media:
            if kind in need and self.modalities not in (need[kind], "full"):
                raise ValueError(
                    f"{kind} input needs modalities='{need[kind]}' or 'full' (loaded: '{self.modalities}')."
                )
            if kind == "video" and self.modalities != "full":
                raise ValueError("video input needs modalities='full'.")

        import numpy as np

        model = self._load()
        labels: List[str] = []
        chunks = []
        if texts:
            chunks.append(model.encode(texts, prompt_name=task))
            labels += [f"text:{t[:60]}" for t in texts]
        for kind, item in media:
            ref = item if isinstance(item, str) else f"<{type(item).__name__}>"
            chunks.append(model.encode({kind: item}))
            labels.append(f"{kind}:{ref}")

        matrix = self._truncate(np.concatenate([np.atleast_2d(np.asarray(c)) for c in chunks], axis=0), dim)
        result: Dict[str, Any] = {
            "model": self.model_id,
            "kind": "dense",
            "labels": labels,
            "embeddings": matrix,
        }
        if query:
            q = self._truncate(np.atleast_2d(model.encode(query, prompt_name="SearchQuery")), dim)
            result["scores"] = (matrix @ q[0]).tolist()  # unit vectors -> cosine
        return result
