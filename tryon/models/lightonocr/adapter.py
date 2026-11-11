"""
LightOnOCR-3 local adapter (Hugging Face Transformers, in-process).

LightOnOCR-3 (LightOn, Apache-2.0, October 2026) turns a page image into markdown. With
the ``grounding`` prompt it also emits a label and a 0-1000 bounding box before every
block (text, title, table, chart, image, header, footer, ...); tables and charts come
back as HTML tables. Fashion fit: size charts, spec and tech sheets, line sheets,
invoices and care-label scans.

Variants (both on the Qwen3.5 vision-language architecture):

- ``0.8b`` -> ``lightonai/LightOnOCR-3-0.8B`` (default; ~0.9B params, ~2 GB in BF16)
- ``4b``   -> ``lightonai/LightOnOCR-3-4B`` (LightOn's recommended quality tier)

The 1B sibling uses the older LightOnOCR-2 architecture and is not wired here.

Requirements: ``transformers>=5.2`` (the card was saved with 5.5.4), ``torch`` and, for PDF
input, ``pypdfium2``. These are newer than the shared ``opentryon[local]`` pin, so use a
separate environment if loading fails. To serve the model instead, run vLLM and use
``parse --model lightonocr-3-vllm``.

References:
  https://huggingface.co/lightonai/LightOnOCR-3-0.8B
  https://huggingface.co/blog/lightonai/lightonocr-3
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Sequence, Union

from tryon.ocr import PageInput, load_pages, package_pages

VARIANTS = {
    "0.8b": "lightonai/LightOnOCR-3-0.8B",
    "4b": "lightonai/LightOnOCR-3-4B",
}
DEFAULT_VARIANT = "0.8b"
GROUNDING_PROMPT = "grounding"
DEFAULT_MAX_NEW_TOKENS = 4096


class LightOnOCRLocalAdapter:
    """Run LightOnOCR-3 in-process with Transformers (weights load on first use)."""

    def __init__(self, variant: str = DEFAULT_VARIANT, model_id: Optional[str] = None, device: Optional[str] = None):
        if variant not in VARIANTS:
            raise ValueError(f"variant must be one of {sorted(VARIANTS)} (got {variant!r}).")
        self.variant = variant
        self.model_id = model_id or os.getenv("LIGHTONOCR_MODEL_ID") or VARIANTS[variant]
        self.device = device
        self._model = None
        self._processor = None

    def _load(self):
        if self._model is not None:
            return
        try:
            import torch
            from transformers import AutoProcessor, Qwen3_5ForConditionalGeneration
        except ImportError as exc:
            raise ImportError(
                "LightOnOCR-3 needs torch and transformers>=5.2 (Qwen3.5 classes): "
                'pip install "transformers>=5.5.4" torch pillow pypdfium2'
            ) from exc
        kwargs: Dict[str, Any] = {"dtype": torch.bfloat16}
        kwargs["device_map"] = self.device or "auto"
        self._model = Qwen3_5ForConditionalGeneration.from_pretrained(self.model_id, **kwargs).eval()
        self._processor = AutoProcessor.from_pretrained(self.model_id)

    def _run_page(self, page, prompt: str, max_new_tokens: int) -> str:
        import torch

        conversation = [{"role": "user", "content": [{"type": "image", "image": page}, {"type": "text", "text": prompt}]}]
        inputs = self._processor.apply_chat_template(
            conversation, add_generation_prompt=True, tokenize=True, return_dict=True,
            return_tensors="pt", enable_thinking=False,
        ).to(self._model.device)
        with torch.inference_mode():
            output_ids = self._model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=True, temperature=0.2)
        generated = output_ids[0, inputs["input_ids"].shape[1]:]
        return self._processor.decode(generated, skip_special_tokens=True)

    def parse_document(
        self,
        image: PageInput,
        grounding: bool = False,
        pages: Optional[Union[str, Sequence[int]]] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """OCR an image or PDF into markdown.

        Args:
            image: image path / URL / bytes / PIL image, or a PDF path / URL / bytes.
            grounding: also return labelled blocks with 0-1000 bounding boxes.
            pages: PDF pages to read, e.g. ``"1-3,5"`` (default: all).
            max_tokens: max new tokens per page (default 4096).
        """
        page_images: List[Any] = load_pages(image, pages)
        self._load()
        prompt = GROUNDING_PROMPT if grounding else ""
        limit = int(max_tokens or DEFAULT_MAX_NEW_TOKENS)
        raw_pages = [self._run_page(p, prompt, limit) for p in page_images]
        return package_pages(self.model_id, "local", grounding, raw_pages)
