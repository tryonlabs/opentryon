"""
SANA-Sprint local text-to-image (NVLabs + MIT HAN Lab, Diffusers).

Ultra-fast 1–4 step T2I via ``SanaSprintPipeline`` (needs diffusers from GitHub main).

Default weights: ``Efficient-Large-Model/Sana_Sprint_1.6B_1024px_diffusers``

Reference:
  https://huggingface.co/docs/diffusers/api/pipelines/sana_sprint
  https://nvlabs.github.io/Sana/Sprint/
"""

from __future__ import annotations

import os
from typing import List, Optional

from PIL import Image

DEFAULT_MODEL_ID = "Efficient-Large-Model/Sana_Sprint_1.6B_1024px_diffusers"


class SanaSprintAdapter:
    """Local SANA-Sprint T2I (Path B)."""

    def __init__(
        self,
        model_id: Optional[str] = None,
        device: Optional[str] = None,
    ):
        try:
            import torch
        except ImportError as exc:
            raise ImportError(
                "SANA-Sprint requires PyTorch. Install with: pip install opentryon[local]"
            ) from exc
        self.model_id = model_id or os.getenv("SANA_SPRINT_MODEL_ID") or DEFAULT_MODEL_ID
        if device is None:
            if torch.cuda.is_available():
                device = "cuda"
            elif getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
                device = "mps"
            else:
                device = "cpu"
        self.device = device
        self._pipe = None

    def _load(self):
        if self._pipe is not None:
            return self._pipe
        try:
            import torch
            from diffusers import SanaSprintPipeline
        except ImportError as exc:
            raise ImportError(
                "SANA-Sprint needs diffusers with SanaSprintPipeline. Install:\n"
                "  pip install opentryon[local]\n"
                '  pip install "git+https://github.com/huggingface/diffusers"\n'
                f"Original error: {exc}"
            ) from exc
        dtype = torch.bfloat16 if self.device != "cpu" else torch.float32
        pipe = SanaSprintPipeline.from_pretrained(self.model_id, torch_dtype=dtype)
        pipe.to(self.device)
        self._pipe = pipe
        return pipe

    def generate_text_to_image(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        num_inference_steps: int = 2,
        guidance_scale: float = 4.5,
        seed: Optional[int] = None,
        **kwargs,
    ) -> List[Image.Image]:
        if not (prompt or "").strip():
            raise ValueError("prompt is required.")
        pipe = self._load()
        gen = None
        if seed is not None:
            import torch

            gen = torch.Generator(device=self.device).manual_seed(int(seed))
        result = pipe(
            prompt=prompt,
            width=int(width),
            height=int(height),
            num_inference_steps=int(num_inference_steps),
            guidance_scale=float(guidance_scale),
            generator=gen,
            **kwargs,
        )
        images = result.images if hasattr(result, "images") else result
        if not isinstance(images, list):
            images = [images]
        return images
