"""
Leffa local virtual try-on adapter (CVPR 2025).

Official code: https://github.com/franciszzj/Leffa
Weights:      https://huggingface.co/franciszzj/Leffa
Paper:        https://arxiv.org/abs/2412.08486

Path B (GPU). Learning flow fields in attention for person + garment try-on
(VITON-HD / DressCode checkpoints) and optional pose transfer.

Code license is MIT. Confirm the Hugging Face weight card before commercial
D2C use. First run downloads the GitHub source (or uses ``LEFFA_HOME``) and
the HF snapshot (DensePose / SCHP / try-on pth).

Requirements:
    pip install opentryon[local]

Examples:
    >>> from tryon.models import LeffaAdapter
    >>> adapter = LeffaAdapter()
    >>> images = adapter.generate_and_decode("person.jpg", "garment.jpg")
"""

from __future__ import annotations

import io
import os
import sys
import warnings
import zipfile
from pathlib import Path
from typing import Any, List, Optional, Union

from PIL import Image, ImageDraw

ImageInput = Union[str, Path, io.BytesIO, bytes, Image.Image]

LEFFA_CODE_URL = "https://github.com/franciszzj/Leffa/archive/refs/heads/main.zip"
LEFFA_WEIGHTS_REPO = "franciszzj/Leffa"
DEFAULT_SIZE = (768, 1024)


