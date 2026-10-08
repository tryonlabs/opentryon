"""
Liquid AI d1 (open-weight "System One" decision models) Local Adapter

``d1`` models are not chat models and write no text. Given a *state* (text,
JSON, images and/or audio) and named typed *questions* (``noul`` yes/no,
``choice``, ``score``) they return calibrated probabilities in one forward pass
(``output_tokens`` is always 0). Good fits for OpenTryOn: garment attribute
classification, try-on/generation QC gating, moderation and routing.

Variants (``variant`` / ``model_id``):
- ``d1-3B``        -- ``LiquidAI/d1-3B``: 3.12B, text + images (SigLIP2 NaFlex
  vision tower), 32K context, bfloat16, ``transformers>=5.14``.
- ``d1-omni-600M`` -- ``LiquidAI/d1-omni-600M``: 587M, text + images + speech
  (one 16 kHz mono clip, <=30 s), 16K context, float16, ``transformers>=5.15``.
  Images and audio cannot be passed together.

License: LFM Open License v1.0 (``lfm1.0``) -- review before commercial use.

Reference:
https://huggingface.co/LiquidAI/d1-3B
https://huggingface.co/LiquidAI/d1-omni-600M

Requirements:
    pip install opentryon[local]
    pip install "transformers>=5.15" torchvision pillow soundfile
This repo's shared ``opentryon[local]`` pin is older (transformers==4.42.4);
use a separate env, exactly as for Limite / Ternary Bonsai.

Examples:
    >>> from tryon.models.liquid_d1 import LiquidD1Adapter
    >>> adapter = LiquidD1Adapter(variant="d1-3B")
    >>> out = adapter.decide(
    ...     questions={"neckline": {"type": "choice", "instructions": "Neckline style?",
    ...                              "criteria": {"v-neck": "V shaped", "crew": "round, high"}}},
    ...     image="dress.jpg",
    ... )
    >>> out["answers"]["neckline"]["choice"]
"""

from __future__ import annotations

import io
import os
from typing import Any, Dict, List, Optional, Union

from PIL import Image

from tryon.decision import Questions, load_questions, load_state

VARIANTS = {
    "d1-3B": "LiquidAI/d1-3B",
    "d1-omni-600M": "LiquidAI/d1-omni-600M",
}
# Per-variant dtype recommended by the model cards (CPU always float32).
_DTYPES = {"d1-3B": "bfloat16", "d1-omni-600M": "float16"}
MAX_AUDIO_SECONDS = 30
AUDIO_SAMPLE_RATE = 16000

ImageInput = Union[str, io.BytesIO, bytes, Image.Image]


def _load_pil(image: ImageInput) -> Image.Image:
    if isinstance(image, Image.Image):
        return image.convert("RGB")
    if isinstance(image, (bytes, bytearray)):
        return Image.open(io.BytesIO(bytes(image))).convert("RGB")
    if hasattr(image, "read"):
        image.seek(0)
        return Image.open(image).convert("RGB")
    if isinstance(image, str):
        if image.startswith(("http://", "https://")):
            import requests

            resp = requests.get(image, timeout=60)
            resp.raise_for_status()
            return Image.open(io.BytesIO(resp.content)).convert("RGB")
        if os.path.exists(image):
            return Image.open(image).convert("RGB")
        raise ValueError(f"Image path does not exist: {image}")
    raise ValueError("Unsupported image input for Liquid d1.")


def _load_audio(audio: Any):
    """16 kHz mono clip as int16 numpy array (path via soundfile, or passthrough array)."""
    import numpy as np

    if isinstance(audio, str):
        if not os.path.exists(audio):
            raise ValueError(f"Audio path does not exist: {audio}")
        try:
            import soundfile as sf
        except ImportError as exc:
            raise ImportError("Reading audio files needs `pip install soundfile`.") from exc
        data, sr = sf.read(audio, dtype="int16", always_2d=True)
        data = data.mean(axis=1).astype("int16")
        if sr != AUDIO_SAMPLE_RATE:
            raise ValueError(
                f"d1-omni-600M expects 16 kHz mono audio; {audio} is {sr} Hz. "
                "Resample first (e.g. ffmpeg -i in.wav -ar 16000 -ac 1 out.wav)."
            )
        return data[: MAX_AUDIO_SECONDS * AUDIO_SAMPLE_RATE]
    arr = np.asarray(audio)
    if arr.ndim != 1:
        raise ValueError("audio array must be 1-D (mono, 16 kHz).")
    return arr[: MAX_AUDIO_SECONDS * AUDIO_SAMPLE_RATE]


