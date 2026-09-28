"""
DeepSeek-VL2 (open-weight) Local Adapter

Local GPU inference adapter for DeepSeek's open-weight DeepSeek-VL2 family.
**No first-party hosted API exists for DeepSeek-VL2** -- DeepSeek's own
Platform API (``tryon.api.deepseek.DeepSeekUnderstandAdapter``) only serves
``deepseek-flash`` / ``deepseek-v4-pro``, so this local adapter is the only
way to run DeepSeek-VL2 today. Runs entirely on your own hardware via
Hugging Face Transformers plus DeepSeek's own ``deepseek_vl2`` package, so
it works for any domain (fashion, documents, UI screenshots, general
photography), not just try-on.

Default model: ``deepseek-ai/deepseek-vl2-tiny`` (3.37B total / 1.0B
activated) -- the practical single-GPU default. Larger siblings trade more
VRAM for quality:
  - ``deepseek-ai/deepseek-vl2-small`` (16.1B total / 2.8B activated)
  - ``deepseek-ai/deepseek-vl2`` (27B total / 4.5B activated, "base")
Reported GPU memory needs vary across DeepSeek's own docs (single-GPU for
tiny; budget 40GB+ for small, more for base) -- check the model card for
current numbers before picking a variant.

Unlike this repo's other local VLMs (Kimi-VL, Qwen3.8), DeepSeek-VL2 does
**not** load via plain ``trust_remote_code=True`` + ``AutoProcessor`` --
DeepSeek ships a separate ``deepseek_vl2`` Python package (not on PyPI) that
provides the processor and the ``<|User|>``/``<|Assistant|>`` conversation
format. Video understanding here uses the same uniform-frame-sampling
fallback as Kimi-VL/Qwen3.8 (no official video recipe for VL2).

Reference:
https://github.com/deepseek-ai/DeepSeek-VL2
https://huggingface.co/deepseek-ai/deepseek-vl2

Requirements:
    pip install opentryon[local]   # torch, transformers, etc.
    pip install "git+https://github.com/deepseek-ai/DeepSeek-VL2.git"
    pip install decord             # only needed for understand_video()

Examples:
    >>> from tryon.models.deepseek_vl2 import DeepSeekVL2Adapter
    >>> adapter = DeepSeekVL2Adapter()  # downloads deepseek-vl2-tiny on first use
    >>> result = adapter.understand_image("garment.jpg", prompt="Describe this outfit.")
    >>> print(result["text"])
"""

from __future__ import annotations

import io
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from PIL import Image

DEFAULT_MODEL_ID = "deepseek-ai/deepseek-vl2-tiny"

ImageInput = Union[str, Path, Image.Image]


