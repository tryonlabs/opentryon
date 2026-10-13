"""
QIE-2511-Extract-Outfit Local Adapter (open weights, Apache-2.0)

``prithivMLmods/QIE-2511-Extract-Outfit`` is a LoRA for Qwen's
``Qwen/Qwen-Image-Edit-2511`` (also compatible with 2509) that does the reverse
of try-on: it pulls the clothing off a person photo and renders it as a clean,
flat, studio-style mockup, keeping fabric texture, colour, stitching and
patterns while removing the body, pose and background. Useful for turning
on-model or street photos into catalogue-style garment images (and as garment
input for try-on).

The LoRA is activated by the trigger prompt ``"Extract the clothing and create a
flat mockup."`` (the default here). The input must show the full outfit: a
cropped photo only extracts the visible region.

This reuses the repo's local Qwen-Image Edit-Plus runner
(:class:`tryon.models.qwen_image.QwenImageLocalAdapter`) and loads the LoRA onto
the pipeline before placement. Same hardware story: CUDA GPU, ~40GB+ VRAM in
bf16 (CPU offload is on by default for smaller cards). Both the base model and
the LoRA are Apache-2.0; the LoRA is a community adapter (author-described
quality, no published metrics).

Requirements:
    pip install opentryon[local]
    pip install -U diffusers transformers accelerate peft

Environment:
    EXTRACT_OUTFIT_LORA_ID -- override the LoRA repo / path
    QWEN_IMAGE_EDIT_MODEL_ID / QWEN_IMAGE_EDIT_PATH -- override the base model (as for qwen-image-local)

Reference:
https://huggingface.co/prithivMLmods/QIE-2511-Extract-Outfit

Examples:
    >>> from tryon.models.extract_outfit import ExtractOutfitAdapter
    >>> adapter = ExtractOutfitAdapter()
    >>> images = adapter.extract_outfit("model_wearing_look.jpg")
    >>> images[0].save("flat_mockup.png")
"""

from __future__ import annotations

import os
from typing import List, Optional

from PIL import Image

from tryon.models.qwen_image.adapter import ImageInput, QwenImageLocalAdapter

DEFAULT_LORA_ID = "prithivMLmods/QIE-2511-Extract-Outfit"
TRIGGER_PROMPT = "Extract the clothing and create a flat mockup."


class ExtractOutfitAdapter(QwenImageLocalAdapter):
    """Qwen-Image-Edit-2511 + the Extract-Outfit LoRA.

    Args:
        lora_id: LoRA repo id / local path. Defaults to ``EXTRACT_OUTFIT_LORA_ID`` env or
            ``prithivMLmods/QIE-2511-Extract-Outfit``.
        edit_model_id, device, dtype, cpu_offload: as for :class:`QwenImageLocalAdapter`.
    """

    def __init__(
        self,
        lora_id: Optional[str] = None,
        edit_model_id: Optional[str] = None,
        device: Optional[str] = None,
        dtype: str = "bfloat16",
        cpu_offload: bool = True,
    ):
        super().__init__(
            model_id=None, edit_model_id=edit_model_id, device=device, dtype=dtype, cpu_offload=cpu_offload
        )
        self.lora_id = lora_id or os.getenv("EXTRACT_OUTFIT_LORA_ID") or DEFAULT_LORA_ID
        self._lora_loaded = False

    def _place(self, pipe):
        """Attach the LoRA before the pipeline is moved / offloaded."""
        if not self._lora_loaded:
            try:
                pipe.load_lora_weights(self.lora_id)
            except ImportError as exc:  # diffusers raises this when peft is missing
                raise ImportError(
                    "Loading the Extract-Outfit LoRA needs peft: pip install -U peft diffusers transformers accelerate"
                ) from exc
            self._lora_loaded = True
        return super()._place(pipe)

    def extract_outfit(
        self,
        image: ImageInput,
        prompt: str = TRIGGER_PROMPT,
        num_inference_steps: int = 40,
        true_cfg_scale: float = 4.0,
        guidance_scale: float = 1.0,
        negative_prompt: str = " ",
        seed: Optional[int] = None,
        num_images: int = 1,
    ) -> List[Image.Image]:
        """Worn outfit photo -> flat studio mockup(s).

        Args:
            image: a photo showing the full outfit (path, URL, PIL, bytes). A single image only.
            prompt: defaults to the LoRA's trigger prompt; other prompts may not activate the behaviour.
        """
        if image is None or isinstance(image, (list, tuple)):
            raise ValueError("extract_outfit takes exactly one image.")
        if not prompt or not prompt.strip():
            raise ValueError("prompt is required (default is the LoRA trigger prompt).")
        return self.generate_image_edit(
            image,
            prompt,
            num_inference_steps=num_inference_steps,
            true_cfg_scale=true_cfg_scale,
            guidance_scale=guidance_scale,
            negative_prompt=negative_prompt,
            seed=seed,
            num_images=num_images,
        )
