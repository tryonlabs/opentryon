"""
CatVTON local virtual try-on adapter.

Official weights: https://huggingface.co/zhengchong/CatVTON
Paper / code: https://github.com/Zheng-Chong/CatVTON (ICLR 2025)

Path B (GPU). Concatenates person + garment in latent space on SD 1.5
inpainting; attention checkpoints are ~50M trainable params. Typical
VRAM is under 8GB at 1024x768 with bf16/fp16.

License: **CC BY-NC-SA 4.0** (code + checkpoints). Not for commercial D2C
without a separate grant. FLUX.1-Fill LoRA lives in the same HF repo
(``flux-lora/``) but official inference code is not released — this adapter
uses the documented SD 1.5 pipeline.

Requirements:
    pip install opentryon[local]

Examples:
    >>> from tryon.models import CatVTONAdapter
    >>> adapter = CatVTONAdapter()
    >>> images = adapter.generate_and_decode("person.jpg", "garment.jpg")
"""

from __future__ import annotations

import io
import os
import warnings
from pathlib import Path
from typing import List, Optional, Union

from PIL import Image, ImageDraw

ImageInput = Union[str, Path, io.BytesIO, bytes, Image.Image]

DEFAULT_ATTN_REPO = "zhengchong/CatVTON"
DEFAULT_BASE_MODEL = "runwayml/stable-diffusion-inpainting"
DEFAULT_HEIGHT = 1024
DEFAULT_WIDTH = 768


def _require_local() -> None:
    try:
        import torch  # noqa: F401
        import diffusers  # noqa: F401
        import accelerate  # noqa: F401
    except ImportError as exc:
        raise ImportError(
            "CatVTON local inference needs torch, diffusers, and accelerate. "
            "Install with: pip install opentryon[local]"
        ) from exc


def _load_pil(image: ImageInput) -> Image.Image:
    if isinstance(image, Image.Image):
        return image.convert("RGB")
    if isinstance(image, (bytes, bytearray)):
        return Image.open(io.BytesIO(bytes(image))).convert("RGB")
    if isinstance(image, io.BytesIO):
        image.seek(0)
        return Image.open(image).convert("RGB")
    source = str(image)
    if source.startswith(("http://", "https://")):
        try:
            from diffusers.utils import load_image
        except ImportError as exc:
            raise ImportError(
                "diffusers is required to load image URLs: pip install opentryon[local]"
            ) from exc
        return load_image(source).convert("RGB")
    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {source}")
    return Image.open(path).convert("RGB")


def _default_mask(person: Image.Image, garment_type: str) -> Image.Image:
    """Geometric agnostic-mask fallback when the caller does not pass one."""
    w, h = person.size
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    kind = (garment_type or "upper_body").lower().replace("-", "_")
    if kind in {"lower", "lower_body", "bottoms"}:
        box = (int(w * 0.18), int(h * 0.42), int(w * 0.82), int(h * 0.98))
    elif kind in {"dress", "dresses", "one_piece", "one-piece"}:
        box = (int(w * 0.14), int(h * 0.12), int(w * 0.86), int(h * 0.94))
    else:
        box = (int(w * 0.14), int(h * 0.10), int(w * 0.86), int(h * 0.62))
    draw.rounded_rectangle(box, radius=max(8, w // 20), fill=255)
    return mask


class CatVTONAdapter:
    """
    Local CatVTON adapter (person + garment → try-on image).

    Args:
        attn_ckpt: HF repo id or local snapshot (default ``zhengchong/CatVTON``).
        base_ckpt: SD 1.5 inpainting repo (default ``runwayml/stable-diffusion-inpainting``;
            set ``CATVTON_BASE_MODEL`` if that id is gated).
        attn_version: ``mix`` (default, 1024), ``vitonhd``, or ``dresscode``.
        device: ``cuda`` / ``cpu``.
        dtype: ``float16`` (default), ``bfloat16``, or ``float32``.
        cpu_offload: unused placeholder for CLI symmetry (pipeline is already compact).
    """

    def __init__(
        self,
        attn_ckpt: Optional[str] = None,
        base_ckpt: Optional[str] = None,
        attn_version: str = "mix",
        device: Optional[str] = None,
        dtype: str = "float16",
        cpu_offload: bool = True,
    ):
        _require_local()
        import torch

        self.attn_ckpt = (
            attn_ckpt
            or os.getenv("CATVTON_ATTN_CKPT")
            or DEFAULT_ATTN_REPO
        )
        self.base_ckpt = (
            base_ckpt
            or os.getenv("CATVTON_BASE_MODEL")
            or DEFAULT_BASE_MODEL
        )
        self.attn_version = attn_version or "mix"
        if device:
            self.device = device
        else:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.dtype_name = dtype
        self.cpu_offload = cpu_offload
        self._pipe = None

    def _torch_dtype(self):
        import torch

        mapping = {
            "float16": torch.float16,
            "fp16": torch.float16,
            "bfloat16": torch.bfloat16,
            "bf16": torch.bfloat16,
            "float32": torch.float32,
            "fp32": torch.float32,
            "no": torch.float32,
        }
        return mapping.get(self.dtype_name.lower(), torch.float16)

    def _load(self):
        if self._pipe is not None:
            return self._pipe
        from .pipeline import CatVTONPipeline

        if self.device == "cpu":
            warnings.warn(
                "CatVTON on CPU is extremely slow. A CUDA GPU is recommended."
            )
        self._pipe = CatVTONPipeline(
            base_ckpt=self.base_ckpt,
            attn_ckpt=self.attn_ckpt,
            attn_ckpt_version=self.attn_version,
            weight_dtype=self._torch_dtype(),
            device=self.device,
        )
        return self._pipe

    def generate_and_decode(
        self,
        person: ImageInput,
        garment: ImageInput,
        mask: Optional[ImageInput] = None,
        garment_type: str = "upper_body",
        num_inference_steps: int = 50,
        guidance_scale: float = 2.5,
        height: int = DEFAULT_HEIGHT,
        width: int = DEFAULT_WIDTH,
        seed: Optional[int] = None,
        repaint: bool = False,
    ) -> List[Image.Image]:
        """Run CatVTON. ``mask`` is the person-image clothing region (white = replace)."""
        import torch

        person_im = _load_pil(person)
        garment_im = _load_pil(garment)
        if mask is not None:
            mask_im = _load_pil(mask).convert("L")
        else:
            warnings.warn(
                "No --mask-image given; using a geometric upper/lower/dress fallback. "
                "Pass an agnostic clothing mask for dataset-quality results."
            )
            mask_im = _default_mask(person_im, garment_type)

        generator = None
        if seed is not None:
            generator = torch.Generator(device=self.device).manual_seed(int(seed))

        pipe = self._load()
        results = pipe(
            person_im,
            garment_im,
            mask_im,
            num_inference_steps=int(num_inference_steps),
            guidance_scale=float(guidance_scale),
            height=int(height),
            width=int(width),
            generator=generator,
        )
        if not repaint:
            return results
        from PIL import ImageFilter
        import numpy as np

        out = []
        for result in results:
            person_r = person_im.resize(result.size, Image.LANCZOS)
            mask_r = mask_im.resize(result.size, Image.NEAREST).filter(
                ImageFilter.GaussianBlur(max(1, result.size[1] // 50))
            )
            person_np = np.array(person_r)
            result_np = np.array(result)
            mask_np = np.expand_dims(np.array(mask_r), axis=2) / 255.0
            blended = person_np * (1 - mask_np) + result_np * mask_np
            out.append(Image.fromarray(blended.astype("uint8")))
        return out
