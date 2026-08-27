"""
MiniMax H3 local Diffusers adapter (open weights).

Runs MiniMaxAI/MiniMax-H3 on a local CUDA GPU via Hugging Face Diffusers
``ModularPipeline`` (t2va / fl2va workflows). Outputs MP4 with native stereo
audio. Local weights produce the 768p H3-Base canvas; the hosted 2K regenerate
path is not open-sourced.

Weights: https://huggingface.co/MiniMaxAI/MiniMax-H3
Diffusers: https://huggingface.co/docs/diffusers/main/en/api/pipelines/minimax_h3
License: MiniMax H3 Community License — local weights exclude the US, EU, UK,
         and South Korea unless separately authorized. The hosted API is
         globally available (``--model minimax-h3``).

Requirements:
  - CUDA GPU (transformer ~61.7GB bf16 + Qwen3-VL conditioner ~62GB; use
    ComponentsManager CPU offload; consumer cards need ~75GB host RAM)
  - `pip install opentryon[local]` plus Diffusers **from main**:
      pip install "git+https://github.com/huggingface/diffusers"
    (MiniMax-H3 ModularPipeline is not in a stable Diffusers release yet.)

Examples:
    >>> from tryon.models import MiniMaxH3LocalAdapter
    >>> adapter = MiniMaxH3LocalAdapter()
    >>> video = adapter.generate_text_to_video(
    ...     prompt="A fashion model walking a runway at dusk, camera tracking",
    ...     width=960,
    ...     height=544,
    ...     num_frames=124,
    ... )
    >>> open("out.mp4", "wb").write(video)
"""

from __future__ import annotations

import io
import os
import tempfile
from typing import Optional, Union

from PIL import Image

DEFAULT_MODEL_ID = "MiniMaxAI/MiniMax-H3"
DEFAULT_WIDTH = 960
DEFAULT_HEIGHT = 544
DEFAULT_NUM_FRAMES = 124
DEFAULT_FRAME_RATE = 24.0
_FRAME_MOD = 17
_FRAME_OFFSET = 5
_MIN_FRAMES = 17 * 7 + 5  # 124 ≈ 5.17s at 24fps
_MAX_FRAMES = 17 * 21 + 5  # 362 ≈ 15.08s


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
    raise ValueError("Unsupported image input for MiniMax H3 local adapter.")


def snap_num_frames(num_frames: int) -> int:
    """Snap to the next ``17*n+5`` value in the 5–15s window at 24 fps."""
    n = int(num_frames)
    k = (n - _FRAME_OFFSET + _FRAME_MOD - 1) // _FRAME_MOD
    snapped = _FRAME_MOD * k + _FRAME_OFFSET
    return max(_MIN_FRAMES, min(_MAX_FRAMES, snapped))


