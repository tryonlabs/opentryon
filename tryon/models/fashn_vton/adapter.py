"""
FASHN VTON v1.5 Local Adapter (open weights, Apache-2.0)

FASHN VTON v1.5 is a 972M-parameter virtual try-on model that generates
photorealistic results **directly in pixel space without segmentation masks**.
Given a person photo and a garment image (worn on a model *or* a flat-lay
product shot) it renders the person wearing the garment. Unlike the other
local try-on models in this repo (Leffa: MIT code; CatVTON: CC BY-NC-SA) the
code **and** weights are Apache-2.0, so it is the commercial-friendly local
option. The hosted equivalents are ``fashn-tryon-max`` / ``fashn-tryon-v1.6``.

Third-party components: DWPose and YOLOX (Apache-2.0) and ``fashn-human-parser``
(see its README for licence terms -- review before commercial use).

Weights (~2 GB total):
- ``fashn-ai/fashn-vton-1.5``  -> ``model.safetensors`` (bfloat16; runs in bf16 on
  Ampere+ GPUs, float32 on older GPUs / CPU)
- ``fashn-ai/DWPose``          -> ``dwpose/yolox_l.onnx``, ``dwpose/dw-ll_ucoco_384.onnx``
- ``fashn-human-parser`` weights (~244 MB) auto-cache in the Hugging Face cache

If ``weights_dir`` is not given the adapter uses ``FASHN_VTON_WEIGHTS_DIR`` and
otherwise downloads the weights to ``~/.cache/opentryon/fashn-vton-1.5`` on
first use.

Reference:
https://github.com/fashn-AI/fashn-vton-1.5
https://huggingface.co/fashn-ai/fashn-vton-1.5

Requirements:
    pip install opentryon[local]
    pip install "git+https://github.com/fashn-AI/fashn-vton-1.5.git"
The package pulls ``onnxruntime-gpu`` for pose detection (needs a working CUDA
setup); for CPU-only hosts run
``pip uninstall onnxruntime-gpu && pip install onnxruntime``.

Examples:
    >>> from tryon.models.fashn_vton import FashnVTONLocalAdapter
    >>> adapter = FashnVTONLocalAdapter()
    >>> images = adapter.generate_and_decode("person.jpg", "garment.jpg", category="tops")
    >>> images[0].save("tryon.png")
"""

from __future__ import annotations

import io
import os
from pathlib import Path
from typing import List, Optional, Union

from PIL import Image

ImageInput = Union[str, Path, io.BytesIO, bytes, Image.Image]

TRYON_REPO = "fashn-ai/fashn-vton-1.5"
DWPOSE_REPO = "fashn-ai/DWPose"
DWPOSE_FILES = ("yolox_l.onnx", "dw-ll_ucoco_384.onnx")
DEFAULT_WEIGHTS_DIR = Path("~/.cache/opentryon/fashn-vton-1.5").expanduser()

CATEGORIES = ("tops", "bottoms", "one-pieces")
GARMENT_PHOTO_TYPES = ("model", "flat-lay")
MAX_SAMPLES = 4


def _load_pil(image: ImageInput) -> Image.Image:
    if isinstance(image, Image.Image):
        return image.convert("RGB")
    if isinstance(image, (bytes, bytearray)):
        return Image.open(io.BytesIO(bytes(image))).convert("RGB")
    if hasattr(image, "read"):
        image.seek(0)
        return Image.open(image).convert("RGB")
    path_or_url = str(image)
    if path_or_url.startswith(("http://", "https://")):
        import requests

        resp = requests.get(path_or_url, timeout=60)
        resp.raise_for_status()
        return Image.open(io.BytesIO(resp.content)).convert("RGB")
    if not os.path.exists(path_or_url):
        raise ValueError(f"Image path does not exist: {path_or_url}")
    return Image.open(path_or_url).convert("RGB")


def _weights_complete(weights_dir: Path) -> bool:
    return (weights_dir / "model.safetensors").exists() and all(
        (weights_dir / "dwpose" / name).exists() for name in DWPOSE_FILES
    )


