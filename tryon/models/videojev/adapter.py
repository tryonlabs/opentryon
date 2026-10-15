"""
VideoJev local adapter (MCG-NJU open-weight video System One models).

Temporal grounding and multiple-choice video QA via direct candidate scoring
(``predict_video``), not autoregressive text generation.

Models:
  - ZhuYuhan/VideoJev-4B (Qwen3.5-4B backbone)
  - ZhuYuhan/VideoJev-35B-A3B (Qwen3.6-35B-A3B backbone)

Reference:
  https://github.com/MCG-NJU/VideoJev
  https://mcg-nju.github.io/VideoJev/
  https://arxiv.org/abs/2610.18615

There is no first-party hosted VideoJev API. Typesafe Jev (``decide jev``) is
text/JSON only; HAL-X THX-01 is also text-only on ``/v1/systemone``.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Union

from tryon.decision import VideoJevQuestions, load_videojev_questions

VARIANTS = {
    "4b": "ZhuYuhan/VideoJev-4B",
    "35b-a3b": "ZhuYuhan/VideoJev-35B-A3B",
}

_DEFAULT_CONTEXT = {"4b": 8192, "35b-a3b": 262144}


class VideoJevAdapter:
    """
    Local Hugging Face adapter for VideoJev-4B / VideoJev-35B-A3B.

    Args:
        variant: ``4b`` (default) or ``35b-a3b``.
        model_id: Override HF repo id or local checkpoint path.
        device: ``cuda`` / ``cpu`` (CUDA strongly recommended).
    """

    def __init__(
        self,
        variant: str = "4b",
        model_id: Optional[str] = None,
        device: Optional[str] = None,
    ):
        key = variant.replace("_", "-").lower()
        if key not in VARIANTS:
            raise ValueError(f"Invalid variant {variant!r}. Supported: {sorted(VARIANTS)}")
        self.variant = key
        env_key = f"VIDEOJEV_MODEL_ID_{key.upper().replace('-', '_')}"
        self.model_id = (
            model_id or os.getenv(env_key) or os.getenv("VIDEOJEV_MODEL_ID") or VARIANTS[key]
        )

        try:
            import torch
        except ImportError as exc:
            raise ImportError(
                "VideoJev requires PyTorch. Install with: pip install opentryon[local]"
            ) from exc

        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device
        self._torch = torch
        self._model = None
        self._processor = None

    def _load(self):
        if self._model is not None:
            return self._model, self._processor
        try:
            from transformers import AutoModel, AutoProcessor
        except ImportError as exc:
            raise ImportError(
                "VideoJev needs a recent transformers with trust_remote_code support. "
                "See docs/docs/local-models/videojev.md for the recommended environment."
            ) from exc

        processor = AutoProcessor.from_pretrained(self.model_id, trust_remote_code=True)
        load_kwargs: Dict[str, Any] = {
            "trust_remote_code": True,
            "dtype": self._torch.bfloat16 if self.device != "cpu" else self._torch.float32,
        }
        if self.device == "cuda":
            load_kwargs["device_map"] = {"": "cuda:0"}
            try:
                import flash_attn  # noqa: F401

                load_kwargs["attn_implementation"] = "flash_attention_2"
            except ImportError:
                pass
        else:
            load_kwargs["device_map"] = {"": "cpu"}

        model = AutoModel.from_pretrained(self.model_id, **load_kwargs)
        if hasattr(model, "prepare_for_inference"):
            model.prepare_for_inference()
        model.eval()
        self._model = model
        self._processor = processor
        return model, processor

    @staticmethod
    def _resolve_video(video: str) -> str:
        if not video:
            raise ValueError("--video is required for VideoJev (path or http(s) URL).")
        if video.startswith(("http://", "https://")):
            return video
        if os.path.isfile(video):
            return video
        raise ValueError(f"Video path does not exist: {video}")

    def decide(
        self,
        questions: VideoJevQuestions,
        video: str,
        fps: float = 2.0,
        max_frames: int = 2048,
        context: Optional[int] = None,
        threshold: float = 0.25,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Run VideoJev ``predict_video`` on a clip and a list of grounding/QA items.

        ``questions`` is a JSON array (or path) in the native VideoJev shape; see
        ``load_videojev_questions`` and the local docs page.
        """
        qs = load_videojev_questions(questions)
        video_path = self._resolve_video(video)
        ctx = context if context is not None else _DEFAULT_CONTEXT[self.variant]
        model, processor = self._load()
        predict = getattr(model, "predict_video", None)
        if predict is None:
            raise RuntimeError(
                f"Loaded model {self.model_id!r} has no predict_video; "
                "use an official VideoJev HF checkpoint with remote code."
            )
        call_kwargs: Dict[str, Any] = {
            "fps": fps,
            "max_frames": max_frames,
            "context": ctx,
            "threshold": threshold,
        }
        call_kwargs.update(kwargs)
        results = predict(processor, video_path, qs, **call_kwargs)
        return {
            "model": self.model_id,
            "variant": self.variant,
            "results": results,
        }