class DeepSeekVL2Adapter:
    """
    Local adapter for DeepSeek's open-weight DeepSeek-VL2 family, following
    the official ``deepseek_vl2`` inference recipe.

    Args:
        model_id: Hugging Face model id. Defaults to
            ``DEEPSEEK_VL2_MODEL_ID`` env or ``"deepseek-ai/deepseek-vl2-tiny"``.
        device: ``"cuda"``/``"cpu"``/etc. Defaults to CUDA if available.
        torch_dtype: Passed through when moving the model. Defaults to
            ``"auto"`` (bf16 on CUDA).

    Raises:
        ImportError: If ``torch``/``transformers`` aren't installed (install
            the ``local`` extra) or if the ``deepseek_vl2`` package (DeepSeek's
            own, not on PyPI) isn't installed.
    """

    def __init__(
        self,
        model_id: Optional[str] = None,
        device: Optional[str] = None,
        torch_dtype: str = "auto",
    ):
        try:
            import torch
            from transformers import AutoModelForCausalLM
        except ImportError as exc:
            raise ImportError(
                "DeepSeek-VL2 requires the 'local' extra: pip install opentryon[local] "
                "(needs torch + transformers)."
            ) from exc

        try:
            from deepseek_vl2.models import DeepseekVLV2Processor
        except ImportError as exc:
            raise ImportError(
                "DeepSeek-VL2 needs DeepSeek's own 'deepseek_vl2' package "
                "(not on PyPI, not part of opentryon[local]):\n"
                '  pip install "git+https://github.com/deepseek-ai/DeepSeek-VL2.git"'
            ) from exc

        self.model_id = model_id or os.getenv("DEEPSEEK_VL2_MODEL_ID") or DEFAULT_MODEL_ID
        self.processor = DeepseekVLV2Processor.from_pretrained(self.model_id)
        self.tokenizer = self.processor.tokenizer

        model = AutoModelForCausalLM.from_pretrained(self.model_id, trust_remote_code=True)
        dtype = torch.bfloat16 if torch_dtype == "auto" else torch_dtype
        target_device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        model = model.to(dtype=dtype, device=target_device)
        self.model = model.eval()

    # -- input loading --------------------------------------------------

    @staticmethod
    def _load_image(image: ImageInput) -> Image.Image:
        if isinstance(image, Image.Image):
            return image.convert("RGB")

        source = str(image)
        if source.startswith("http://") or source.startswith("https://"):
            import requests

            resp = requests.get(source, timeout=60)
            resp.raise_for_status()
            return Image.open(io.BytesIO(resp.content)).convert("RGB")

        return Image.open(source).convert("RGB")

    @staticmethod
    def _sample_frames(video_path: Union[str, Path], num_frames: int) -> List[Image.Image]:
        try:
            import decord
        except ImportError as exc:
            raise ImportError(
                "Video understanding with DeepSeek-VL2 requires 'decord': pip install decord"
            ) from exc

        vr = decord.VideoReader(str(video_path))
        total = len(vr)
        if total == 0:
            raise ValueError(f"No frames found in video: {video_path}")
        indices = sorted(set(int(i * (total - 1) / max(num_frames - 1, 1)) for i in range(num_frames)))
        frames = vr.get_batch(indices).asnumpy()
        return [Image.fromarray(frame).convert("RGB") for frame in frames]

    # -- core generation --------------------------------------------------

    def _generate(
        self,
        images: List[Image.Image],
        prompt: str,
        max_new_tokens: int,
        do_sample: bool,
        temperature: float,
    ) -> Dict[str, Any]:
        image_tags = "<image>\n" * len(images)
        conversation = [
            {
                "role": "<|User|>",
                "content": f"{image_tags}{prompt}",
                "images": [f"image_{i}" for i in range(len(images))],
            },
            {"role": "<|Assistant|>", "content": ""},
        ]
        prepare_inputs = self.processor(
            conversations=conversation,
            images=images,
            force_batchify=True,
            system_prompt="",
        ).to(self.model.device)

        inputs_embeds = self.model.prepare_inputs_embeds(**prepare_inputs)
        gen_kwargs: Dict[str, Any] = dict(
            inputs_embeds=inputs_embeds,
            attention_mask=prepare_inputs.attention_mask,
            pad_token_id=self.tokenizer.eos_token_id,
            bos_token_id=self.tokenizer.bos_token_id,
            eos_token_id=self.tokenizer.eos_token_id,
            max_new_tokens=max_new_tokens,
            use_cache=True,
            do_sample=do_sample,
        )
        if do_sample:
            gen_kwargs["temperature"] = temperature

        outputs = self.model.language.generate(**gen_kwargs)
        text = self.tokenizer.decode(outputs[0].cpu().tolist(), skip_special_tokens=True)
        return {"text": text.strip(), "model": self.model_id}

    # -- public API ---------------------------------------------------------

    def understand_image(
        self,
        image: Union[ImageInput, List[ImageInput]],
        prompt: str = "Describe the content of the image in detail.",
        max_new_tokens: int = 512,
        do_sample: bool = False,
        temperature: float = 0.8,
    ) -> Dict[str, Any]:
        """Understand one or more local/remote images."""
        images = image if isinstance(image, list) else [image]
        loaded = [self._load_image(img) for img in images]
        return self._generate(loaded, prompt, max_new_tokens, do_sample, temperature)

    def understand_video(
        self,
        video: Union[str, Path],
        prompt: str = "Describe what happens in this video.",
        num_frames: int = 8,
        max_new_tokens: int = 512,
        do_sample: bool = False,
        temperature: float = 0.8,
    ) -> Dict[str, Any]:
        """Understand a video by uniformly sampling ``num_frames`` frames and
        passing them as a multi-image prompt (no official DeepSeek-VL2 video
        recipe -- same fallback used by Kimi-VL/Qwen3.8 local)."""
        frames = self._sample_frames(video, num_frames=num_frames)
        return self._generate(frames, prompt, max_new_tokens, do_sample, temperature)

    def understand(
        self,
        image: Optional[Union[ImageInput, List[ImageInput]]] = None,
        video: Optional[Union[str, Path]] = None,
        prompt: str = "Describe the content in detail.",
        num_frames: int = 8,
        max_new_tokens: int = 512,
        do_sample: bool = False,
        temperature: float = 0.8,
    ) -> Dict[str, Any]:
        """CLI-friendly single entry point: pass ``image`` and/or ``video``."""
        if image is None and video is None:
            raise ValueError("Provide at least one of `image` or `video`.")
        if video is not None:
            return self.understand_video(
                video, prompt=prompt, num_frames=num_frames,
                max_new_tokens=max_new_tokens, do_sample=do_sample, temperature=temperature,
            )
        return self.understand_image(
            image, prompt=prompt, max_new_tokens=max_new_tokens,
            do_sample=do_sample, temperature=temperature,
        )
