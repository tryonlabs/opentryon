"""
NVIDIA Cosmos 3 local Diffusers adapter (open weights).

Runs NVIDIA Cosmos 3 (Generator "Nano", 16B) on a local / cloud GPU via Hugging
Face Diffusers (`Cosmos3OmniPipeline`). Supports text-to-video and
image-to-video. This is the self-hosted counterpart to the hosted NIM adapter
(`tryon.api.nvidia.Cosmos3VideoAdapter`, registry id ``cosmos3``).

Weights: https://huggingface.co/nvidia/Cosmos3-Nano
License: OpenMDW 1.1 (commercial and non-commercial use permitted)
Precision: only BF16 is tested upstream; FP16/FP8/FP4 are not supported.

Requirements:
  - CUDA GPU with large VRAM (16B-parameter model; BF16 only)
  - `pip install opentryon[local]` plus a Diffusers build that ships
    ``Cosmos3OmniPipeline`` (install from main if your release lacks it):
      pip install "git+https://github.com/huggingface/diffusers"
  - accelerate, torch

Prompting: the upstream examples pass structured JSON captions
(``json.dumps({...})``). Plain text prompts are accepted; a ``dict`` prompt is
serialised to JSON automatically.

Examples:
    >>> from tryon.models import Cosmos3LocalAdapter
    >>> adapter = Cosmos3LocalAdapter()
    >>> video = adapter.generate_text_to_video(
    ...     prompt="A fashion model walking a runway at dusk, tracking camera",
    ...     num_frames=189, height=720, width=1280,
    ... )
    >>> open("out.mp4", "wb").write(video)

    >>> video = adapter.generate_image_to_video(image="look.jpg", prompt="Slow turn, soft fabric motion")
"""

from __future__ import annotations

import io
import json
import os
import tempfile
from typing import Any, Dict, Optional, Union

from PIL import Image

DEFAULT_MODEL_ID = "nvidia/Cosmos3-Nano"
DEFAULT_WIDTH = 1280
DEFAULT_HEIGHT = 720
DEFAULT_NUM_FRAMES = 189
DEFAULT_FPS = 24
DEFAULT_STEPS = 35
DEFAULT_GUIDANCE = 6.0
DEFAULT_FLOW_SHIFT = 10.0


def _load_pil(image: Union[str, io.BytesIO, Image.Image, bytes]) -> Image.Image:
    if isinstance(image, Image.Image):
        return image.convert("RGB")
    if isinstance(image, str):
        if image.startswith(("http://", "https://")):
            try:
                from diffusers.utils import load_image
            except ImportError as exc:
                raise ImportError("diffusers is required to load image URLs.") from exc
            return load_image(image).convert("RGB")
        if os.path.exists(image):
            return Image.open(image).convert("RGB")
        raise ValueError(f"Image path does not exist: {image}")
    if isinstance(image, (bytes, bytearray)):
        return Image.open(io.BytesIO(bytes(image))).convert("RGB")
    if hasattr(image, "read"):
        image.seek(0)
        return Image.open(image).convert("RGB")
    raise ValueError("Unsupported image input for Cosmos 3 local adapter.")


def _prompt_text(prompt: Union[str, Dict[str, Any], None]) -> Optional[str]:
    if prompt is None:
        return None
    if isinstance(prompt, (dict, list)):
        return json.dumps(prompt)
    return str(prompt)


