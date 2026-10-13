"""
FLUX.2-klein-4B Virtual Try-On LoRA Adapter (local, Apache-2.0)

``xocialize/tryon-FLUX.2-klein-4B-lora`` is a rank-32 edit LoRA for
``black-forest-labs/FLUX.2-klein-4B`` (Apache-2.0, ~13GB VRAM, distilled) that
dresses a person in a specified outfit. Both the base model and the LoRA are
Apache-2.0, so unlike the popular FLUX.2 klein **9B** try-on LoRAs (9B is under
the FLUX Non-Commercial License) this stack is commercially clean.

Three ordered reference images produce one output with identity, pose and
background preserved -- the order is load-bearing:

1. **person**  -- full-body photo with the clothing region masked out
   ("clothing-agnostic", the outfit area greyed, as in VITON-style training)
2. **top**     -- the upper-body garment, isolated / product-style
3. **bottom**  -- the lower-body garment, isolated; for a one-piece dress use the
   dress in both slots (``dress=``)

Pre-processing is on you: this adapter does **not** segment clothing. Either pass
an already clothing-agnostic person image, or pass ``mask`` (white = clothing
region to replace) and the adapter greys that area out. Any parser can make the
mask; note that ``fashn-human-parser`` and ``segformer_b2_clothes`` (the one the
LoRA author used) carry their own licences -- review them for commercial use.

Prompt: ``TRYON a full-body photo of a person. Replace the outfit with the top and
bottom as shown in the reference images. The final image is a full body shot.``

Maturity (from the model card): a v1 community LoRA trained on only 273 full-body
tuples (Pexels frames, step-2000 checkpoint), with no published metrics. Known
limits: garment-part segmentation can drag nearby objects into the bottom crop
(faint artifacts), and all-dark outfits are the weakest case. The card gives no
sampler settings; the defaults here are BFL's FLUX.2-klein-4B defaults (4 steps,
guidance 1.0) -- tune ``num_inference_steps`` / ``guidance_scale`` on your data.

Reference:
https://huggingface.co/xocialize/tryon-FLUX.2-klein-4B-lora
https://huggingface.co/black-forest-labs/FLUX.2-klein-4B

Requirements:
    pip install opentryon[local]
    pip install git+https://github.com/huggingface/diffusers.git peft accelerate
    (Flux2KleinPipeline is not in a stable diffusers release yet; CUDA GPU, ~13GB+ VRAM.)

Environment:
    KLEIN_TRYON_LORA_ID    -- LoRA repo / path (default xocialize/tryon-FLUX.2-klein-4B-lora)
    KLEIN_TRYON_BASE_ID    -- base model repo / path (default black-forest-labs/FLUX.2-klein-4B)

Examples:
    >>> from tryon.models.klein_tryon import Klein4BTryOnAdapter
    >>> adapter = Klein4BTryOnAdapter()
    >>> images = adapter.generate_and_decode(
    ...     person="person_agnostic.png", top="shirt.png", bottom="jeans.png")
    >>> images[0].save("tryon.png")
"""

from __future__ import annotations

import io
import os
from pathlib import Path
from typing import Any, List, Optional, Tuple, Union

from PIL import Image

ImageInput = Union[str, Path, io.BytesIO, bytes, Image.Image]

DEFAULT_LORA_ID = "xocialize/tryon-FLUX.2-klein-4B-lora"
DEFAULT_LORA_WEIGHT = "tryon-klein-4b.safetensors"
DEFAULT_BASE_ID = "black-forest-labs/FLUX.2-klein-4B"
TRYON_PROMPT = (
    "TRYON a full-body photo of a person. Replace the outfit with the top and bottom as shown in the "
    "reference images. The final image is a full body shot."
)
GREY = (128, 128, 128)
MAX_SIDE = 1024
MULTIPLE = 16


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


def apply_agnostic_mask(person: Image.Image, mask: Image.Image) -> Image.Image:
    """Grey out the clothing region (``mask`` white = replace) -> a clothing-agnostic person image."""
    mask_l = mask.convert("L").resize(person.size)
    binary = mask_l.point(lambda v: 255 if v >= 128 else 0)
    return Image.composite(Image.new("RGB", person.size, GREY), person, binary)


def output_size(person: Image.Image, height: Optional[int], width: Optional[int]) -> Tuple[int, int]:
    """(height, width): explicit values rounded to multiples of 16, else the person's size scaled to <= 1024 on the long side."""
    def snap(v: int) -> int:
        return max(MULTIPLE, int(round(v / MULTIPLE)) * MULTIPLE)

    if height and width:
        return snap(int(height)), snap(int(width))
    w, h = person.size
    scale = min(1.0, MAX_SIDE / max(w, h))
    return snap(int(h * scale)), snap(int(w * scale))