def ensure_weights(weights_dir: Path) -> Path:
    """Download ``model.safetensors`` and the DWPose ONNX files if missing."""
    if _weights_complete(weights_dir):
        return weights_dir
    try:
        from huggingface_hub import hf_hub_download
    except ImportError as exc:
        raise ImportError(
            "huggingface_hub is required to download FASHN VTON weights. "
            "Install with: pip install opentryon[local]"
        ) from exc
    weights_dir.mkdir(parents=True, exist_ok=True)
    hf_hub_download(repo_id=TRYON_REPO, filename="model.safetensors", local_dir=str(weights_dir))
    for name in DWPOSE_FILES:
        hf_hub_download(repo_id=DWPOSE_REPO, filename=name, local_dir=str(weights_dir / "dwpose"))
    return weights_dir


class FashnVTONLocalAdapter:
    """
    Local adapter for the open-weight FASHN VTON v1.5 pipeline.

    Args:
        weights_dir: Directory holding ``model.safetensors`` and ``dwpose/``.
            Defaults to ``FASHN_VTON_WEIGHTS_DIR`` or
            ``~/.cache/opentryon/fashn-vton-1.5`` (auto-downloaded on first use).
        device: ``cuda`` / ``cpu``. Defaults to the pipeline's own choice (GPU when available).
    """

    def __init__(self, weights_dir: Optional[str] = None, device: Optional[str] = None):
        try:
            import torch  # noqa: F401
            from fashn_vton import TryOnPipeline
        except ImportError as exc:
            raise ImportError(
                "FASHN VTON v1.5 local inference needs torch and the fashn_vton package. Install with:\n"
                "  pip install opentryon[local]\n"
                '  pip install "git+https://github.com/fashn-AI/fashn-vton-1.5.git"\n'
                "(CPU-only hosts: pip uninstall onnxruntime-gpu && pip install onnxruntime)\n"
                f"Original error: {exc}"
            ) from exc
        self._Pipeline = TryOnPipeline
        self.weights_dir = Path(
            weights_dir or os.getenv("FASHN_VTON_WEIGHTS_DIR") or DEFAULT_WEIGHTS_DIR
        ).expanduser()
        self.device = device
        self._pipeline = None

    def _load(self):
        if self._pipeline is None:
            ensure_weights(self.weights_dir)
            self._pipeline = self._Pipeline(weights_dir=str(self.weights_dir), device=self.device)
        return self._pipeline

    def generate_and_decode(
        self,
        person: ImageInput,
        garment: ImageInput,
        category: str = "tops",
        garment_photo_type: str = "model",
        num_samples: int = 1,
        num_timesteps: int = 30,
        guidance_scale: float = 1.5,
        seed: Optional[int] = 42,
        segmentation_free: bool = True,
    ) -> List[Image.Image]:
        """Try ``garment`` on ``person`` and return the generated PIL images.

        Args:
            category: ``tops`` (t-shirts, blouses, jackets), ``bottoms`` (pants, skirts, shorts)
                or ``one-pieces`` (dresses, jumpsuits).
            garment_photo_type: ``model`` if the garment is worn by someone, ``flat-lay`` for product shots.
            num_samples: 1-4 images per call.
            num_timesteps: diffusion steps (20 fast, 30 balanced, 50 quality).
            guidance_scale: classifier-free guidance strength (upstream default 1.5).
            segmentation_free: default True preserves body features and allows unconstrained garment volume.
        """
        if category not in CATEGORIES:
            raise ValueError(f"category must be one of {list(CATEGORIES)} (got {category!r}).")
        if garment_photo_type not in GARMENT_PHOTO_TYPES:
            raise ValueError(
                f"garment_photo_type must be one of {list(GARMENT_PHOTO_TYPES)} (got {garment_photo_type!r})."
            )
        if not 1 <= int(num_samples) <= MAX_SAMPLES:
            raise ValueError(f"num_samples must be between 1 and {MAX_SAMPLES} (got {num_samples}).")
        if int(num_timesteps) < 1:
            raise ValueError("num_timesteps must be >= 1.")

        person_img = _load_pil(person)
        garment_img = _load_pil(garment)
        result = self._load()(
            person_image=person_img,
            garment_image=garment_img,
            category=category,
            garment_photo_type=garment_photo_type,
            num_samples=int(num_samples),
            num_timesteps=int(num_timesteps),
            guidance_scale=float(guidance_scale),
            seed=seed,
            segmentation_free=bool(segmentation_free),
        )
        return list(result.images)