class Cosmos3LocalAdapter:
    """Local open-weight NVIDIA Cosmos 3 video adapter (Diffusers, BF16, CUDA)."""

    def __init__(
        self,
        model_id: Optional[str] = None,
        device: Optional[str] = None,
        cpu_offload: bool = False,
        enable_safety_checker: bool = True,
    ):
        try:
            import torch
            from diffusers import Cosmos3OmniPipeline  # noqa: F401
        except ImportError as exc:
            raise ImportError(
                "Cosmos 3 local inference requires torch and a Diffusers build with "
                "Cosmos3OmniPipeline. Install local extras, then Diffusers from main:\n"
                "  pip install opentryon[local]\n"
                '  pip install "git+https://github.com/huggingface/diffusers"\n'
                f"Original error: {exc}"
            ) from exc

        self.torch = torch
        self.model_id = (
            model_id
            or os.getenv("COSMOS3_MODEL_PATH")
            or os.getenv("COSMOS3_MODEL_ID")
            or DEFAULT_MODEL_ID
        )
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        if self.device == "cpu":
            raise RuntimeError(
                "Cosmos 3 local inference requires a CUDA GPU. CPU-only runs are not supported."
            )
        self.cpu_offload = bool(cpu_offload)
        self.enable_safety_checker = bool(enable_safety_checker)
        self._pipe = None

    def _load(self):
        if self._pipe is not None:
            return self._pipe
        from diffusers import Cosmos3OmniPipeline
        from diffusers.schedulers.scheduling_unipc_multistep import UniPCMultistepScheduler

        kwargs: Dict[str, Any] = {
            "torch_dtype": self.torch.bfloat16,
            "enable_safety_checker": self.enable_safety_checker,
        }
        if not self.cpu_offload:
            kwargs["device_map"] = self.device
        pipe = Cosmos3OmniPipeline.from_pretrained(self.model_id, **kwargs)
        if self.cpu_offload:
            pipe.enable_model_cpu_offload()
        pipe.scheduler = UniPCMultistepScheduler.from_config(
            pipe.scheduler.config, flow_shift=DEFAULT_FLOW_SHIFT
        )
        self._pipe = pipe
        return pipe

    def _run(self, call_kwargs: Dict[str, Any], fps: int) -> bytes:
        from diffusers.utils import export_to_video

        pipe = self._load()
        result = pipe(**call_kwargs)
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            out_path = tmp.name
        try:
            export_to_video(result.video, out_path, fps=fps)
            with open(out_path, "rb") as f:
                return f.read()
        finally:
            try:
                os.remove(out_path)
            except OSError:
                pass

    def _common(
        self,
        negative_prompt: Optional[Union[str, Dict[str, Any]]],
        num_frames: int,
        height: int,
        width: int,
        num_inference_steps: int,
        guidance_scale: float,
        seed: Optional[int],
    ) -> Dict[str, Any]:
        kwargs: Dict[str, Any] = {
            "num_frames": int(num_frames),
            "height": int(height),
            "width": int(width),
            "num_inference_steps": int(num_inference_steps),
            "guidance_scale": float(guidance_scale),
        }
        neg = _prompt_text(negative_prompt)
        if neg:
            kwargs["negative_prompt"] = neg
        if seed is not None:
            kwargs["generator"] = self.torch.Generator(device=self.device).manual_seed(int(seed))
        return kwargs

    def generate_text_to_video(
        self,
        prompt: Union[str, Dict[str, Any]],
        negative_prompt: Optional[Union[str, Dict[str, Any]]] = None,
        num_frames: int = DEFAULT_NUM_FRAMES,
        height: int = DEFAULT_HEIGHT,
        width: int = DEFAULT_WIDTH,
        fps: int = DEFAULT_FPS,
        num_inference_steps: int = DEFAULT_STEPS,
        guidance_scale: float = DEFAULT_GUIDANCE,
        seed: Optional[int] = None,
    ) -> bytes:
        """Generate an MP4 (bytes) from a text prompt."""
        if not prompt:
            raise ValueError("prompt is required for text-to-video.")
        kwargs = self._common(
            negative_prompt, num_frames, height, width, num_inference_steps, guidance_scale, seed
        )
        kwargs["prompt"] = _prompt_text(prompt)
        return self._run(kwargs, fps)

    def generate_image_to_video(
        self,
        image: Union[str, io.BytesIO, Image.Image, bytes],
        prompt: Optional[Union[str, Dict[str, Any]]] = None,
        negative_prompt: Optional[Union[str, Dict[str, Any]]] = None,
        num_frames: int = DEFAULT_NUM_FRAMES,
        height: int = DEFAULT_HEIGHT,
        width: int = DEFAULT_WIDTH,
        fps: int = DEFAULT_FPS,
        num_inference_steps: int = DEFAULT_STEPS,
        guidance_scale: float = DEFAULT_GUIDANCE,
        seed: Optional[int] = None,
    ) -> bytes:
        """Animate a first-frame image into an MP4 (bytes)."""
        kwargs = self._common(
            negative_prompt, num_frames, height, width, num_inference_steps, guidance_scale, seed
        )
        kwargs["prompt"] = _prompt_text(prompt) or ""
        kwargs["image"] = _load_pil(image)
        return self._run(kwargs, fps)
