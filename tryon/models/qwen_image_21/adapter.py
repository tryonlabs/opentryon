"""
Qwen-Image-2.1 open weights (Diffusers ``QwenImage21Pipeline``).

Checkpoints:
  - Qwen/Qwen-Image-2.1 — full model
  - Qwen/Qwen-Image-2.1-Turbo — 8-step Turbo schedule (T2I + edit)

Also on ModelScope: https://modelscope.cn/models/Qwen/Qwen-Image-2.1-Turbo

Hosted DashScope twins: ``qwen-image-2.1-pro`` / ``qwen-image-2.1-turbo``.
"""

from __future__ import annotations

import io
import os
from pathlib import Path
from typing import Any, List, Optional, Tuple, Union

from PIL import Image

DEFAULT_MODEL_ID = "Qwen/Qwen-Image-2.1"
DEFAULT_TURBO_MODEL_ID = "Qwen/Qwen-Image-2.1-Turbo"
MAX_REFERENCE_IMAGES = 10

DEFAULT_TRYON_PROMPT = (
    "The person in the first image, keeping their face, pose and background "
    "unchanged, wearing the garment shown in the second image. Preserve identity "
    "and lighting; match the garment's fabric, color, and details faithfully."
)

ImageInput = Union[str, Path, io.BytesIO, bytes, Image.Image]


def _load_pil(image: ImageInput) -> Image.Image:
    if isinstance(image, Image.Image):
        return image.convert("RGBA")
    if isinstance(image, (bytes, bytearray)):
        return Image.open(io.BytesIO(bytes(image))).convert("RGBA")
    if isinstance(image, io.BytesIO):
        image.seek(0)
        return Image.open(image).convert("RGBA")
    source = str(image)
    if source.startswith(("http://", "https://")):
        try:
            from diffusers.utils import load_image
        except ImportError as exc:
            raise ImportError("diffusers is required: pip install -U diffusers") from exc
        return load_image(source).convert("RGBA")
    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {source}")
    return Image.open(path).convert("RGBA")


