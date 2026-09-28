"""
DeepSeek-OCR (open-weight) Local Adapter

Local GPU inference adapter for DeepSeek's open-weight DeepSeek-OCR --
"Contexts Optical Compression": a document/image OCR model that reads
scans, screenshots, and photographed documents and returns markdown or
plain text. **No first-party hosted API exists for DeepSeek-OCR** --
DeepSeek's own Platform API (``tryon.api.deepseek.DeepSeekUnderstandAdapter``)
only serves ``deepseek-flash`` / ``deepseek-v4-pro``, so this local adapter
is the only way to run DeepSeek-OCR today.

Real fashion fit: garment care labels, size tags, SKU/product-copy sheets,
receipts -- distinct value from general captioning (``understand`` on
Kimi/Qwen3.8/GLM/DeepSeek-flash) even though it lives under the same
``understand`` service.

Default model: ``deepseek-ai/DeepSeek-OCR`` (3B params, MIT). DeepSeek also
publishes ``deepseek-ai/DeepSeek-OCR-2`` ("Visual Causal Flow") which may
have a different ``model.infer()`` signature -- pass
``model_id="deepseek-ai/DeepSeek-OCR-2"`` (or set ``DEEPSEEK_OCR_MODEL_ID``)
only after checking its model card, since this adapter follows the v1 API.

Reference:
https://github.com/deepseek-ai/DeepSeek-OCR
https://huggingface.co/deepseek-ai/DeepSeek-OCR

Requirements:
    pip install opentryon[local]   # torch, transformers, etc.
    pip install flash-attn         # DeepSeek-OCR's model card requires
                                    # flash_attention_2; official pins are
                                    # torch==2.6.0 / transformers==4.46.3 /
                                    # flash-attn==2.7.3, newer than this
                                    # repo's shared opentryon[local] pin --
                                    # upgrade in a separate env if loading fails.

Examples:
    >>> from tryon.models.deepseek_ocr import DeepSeekOCRAdapter
    >>> adapter = DeepSeekOCRAdapter()  # downloads DeepSeek-OCR on first use
    >>> result = adapter.understand_image("care_label.jpg", mode="markdown")
    >>> print(result["text"])
"""

from __future__ import annotations

import io
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional, Union

from PIL import Image

DEFAULT_MODEL_ID = "deepseek-ai/DeepSeek-OCR"

# DeepSeek's own documented prompt conventions.
FREE_OCR_PROMPT = "<image>\nFree OCR."
MARKDOWN_PROMPT = "<image>\n<|grounding|>Convert the document to markdown. "

ImageInput = Union[str, Path, Image.Image, bytes]


