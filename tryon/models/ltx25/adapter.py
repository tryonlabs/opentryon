"""
LTX-2.5 local Diffusers adapter (open weights).

Runs Lightricks LTX-2.5 on a local / cloud GPU via Hugging Face Diffusers
(`LTX2Pipeline` / `LTX2ImageToVideoPipeline`). Supports text-to-video and
image-to-video with synchronized audio encoded into an MP4.

Weights: https://huggingface.co/Lightricks/LTX-2.5-Diffusers
Product: https://ltx.io/model/ltx-2-5
License: LTX-2.x Community License (free commercial use under $10M ARR;
         gated HF access — set HF_TOKEN after accepting the model terms).

Requirements:
  - CUDA GPU (practical floor ~16GB VRAM with CPU offload; 24GB+ preferred)
  - `pip install opentryon[local]` plus Diffusers **from main**:
      pip install "git+https://github.com/huggingface/diffusers"
    (LTX-2.5 is not in a stable Diffusers release yet.)
  - accelerate, torch

Examples:
    >>> from tryon.models import LTX25Adapter
    >>> adapter = LTX25Adapter()
    >>> video = adapter.generate_text_to_video(
    ...     prompt="A fashion model walking a runway at dusk, camera tracking, soft ambient sound",
    ...     width=960,
    ...     height=544,
    ...     num_frames=121,
    ... )
    >>> open("out.mp4", "wb").write(video)

    >>> video = adapter.generate_image_to_video(
    ...     image="look.jpg",
    ...     prompt="Gentle fabric motion as the model turns, atelier ambience",
    ... )
"""

from __future__ import annotations

import io
import os
import tempfile
from typing import Optional, Union

from PIL import Image

DEFAULT_MODEL_ID = "Lightricks/LTX-2.5-Diffusers"
DEFAULT_WIDTH = 960
DEFAULT_HEIGHT = 544
DEFAULT_NUM_FRAMES = 121
DEFAULT_FRAME_RATE = 24.0


def _load_pil(image: Union[str, io.BytesIO, Image.Image, bytes]) -> Image.Image:
    if isinstance(image, Image.Image):
        return image.convert("RGB")
    if isinstance(image, str):
        if image.startswith(("http://", "https://")):
            try:
                from diffusers.utils import load_image
            except ImportError as exc:
                raise ImportError(
                    "diffusers is required to load image URLs. "
                    'Install with: pip install "git+https://github.com/huggingface/diffusers"'
                ) from exc
            return load_image(image).convert("RGB")
        if os.path.exists(image):
            return Image.open(image).convert("RGB")
        raise ValueError(f"Image path does not exist: {image}")
    if isinstance(image, (bytes, bytearray)):
        return Image.open(io.BytesIO(bytes(image))).convert("RGB")
    if hasattr(image, "read"):
        image.seek(0)
        return Image.open(image).convert("RGB")
    raise ValueError("Unsupported image input for LTX-2.5 local adapter.")