class QwenImage21LocalAdapter:
    """
    Local Qwen-Image-2.1 / 2.1-Turbo (unified T2I + edit on one pipeline).

    Args:
        model_id: HF repo id (default ``QWEN_IMAGE_21_MODEL_ID`` or Turbo id when
            ``turbo=True``).
        turbo: When True and ``model_id`` is unset, use ``Qwen/Qwen-Image-2.1-Turbo``.
        device: CUDA device (default auto).
        dtype: ``bfloat16`` (default), ``float16``, or ``float32``.
        cpu_offload: Enable ``enable_model_cpu_offload()`` when True (default).
    """

    def __init__(
        self,
        model_id: Optional[str] = None,
        turbo: bool = False,
        device: Optional[str] = None,
        dtype: str = "bfloat16",
        cpu_offload: bool = True,
    ):
        try:
            import torch
        except ImportError as exc:
            raise ImportError(
                "Qwen-Image-2.1 local inference requires opentryon[local] "
                "and a recent Diffusers build with QwenImage21Pipeline."
            ) from exc

        self.torch = torch
        env_id = os.getenv("QWEN_IMAGE_21_MODEL_ID") or os.getenv("QWEN_IMAGE_21_MODEL_PATH")
        if model_id:
            self.model_id = model_id
        elif env_id:
            self.model_id = env_id
        elif turbo:
            self.model_id = DEFAULT_TURBO_MODEL_ID
        else:
            self.model_id = DEFAULT_MODEL_ID
        self.is_turbo = "turbo" in self.model_id.lower()
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        if self.device == "cpu":
            raise RuntimeError(
                "Qwen-Image-2.1 local inference requires a CUDA GPU and recent Diffusers."
            )
        dtype_map = {
            "bfloat16": torch.bfloat16,
            "bf16": torch.bfloat16,
            "float16": torch.float16,
            "fp16": torch.float16,
            "float32": torch.float32,
        }
        self.dtype = dtype_map.get(dtype.lower(), torch.bfloat16)
        self.cpu_offload = bool(cpu_offload)
        self._pipe = None

    def _load_pipe(self):
        if self._pipe is not None:
            return self._pipe
        try:
            from diffusers import QwenImage21Pipeline
        except ImportError as exc:
            raise ImportError(
                "QwenImage21Pipeline is missing. Install latest Diffusers:\n"
                "  pip install -U diffusers transformers accelerate\n"
                "  # or: pip install git+https://github.com/huggingface/diffusers"
            ) from exc
        pipe = QwenImage21Pipeline.from_pretrained(self.model_id, torch_dtype=self.dtype)
        if self.cpu_offload:
            pipe.enable_model_cpu_offload()
        else:
            pipe.to(self.device)
        self._pipe = pipe
        return self._pipe

    def _generator(self, seed: Optional[int]):
        if seed is None:
            return None
        return self.torch.Generator(device="cpu").manual_seed(int(seed))

    def _run(
        self,
        prompt: str,
        *,
        image: Optional[Union[Image.Image, List[Image.Image]]] = None,
        width: int = 1328,
        height: int = 1328,
        use_kv_cache: bool = True,
        seed: Optional[int] = None,
        num_images: int = 1,
    ) -> List[Image.Image]:
        if not prompt:
            raise ValueError("prompt is required.")
        pipe = self._load_pipe()
        kwargs: dict[str, Any] = {
            "prompt": prompt,
            "width": int(width),
            "height": int(height),
            "use_kv_cache": bool(use_kv_cache),
            "generator": self._generator(seed),
        }
        if image is not None:
            kwargs["image"] = image
        with self.torch.inference_mode():
            out = pipe(**kwargs)
        images = list(out.images)
        if num_images and len(images) > int(num_images):
            images = images[: int(num_images)]
        return images

    def generate_text_to_image(
        self,
        prompt: str,
        width: int = 1328,
        height: int = 1328,
        use_kv_cache: bool = True,
        seed: Optional[int] = None,
        num_images: int = 1,
    ) -> List[Image.Image]:
        return self._run(
            prompt,
            width=width,
            height=height,
            use_kv_cache=use_kv_cache,
            seed=seed,
            num_images=num_images,
        )

    def generate_image_edit(
        self,
        image: Union[ImageInput, List[ImageInput]],
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        use_kv_cache: bool = True,
        seed: Optional[int] = None,
        num_images: int = 1,
    ) -> List[Image.Image]:
        images = image if isinstance(image, list) else [image]
        loaded = [_load_pil(img) for img in images]
        if len(loaded) > MAX_REFERENCE_IMAGES:
            raise ValueError(f"At most {MAX_REFERENCE_IMAGES} reference images supported.")
        image_arg: Union[Image.Image, List[Image.Image]] = (
            loaded[0] if len(loaded) == 1 else loaded
        )
        return self._run(
            prompt,
            image=image_arg,
            width=width,
            height=height,
            use_kv_cache=use_kv_cache,
            seed=seed,
            num_images=num_images,
        )

    def generate_multi_image(
        self,
        images: List[ImageInput],
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        use_kv_cache: bool = True,
        seed: Optional[int] = None,
        num_images: int = 1,
    ) -> List[Image.Image]:
        return self.generate_image_edit(
            images,
            prompt,
            width=width,
            height=height,
            use_kv_cache=use_kv_cache,
            seed=seed,
            num_images=num_images,
        )

    @staticmethod
    def build_tryon_prompt(
        prompt: Optional[str] = None,
        garment_description: Optional[str] = None,
    ) -> str:
        if prompt:
            return prompt
        if garment_description:
            return (
                "The person in the first image, keeping their face, pose and "
                f"background unchanged, wearing the {garment_description} shown "
                "in the second image. Preserve identity and lighting."
            )
        return DEFAULT_TRYON_PROMPT

    def generate_virtual_tryon(
        self,
        person: Optional[ImageInput] = None,
        garment: Optional[ImageInput] = None,
        *,
        person_image: Optional[ImageInput] = None,
        garment_image: Optional[ImageInput] = None,
        prompt: Optional[str] = None,
        garment_description: Optional[str] = None,
        width: int = 1024,
        height: int = 1024,
        use_kv_cache: bool = True,
        seed: Optional[int] = None,
        num_images: int = 1,
    ) -> List[Image.Image]:
        resolved_person = person or person_image
        resolved_garment = garment or garment_image
        if resolved_person is None or resolved_garment is None:
            raise ValueError("person and garment images are required for try-on.")
        styling = self.build_tryon_prompt(prompt=prompt, garment_description=garment_description)
        return self.generate_multi_image(
            [resolved_person, resolved_garment],
            styling,
            width=width,
            height=height,
            use_kv_cache=use_kv_cache,
            seed=seed,
            num_images=num_images,
        )
