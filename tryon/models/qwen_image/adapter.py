"""
Qwen-Image (open-weight) local Diffusers adapter.

Local GPU inference for the Qwen-Image series on Hugging Face — the open
counterpart to the hosted DashScope ``qwen-image`` API
(``tryon.api.qwen.QwenImageAdapter``).

Two checkpoints (different pipelines):

- **T2I** ``Qwen/Qwen-Image-2512`` via ``QwenImagePipeline``
  (fallback ``Qwen/Qwen-Image``).
- **Edit / VTON** ``Qwen/Qwen-Image-Edit-2511`` via
  ``QwenImageEditPlusPipeline`` (1–3 refs; person + product).

Apache-2.0 weights. Needs a recent Diffusers with QwenImage* pipelines and
transformers >= 4.51.3 (Qwen2.5-VL text encoder).

Docs:
    https://huggingface.co/Qwen/Qwen-Image-2512
    https://huggingface.co/Qwen/Qwen-Image-Edit-2511
    https://huggingface.co/docs/diffusers/main/en/api/pipelines/qwenimage

Requirements:
    pip install opentryon[local]
    pip install -U diffusers transformers accelerate

Examples:
    >>> from tryon.models import QwenImageLocalAdapter
    >>> adapter = QwenImageLocalAdapter()
    >>> images = adapter.generate_text_to_image("editorial lookbook, linen trench")
    >>> tryon = adapter.generate_virtual_tryon("person.jpg", "garment.jpg")
"""

from __future__ import annotations

import io
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from PIL import Image

DEFAULT_T2I_MODEL_ID = "Qwen/Qwen-Image-2512"
DEFAULT_EDIT_MODEL_ID = "Qwen/Qwen-Image-Edit-2511"

# Official Qwen-Image packed resolutions (model card).
ASPECT_RATIOS: Dict[str, Tuple[int, int]] = {
    "1:1": (1328, 1328),
    "16:9": (1664, 928),
    "9:16": (928, 1664),
    "4:3": (1472, 1140),
    "3:4": (1140, 1472),
    "3:2": (1584, 1056),
    "2:3": (1056, 1584),
}

EDIT_PLUS_MARKERS = ("2509", "2511", "edit-plus", "edit_plus")

DEFAULT_TRYON_PROMPT = (
    "The person in the first image, keeping their face, pose and background "
    "unchanged, wearing the garment shown in the second image. Preserve identity "
    "and lighting; match the garment's fabric, color, and details faithfully."
)

DEFAULT_NEGATIVE = " "

ImageInput = Union[str, Path, io.BytesIO, bytes, Image.Image]


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
                "diffusers is required to load image URLs: pip install -U diffusers"
            ) from exc
        return load_image(source).convert("RGB")
    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {source}")
    return Image.open(path).convert("RGB")


def _uses_edit_plus(model_id: str) -> bool:
    lowered = model_id.lower()
    return any(marker in lowered for marker in EDIT_PLUS_MARKERS)


