"""
Kimi-VL (open-weight) Local Adapter

Local GPU inference adapter for Moonshot AI's open-weight Kimi-VL family on
Hugging Face -- the open-weight counterpart to the closed Kimi K2.6/K2.7 Code
APIs (`tryon.api.kimi.KimiUnderstandAdapter`). Runs entirely on your own
hardware via Hugging Face Transformers, so it works for any domain (fashion,
documents, UI screenshots, general photography, etc.), not just try-on.

Default model: `moonshotai/Kimi-VL-A3B-Thinking-2506` -- a 16B-parameter
Mixture-of-Experts vision-language model with only ~3B activated parameters,
which makes it practical to run on a single high-end GPU (24GB+ VRAM
recommended, bf16/fp16). It natively supports image and multi-image input,
plus a visible "thinking" chain-of-thought. Video understanding is
implemented here by uniformly sampling frames and passing them as a
multi-image prompt (the model card's official recipe uses vLLM for native
video token handling; this fallback works with plain `transformers`).

For teams with multi-GPU / cluster inference (vLLM, SGLang) who want a model
closer in scale to the hosted `kimi-k2.6` / `kimi-k2.7-code` APIs, pass
`model_id="moonshotai/Kimi-K2.5"` instead -- a 1T-total/32B-activated-param
open-weight model (not single-GPU friendly; needs distributed serving).

Reference:
https://huggingface.co/moonshotai/Kimi-VL-A3B-Thinking-2506
https://github.com/MoonshotAI/Kimi-VL
https://huggingface.co/moonshotai/Kimi-K2.5

Requirements:
    pip install opentryon[local]   # torch, transformers, etc.
    pip install decord             # only needed for understand_video()

Examples:
    >>> from tryon.models import KimiVLAdapter
    >>> adapter = KimiVLAdapter()  # downloads model on first use
    >>> result = adapter.understand_image("garment.jpg", prompt="Describe this outfit.")
    >>> print(result["text"])

    Video understanding via frame sampling:
        >>> result = adapter.understand_video(
        ...     "runway_clip.mp4", prompt="Summarize the styling shown.", num_frames=8
        ... )
"""

import io
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from PIL import Image

DEFAULT_MODEL_ID = "moonshotai/Kimi-VL-A3B-Thinking-2506"
THINK_START, THINK_END = "\u25c1think\u25b7", "\u25c1/think\u25b7"

ImageInput = Union[str, Path, Image.Image]


class KimiVLAdapter:
    """
    Local Hugging Face Transformers adapter for the Kimi-VL open-weight
    model family.

    Args:
        model_id (str, optional): Hugging Face model id. Defaults to
            `"moonshotai/Kimi-VL-A3B-Thinking-2506"`. Pass
            `"moonshotai/Kimi-VL-A3B-Instruct"` for the faster non-thinking
            variant, or `"moonshotai/Kimi-K2.5"` for the much larger,
            cluster-scale open-weight model.
        device (str, optional): Passed through as `device_map`. Defaults to
            `"auto"`.
        torch_dtype: Passed through to `from_pretrained`. Defaults to
            `"auto"`.
        trust_remote_code (bool): Kimi-VL ships custom modeling/processor
            code on the Hub. Defaults to True (required for it to load).

    Raises:
        ImportError: If `torch`/`transformers` aren't installed (install the
            `local` extra: `pip install opentryon[local]`).
    """

    def __init__(
        self,
        model_id: str = DEFAULT_MODEL_ID,
        device: Optional[str] = None,
        torch_dtype: str = "auto",
        trust_remote_code: bool = True,
    ):
        try:
            from transformers import AutoModelForCausalLM, AutoProcessor
        except ImportError as exc:
            raise ImportError(
                "Kimi-VL requires the 'local' extra: pip install opentryon[local] "
                "(needs torch + transformers)."
            ) from exc

        self.model_id = model_id
        self.model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=torch_dtype,
            device_map=device or "auto",
            trust_remote_code=trust_remote_code,
        )
        self.processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=trust_remote_code)

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
                "Video understanding with Kimi-VL requires 'decord': pip install decord"
            ) from exc

        vr = decord.VideoReader(str(video_path))
        total = len(vr)
        if total == 0:
            raise ValueError(f"No frames found in video: {video_path}")
        indices = sorted(set(int(i * (total - 1) / max(num_frames - 1, 1)) for i in range(num_frames)))
        frames = vr.get_batch(indices).asnumpy()
        return [Image.fromarray(frame).convert("RGB") for frame in frames]

    @staticmethod
    def _split_thinking(text: str) -> Dict[str, Optional[str]]:
        if THINK_START in text and THINK_END in text:
            thinking = text[text.index(THINK_START) + len(THINK_START):text.index(THINK_END)].strip()
            summary = text[text.index(THINK_END) + len(THINK_END):].strip()
            return {"thinking": thinking, "text": summary}
        return {"thinking": None, "text": text.strip()}

    # -- core generation --------------------------------------------------

    def _generate(
        self, images: List[Image.Image], prompt: str, max_new_tokens: int, temperature: float
    ) -> Dict[str, Any]:
        content = [{"type": "image", "image": img} for img in images] + [{"type": "text", "text": prompt}]
        messages = [{"role": "user", "content": content}]

        text = self.processor.apply_chat_template(messages, add_generation_prompt=True, return_tensors="pt")
        inputs = self.processor(images=images, text=text, return_tensors="pt", padding=True, truncation=True).to(
            self.model.device
        )
        generated_ids = self.model.generate(**inputs, max_new_tokens=max_new_tokens, temperature=temperature)
        trimmed = [out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)]
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
    ) -> Dict[str, Any]:
        """Understand one or more local/remote images."""
        images = image if isinstance(image, list) else [image]
        loaded = [self._load_image(img) for img in images]
        return self._generate(loaded, prompt, max_new_tokens, temperature)

    def understand_video(
        self,
        video: Union[str, Path],
        prompt: str = "Describe what happens in this video.",
        num_frames: int = 8,
        max_new_tokens: int = 4096,
        temperature: float = 0.8,
    ) -> Dict[str, Any]:
        """Understand a video by uniformly sampling `num_frames` frames and
        passing them to the model as a multi-image prompt."""
        frames = self._sample_frames(video, num_frames=num_frames)
        return self._generate(frames, prompt, max_new_tokens, temperature)

    def understand(
        self,
        image: Optional[Union[ImageInput, List[ImageInput]]] = None,
        video: Optional[Union[str, Path]] = None,
        prompt: str = "Describe the content in detail.",
        num_frames: int = 8,
        max_new_tokens: int = 4096,
        temperature: float = 0.8,
    ) -> Dict[str, Any]:
        """CLI-friendly single entry point: pass `image` and/or `video`."""
        if image is None and video is None:
            raise ValueError("Provide at least one of `image` or `video`.")
        if video is not None:
            return self.understand_video(
                video, prompt=prompt, num_frames=num_frames, max_new_tokens=max_new_tokens, temperature=temperature
            )
        return self.understand_image(image, prompt=prompt, max_new_tokens=max_new_tokens, temperature=temperature)