def _require_local() -> None:
    try:
        import torch  # noqa: F401
        import diffusers  # noqa: F401
        import transformers  # noqa: F401
        from huggingface_hub import snapshot_download  # noqa: F401
    except ImportError as exc:
        raise ImportError(
            "Leffa local inference needs torch, diffusers, transformers, and "
            "huggingface_hub. Install with: pip install opentryon[local]"
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


def _cache_root() -> Path:
    hf_home = os.getenv("HF_HOME") or str(Path.home() / ".cache" / "huggingface")
    return Path(hf_home) / "opentryon-leffa"


def _find_leffa_package(root: Path) -> Optional[Path]:
    if (root / "leffa" / "model.py").is_file():
        return root
    for child in root.iterdir() if root.is_dir() else []:
        if child.is_dir() and (child / "leffa" / "model.py").is_file():
            return child
    return None


def _ensure_leffa_source() -> Path:
    env = os.getenv("LEFFA_HOME")
    if env:
        found = _find_leffa_package(Path(env).expanduser())
        if found is not None:
            return found
        raise FileNotFoundError(
            f"LEFFA_HOME={env} does not contain leffa/model.py. "
            "Clone https://github.com/franciszzj/Leffa or unset LEFFA_HOME."
        )
    dest = _cache_root() / "src"
    found = _find_leffa_package(dest)
    if found is not None:
        return found
    dest.mkdir(parents=True, exist_ok=True)
    zip_path = dest / "leffa-main.zip"
    try:
        import urllib.request

        urllib.request.urlretrieve(LEFFA_CODE_URL, zip_path)
    except Exception as exc:
        raise RuntimeError(
            "Could not download Leffa source from GitHub. Clone "
            "https://github.com/franciszzj/Leffa and set LEFFA_HOME to that path."
        ) from exc
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(dest)
    found = _find_leffa_package(dest)
    if found is None:
        raise RuntimeError("Leffa zip extracted but leffa/model.py was not found.")
    return found


def _ensure_weights(ckpt_dir: Optional[str] = None) -> Path:
    from huggingface_hub import snapshot_download

    if ckpt_dir:
        path = Path(ckpt_dir).expanduser()
        if not path.is_dir():
            raise FileNotFoundError(f"LEFFA_CKPT / ckpt_dir is not a directory: {path}")
        return path
    env = os.getenv("LEFFA_CKPT")
    if env:
        path = Path(env).expanduser()
        if path.is_dir():
            return path
    local_dir = _cache_root() / "ckpts"
    snapshot_download(repo_id=LEFFA_WEIGHTS_REPO, local_dir=str(local_dir))
    return local_dir


def _resize_and_center(image: Image.Image, width: int, height: int) -> Image.Image:
    image = image.convert("RGB")
    src_w, src_h = image.size
    scale = min(width / src_w, height / src_h)
    new_w, new_h = max(1, int(src_w * scale)), max(1, int(src_h * scale))
    resized = image.resize((new_w, new_h), Image.LANCZOS)
    canvas = Image.new("RGB", (width, height), (255, 255, 255))
    canvas.paste(resized, ((width - new_w) // 2, (height - new_h) // 2))
    return canvas


def _geometric_mask(person: Image.Image, garment_type: str) -> Image.Image:
    w, h = person.size
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    kind = (garment_type or "upper_body").lower().replace("-", "_")
    if kind in {"lower", "lower_body", "bottoms"}:
        box = (int(w * 0.18), int(h * 0.42), int(w * 0.82), int(h * 0.98))
    elif kind in {"dress", "dresses", "one_piece"}:
        box = (int(w * 0.14), int(h * 0.12), int(w * 0.86), int(h * 0.94))
    else:
        box = (int(w * 0.14), int(h * 0.10), int(w * 0.86), int(h * 0.62))
    draw.rounded_rectangle(box, radius=max(8, w // 20), fill=255)
    return mask


def _blank_densepose(person: Image.Image) -> Image.Image:
    return Image.new("RGB", person.size, (128, 128, 128))


class LeffaAdapter:
    """
    Local Leffa adapter (virtual try-on; optional pose transfer).

    Args:
        ckpt_dir: Hugging Face snapshot or local dir with virtual_tryon.pth.
        src_dir: Clone of franciszzj/Leffa (else ``LEFFA_HOME`` / auto-download).
        vt_model_type: ``viton_hd`` (default) or ``dress_code``.
        device: ``cuda`` / ``cpu``.
        dtype: ``float16`` (official demo default).
    """

    def __init__(
        self,
        ckpt_dir: Optional[str] = None,
        src_dir: Optional[str] = None,
        vt_model_type: str = "viton_hd",
        device: Optional[str] = None,
        dtype: str = "float16",
    ):
        _require_local()
        import torch

        self.ckpt_dir_arg = ckpt_dir
        self.src_dir_arg = src_dir
        self.vt_model_type = vt_model_type or "viton_hd"
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.dtype = dtype
        self._src: Optional[Path] = None
        self._ckpt: Optional[Path] = None
        self._inference: dict = {}
        self._transform = None
        self._masker = None

    def _prepare_imports(self) -> Any:
        src = Path(self.src_dir_arg).expanduser() if self.src_dir_arg else _ensure_leffa_source()
        src_str = str(src)
        if src_str not in sys.path:
            sys.path.insert(0, src_str)
        self._src = src
        self._ckpt = _ensure_weights(self.ckpt_dir_arg)
        return src

    def _load_inference(self, control_type: str, vt_model_type: str):
        key = (control_type, vt_model_type if control_type == "virtual_tryon" else "pose")
        if key in self._inference:
            return self._inference[key]
        self._prepare_imports()
        from leffa.inference import LeffaInference
        from leffa.model import LeffaModel

        ckpt = self._ckpt
        assert ckpt is not None
        if control_type == "pose_transfer":
            pretrained = str(ckpt / "stable-diffusion-xl-1.0-inpainting-0.1")
            weights = str(ckpt / "pose_transfer.pth")
        elif vt_model_type == "dress_code":
            pretrained = str(ckpt / "stable-diffusion-inpainting")
            weights = str(ckpt / "virtual_tryon_dc.pth")
        else:
            pretrained = str(ckpt / "stable-diffusion-inpainting")
            weights = str(ckpt / "virtual_tryon.pth")
        if not Path(weights).is_file():
            raise FileNotFoundError(
                f"Leffa checkpoint missing: {weights}. Re-download "
                f"{LEFFA_WEIGHTS_REPO} or set LEFFA_CKPT."
            )
        if not Path(pretrained).exists():
            # HF snapshot may store the inpainting UNet under this name; if
            # not, fall back to the Hub id used by the official app.
            pretrained = (
                "diffusers/stable-diffusion-xl-1.0-inpainting-0.1"
                if control_type == "pose_transfer"
                else "runwayml/stable-diffusion-inpainting"
            )
        model = LeffaModel(
            pretrained_model_name_or_path=pretrained,
            pretrained_model=weights,
            dtype=self.dtype,
        )
        inference = LeffaInference(model=model)
        self._inference[key] = inference
        return inference

    def _try_official_mask_densepose(
        self,
        src_image: Image.Image,
        garment_type: str,
        vt_model_type: str,
    ):
        """Use Leffa's AutoMasker / DensePose when those extras imported cleanly."""
        self._prepare_imports()
        try:
            import numpy as np
            from leffa_utils.densepose_predictor import DensePosePredictor
            from leffa_utils.utils import get_agnostic_mask_dc, get_agnostic_mask_hd
            from preprocess.humanparsing.run_parsing import Parsing
            from preprocess.openpose.run_openpose import OpenPose
        except Exception as exc:
            warnings.warn(
                f"Leffa AutoMasker extras unavailable ({exc}). "
                "Pass --mask-image (and optionally --densepose-image), or install "
                "the full Leffa demo deps from the upstream repo."
            )
            return None, None
        ckpt = self._ckpt
        assert ckpt is not None
        parsing = Parsing(
            atr_path=str(ckpt / "humanparsing" / "parsing_atr.onnx"),
            lip_path=str(ckpt / "humanparsing" / "parsing_lip.onnx"),
        )
        openpose = OpenPose(body_model_path=str(ckpt / "openpose" / "body_pose_model.pth"))
        model_parse, _ = parsing(src_image.resize((384, 512)))
        keypoints = openpose(src_image.resize((384, 512)))
        if vt_model_type == "dress_code":
            mask = get_agnostic_mask_dc(model_parse, keypoints, garment_type)
        else:
            mask = get_agnostic_mask_hd(model_parse, keypoints, garment_type)
        mask = mask.resize(src_image.size)
        predictor = DensePosePredictor(
            config_path=str(ckpt / "densepose" / "densepose_rcnn_R_50_FPN_s1x.yaml"),
            weights_path=str(ckpt / "densepose" / "model_final_162be9.pkl"),
        )
        src_array = np.array(src_image)
        if vt_model_type == "dress_code":
            iuv = predictor.predict_iuv(src_array)
            seg = iuv[:, :, 0:1]
            seg = np.concatenate([seg] * 3, axis=-1)
            densepose = Image.fromarray(seg)
        else:
            seg = predictor.predict_seg(src_array)[:, :, ::-1]
            densepose = Image.fromarray(seg)
        return mask, densepose

    def generate_and_decode(
        self,
        person: ImageInput,
        garment: ImageInput,
        mask: Optional[ImageInput] = None,
        densepose: Optional[ImageInput] = None,
        garment_type: str = "upper_body",
        vt_model_type: Optional[str] = None,
        num_inference_steps: int = 30,
        guidance_scale: float = 2.5,
        seed: int = 42,
        ref_acceleration: bool = False,
        repaint: bool = False,
        control_type: str = "virtual_tryon",
    ) -> List[Image.Image]:
        """Virtual try-on (default) or pose transfer when ``control_type='pose_transfer'``."""
        vt = vt_model_type or self.vt_model_type
        src_image = _resize_and_center(_load_pil(person), *DEFAULT_SIZE)
        ref_image = _resize_and_center(_load_pil(garment), *DEFAULT_SIZE)

        mask_im: Optional[Image.Image] = None
        dense_im: Optional[Image.Image] = None
        if mask is not None:
            mask_im = _resize_and_center(_load_pil(mask), *DEFAULT_SIZE).convert("L")
        if densepose is not None:
            dense_im = _resize_and_center(_load_pil(densepose), *DEFAULT_SIZE)

        if control_type == "pose_transfer":
            mask_im = mask_im or Image.new("L", DEFAULT_SIZE, 255)
            if dense_im is None:
                _, dense_im = self._try_official_mask_densepose(src_image, garment_type, "dress_code")
                dense_im = dense_im or _blank_densepose(src_image)
        else:
            if mask_im is None or dense_im is None:
                auto_mask, auto_dp = self._try_official_mask_densepose(
                    src_image, garment_type, vt
                )
                mask_im = mask_im or auto_mask or _geometric_mask(src_image, garment_type)
                dense_im = dense_im or auto_dp or _blank_densepose(src_image)
                if auto_mask is None:
                    warnings.warn(
                        "Using a geometric clothing mask and a blank DensePose map. "
                        "Quality is much better with Leffa's AutoMasker extras or "
                        "explicit --mask-image / --densepose-image."
                    )

        self._prepare_imports()
        from leffa.transform import LeffaTransform

        if self._transform is None:
            self._transform = LeffaTransform()
        data = {
            "src_image": [src_image],
            "ref_image": [ref_image],
            "mask": [mask_im],
            "densepose": [dense_im],
        }
        data = self._transform(data)
        inference = self._load_inference(control_type, vt)
        output = inference(
            data,
            ref_acceleration=bool(ref_acceleration),
            num_inference_steps=int(num_inference_steps),
            guidance_scale=float(guidance_scale),
            seed=int(seed),
            repaint=bool(repaint),
        )
        generated = output["generated_image"]
        if isinstance(generated, list):
            return list(generated)
        return [generated]