class Klein4BTryOnAdapter:
    """
    Local Diffusers adapter: FLUX.2-klein-4B + the try-on LoRA.

    Args:
        lora_id: LoRA repo / path. Defaults to ``KLEIN_TRYON_LORA_ID`` or ``xocialize/tryon-FLUX.2-klein-4B-lora``.
        lora_weight_name: file inside the repo (default ``tryon-klein-4b.safetensors``).
        base_model_id: base repo / path. Defaults to ``KLEIN_TRYON_BASE_ID`` or ``black-forest-labs/FLUX.2-klein-4B``.
        device: ``cuda`` required (default auto).
        dtype: ``bfloat16`` (default), ``float16`` or ``float32``.
        cpu_offload: enable model CPU offload (default True; ~13GB VRAM without).
    """

    def __init__(
        self,
        lora_id: Optional[str] = None,
        lora_weight_name: str = DEFAULT_LORA_WEIGHT,
        base_model_id: Optional[str] = None,
        device: Optional[str] = None,
        dtype: str = "bfloat16",
        cpu_offload: bool = True,
    ):
        try:
            import torch
        except ImportError as exc:
            raise ImportError(
                "FLUX.2-klein try-on needs the local extra: pip install opentryon[local], plus\n"
                "  pip install git+https://github.com/huggingface/diffusers.git peft accelerate"
            ) from exc
        self.torch = torch
        self.lora_id = lora_id or os.getenv("KLEIN_TRYON_LORA_ID") or DEFAULT_LORA_ID
        self.lora_weight_name = lora_weight_name
        self.base_model_id = base_model_id or os.getenv("KLEIN_TRYON_BASE_ID") or DEFAULT_BASE_ID
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        if self.device == "cpu":
            raise RuntimeError("FLUX.2-klein try-on requires a CUDA GPU (~13GB+ VRAM); CPU-only is not supported.")
        dtypes = {"bfloat16": torch.bfloat16, "bf16": torch.bfloat16, "float16": torch.float16,
                  "fp16": torch.float16, "float32": torch.float32}
        if dtype.lower() not in dtypes:
            raise ValueError(f"dtype must be one of {sorted(dtypes)} (got {dtype!r}).")
        self.dtype = dtypes[dtype.lower()]
        self.cpu_offload = bool(cpu_offload)
        self._pipe = None

    def _load(self):
        if self._pipe is not None:
            return self._pipe
        try:
            from diffusers import Flux2KleinPipeline
        except ImportError as exc:
            raise ImportError(
                "Flux2KleinPipeline is missing. Install diffusers from GitHub:\n"
                "  pip install git+https://github.com/huggingface/diffusers.git peft accelerate"
            ) from exc
        pipe = Flux2KleinPipeline.from_pretrained(self.base_model_id, torch_dtype=self.dtype)
        try:
            pipe.load_lora_weights(self.lora_id, weight_name=self.lora_weight_name)
        except ImportError as exc:
            raise ImportError("Loading the try-on LoRA needs peft: pip install -U peft diffusers accelerate") from exc
        if self.cpu_offload:
            pipe.enable_model_cpu_offload()
        else:
            pipe.to(self.device)
        self._pipe = pipe
        return pipe

    def generate_and_decode(
        self,
        person: ImageInput,
        top: Optional[ImageInput] = None,
        bottom: Optional[ImageInput] = None,
        dress: Optional[ImageInput] = None,
        mask: Optional[ImageInput] = None,
        prompt: str = TRYON_PROMPT,
        num_inference_steps: int = 4,
        guidance_scale: float = 1.0,
        height: Optional[int] = None,
        width: Optional[int] = None,
        seed: Optional[int] = None,
        num_images: int = 1,
    ) -> List[Image.Image]:
        """Dress ``person`` in ``top`` + ``bottom`` (or a one-piece ``dress``) and return PIL images.

        Args:
            person: full-body photo, already clothing-agnostic -- or pass ``mask`` to have it greyed here.
            top / bottom: isolated garment images. ``dress``: one-piece garment used in both slots
                (mutually exclusive with ``top`` / ``bottom``).
            mask: optional clothing-region mask (white = replace) applied to ``person`` as a grey fill.
            prompt: defaults to the LoRA's trigger prompt (must start with ``TRYON``).
        """
        if person is None:
            raise ValueError("person is required (a full-body, clothing-agnostic photo).")
        if dress is not None:
            if top is not None or bottom is not None:
                raise ValueError("Pass either dress, or top and bottom -- not both.")
            top = bottom = dress
        elif top is None or bottom is None:
            raise ValueError("Provide top and bottom (the LoRA was trained on both), or a one-piece dress.")
        if not prompt or not prompt.strip():
            raise ValueError("prompt is required (default is the LoRA trigger prompt).")
        if not prompt.lstrip().startswith("TRYON"):
            raise ValueError("prompt must start with the trigger word TRYON.")
        if int(num_inference_steps) < 1 or int(num_images) < 1:
            raise ValueError("num_inference_steps and num_images must be >= 1.")

        person_img = _load_pil(person)
        if mask is not None:
            person_img = apply_agnostic_mask(person_img, _load_pil(mask))
        refs = [person_img, _load_pil(top), _load_pil(bottom)]  # order is load-bearing: person, top, bottom
        h, w = output_size(person_img, height, width)

        pipe = self._load()
        kwargs: dict = {
            "image": refs,
            "prompt": prompt,
            "height": h,
            "width": w,
            "num_inference_steps": int(num_inference_steps),
            "guidance_scale": float(guidance_scale),
            "num_images_per_prompt": int(num_images),
        }
        if seed is not None:
            kwargs["generator"] = self.torch.Generator(device="cpu").manual_seed(int(seed))
        with self.torch.inference_mode():
            result = pipe(**kwargs)
        return list(result.images)