class QwenImageLocalAdapter:
    """
    Local Hugging Face Diffusers adapter for Qwen-Image T2I, I2I, and try-on.

    Args:
        model_id: T2I weights. Defaults to ``QWEN_IMAGE_LOCAL_MODEL_ID`` /
            ``QWEN_IMAGE_LOCAL_PATH`` / ``Qwen/Qwen-Image-2512``.
        edit_model_id: Edit / multi-ref weights. Defaults to
            ``QWEN_IMAGE_EDIT_MODEL_ID`` / ``QWEN_IMAGE_EDIT_PATH`` /
            ``Qwen/Qwen-Image-Edit-2511``.
        device: ``"cuda"`` required (default auto).
        dtype: ``bfloat16`` (default), ``float16``, or ``float32``.
        cpu_offload: Enable ``enable_model_cpu_offload()`` (default True).
    """

    def __init__(
        self,
        model_id: Optional[str] = None,
        edit_model_id: Optional[str] = None,
        device: Optional[str] = None,
        dtype: str = "bfloat16",
        cpu_offload: bool = True,
    ):
        try:
            import torch
        except ImportError as exc:
            raise ImportError(
                "Qwen-Image local inference requires the 'local' extra: "
                "pip install opentryon[local]. Also upgrade Diffusers for "
                "QwenImagePipeline support: pip install -U diffusers transformers"
            ) from exc

        self.torch = torch
        self.model_id = (
            model_id
            or os.getenv("QWEN_IMAGE_LOCAL_PATH")
            or os.getenv("QWEN_IMAGE_LOCAL_MODEL_ID")
            or DEFAULT_T2I_MODEL_ID
        )
        self.edit_model_id = (
            edit_model_id
            or os.getenv("QWEN_IMAGE_EDIT_PATH")
            or os.getenv("QWEN_IMAGE_EDIT_MODEL_ID")
            or DEFAULT_EDIT_MODEL_ID
        )
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        if self.device == "cpu":
            raise RuntimeError(
                "Qwen-Image local inference requires a CUDA GPU. "
                "bf16 T2I is ~40GB+ VRAM; enable cpu_offload on smaller cards. "
                "CPU-only is not supported."
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
        self._t2i_pipe = None
        self._edit_pipe = None
        self._edit_plus = True

    def _place(self, pipe):
        if self.cpu_offload:
            pipe.enable_model_cpu_offload()
        else:
            pipe.to(self.device)
        return pipe

    def _load_t2i(self):
        if self._t2i_pipe is not None:
            return self._t2i_pipe
        try:
            from diffusers import QwenImagePipeline
        except ImportError as exc:
            raise ImportError(
                "QwenImagePipeline is missing. Upgrade Diffusers:\n"
                "  pip install -U diffusers transformers accelerate\n"
                "  # or: pip install git+https://github.com/huggingface/diffusers"
            ) from exc
        pipe = QwenImagePipeline.from_pretrained(self.model_id, torch_dtype=self.dtype)
        self._t2i_pipe = self._place(pipe)
        return self._t2i_pipe

    def _load_edit(self):
        if self._edit_pipe is not None:
            return self._edit_pipe
        use_plus = _uses_edit_plus(self.edit_model_id)
        if use_plus:
            try:
                from diffusers import QwenImageEditPlusPipeline
            except ImportError as exc:
                raise ImportError(
                    "QwenImageEditPlusPipeline is missing. Upgrade Diffusers:\n"
                    "  pip install -U diffusers transformers accelerate"
                ) from exc
            pipe = QwenImageEditPlusPipeline.from_pretrained(
                self.edit_model_id, torch_dtype=self.dtype
            )
            self._edit_plus = True
        else:
            try:
                from diffusers import QwenImageEditPipeline
            except ImportError as exc:
                raise ImportError(
                    "QwenImageEditPipeline is missing. Upgrade Diffusers:\n"
                    "  pip install -U diffusers transformers accelerate"
                ) from exc
            pipe = QwenImageEditPipeline.from_pretrained(
                self.edit_model_id, torch_dtype=self.dtype
            )
            self._edit_plus = False
        self._edit_pipe = self._place(pipe)
        return self._edit_pipe

    @staticmethod
    def _resolve_hw(
        width: Optional[int],
        height: Optional[int],
        aspect_ratio: Optional[str],
    ) -> Tuple[int, int]:
        if width and height:
            return int(width), int(height)
        key = aspect_ratio or "1:1"
        if key not in ASPECT_RATIOS:
            raise ValueError(
                f"Invalid aspect_ratio: {key!r}. Supported: {sorted(ASPECT_RATIOS)}"
            )
        return ASPECT_RATIOS[key]

    def _generator(self, seed: Optional[int]):
        if seed is None:
            return None
        return self.torch.Generator(device="cpu").manual_seed(int(seed))

    # -- public API ---------------------------------------------------------

    def generate_text_to_image(
        self,
        prompt: str,
        aspect_ratio: Optional[str] = "1:1",
        width: Optional[int] = None,
        height: Optional[int] = None,
        num_inference_steps: int = 50,
        true_cfg_scale: float = 4.0,
        negative_prompt: str = DEFAULT_NEGATIVE,
        seed: Optional[int] = None,
        num_images: int = 1,
    ) -> List[Image.Image]:
        """Generate image(s) from a text prompt (local Qwen-Image T2I)."""
        if not prompt:
            raise ValueError("prompt is required.")
        w, h = self._resolve_hw(width, height, aspect_ratio)
        pipe = self._load_t2i()
        with self.torch.inference_mode():
            out = pipe(
                prompt=prompt,
                negative_prompt=negative_prompt or DEFAULT_NEGATIVE,
                width=w,
                height=h,
                num_inference_steps=int(num_inference_steps),
                true_cfg_scale=float(true_cfg_scale),
                num_images_per_prompt=int(num_images),
                generator=self._generator(seed),
            )
        return list(out.images)

    def generate_image_edit(
        self,
        image: Union[ImageInput, List[ImageInput]],
        prompt: str,
        num_inference_steps: int = 40,
        true_cfg_scale: float = 4.0,
        guidance_scale: float = 1.0,
        negative_prompt: str = DEFAULT_NEGATIVE,
        seed: Optional[int] = None,
        num_images: int = 1,
    ) -> List[Image.Image]:
        """Edit one image, or 1–3 refs with Edit-Plus (2509 / 2511)."""
        images = image if isinstance(image, list) else [image]
        return self.generate_multi_image(
            images,
            prompt,
            num_inference_steps=num_inference_steps,
            true_cfg_scale=true_cfg_scale,
            guidance_scale=guidance_scale,
            negative_prompt=negative_prompt,
            seed=seed,
            num_images=num_images,
        )

    def generate_multi_image(
        self,
        images: List[ImageInput],
        prompt: str,
        num_inference_steps: int = 40,
        true_cfg_scale: float = 4.0,
        guidance_scale: float = 1.0,
        negative_prompt: str = DEFAULT_NEGATIVE,
        seed: Optional[int] = None,
        num_images: int = 1,
    ) -> List[Image.Image]:
        """Compose 1–3 reference images with a text instruction (Edit-Plus)."""
        if not prompt:
            raise ValueError("prompt is required.")
        if not images:
            raise ValueError("At least one input image is required.")
        if len(images) > 3:
            raise ValueError("Qwen-Image local I2I accepts at most 3 reference images.")
        pipe = self._load_edit()
        loaded = [_load_pil(img) for img in images]
        if not self._edit_plus:
            if len(loaded) != 1:
                raise ValueError(
                    f"{self.edit_model_id} is single-image QwenImageEditPipeline. "
                    "Use Qwen/Qwen-Image-Edit-2511 (or 2509) for 2–3 refs / VTON."
                )
            image_arg: Any = loaded[0]
        else:
            image_arg = loaded if len(loaded) > 1 else loaded[0]
        kwargs: Dict[str, Any] = {
            "image": image_arg,
            "prompt": prompt,
            "negative_prompt": negative_prompt or DEFAULT_NEGATIVE,
            "num_inference_steps": int(num_inference_steps),
            "true_cfg_scale": float(true_cfg_scale),
            "num_images_per_prompt": int(num_images),
            "generator": self._generator(seed),
        }
        if self._edit_plus:
            kwargs["guidance_scale"] = float(guidance_scale)
        with self.torch.inference_mode():
            out = pipe(**kwargs)
        return list(out.images)

    @staticmethod
    def build_tryon_prompt(
        prompt: Optional[str] = None,
        garment_description: Optional[str] = None,
    ) -> str:
        """Build the styling prompt for a virtual try-on composition."""
        if prompt:
            return prompt
        if garment_description:
            return (
                "The person in the first image, keeping their face, pose and "
                f"background unchanged, wearing the {garment_description} shown "
                "in the second image. Preserve identity and lighting; match the "
                "garment's fabric, color, and details faithfully."
            )
        return DEFAULT_TRYON_PROMPT

    def generate_virtual_tryon(
        self,
        person: Optional[ImageInput] = None,
        garment: Optional[ImageInput] = None,
        *,
        source_image: Optional[ImageInput] = None,
        reference_image: Optional[ImageInput] = None,
        model_image: Optional[ImageInput] = None,
        cloth_image: Optional[ImageInput] = None,
        person_image: Optional[ImageInput] = None,
        garment_image: Optional[ImageInput] = None,
        prompt: Optional[str] = None,
        garment_description: Optional[str] = None,
        num_inference_steps: int = 40,
        true_cfg_scale: float = 4.0,
        guidance_scale: float = 1.0,
        negative_prompt: str = DEFAULT_NEGATIVE,
        seed: Optional[int] = None,
        num_images: int = 1,
    ) -> List[Image.Image]:
        """
        Virtual try-on via local Qwen-Image-Edit-Plus: person (first) + garment.

        Needs Edit-Plus weights (2509 / 2511). Not a dedicated garment-fit model.
        """
        resolved_person = person or source_image or person_image or model_image
        resolved_garment = garment or reference_image or garment_image or cloth_image
        if resolved_person is None:
            raise ValueError(
                "Person image is required. Pass person, source_image, person_image, "
                "or model_image."
            )
        if resolved_garment is None:
            raise ValueError(
                "Garment image is required. Pass garment, reference_image, "
                "garment_image, or cloth_image."
            )
        styling = self.build_tryon_prompt(
            prompt=prompt, garment_description=garment_description
        )
        return self.generate_multi_image(
            images=[resolved_person, resolved_garment],
            prompt=styling,
            num_inference_steps=num_inference_steps,
            true_cfg_scale=true_cfg_scale,
            guidance_scale=guidance_scale,
            negative_prompt=negative_prompt,
            seed=seed,
            num_images=num_images,
        )
