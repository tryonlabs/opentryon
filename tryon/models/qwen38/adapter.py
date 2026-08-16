"""
Qwen3.8 (open-weight) Local Adapter

Local GPU inference for Qwen's open-weight Qwen3.8 multimodal models on
Hugging Face — the open counterpart to the hosted ``qwen3.8-max`` DashScope
API (``tryon.api.qwen.QwenUnderstandAdapter``).

Default model: ``Qwen/Qwen3.8-27B`` — a dense ~27B native vision-language
model (text + image + video) with flexible thinking control. Practical on
high-end multi-GPU setups (bf16 ~50GB+ recommended; quantized community
checkpoints also exist).

For datacenter-scale MoE closest to hosted Max, pass
``model_id="Qwen/Qwen3.8-2.4T-A95B"`` and serve with vLLM/SGLang — not
single-GPU friendly.

Reference:
https://huggingface.co/Qwen/Qwen3.8-27B
https://huggingface.co/collections/Qwen/qwen38

Requirements:
    pip install opentryon[local]   # torch, transformers, etc.
    pip install -U transformers    # Qwen3.8 needs a recent transformers
    pip install decord             # only needed for understand_video()

Examples:
    >>> from tryon.models import Qwen38Adapter
    >>> adapter = Qwen38Adapter()
    >>> result = adapter.understand_image("garment.jpg", prompt="Describe this outfit.")
    >>> print(result["text"])
"""

from __future__ import annotations

import io
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from PIL import Image

DEFAULT_MODEL_ID = "Qwen/Qwen3.8-27B"
THINK_START, THINK_END = "<think>", "</think>"

ImageInput = Union[str, Path, Image.Image]


class Qwen38Adapter:
    """
    Local Hugging Face Transformers adapter for the Qwen3.8 open-weight
    multimodal family (``AutoModelForImageTextToText``).

    Args:
        model_id: Hugging Face model id. Defaults to ``QWEN38_MODEL_ID`` env
            or ``Qwen/Qwen3.8-27B``.
        device: Passed as ``device_map``. Defaults to ``"auto"``.
        torch_dtype: Passed to ``from_pretrained``. Defaults to ``"auto"``.
        trust_remote_code: Kept for Hub compatibility; defaults to True.
    """

    def __init__(
        self,
        model_id: Optional[str] = None,
        device: Optional[str] = None,
        torch_dtype: str = "auto",
        trust_remote_code: bool = True,
    ):
        try:
            import torch
            from transformers import AutoModelForImageTextToText, AutoProcessor
        except ImportError as exc:
            raise ImportError(
                "Qwen3.8 requires the 'local' extra: pip install opentryon[local] "
                "(needs torch + transformers). Also upgrade transformers for "
                "Qwen3.8 architecture support: pip install -U transformers"
            ) from exc

        self.model_id = model_id or os.getenv("QWEN38_MODEL_ID") or DEFAULT_MODEL_ID
        dtype = torch_dtype
        if dtype == "auto":
            dtype = torch.bfloat16 if torch.cuda.is_available() else "auto"

        self.model = AutoModelForImageTextToText.from_pretrained(
            self.model_id,
            torch_dtype=dtype,
            device_map=device or "auto",
            trust_remote_code=trust_remote_code,
        )
        self.processor = AutoProcessor.from_pretrained(
            self.model_id, trust_remote_code=trust_remote_code
        )

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
                "Video understanding with Qwen3.8 local requires 'decord': pip install decord"
            ) from exc

        vr = decord.VideoReader(str(video_path))
        total = len(vr)
        if total == 0:
            raise ValueError(f"No frames found in video: {video_path}")
        indices = sorted(
            set(int(i * (total - 1) / max(num_frames - 1, 1)) for i in range(num_frames))
        )
        frames = vr.get_batch(indices).asnumpy()
        return [Image.fromarray(frame).convert("RGB") for frame in frames]

    @staticmethod
    def _split_thinking(text: str) -> Dict[str, Optional[str]]:
        if THINK_START in text and THINK_END in text:
            thinking = text[
                text.index(THINK_START) + len(THINK_START) : text.index(THINK_END)
            ].strip()
            summary = text[text.index(THINK_END) + len(THINK_END) :].strip()
            return {"thinking": thinking, "text": summary}
        return {"thinking": None, "text": text.strip()}

    # -- core generation --------------------------------------------------

    def _generate(
        self,
        images: List[Image.Image],
        prompt: str,
        max_new_tokens: int,
        temperature: float,
        enable_thinking: bool,
    ) -> Dict[str, Any]:
        content = [{"type": "image", "image": img} for img in images] + [
            {"type": "text", "text": prompt}
        ]
        messages = [{"role": "user", "content": content}]

        text = self.processor.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=False,
            enable_thinking=enable_thinking,
        )
        inputs = self.processor(
            images=images, text=[text], return_tensors="pt", padding=True
        )
        # Move tensors to the model's first device when using device_map="auto".
        try:
            target = next(self.model.parameters()).device
            inputs = {k: v.to(target) if hasattr(v, "to") else v for k, v in inputs.items()}
        except StopIteration:
            pass

        generate_kwargs: Dict[str, Any] = {"max_new_tokens": max_new_tokens}
        if temperature and temperature > 0:
            generate_kwargs["temperature"] = temperature
            generate_kwargs["do_sample"] = True
        else:
            generate_kwargs["do_sample"] = False

        generated_ids = self.model.generate(**inputs, **generate_kwargs)
        trimmed = [
            out_ids[len(in_ids) :]
            for in_ids, out_ids in zip(inputs["input_ids"], generated_ids)
        ]
        response = self.processor.batch_decode(
            trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
        )[0]

        result = self._split_thinking(response)
        result["model"] = self.model_id
        return result

    # -- public API ---------------------------------------------------------

    def understand_image(
        self,
        image: Union[ImageInput, List[ImageInput]],
        prompt: str = "Describe the content of the image in detail.",
        max_new_tokens: int = 4096,
        temperature: float = 0.8,
        enable_thinking: bool = True,
    ) -> Dict[str, Any]:
        """Understand one or more local/remote images."""
        images = image if isinstance(image, list) else [image]
        loaded = [self._load_image(img) for img in images]
        return self._generate(
            loaded, prompt, max_new_tokens, temperature, enable_thinking
        )

    def understand_video(
        self,
        video: Union[str, Path],
        prompt: str = "Describe what happens in this video.",
        num_frames: int = 8,
        max_new_tokens: int = 4096,
        temperature: float = 0.8,
        enable_thinking: bool = True,
    ) -> Dict[str, Any]:
        """Understand a video by sampling frames as a multi-image prompt."""
        frames = self._sample_frames(video, num_frames=num_frames)
        return self._generate(
            frames, prompt, max_new_tokens, temperature, enable_thinking
        )

    def understand(
        self,
        image: Optional[Union[ImageInput, List[ImageInput]]] = None,
        video: Optional[Union[str, Path]] = None,
        prompt: str = "Describe the content in detail.",
        num_frames: int = 8,
        max_new_tokens: int = 4096,
        temperature: float = 0.8,
        enable_thinking: bool = True,
    ) -> Dict[str, Any]:
        """CLI-friendly single entry point: pass ``image`` and/or ``video``."""
        if image is None and video is None:
            raise ValueError("Provide at least one of `image` or `video`.")
        if video is not None:
            return self.understand_video(
                video,
                prompt=prompt,
                num_frames=num_frames,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                enable_thinking=enable_thinking,
            )
        return self.understand_image(
            image,
            prompt=prompt,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            enable_thinking=enable_thinking,
        )