class LiquidD1Adapter:
    """
    Local Hugging Face Transformers adapter for Liquid AI d1 decision models.

    Args:
        variant: ``"d1-3B"`` (default) or ``"d1-omni-600M"``.
        model_id: Override the HF repo id / local path. Defaults to
            ``LIQUID_D1_MODEL_ID`` env or the variant's official repo.
        device: ``cuda`` / ``mps`` / ``cpu``. Defaults to best available.
    """

    def __init__(
        self,
        variant: str = "d1-3B",
        model_id: Optional[str] = None,
        device: Optional[str] = None,
    ):
        if variant not in VARIANTS:
            raise ValueError(f"Invalid variant: {variant!r}. Supported: {sorted(VARIANTS)}")
        try:
            import torch
            import transformers
            from transformers import AutoModel
        except ImportError as exc:
            raise ImportError(
                "Liquid d1 local inference requires torch and a recent transformers. Install with:\n"
                "  pip install opentryon[local]\n"
                '  pip install "transformers>=5.15" torchvision pillow soundfile\n'
                f"Original error: {exc}"
            ) from exc

        min_major_minor = (5, 14) if variant == "d1-3B" else (5, 15)
        try:
            major, minor = (int(p) for p in transformers.__version__.split(".")[:2])
        except ValueError:
            major, minor = min_major_minor
        if (major, minor) < min_major_minor:
            raise ImportError(
                f"{variant} needs transformers>={min_major_minor[0]}.{min_major_minor[1]} "
                f"(found {transformers.__version__}). Use a separate environment; the shared "
                "opentryon[local] pin is older."
            )

        self.variant = variant
        self.model_id = model_id or os.getenv("LIQUID_D1_MODEL_ID") or VARIANTS[variant]
        if device is None:
            if torch.cuda.is_available():
                device = "cuda"
            elif getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
                device = "mps"
            else:
                device = "cpu"
        self.device = device
        dtype_name = "float32" if device == "cpu" else _DTYPES[variant]
        self.dtype = getattr(torch, dtype_name)
        self._AutoModel = AutoModel
        self._model = None

    def _load(self):
        if self._model is None:
            self._model = self._AutoModel.from_pretrained(
                self.model_id, trust_remote_code=True, dtype=self.dtype
            ).to(self.device)
            self._model.eval()
        return self._model

    def decide(
        self,
        questions: Questions,
        state: Optional[Any] = None,
        image: Optional[Union[ImageInput, List[ImageInput]]] = None,
        audio: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Answer ``questions`` about the state (text/JSON) and/or image(s)/audio.

        Returns ``{"model", "answers", "usage"}`` where each answer carries
        ``choice``/``score``/``noul`` plus ``probabilities`` / ``confidence``.
        """
        qs = load_questions(questions)
        st = load_state(state)
        if image is not None and audio is not None:
            raise ValueError("Pass either image or audio, not both (d1-omni limitation).")
        if audio is not None and self.variant != "d1-omni-600M":
            raise ValueError("audio input is only supported by d1-omni-600M.")
        if st in (None, "") and image is None and audio is None:
            raise ValueError("Provide a state and/or an image (or audio for d1-omni-600M).")

        kwargs: Dict[str, Any] = {}
        if image is not None:
            images = image if isinstance(image, list) else [image]
            kwargs["images"] = [_load_pil(i) for i in images]
        if audio is not None:
            kwargs["audio"] = _load_audio(audio)

        model = self._load()
        result = model.system_one(None if st == "" else st, qs, **kwargs)
        return {"model": self.model_id, "answers": result.get("answers", {}), "usage": result.get("usage")}