class DeepSeekOCRAdapter:
    """
    Local adapter for DeepSeek's open-weight DeepSeek-OCR, following the
    official ``model.infer()`` inference recipe.

    Args:
        model_id: Hugging Face model id. Defaults to
            ``DEEPSEEK_OCR_MODEL_ID`` env or ``"deepseek-ai/DeepSeek-OCR"``.
        device: Kept for interface parity; DeepSeek-OCR's official recipe
            requires CUDA (``.cuda()``), so this is not configurable.

    Raises:
        ImportError: If ``torch``/``transformers`` aren't installed (install
            the ``local`` extra).
    """

    def __init__(
        self,
        model_id: Optional[str] = None,
        device: Optional[str] = None,
    ):
        try:
            import torch
            from transformers import AutoModel, AutoTokenizer
        except ImportError as exc:
            raise ImportError(
                "DeepSeek-OCR requires the 'local' extra: pip install opentryon[local] "
                "(needs torch + transformers). It also needs flash-attn "
                "(pip install flash-attn) and, per the model card, "
                "torch==2.6.0 / transformers==4.46.3 -- upgrade in a separate "
                "env if loading fails with this repo's shared pin."
            ) from exc

        self.model_id = model_id or os.getenv("DEEPSEEK_OCR_MODEL_ID") or DEFAULT_MODEL_ID
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_id, trust_remote_code=True)
        model = AutoModel.from_pretrained(
            self.model_id,
            _attn_implementation="flash_attention_2",
            trust_remote_code=True,
            use_safetensors=True,
        )
        model = model.eval()
        if device != "cpu" and torch.cuda.is_available():
            model = model.cuda()
        self.model = model.to(torch.bfloat16)

    # -- input loading --------------------------------------------------

    @staticmethod
    def _resolve_image_path(image: ImageInput) -> "tuple[str, bool]":
        """DeepSeek-OCR's ``model.infer()`` needs a local file path -- pass
        an existing local path through, otherwise save to a temp JPEG.
        Returns ``(path, is_temp_file)``."""
        if isinstance(image, (str, Path)):
            source = str(image)
            if not (source.startswith("http://") or source.startswith("https://")):
                return source, False
            import requests

            resp = requests.get(source, timeout=60)
            resp.raise_for_status()
            pil_image = Image.open(io.BytesIO(resp.content)).convert("RGB")
        elif isinstance(image, Image.Image):
            pil_image = image.convert("RGB")
        elif isinstance(image, (bytes, bytearray)):
            pil_image = Image.open(io.BytesIO(image)).convert("RGB")
        else:
            raise ValueError("Unsupported image input for DeepSeek-OCR.")

        fd, tmp_path = tempfile.mkstemp(suffix=".jpg")
        os.close(fd)
        pil_image.save(tmp_path, format="JPEG", quality=95)
        return tmp_path, True

    # -- core inference --------------------------------------------------

    def _infer(
        self,
        image_path: str,
        prompt: str,
        base_size: int,
        image_size: int,
        crop_mode: bool,
    ) -> str:
        output_dir = tempfile.mkdtemp(prefix="deepseek-ocr-")
        try:
            result = self.model.infer(
                self.tokenizer,
                prompt=prompt,
                image_file=image_path,
                output_path=output_dir,
                base_size=base_size,
                image_size=image_size,
                crop_mode=crop_mode,
                save_results=True,
                eval_mode=True,
            )
            text = self._extract_text(result, output_dir)
            return text
        finally:
            shutil.rmtree(output_dir, ignore_errors=True)

    @staticmethod
    def _extract_text(result: Any, output_dir: str) -> str:
        # `eval_mode=True` returns the OCR text directly on current model
        # cards; fall back to reading the markdown file `save_results=True`
        # writes to `output_dir` if the return value isn't a usable string
        # (upstream API has changed shape between releases).
        if isinstance(result, str) and result.strip():
            return result.strip()
        if isinstance(result, (tuple, list)) and result and isinstance(result[0], str) and result[0].strip():
            return result[0].strip()

        for pattern in ("*.mmd", "*.md", "*result*.md", "*.txt"):
            matches = sorted(Path(output_dir).glob(pattern))
            if matches:
                return matches[0].read_text(encoding="utf-8", errors="replace").strip()

        raise RuntimeError(
            "DeepSeek-OCR ran but produced no readable output (checked the "
            "return value and common result filenames in the output dir). "
            "Check the installed deepseek-ai/DeepSeek-OCR model card for the "
            "current model.infer() output contract."
        )

    # -- public API ---------------------------------------------------------

    def understand_image(
        self,
        image: ImageInput,
        prompt: Optional[str] = None,
        mode: str = "markdown",
        base_size: int = 1024,
        image_size: int = 640,
        crop_mode: bool = True,
    ) -> Dict[str, Any]:
        """Run OCR on a single image.

        Args:
            prompt: Raw DeepSeek-OCR prompt. Overrides ``mode`` if given.
            mode: ``"markdown"`` (document -> markdown, default) or
                ``"free"`` (plain free-form OCR text).
            base_size/image_size/crop_mode: DeepSeek-OCR resolution knobs;
                defaults match the "Small" preset in the model card.
        """
        if prompt is None:
            if mode not in {"markdown", "free"}:
                raise ValueError(f"mode must be 'markdown' or 'free' (got {mode!r}).")
            prompt = MARKDOWN_PROMPT if mode == "markdown" else FREE_OCR_PROMPT

        image_path, is_temp = self._resolve_image_path(image)
        try:
            text = self._infer(image_path, prompt, base_size, image_size, crop_mode)
        finally:
            if is_temp and os.path.exists(image_path):
                os.remove(image_path)
        return {"text": text, "model": self.model_id, "mode": mode}

    def understand(
        self,
        image: Optional[ImageInput] = None,
        prompt: Optional[str] = None,
        mode: str = "markdown",
        base_size: int = 1024,
        image_size: int = 640,
        crop_mode: bool = True,
    ) -> Dict[str, Any]:
        """CLI-friendly entry point: ``image`` is required (OCR has no
        text-only or video path)."""
        if image is None:
            raise ValueError("image is required for DeepSeek-OCR.")
        return self.understand_image(
            image, prompt=prompt, mode=mode,
            base_size=base_size, image_size=image_size, crop_mode=crop_mode,
        )