class LTX25Adapter:
    """Local open-weight LTX-2.5 video adapter (Diffusers)."""

    def __init__(
        self,
        model_id: Optional[str] = None,
        device: Optional[str] = None,
        dtype: str = "bfloat16",
        cpu_offload: bool = True,
    ):
        try:
            import torch
            from diffusers import LTX2Pipeline
        except ImportError as exc:
            raise ImportError(
                "LTX-2.5 local inference requires torch and Diffusers with LTX2 support. "
                "Install local extras, then Diffusers from main:\n"
                "  pip install opentryon[local]\n"
                '  pip install "git+https://github.com/huggingface/diffusers"\n'
                f"Original error: {exc}"
            ) from exc

        self.torch = torch
        self.model_id = (
            model_id
            or os.getenv("LTX_MODEL_PATH")
            or os.getenv("LTX_MODEL_ID")
            or DEFAULT_MODEL_ID
        )
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        if self.device == "cpu":
            raise RuntimeError(
                "LTX-2.5 local inference requires a CUDA GPU. "
                "CPU-only runs are not supported."
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

        self._t2v_pipe = None
        self._i2v_pipe = None

    def _import_utils(self):
        try:
            from diffusers.pipelines.ltx2.utils import (
                DEFAULT_NEGATIVE_PROMPT,
                DISTILLED_SIGMA_VALUES,
            )
            from diffusers.utils import encode_video
        except ImportError as exc:
            raise ImportError(
                "Your Diffusers install does not include LTX-2 helpers. "
                'Upgrade with: pip install "git+https://github.com/huggingface/diffusers"\n'
                f"Original error: {exc}"
            ) from exc
        return DEFAULT_NEGATIVE_PROMPT, DISTILLED_SIGMA_VALUES, encode_video

    def _load_t2v(self):
        if self._t2v_pipe is not None:
            return self._t2v_pipe
        from diffusers import LTX2Pipeline

        pipe = LTX2Pipeline.from_pretrained(self.model_id, dtype=self.dtype)
        if self.cpu_offload:
            pipe.enable_model_cpu_offload()
        else:
            pipe.to(self.device)
        self._t2v_pipe = pipe
        return pipe

    def _load_i2v(self):
        if self._i2v_pipe is not None:
            return self._i2v_pipe
        try:
            from diffusers import LTX2ImageToVideoPipeline
        except ImportError as exc:
            raise ImportError(
                "LTX2ImageToVideoPipeline is missing. "
                'Install Diffusers from main: pip install "git+https://github.com/huggingface/diffusers"'
            ) from exc

        pipe = LTX2ImageToVideoPipeline.from_pretrained(self.model_id, dtype=self.dtype)
        if self.cpu_offload:
            pipe.enable_model_cpu_offload()
        else:
            pipe.to(self.device)
        self._i2v_pipe = pipe
        return pipe

    def _encode_mp4(self, pipe, video, audio, frame_rate: float, encode_video) -> bytes:
        sample_rate = getattr(
            getattr(pipe, "vocoder", None), "config", None
        )
        audio_sr = 48000
        if sample_rate is not None and hasattr(sample_rate, "output_sampling_rate"):
            audio_sr = int(sample_rate.output_sampling_rate)

        audio_tensor = None
        if audio is not None:
            try:
                audio_tensor = audio[0].float().cpu()
            except Exception:
                audio_tensor = audio

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            out_path = tmp.name
        try:
            encode_kwargs = {
                "fps": int(frame_rate) if float(frame_rate).is_integer() else frame_rate,
                "output_path": out_path,
            }
            # video[0] is the first batch item (numpy frames)
            frames = video[0] if isinstance(video, (list, tuple)) else video
            if audio_tensor is not None:
                encode_kwargs["audio"] = audio_tensor
                encode_kwargs["audio_sample_rate"] = audio_sr
            encode_video(frames, **encode_kwargs)
            with open(out_path, "rb") as f:
                return f.read()
        finally:
            try:
                os.unlink(out_path)
            except OSError:
                pass

    def _distilled_kwargs(
        self,
        *,
        prompt: str,
        negative_prompt: Optional[str],
        width: int,
        height: int,
        num_frames: int,
        frame_rate: float,
        seed: Optional[int],
        default_neg,
        sigmas,
    ) -> dict:
        if width % 32 != 0 or height % 32 != 0:
            raise ValueError("width and height must be divisible by 32.")
        if num_frames % 8 != 1:
            raise ValueError(
                "num_frames must satisfy num_frames % 8 == 1 "
                f"(got {num_frames}; try 97, 121, or 129)."
            )

        generator = None
        if seed is not None:
            generator = self.torch.Generator(device="cuda").manual_seed(int(seed))

        return {
            "prompt": prompt,
            "negative_prompt": negative_prompt or default_neg,
            "width": int(width),
            "height": int(height),
            "num_frames": int(num_frames),
            "frame_rate": float(frame_rate),
            "sigmas": sigmas,
            "guidance_scale": 1.0,
            "audio_guidance_scale": 1.0,
            "stg_scale": 0.0,
            "audio_stg_scale": 0.0,
            "modality_scale": 1.0,
            "audio_modality_scale": 1.0,
            "generator": generator,
            "output_type": "np",
            "return_dict": False,
        }

    def generate_text_to_video(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        width: int = DEFAULT_WIDTH,
        height: int = DEFAULT_HEIGHT,
        num_frames: int = DEFAULT_NUM_FRAMES,
        frame_rate: float = DEFAULT_FRAME_RATE,
        seed: Optional[int] = None,
    ) -> bytes:
        if not prompt:
            raise ValueError("prompt is required.")
        default_neg, sigmas, encode_video = self._import_utils()
        pipe = self._load_t2v()
        kwargs = self._distilled_kwargs(
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            num_frames=num_frames,
            frame_rate=frame_rate,
            seed=seed,
            default_neg=default_neg,
            sigmas=sigmas,
        )
        video, audio = pipe(**kwargs)
        return self._encode_mp4(pipe, video, audio, frame_rate, encode_video)

    def generate_image_to_video(
        self,
        image: Union[str, io.BytesIO, Image.Image, bytes],
        prompt: str,
        negative_prompt: Optional[str] = None,
        width: int = DEFAULT_WIDTH,
        height: int = DEFAULT_HEIGHT,
        num_frames: int = DEFAULT_NUM_FRAMES,
        frame_rate: float = DEFAULT_FRAME_RATE,
        seed: Optional[int] = None,
    ) -> bytes:
        if not prompt:
            raise ValueError("prompt is required.")
        default_neg, sigmas, encode_video = self._import_utils()
        pipe = self._load_i2v()
        pil = _load_pil(image)
        kwargs = self._distilled_kwargs(
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            num_frames=num_frames,
            frame_rate=frame_rate,
            seed=seed,
            default_neg=default_neg,
            sigmas=sigmas,
        )
        kwargs["image"] = pil
        video, audio = pipe(**kwargs)
        return self._encode_mp4(pipe, video, audio, frame_rate, encode_video)
