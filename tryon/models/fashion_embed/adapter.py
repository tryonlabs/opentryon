"""
Fashion retrieval embedding adapters (open weights, local)

Domain-specific encoders fine-tuned on fashion / e-commerce catalogue data,
exposed through the ``embed`` service. They map product photos and (for the
text-capable models) text into one 768-d space, so you can search a catalogue
by description, by photo, or by "more like this".

Models (``variant``):

- ``marqo-fashionsiglip`` -- ``Marqo/marqo-fashionSigLIP`` (ViT-B/16 SigLIP,
  ~0.2B, Apache-2.0): image + text. Marqo reports up to +57% MRR / recall over
  FashionCLIP (vendor-reported).
- ``moda-fashion-distilled`` -- ``HopitAI/moda-fashion-distilled`` (MIT): MODA's
  image-to-image checkpoint, distilled from a 3-model ensemble. **Image-only**
  here: the card documents no text usage (MODA text search is a different
  model). Reports 67.63 fine R@1 on LookBench vs 63.84 for FashionSigLIP
  (vendor-reported).
- ``moda-pro-lite`` -- ``HopitAI/moda-pro-lite`` (213M, Apache-2.0): MODA's
  text-to-image encoder (bare encoder; the "Plus" multi-view recipe is not
  wired).
- ``zooclaw-fashionsiglip2`` -- ``srpone/zooclaw-fashionsiglip2`` (SigLIP2-base,
  ~375M, Apache-2.0, 384px images / 64 text tokens): image + text; benchmarks are
  in arXiv 2606.27708.

All vectors are L2-normalised (cosine = dot product).

Requirements:
    pip install opentryon[local]
    pip install open_clip_torch        # Marqo / MODA
    pip install -U transformers        # ZooClaw (already in opentryon[local])

Examples:
    >>> from tryon.models.fashion_embed import FashionOpenCLIPAdapter
    >>> adapter = FashionOpenCLIPAdapter(variant="marqo-fashionsiglip")
    >>> out = adapter.embed(image=["boot1.jpg", "boot2.jpg"], query="black leather ankle boots")
    >>> out["scores"]
"""

from __future__ import annotations

import io
import os
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from PIL import Image

OPEN_CLIP_VARIANTS: Dict[str, Tuple[str, bool]] = {
    # variant -> (hub id, supports text)
    "marqo-fashionsiglip": ("Marqo/marqo-fashionSigLIP", True),
    "moda-fashion-distilled": ("HopitAI/moda-fashion-distilled", False),
    "moda-pro-lite": ("HopitAI/moda-pro-lite", True),
}
ZOOCLAW_ID = "srpone/zooclaw-fashionsiglip2"
ZOOCLAW_TEXT_TOKENS = 64

ImageInput = Union[str, io.BytesIO, bytes, Image.Image]


def _as_list(value: Optional[Union[Any, Sequence[Any]]]) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def _load_pil(image: ImageInput) -> Image.Image:
    if isinstance(image, Image.Image):
        return image.convert("RGB")
    if isinstance(image, (bytes, bytearray)):
        return Image.open(io.BytesIO(bytes(image))).convert("RGB")
    if hasattr(image, "read"):
        image.seek(0)
        return Image.open(image).convert("RGB")
    text = str(image)
    if text.startswith(("http://", "https://")):
        import requests

        resp = requests.get(text, timeout=60)
        resp.raise_for_status()
        return Image.open(io.BytesIO(resp.content)).convert("RGB")
    if not os.path.exists(text):
        raise ValueError(f"Image path does not exist: {text}")
    return Image.open(text).convert("RGB")


def _label(image: Any) -> str:
    return f"image:{image}" if isinstance(image, str) else f"image:<{type(image).__name__}>"


class _FashionEmbedBase:
    """Shared ``embed`` flow: encode texts / images, optionally score against a query."""

    supports_text = True
    model_id = ""

    def _encode_texts(self, texts: List[str]):  # -> torch.Tensor (n, d), L2-normalised
        raise NotImplementedError

    def _encode_images(self, images: List[Image.Image]):  # -> torch.Tensor (n, d), L2-normalised
        raise NotImplementedError

    def embed(
        self,
        text: Optional[Union[str, Sequence[str]]] = None,
        image: Optional[Union[ImageInput, Sequence[ImageInput]]] = None,
        query: Optional[str] = None,
        query_image: Optional[ImageInput] = None,
    ) -> Dict[str, Any]:
        """One vector per input (text first, then images, in the order given).

        Args:
            text: product titles / descriptions (text-capable models only).
            image: product photos (paths, URLs or PIL).
            query: optional text query; ``scores`` = cosine similarity to every input.
            query_image: optional image query ("more like this"); mutually exclusive with ``query``.
        """
        import numpy as np

        texts = [str(t) for t in _as_list(text)]
        images = _as_list(image)
        if not texts and not images:
            raise ValueError("Provide at least one text or image to embed.")
        if query and query_image is not None:
            raise ValueError("Pass either query (text) or query_image, not both.")
        if (texts or query) and not self.supports_text:
            raise ValueError(
                f"{self.model_id} is an image-only checkpoint here; use --image / --query-image, or a "
                "text-capable model (marqo-fashionsiglip, moda-pro-lite, zooclaw-fashionsiglip2)."
            )

        labels: List[str] = []
        chunks = []
        if texts:
            chunks.append(self._encode_texts(texts))
            labels += [f"text:{t[:60]}" for t in texts]
        if images:
            chunks.append(self._encode_images([_load_pil(i) for i in images]))
            labels += [_label(i) for i in images]
        matrix = np.concatenate([c.detach().float().cpu().numpy() for c in chunks], axis=0)

        result: Dict[str, Any] = {"model": self.model_id, "kind": "dense", "labels": labels, "embeddings": matrix}
        if query:
            q = self._encode_texts([query]).detach().float().cpu().numpy()[0]
            result["scores"] = (matrix @ q).tolist()
        elif query_image is not None:
            q = self._encode_images([_load_pil(query_image)]).detach().float().cpu().numpy()[0]
            result["scores"] = (matrix @ q).tolist()
        return result


