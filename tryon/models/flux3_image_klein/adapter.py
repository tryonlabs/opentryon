"""
FLUX 3 Image Klein — local Diffusers (ModularPipeline).

Distilled default: ``black-forest-labs/flux-3-image-klein`` (16 steps, no CFG).
Base (fine-tune / research): ``black-forest-labs/flux-3-image-klein-base``.

Reference:
  https://docs.bfl.ml/flux_3/flux3_image_klein
  https://huggingface.co/blog/flux-3
"""

from __future__ import annotations

import os
from typing import List, Optional, Union

from PIL import Image

DEFAULT_MODEL_ID = "black-forest-labs/flux-3-image-klein"
BASE_MODEL_ID = "black-forest-labs/flux-3-image-klein-base"


def _is_base_checkpoint(model_id: str) -> bool:
    tail = model_id.rstrip("/").split("/")[-1]
    return tail.endswith("klein-base") or tail == "flux-3-image-klein-base"


class Flux3ImageKleinLocalAdapter:
    """Local FLUX 3 Image Klein T2I and multi-reference edit (Path B)."""

    def __init__(
        self,
        model_id: Optional[str] = None,
        device: Optional[str] = None,
        guidance_scale: Optional[float] = None,
    ):
        try:
            import torch
        except ImportError as exc:
            raise ImportError(
                "FLUX 3 Image Klein (local) requires PyTorch. Install with: pip install opentryon[local]"
            ) from exc

        self.model_id = (
            model_id or os.getenv("FLUX3_IMAGE_KLEIN_MODEL_ID") or DEFAULT_MODEL_ID
        )
        if device is None:
            if torch.cuda.is_available():
                device = "cuda"
            elif getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
                device = "mps"
            else:
                device = "cpu"
        self.device = device
        self._is_base = _is_base_checkpoint(self.model_id)
        if guidance_scale is None:
            guidance_scale = 3.5 if self._is_base else 1.0
        self.guidance_scale = float(guidance_scale)
        self._pipe = None

    def _load_pil(self, image_input: Union[str, Image.Image]) -> Image.Image:
        if isinstance(image_input, Image.Image):
            return image_input.convert("RGB")
        if isinstance(image_input, str):
            if image_input.startswith(("http://", "https://")):
                try:
                    from diffusers.utils import load_image
                except ImportError as exc:
                    raise ImportError(
                        "URL images need diffusers. Install: pip install opentryon[local]"
                    ) from exc
                return load_image(image_input).convert("RGB")
            return Image.open(image_input).convert("RGB")
        raise ValueError("image must be a path, URL, or PIL Image")

    def _load(self):
        if self._pipe is not None:
            return self._pipe
        try:
            import torch
            from diffusers import ModularPipeline
        except ImportError as exc:
            raise ImportError(
                "FLUX 3 Image Klein needs diffusers with ModularPipeline (FLUX.3 Klein). Install:\n"
                "  pip install opentryon[local]\n"
                "  pip install -U diffusers transformers\n"
                f"Original error: {exc}"
            ) from exc

        pipe = ModularPipeline.from_pretrained(self.model_id)
        if self._is_base:
            pipe.load_components(dtype={"vae": torch.float32, "default": torch.bfloat16})
            if self.guidance_scale != 1.0 and hasattr(pipe, "guider") and pipe.guider is not None:
                pipe.guider = pipe.guider.new(guidance_scale=self.guidance_scale)
        else:
            dtype = torch.bfloat16 if self.device != "cpu" else torch.float32
            pipe.load_components(dtype=dtype)

        pipe.to(self.device)
        self._pipe = pipe
        return pipe

    def _default_steps(self) -> int:
        return 50 if self._is_base else 16

    def _run(
        self,
        prompt: str,
        *,
        images: Optional[Union[Image.Image, List[Image.Image]]] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        num_inference_steps: Optional[int] = None,
        seed: Optional[int] = None,
        **kwargs,
    ) -> List[Image.Image]:
        if not (prompt or "").strip():
            raise ValueError("prompt is required.")

        pipe = self._load()
        steps = int(num_inference_steps) if num_inference_steps is not None else self._default_steps()

        call: dict = {"prompt": prompt, "output": "images", "num_inference_steps": steps}
        if width is not None:
            call["width"] = int(width)
        if height is not None:
            call["height"] = int(height)
        if images is not None:
            call["image"] = images
        if seed is not None:
            import torch

            call["generator"] = torch.Generator(device=self.device).manual_seed(int(seed))

        for key in list(kwargs.keys()):
            if kwargs[key] is None:
                kwargs.pop(key)
        call.update(kwargs)

        result = pipe(**call)
        if isinstance(result, list):
            return result
        if hasattr(result, "images"):
            imgs = result.images
            return imgs if isinstance(imgs, list) else [imgs]
        return [result]

    def generate_text_to_image(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        num_inference_steps: Optional[int] = None,
        seed: Optional[int] = None,
        **kwargs,
    ) -> List[Image.Image]:
        return self._run(
            prompt,
            width=width,
            height=height,
            num_inference_steps=num_inference_steps,
            seed=seed,
            **kwargs,
        )

    def generate_image_edit(
        self,
        prompt: str,
        input_image: Union[str, Image.Image],
        reference_images: Optional[List[Union[str, Image.Image]]] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        num_inference_steps: Optional[int] = None,
        seed: Optional[int] = None,
        **kwargs,
    ) -> List[Image.Image]:
        refs: List[Image.Image] = [self._load_pil(input_image)]
        if reference_images:
            refs.extend(self._load_pil(img) for img in reference_images)
        image_arg: Union[Image.Image, List[Image.Image]] = refs[0] if len(refs) == 1 else refs
        return self._run(
            prompt,
            images=image_arg,
            width=width,
            height=height,
            num_inference_steps=num_inference_steps,
            seed=seed,
            **kwargs,
        )
