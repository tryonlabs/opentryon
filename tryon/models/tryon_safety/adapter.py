"""
Try-On Safety Classifier Adapter (Genlook, Apache-2.0, local)

``Genlook/tryon-safety-classifier`` decides, from product photos, what a
virtual try-on of that product would show -- *how much skin or sexual content
ends up in the result* -- so a store or app can gate garments **before** they
are rendered onto a shopper's photo. It differs from a generic NSFW detector: a
lingerie flat lay contains no nudity, but its try-on would; a fetish mask on a
mannequin is not explicit but is still a sexual product.

Heads (one prediction per *product*, computed over all its photos):

- ``level``    -- ``ok`` / ``revealing`` / ``lingerie`` / ``adult`` (by severity)
- ``subject``  -- ``human_clothing`` / ``pet`` / ``not_clothing``
- ``swimwear`` -- ``not_swimwear`` / ``regular`` / ``near_micro`` / ``micro``
- ``ravewear`` -- boolean tag (does not change the level)
- ``blocked``  -- ``P(adult) >= adult_threshold`` (0.3 by default); use this rather
  than the top level for a safety gate (catches more adult products for a small
  rise in false blocks)

Variants: ``finetuned`` (default, ~0.9GB, best at catching adult products) and
``frozen`` (~120KB of heads on top of the public SigLIP 2 weights).

Reported (model card, 5-fold cross-validation over 2,596 products): 94.6% four-level
accuracy (finetuned); adult products missed at threshold 0.3: 34 of 534 with 52 false
blocks; lingerie recall 90%. Hardest cases: sheer lingerie vs adult, festival / rave wear.
The right gate depends on your audience (some stores allow ``lingerie``, some block
``revealing``). It classifies **products**, not people. Trained mostly on western
e-commerce photography.

Implementation note: the model repo ships its own ``tryon_safety.py``. Rather than
downloading and executing that file from the Hub, this adapter re-implements the same
small inference path (open_clip SigLIP2 tower + four linear heads, ~40 lines) and only
downloads ``config.json`` and ``model.safetensors`` (safetensors holds tensors, no code).
Weights are pinned to the ``v1.0`` tag by default.

Reference:
https://huggingface.co/Genlook/tryon-safety-classifier

Requirements:
    pip install opentryon[local]
    pip install open_clip_torch safetensors huggingface_hub

Examples:
    >>> from tryon.models.tryon_safety import TryOnSafetyAdapter
    >>> adapter = TryOnSafetyAdapter()
    >>> result = adapter.classify(["front.jpg", "back.jpg"])   # all photos of ONE product
    >>> result["blocked"], result["level"], result["probs"]
"""

from __future__ import annotations

import io
import json
import os
from typing import Any, Dict, List, Optional, Union

from PIL import Image

DEFAULT_REPO = "Genlook/tryon-safety-classifier"
DEFAULT_REVISION = "v1.0"
VARIANTS = ("finetuned", "frozen")

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