class MiniMaxH3LocalAdapter:
    """Local open-weight MiniMax H3 video adapter (Diffusers ModularPipeline)."""

    def __init__(
        self,
        model_id: Optional[str] = None,
        device: Optional[str] = None,
        dtype: str = "bfloat16",
        cpu_offload: bool = True,
    ):
        try:
            import torch
            from diffusers import ModularPipeline  # noqa: F401
        except ImportError as exc:
            raise ImportError(
                "MiniMax H3 local inference requires torch and Diffusers with "
                "ModularPipeline MiniMax-H3 support. Install local extras, then "
                "Diffusers from main:\n"
                "  pip install opentryon[local]\n"
                '  pip install "git+https://github.com/huggingface/diffusers"\n'
                f"Original error: {exc}"
            ) from exc

        self.torch = torch
        self.model_id = (
            model_id
            or os.getenv("MINIMAX_H3_MODEL_PATH")
            or os.getenv("MINIMAX_H3_MODEL_ID")
            or DEFAULT_MODEL_ID
        )
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        if self.device == "cpu":
            raise RuntimeError(
                "MiniMax H3 local inference requires a CUDA GPU. "
                "CPU-only runs are not supported. Use --model minimax-h3 for the hosted API."
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
            from diffusers import ComponentsManager, ModularPipeline
        except ImportError as exc:
            raise ImportError(
                "Your Diffusers install does not include MiniMax-H3 ModularPipeline. "
                'Upgrade with: pip install "git+https://github.com/huggingface/diffusers"\n'
                f"Original error: {exc}"
            ) from exc

        manager = ComponentsManager()
        if self.cpu_offload:
            manager.enable_auto_cpu_offload(device=self.device)
        pipe = ModularPipeline.from_pretrained(
            self.model_id, components_manager=manager
        )
        # fl2va shares transformer/ with t2va — covers text and first/last frames.
        pipe.load_components(workflow="fl2va", dtype=self.dtype)
        if not self.cpu_offload:
            try:
                pipe.to(self.device)
            except Exception:
                pass
        self._pipe = pipe
        return pipe

    def _encode_mp4(self, results, frame_rate: float) -> bytes:
        try:
            from diffusers.utils.export_utils import encode_video
        except ImportError:
            try:
                from diffusers.utils import encode_video
            except ImportError as exc:
                raise ImportError(
                    "encode_video is missing. "
                    'Install Diffusers from main: pip install "git+https://github.com/huggingface/diffusers"'
                ) from exc

        videos = results["videos"] if isinstance(results, dict) else results.videos
        audio = results["audio"] if isinstance(results, dict) else getattr(results, "audio", None)
        sampling_rate = (
            results["sampling_rate"]
            if isinstance(results, dict)
            else getattr(results, "sampling_rate", 32000)
        )
        frames = videos[0] if isinstance(videos, (list, tuple)) else videos
        audio_tensor = None
        if audio is not None:
            try:
                audio_tensor = audio[0]
            except Exception:
                audio_tensor = audio

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            out_path = tmp.name
        try:
            encode_kwargs = {
                "fps": int(frame_rate) if float(frame_rate).is_integer() else frame_rate,
                "output_path": out_path,
            }
            if audio_tensor is not None:
                encode_kwargs["audio"] = audio_tensor
                encode_kwargs["audio_sample_rate"] = sampling_rate
            encode_video(frames, **encode_kwargs)
            with open(out_path, "rb") as f:
                return f.read()
        finally:
            try:
                os.unlink(out_path)
            except OSError:
                pass

    def _generate(
        self,
        prompt: str,
        *,
        image: Optional[Union[str, io.BytesIO, Image.Image, bytes]] = None,
        last_image: Optional[Union[str, io.BytesIO, Image.Image, bytes]] = None,
        width: int = DEFAULT_WIDTH,
        height: int = DEFAULT_HEIGHT,
        num_frames: int = DEFAULT_NUM_FRAMES,
        seed: Optional[int] = None,
    ) -> bytes:
        if not (prompt or "").strip():
            raise ValueError("prompt is required.")
        if width % 32 != 0 or height % 32 != 0:
            raise ValueError("width and height must be divisible by 32.")

        pipe = self._load_pipe()
        frames = snap_num_frames(num_frames)
        generator = None
        if seed is not None:
            generator = self.torch.Generator(device="cuda").manual_seed(int(seed))

        kwargs = {
            "prompt": prompt,
            "num_frames": frames,
            "height": int(height),
            "width": int(width),
            "generator": generator,
            "output": ["videos", "audio", "sampling_rate"],
        }
        if image is not None:
            kwargs["image"] = _load_pil(image)
        if last_image is not None:
            kwargs["last_image"] = _load_pil(last_image)

        results = pipe(**kwargs)
        return self._encode_mp4(results, DEFAULT_FRAME_RATE)

    def generate_text_to_video(
        self,
        prompt: str,
        width: int = DEFAULT_WIDTH,
        height: int = DEFAULT_HEIGHT,
        num_frames: int = DEFAULT_NUM_FRAMES,
        seed: Optional[int] = None,
        last_image: Optional[Union[str, io.BytesIO, Image.Image, bytes]] = None,
    ) -> bytes:
        return self._generate(
            prompt,
            last_image=last_image,
            width=width,
            height=height,
            num_frames=num_frames,
            seed=seed,
        )

    def generate_image_to_video(
        self,
        image: Union[str, io.BytesIO, Image.Image, bytes],
        prompt: str,
        width: int = DEFAULT_WIDTH,
        height: int = DEFAULT_HEIGHT,
        num_frames: int = DEFAULT_NUM_FRAMES,
        seed: Optional[int] = None,
        last_image: Optional[Union[str, io.BytesIO, Image.Image, bytes]] = None,
    ) -> bytes:
        return self._generate(
            prompt,
            image=image,
            last_image=last_image,
            width=width,
            height=height,
            num_frames=num_frames,
            seed=seed,
        )