class FashionOpenCLIPAdapter(_FashionEmbedBase):
    """
    open_clip adapter for Marqo-FashionSigLIP and the MODA checkpoints.

    Args:
        variant: ``marqo-fashionsiglip`` (default), ``moda-fashion-distilled`` or ``moda-pro-lite``.
        model_id: Override the Hugging Face repo id / local path.
        device: Defaults to ``cuda`` if available, else ``cpu``.
    """

    def __init__(self, variant: str = "marqo-fashionsiglip", model_id: Optional[str] = None, device: Optional[str] = None):
        if variant not in OPEN_CLIP_VARIANTS:
            raise ValueError(f"Invalid variant: {variant!r}. Supported: {sorted(OPEN_CLIP_VARIANTS)}")
        try:
            import open_clip
            import torch
        except ImportError as exc:
            raise ImportError(
                "Fashion embeddings need torch and open_clip. Install with:\n"
                "  pip install opentryon[local]\n"
                "  pip install open_clip_torch\n"
                f"Original error: {exc}"
            ) from exc
        self.variant = variant
        hub_id, self.supports_text = OPEN_CLIP_VARIANTS[variant]
        self.model_id = model_id or hub_id
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self._open_clip = open_clip
        self._torch = torch
        self._model = None
        self._preprocess = None
        self._tokenizer = None

    def _load(self):
        if self._model is None:
            hub = f"hf-hub:{self.model_id}"
            model, _, preprocess = self._open_clip.create_model_and_transforms(hub)
            self._model = model.to(self.device).eval()
            self._preprocess = preprocess
            self._tokenizer = self._open_clip.get_tokenizer(hub) if self.supports_text else None
        return self._model

    def _norm(self, x):
        return self._torch.nn.functional.normalize(x.float(), dim=-1)

    def _encode_texts(self, texts: List[str]):
        model = self._load()
        tokens = self._tokenizer(texts).to(self.device)
        with self._torch.no_grad():
            return self._norm(model.encode_text(tokens))

    def _encode_images(self, images: List[Image.Image]):
        model = self._load()
        batch = self._torch.stack([self._preprocess(i) for i in images]).to(self.device)
        with self._torch.no_grad():
            return self._norm(model.encode_image(batch))


class ZooClawFashionSigLIP2Adapter(_FashionEmbedBase):
    """
    Transformers adapter for ZooClaw-FashionSigLIP2 (SigLIP2-base fine-tune).

    Args:
        model_id: Override the repo id / local path (default ``srpone/zooclaw-fashionsiglip2``).
        device: Defaults to ``cuda`` if available, else ``cpu``.
    """

    def __init__(self, model_id: Optional[str] = None, device: Optional[str] = None):
        try:
            import torch
            from transformers import AutoModel, AutoProcessor
        except ImportError as exc:
            raise ImportError(
                "ZooClaw-FashionSigLIP2 needs torch and transformers. Install with: pip install opentryon[local]\n"
                f"Original error: {exc}"
            ) from exc
        self.model_id = model_id or ZOOCLAW_ID
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self._torch = torch
        self._AutoModel = AutoModel
        self._AutoProcessor = AutoProcessor
        self._model = None
        self._processor = None

    def _load(self):
        if self._model is None:
            self._processor = self._AutoProcessor.from_pretrained(self.model_id)
            self._model = self._AutoModel.from_pretrained(self.model_id).to(self.device).eval()
        return self._model

    def _norm(self, x):
        return self._torch.nn.functional.normalize(x.float(), dim=-1)

    def _encode_texts(self, texts: List[str]):
        model = self._load()
        inputs = self._processor(
            text=texts, padding="max_length", max_length=ZOOCLAW_TEXT_TOKENS, truncation=True, return_tensors="pt"
        ).to(self.device)
        with self._torch.no_grad():
            return self._norm(model.get_text_features(**inputs))

    def _encode_images(self, images: List[Image.Image]):
        model = self._load()
        inputs = self._processor(images=images, return_tensors="pt").to(self.device)
        with self._torch.no_grad():
            return self._norm(model.get_image_features(**inputs))
