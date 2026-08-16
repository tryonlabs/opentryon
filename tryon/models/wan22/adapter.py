"""
Wan 2.2 local Diffusers adapter (open weights).

Runs Alibaba Wan open-weight video models on a local CUDA GPU via Hugging Face
Diffusers (``WanPipeline`` / ``WanImageToVideoPipeline``). Default checkpoint
is the consumer-friendly TI2V-5B unified T2V+I2V model.

Weights:
  https://huggingface.co/Wan-AI/Wan2.2-TI2V-5B-Diffusers
  https://huggingface.co/Wan-AI/Wan2.2-T2V-A14B-Diffusers
  https://huggingface.co/Wan-AI/Wan2.2-I2V-A14B-Diffusers

Docs: https://huggingface.co/docs/diffusers/en/api/pipelines/wan

Env:
  WAN_MODEL_ID / WAN_MODEL_PATH
  HF_TOKEN (if gated)

Examples:
    >>> from tryon.models import Wan22Adapter
    >>> adapter = Wan22Adapter()
    >>> video = adapter.generate_text_to_video(
    ...     prompt="A fashion model walking a runway at dusk",
    ...     num_frames=81,
    ... )
"""

from __future__ import annotations

import io
import os
import tempfile
from typing import Optional, Union

from PIL import Image

DEFAULT_MODEL_ID = "Wan-AI/Wan2.2-TI2V-5B-Diffusers"
DEFAULT_NUM_FRAMES = 81
DEFAULT_FPS = 16


def _load_pil(image: Union[str, io.BytesIO, Image.Image, bytes]) -> Image.Image:
    if isinstance(image, Image.Image):
        return image.convert("RGB")
    if isinstance(image, str):
        if image.startswith(("http://", "https://")):
            try:
                from diffusers.utils import load_image
            except ImportError as exc:
                raise ImportError(
                    "diffusers is required to load image URLs."
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
    raise ValueError("Unsupported image input for Wan local adapter.")


class Wan22Adapter:
    """Local open-weight Wan 2.2 video adapter (Diffusers)."""

    def __init__(
        self,
        model_id: Optional[str] = None,
        device: Optional[str] = None,
        dtype: str = "bfloat16",
        cpu_offload: bool = True,
    ):
        try:
            import torch
            from diffusers import WanPipeline  # noqa: F401
        except ImportError as exc:
            raise ImportError(
                "Wan local inference requires torch and Diffusers with Wan support.\n"
                "  pip install opentryon[local]\n"
                "  pip install -U diffusers transformers accelerate ftfy\n"
                f"Original error: {exc}"
            ) from exc

        self.torch = torch
        self.model_id = (
            model_id
            or os.getenv("WAN_MODEL_PATH")
            or os.getenv("WAN_MODEL_ID")
            or DEFAULT_MODEL_ID
        )
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        if self.device == "cpu":
            raise RuntimeError(
                "Wan local inference requires a CUDA GPU. CPU-only is not supported."
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

    def _load_t2v(self):
        if self._t2v_pipe is not None:
            return self._t2v_pipe
        from diffusers import WanPipeline

        pipe = WanPipeline.from_pretrained(self.model_id, torch_dtype=self.dtype)
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
            from diffusers import WanImageToVideoPipeline
        except ImportError as exc:
            raise ImportError(
                "WanImageToVideoPipeline missing. Upgrade diffusers."
            ) from exc
        # TI2V-5B uses WanPipeline for both; I2V-A14B uses WanImageToVideoPipeline.
        try:
            pipe = WanImageToVideoPipeline.from_pretrained(
                self.model_id, torch_dtype=self.dtype
            )
        except Exception:
            # Fall back: some unified checkpoints load as WanPipeline with image=
            pipe = self._load_t2v()
            self._i2v_pipe = pipe
            return pipe
        if self.cpu_offload:
            pipe.enable_model_cpu_offload()
        else:
            pipe.to(self.device)
        self._i2v_pipe = pipe
        return pipe

    def _frames_to_mp4(self, frames, fps: float) -> bytes:
        try:
            from diffusers.utils import export_to_video
        except ImportError as exc:
            raise ImportError("diffusers.utils.export_to_video is required.") from exc

        # frames may be list[PIL] or nested batch
        video_frames = frames
        if video_frames and isinstance(video_frames[0], list):
            video_frames = video_frames[0]

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            out_path = tmp.name
        try:
            export_to_video(video_frames, out_path, fps=int(fps))
            with open(out_path, "rb") as f:
                return f.read()
        finally:
            try:
                os.unlink(out_path)
            except OSError:
                pass

    def generate_text_to_video(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        num_frames: int = DEFAULT_NUM_FRAMES,
        guidance_scale: float = 5.0,
        num_inference_steps: int = 40,
        seed: Optional[int] = None,
        fps: float = DEFAULT_FPS,
        height: Optional[int] = None,
        width: Optional[int] = None,
    ) -> bytes:
        if not prompt:
            raise ValueError("prompt is required.")
        pipe = self._load_t2v()
        generator = None
        if seed is not None:
            generator = self.torch.Generator(device="cuda").manual_seed(int(seed))
        kwargs = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "num_frames": int(num_frames),
            "guidance_scale": float(guidance_scale),
            "num_inference_steps": int(num_inference_steps),
            "generator": generator,
        }
        if height is not None:
            kwargs["height"] = int(height)
        if width is not None:
            kwargs["width"] = int(width)
        result = pipe(**kwargs)
        frames = result.frames if hasattr(result, "frames") else result[0]
        return self._frames_to_mp4(frames, fps)

    def generate_image_to_video(
        self,
        image: Union[str, io.BytesIO, Image.Image, bytes],
        prompt: str,
        negative_prompt: Optional[str] = None,
        num_frames: int = DEFAULT_NUM_FRAMES,
        guidance_scale: float = 5.0,
        num_inference_steps: int = 40,
        seed: Optional[int] = None,
        fps: float = DEFAULT_FPS,
        height: Optional[int] = None,
        width: Optional[int] = None,
    ) -> bytes:
        if not prompt:
            raise ValueError("prompt is required.")
        pipe = self._load_i2v()
        pil = _load_pil(image)
        generator = None
        if seed is not None:
            generator = self.torch.Generator(device="cuda").manual_seed(int(seed))
        kwargs = {
            "image": pil,
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "num_frames": int(num_frames),
            "guidance_scale": float(guidance_scale),
            "num_inference_steps": int(num_inference_steps),
            "generator": generator,
        }
        if height is not None:
            kwargs["height"] = int(height)
        if width is not None:
            kwargs["width"] = int(width)
        result = pipe(**kwargs)
        frames = result.frames if hasattr(result, "frames") else result[0]
        return self._frames_to_mp4(frames, fps)
