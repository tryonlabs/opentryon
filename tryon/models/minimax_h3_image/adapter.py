"""
MiniMax H3-Image local Diffusers adapter (open weights).

Runs MiniMaxAI/MiniMax-H3-Image via Hugging Face Diffusers ``ModularPipeline``
(text2image and image_conditioned edit). The text encoder is large (~62GB bf16);
use ComponentsManager auto CPU offload and substantial host RAM.

Weights: https://huggingface.co/MiniMaxAI/MiniMax-H3-Image
Docs: https://huggingface.co/docs/diffusers/api/pipelines/minimax_h3_image
License: MiniMax H3 Community License (same regional limits as MiniMax-H3 video).
Hosted twin: ``--model minimax-h3-image`` (``MINIMAX_API_KEY``).
"""

from __future__ import annotations

import os
from typing import Any, List, Optional, Union

from PIL import Image

DEFAULT_MODEL_ID = "MiniMaxAI/MiniMax-H3-Image"
DEFAULT_WIDTH = 2048
DEFAULT_HEIGHT = 2048


class MiniMaxH3ImageLocalAdapter:
    """Local open-weight MiniMax H3-Image (T2I + multi-reference edit)."""

    def __init__(
        self,
        model_id: Optional[str] = None,
        device: Optional[str] = None,
        cpu_offload: bool = True,
    ):
        try:
            import torch
            from diffusers import ModularPipeline  # noqa: F401
        except ImportError as exc:
            raise ImportError(
                "MiniMax H3-Image (local) needs PyTorch and a recent Diffusers with "
                "MiniMaxH3ImageModularPipeline. Install:\n"
                "  pip install opentryon[local]\n"
                "  pip install -U 'diffusers>=0.43.0'\n"
                f"Original error: {exc}"
            ) from exc

        self.model_id = model_id or os.getenv("MINIMAX_H3_IMAGE_MODEL_ID") or DEFAULT_MODEL_ID
        if device is None:
            if torch.cuda.is_available():
                device = "cuda"
            elif getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
                device = "mps"
            else:
                device = "cpu"
        self.device = device
        self.cpu_offload = bool(cpu_offload)
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
            if os.path.exists(image_input):
                return Image.open(image_input).convert("RGB")
            raise ValueError(f"Image path does not exist: {image_input}")
        raise ValueError("image must be a path, URL, or PIL Image")

    def _load(self):
        if self._pipe is not None:
            return self._pipe
        try:
            import torch
            from diffusers import ComponentsManager, ModularPipeline
        except ImportError as exc:
            raise ImportError(
                "MiniMax H3-Image local needs diffusers ComponentsManager + ModularPipeline."
            ) from exc

        manager = None
        if self.cpu_offload and self.device != "cpu":
            manager = ComponentsManager()
            manager.enable_auto_cpu_offload(device=self.device)

        pipe = ModularPipeline.from_pretrained(
            self.model_id,
            components_manager=manager,
        )
        dtype = torch.bfloat16 if self.device != "cpu" else torch.float32
        pipe.load_components(dtype=dtype)
        if not self.cpu_offload:
            pipe.to(self.device)
        self._pipe = pipe
        return pipe

    def _run(
        self,
        prompt: str,
        *,
        image: Optional[Union[Image.Image, List[Image.Image]]] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        seed: Optional[int] = None,
        **kwargs: Any,
    ) -> List[Image.Image]:
        if not (prompt or "").strip():
            raise ValueError("prompt is required.")

        pipe = self._load()
        w = int(width) if width is not None else DEFAULT_WIDTH
        h = int(height) if height is not None else DEFAULT_HEIGHT

        call: Dict[str, Any] = {
            "prompt": prompt,
            "width": w,
            "height": h,
            "output": "images",
        }
        if image is not None:
            call["image"] = image
        if seed is not None:
            import torch

            gen_device = self.device if self.device != "cpu" else "cpu"
            call["generator"] = torch.Generator(device=gen_device).manual_seed(int(seed))
        call.update({k: v for k, v in kwargs.items() if v is not None})

        result = pipe(**call)
        if isinstance(result, list):
            return [im.convert("RGB") if isinstance(im, Image.Image) else im for im in result]
        if hasattr(result, "images"):
            imgs = result.images
            return imgs if isinstance(imgs, list) else [imgs]
        if isinstance(result, Image.Image):
            return [result.convert("RGB")]
        return list(result)

    def generate_text_to_image(
        self,
        prompt: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        seed: Optional[int] = None,
        **kwargs: Any,
    ) -> List[Image.Image]:
        return self._run(prompt, width=width, height=height, seed=seed, **kwargs)

    def generate_image_edit(
        self,
        prompt: str,
        image: Union[str, Image.Image, List[Union[str, Image.Image]]],
        width: Optional[int] = None,
        height: Optional[int] = None,
        seed: Optional[int] = None,
        **kwargs: Any,
    ) -> List[Image.Image]:
        if isinstance(image, list):
            refs = [self._load_pil(img) for img in image]
        else:
            refs = [self._load_pil(image)]
        image_arg: Union[Image.Image, List[Image.Image]] = refs[0] if len(refs) == 1 else refs
        return self._run(
            prompt,
            image=image_arg,
            width=width,
            height=height,
            seed=seed,
            **kwargs,
        )