"""
Limite 1B - Violetto (Paradigma Inc, open-weight) Local Adapter

Local GPU/CPU inference adapter for Paradigma's Limite 1B - Violetto --
a dense 1B-parameter autoregressive transformer trained specifically for
high-throughput **mathematical reasoning**, not general-purpose chat or
image/video understanding. No first-party hosted API exists (Paradigma
publishes weights only) -- this local adapter is the only way to use it.

Out of the fashion/media scope every other OpenTryOn model targets --
added as a reference point for a possible future "generic model gateway"
direction, not because it fits virtual try-on/generation. Text only: no
image, video, or audio input.

Default model: ``paradigma-inc/limite-1b-violetto`` (~2.1GB on disk,
extremely light for a local model in this registry). Single-turn use only
(system prompt + current user message) -- the model card notes it may
reinterpret multi-turn context as a different math task.

Reference:
https://huggingface.co/paradigma-inc/limite-1b-violetto
https://github.com/paradigma-inc/limite-violetto

Requirements:
    pip install opentryon[local]   # torch, transformers, etc.

The model card recommends Python 3.12 / torch 2.11 / transformers 5.6.2 and
``attn_implementation="sdpa"`` (FlashAttention2 + StaticCache is explicitly
called out upstream as numerically incorrect -- sdpa is the safe default
used here). This repo's shared ``opentryon[local]`` pin is older
(transformers==4.42.4) -- upgrade in a separate env if loading fails.

Examples:
    >>> from tryon.models.limite import LimiteAdapter
    >>> adapter = LimiteAdapter()  # downloads paradigma-inc/limite-1b-violetto on first use
    >>> result = adapter.understand(prompt="If x + 3 = 8, what is x?")
    >>> print(result["text"])
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

DEFAULT_MODEL_ID = "paradigma-inc/limite-1b-violetto"


class LimiteAdapter:
    """
    Local Hugging Face Transformers adapter for Paradigma's Limite 1B -
    Violetto math-reasoning model.

    Args:
        model_id: Hugging Face model id. Defaults to ``LIMITE_MODEL_ID`` env
            or ``"paradigma-inc/limite-1b-violetto"``.
        device: Passed as ``device_map``. Defaults to ``"auto"``.
        torch_dtype: Passed to ``from_pretrained``. Defaults to ``"auto"``.
        trust_remote_code: Limite ships custom modeling code on the Hub.
            Defaults to True (required for it to load).

    Raises:
        ImportError: If ``torch``/``transformers`` aren't installed (install
            the ``local`` extra: ``pip install opentryon[local]``).
    """

    def __init__(
        self,
        model_id: Optional[str] = None,
        device: Optional[str] = None,
        torch_dtype: str = "auto",
        trust_remote_code: bool = True,
    ):
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:
            raise ImportError(
                "Limite 1B - Violetto requires the 'local' extra: "
                "pip install opentryon[local] (needs torch + transformers)."
            ) from exc

        self.model_id = model_id or os.getenv("LIMITE_MODEL_ID") or DEFAULT_MODEL_ID
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_id, trust_remote_code=trust_remote_code
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_id,
            trust_remote_code=trust_remote_code,
            torch_dtype=torch_dtype,
            device_map=device or "auto",
            attn_implementation="sdpa",
        )

    def understand(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_new_tokens: int = 512,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Solve a single-turn math prompt.

        Only a system prompt + the current user message are sent -- no
        multi-turn history -- matching the model card's recommended usage
        (it may reinterpret earlier turns as a different math problem).
        Sampling defaults (temperature 0.6 / top_p 0.95) come from the
        model's own ``generation_config.json`` unless overridden here.
        """
        import torch

        prompt = (prompt or "").strip()
        if not prompt:
            raise ValueError("prompt is required.")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        text = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)

        gen_kwargs: Dict[str, Any] = {"max_new_tokens": max_new_tokens}
        if temperature is not None:
            gen_kwargs["temperature"] = temperature
            gen_kwargs["do_sample"] = True
        if top_p is not None:
            gen_kwargs["top_p"] = top_p
            gen_kwargs["do_sample"] = True

        with torch.inference_mode():
            output_ids = self.model.generate(**inputs, **gen_kwargs)

        answer = self.tokenizer.decode(
            output_ids[0, inputs["input_ids"].shape[1]:], skip_special_tokens=True
        )
        return {"text": answer.strip(), "model": self.model_id}
