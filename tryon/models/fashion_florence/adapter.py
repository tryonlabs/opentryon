"""
Fashion Florence Local Adapter (open weights, MIT)

``anushreeberlia/fashion-florence`` is a LoRA fine-tune of Microsoft's
Florence-2-large (0.77B parameters, LoRA merged into the base weights) trained
on ~78k Marqo/iMaterialist examples. Given a single clothing image it returns
structured fashion tags as JSON:

======================  ==============================================================
``category``            one of ``top``, ``bottom``, ``dress``, ``layer``, ``shoes``, ``accessory``
``primary_color``       dominant colour, e.g. ``"navy blue"``
``material``            fabric / material, e.g. ``"cotton"``
``style_tags``          list of style descriptors, e.g. ``["casual", "minimalist"]``
======================  ==============================================================

Use it for cheap, deterministic, self-hosted catalogue tagging instead of a
hosted VLM. Reported results on 3,915 held-out iMaterialist examples (model
card): 100% JSON parse rate, 89.5% category accuracy, 52.7% colour and 42.6%
material exact-match (near-synonyms such as "navy" vs "navy blue" count as
misses), style-tag macro F1 0.888. Shoes and accessories are the weak classes
(few test examples). The authors' paper (arXiv 2605.09827) reports higher
category / material accuracy on a different test set -- measure on your own
catalogue before relying on it.

Runs with ``trust_remote_code=True`` (Florence-2 ships custom modelling code).
That code is tied to older transformers releases: it works with the 4.4x line
pinned by ``opentryon[local]`` and may break on much newer transformers.
CPU works (slow); a GPU uses float16.

Reference:
https://huggingface.co/anushreeberlia/fashion-florence
https://arxiv.org/abs/2605.09827

Requirements:
    pip install opentryon[local]

Examples:
    >>> from tryon.models.fashion_florence import FashionFlorenceAdapter
    >>> adapter = FashionFlorenceAdapter()
    >>> out = adapter.understand("dress.jpg")
    >>> out["tags"]
    {'category': 'dress', 'primary_color': 'navy blue', 'material': 'cotton', 'style_tags': ['casual']}
"""

from __future__ import annotations

import io
import json
import os
import re
from typing import Any, Dict, List, Optional, Union

from PIL import Image

DEFAULT_MODEL_ID = "anushreeberlia/fashion-florence"
DEFAULT_PROMPT = "Analyze this clothing item image and return structured fashion tags as JSON."
CATEGORIES = ("top", "bottom", "dress", "layer", "shoes", "accessory")

ImageInput = Union[str, io.BytesIO, bytes, Image.Image]


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


def parse_tags(text: str) -> Optional[Dict[str, Any]]:
    """Parse the model's JSON output; tolerate surrounding text. Returns ``None`` if no JSON object is found."""
    candidates = [text.strip()]
    match = re.search(r"\{.*\}", text, re.S)
    if match:
        candidates.append(match.group(0))
    for cand in candidates:
        try:
            data = json.loads(cand)
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(data, dict):
            return data
    return None


class FashionFlorenceAdapter:
    """
    Local adapter for the Fashion Florence tagger.

    Args:
        model_id: HF repo id / local path. Defaults to ``FASHION_FLORENCE_MODEL_ID`` env or
            ``anushreeberlia/fashion-florence``.
        device: ``cuda`` / ``cpu``. Defaults to ``cuda`` if available, else ``cpu``.
    """

    def __init__(self, model_id: Optional[str] = None, device: Optional[str] = None):
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoProcessor
        except ImportError as exc:
            raise ImportError(
                "Fashion Florence needs torch and transformers. Install with: pip install opentryon[local]\n"
                f"Original error: {exc}"
            ) from exc
        self._torch = torch
        self._AutoModel = AutoModelForCausalLM
        self._AutoProcessor = AutoProcessor
        self.model_id = model_id or os.getenv("FASHION_FLORENCE_MODEL_ID") or DEFAULT_MODEL_ID
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.dtype = torch.float16 if str(self.device).startswith("cuda") else torch.float32
        self._model = None
        self._processor = None

    def _load(self):
        if self._model is None:
            self._model = self._AutoModel.from_pretrained(
                self.model_id, torch_dtype=self.dtype, trust_remote_code=True
            ).to(self.device)
            self._model.eval()
            self._processor = self._AutoProcessor.from_pretrained(self.model_id, trust_remote_code=True)
        return self._model

    def _tag_one(self, image: Image.Image, prompt: str, max_new_tokens: int, num_beams: int) -> str:
        model = self._load()
        inputs = self._processor(text=prompt, images=image, return_tensors="pt").to(self.device, self.dtype)
        with self._torch.no_grad():
            generated_ids = model.generate(
                input_ids=inputs["input_ids"],
                pixel_values=inputs["pixel_values"],
                max_new_tokens=int(max_new_tokens),
                num_beams=int(num_beams),
            )
        return self._processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

    def understand(
        self,
        image: Union[ImageInput, List[ImageInput]],
        prompt: Optional[str] = None,
        max_new_tokens: int = 256,
        num_beams: int = 3,
    ) -> Dict[str, Any]:
        """Tag one image (flat result) or several (``{"results": [...]}``).

        Each result is ``{"tags": {...} | None, "raw": "<model text>"}``; ``tags`` is ``None`` only if the
        output contained no JSON object. ``prompt`` overrides the default tagging instruction (the fine-tune
        expects the default; changing it may degrade the JSON schema).
        """
        images = image if isinstance(image, list) else [image]
        if not images or any(i is None for i in images):
            raise ValueError("At least one image is required.")
        if int(max_new_tokens) < 1 or int(num_beams) < 1:
            raise ValueError("max_new_tokens and num_beams must be >= 1.")
        use_prompt = prompt or DEFAULT_PROMPT
        results = []
        for item in images:
            raw = self._tag_one(_load_pil(item), use_prompt, max_new_tokens, num_beams)
            results.append({
                "image": item if isinstance(item, str) else f"<{type(item).__name__}>",
                "tags": parse_tags(raw),
                "raw": raw,
            })
        if len(results) == 1:
            single = results[0]
            return {"model": self.model_id, "tags": single["tags"], "raw": single["raw"]}
        return {"model": self.model_id, "results": results}