class TryOnSafetyAdapter:
    """
    Local product-level try-on safety classifier.

    Args:
        model_id: Hub repo id or a local folder holding ``config.json`` and ``model.safetensors``
            (plus ``frozen/model.safetensors`` for the frozen variant). Defaults to
            ``TRYON_SAFETY_MODEL_ID`` env or ``Genlook/tryon-safety-classifier``.
        variant: ``finetuned`` (default) or ``frozen``.
        revision: Hub revision / tag (default ``v1.0``); ignored for local folders.
        device: defaults to ``cuda`` if available, else ``cpu``.
    """

    def __init__(
        self,
        model_id: Optional[str] = None,
        variant: str = "finetuned",
        revision: Optional[str] = DEFAULT_REVISION,
        device: Optional[str] = None,
    ):
        if variant not in VARIANTS:
            raise ValueError(f"variant must be one of {list(VARIANTS)} (got {variant!r}).")
        try:
            import open_clip
            import torch
            from safetensors.torch import load_file
        except ImportError as exc:
            raise ImportError(
                "The try-on safety classifier needs torch, open_clip and safetensors. Install with:\n"
                "  pip install opentryon[local]\n"
                "  pip install open_clip_torch safetensors huggingface_hub\n"
                f"Original error: {exc}"
            ) from exc
        self._open_clip = open_clip
        self._torch = torch
        self._load_file = load_file
        self.model_id = model_id or os.getenv("TRYON_SAFETY_MODEL_ID") or DEFAULT_REPO
        self.variant = variant
        self.revision = revision
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self._ready = False

    # -- loading ------------------------------------------------------------

    def _fetch(self, name: str, subfolder: Optional[str] = None) -> str:
        if os.path.isdir(self.model_id):
            return os.path.join(self.model_id, subfolder or "", name)
        from huggingface_hub import hf_hub_download

        return hf_hub_download(self.model_id, name, subfolder=subfolder, revision=self.revision)

    def _load(self) -> None:
        if self._ready:
            return
        with open(self._fetch("config.json"), "r", encoding="utf-8") as f:
            self.config = json.load(f)
        if self.variant not in self.config["variants"]:
            raise ValueError(f"Variant {self.variant!r} not in model config: {list(self.config['variants'])}")
        self.cfg = self.config["variants"][self.variant]
        state = self._load_file(self._fetch("model.safetensors", self.cfg.get("subfolder")))

        torch = self._torch
        model, _, self.preprocess = self._open_clip.create_model_and_transforms(self.config["open_clip_name"])
        self.visual = model.visual.eval()
        if self.variant == "finetuned":
            self.visual.load_state_dict({k[len("visual."):]: v.float() for k, v in state.items() if k.startswith("visual.")})
        self.visual = self.visual.to(self.device)
        self.heads = {}
        for name in self.config["heads"]:
            w, b = state[f"heads.{name}.weight"].float(), state[f"heads.{name}.bias"].float()
            lin = torch.nn.Linear(w.shape[1], w.shape[0])
            lin.weight.data, lin.bias.data = w, b
            self.heads[name] = lin.to(self.device).eval()
        self._ready = True

    # -- public API -----------------------------------------------------------

    def classify(
        self,
        image: Union[ImageInput, List[ImageInput]],
        adult_threshold: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Classify **one product** from all of its photos.

        Args:
            image: one or more photos of the same product (more photos -> a steadier score).
            adult_threshold: override the variant's default (0.3) for ``blocked``.

        Returns:
            ``{"model", "variant", "level", "blocked", "adult_threshold", "probs", "subject", "swimwear",
            "ravewear", "n_images"}``.
        """
        images = image if isinstance(image, list) else [image]
        if not images or any(i is None for i in images):
            raise ValueError("At least one product photo is required.")
        if adult_threshold is not None and not 0.0 <= float(adult_threshold) <= 1.0:
            raise ValueError("adult_threshold must be between 0 and 1.")
        pil = [_load_pil(i) for i in images]
        self._load()

        torch = self._torch
        F = torch.nn.functional
        labels = self.config["heads"]
        with torch.no_grad():
            batch = torch.stack([self.preprocess(i) for i in pil]).to(self.device)
            emb = F.normalize(self.visual(batch), dim=-1)
            if self.variant == "finetuned":
                x = emb * self.cfg["embedding_scale"]
                probs = {n: h(x).softmax(-1).mean(0) for n, h in self.heads.items()}
            else:
                x = torch.cat([emb.mean(0), emb.max(0).values])[None]
                probs = {n: h(x).softmax(-1)[0] for n, h in self.heads.items()}
        safety = {k: float(v) for k, v in zip(labels["safety"], probs["safety"])}
        threshold = self.cfg["adult_threshold"] if adult_threshold is None else float(adult_threshold)

        def pick(name: str) -> str:
            return labels[name][int(probs[name].argmax())]

        return {
            "model": self.model_id,
            "variant": self.variant,
            "level": max(safety, key=safety.get),
            "blocked": safety["adult"] >= threshold,
            "adult_threshold": threshold,
            "probs": safety,
            "subject": pick("subject"),
            "swimwear": pick("swim"),
            "ravewear": pick("rave") == "yes",
            "n_images": len(pil),
        }
