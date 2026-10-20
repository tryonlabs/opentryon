"""
vLLM-SR Decision 3.0 — local Hugging Face adapter (Apache-2.0).

Uses ``transformers.AutoModel`` with ``trust_remote_code=True`` and ``model.system_one()``.

Reference: https://huggingface.co/vllm-sr/d3-turbo

Requirements (separate env recommended; shared opentryon[local] pin is older):
    pip install "transformers==5.17.0" torch torchvision pillow opencv-python-headless safetensors accelerate
    pip install flash-linear-attention  # optional GPU kernels
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Union

from tryon.d3_media import (
    load_assets,
    prepare_images_for_local,
    prepare_videos_for_local,
)
from tryon.decision import Questions, load_d3_questions, load_state

DEFAULT_MODEL_IDS = {
    "turbo": "vllm-sr/d3-turbo",
    "flash": "vllm-sr/d3-flash",
    "mini": "vllm-sr/d3-mini",
    "nano": "vllm-sr/d3-nano",
    "lite": "vllm-sr/d3-lite",
    "edge": "vllm-sr/d3-edge",
}


class D3LocalAdapter:
    """Local Decision 3.0 weights via Hugging Face Transformers."""

    def __init__(
        self,
        variant: str = "turbo",
        model_id: Optional[str] = None,
        device: Optional[str] = None,
    ):
        key = variant.replace("_", "-").lower()
        if key not in DEFAULT_MODEL_IDS:
            raise ValueError(f"Invalid variant {variant!r}. Supported: {sorted(DEFAULT_MODEL_IDS)}")
        self.variant = key
        env_key = f"D3_MODEL_ID_{key.upper().replace('-', '_')}"
        self.model_id = (
            model_id or os.getenv(env_key) or os.getenv("D3_MODEL_ID") or DEFAULT_MODEL_IDS[key]
        )

        try:
            import torch
        except ImportError as exc:
            raise ImportError(
                "Decision 3.0 (local) requires PyTorch. Install with: pip install opentryon[local]"
            ) from exc

        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device
        self._torch = torch
        self._model = None

    def _load(self):
        if self._model is not None:
            return self._model
        try:
            import transformers
            from transformers import AutoModel
        except ImportError as exc:
            raise ImportError(
                "Decision 3.0 local inference needs a recent transformers (>=5.17). Install with:\n"
                '  pip install "transformers==5.17.0" torch torchvision pillow opencv-python-headless\n'
                f"Original error: {exc}"
            ) from exc
        try:
            major, minor = (int(p) for p in transformers.__version__.split(".")[:2])
        except ValueError:
            major, minor = (5, 17)
        if (major, minor) < (5, 17):
            raise ImportError(
                f"d3 models need transformers>=5.17 (found {transformers.__version__}). "
                "Use a separate environment; the shared opentryon[local] pin is older."
            )

        model = AutoModel.from_pretrained(
            self.model_id,
            trust_remote_code=True,
            torch_dtype=self._torch.bfloat16 if self.device != "cpu" else self._torch.float32,
        )
        model = model.to(self.device)
        model.eval()
        self._model = model
        return self._model

    def decide(
        self,
        questions: Questions,
        state: Optional[Any] = None,
        image: Optional[Union[str, List[str]]] = None,
        video: Optional[Union[str, List[str]]] = None,
        assets: Optional[Union[str, Dict[str, Any]]] = None,
        long_context: bool = False,
    ) -> Dict[str, Any]:
        qs = load_d3_questions(questions)
        st = load_state(state)
        images_list: List[str] = []
        if image is not None:
            images_list = image if isinstance(image, list) else [image]
        videos_list: List[str] = []
        if video is not None:
            videos_list = video if isinstance(video, list) else [video]
        asset_map = load_assets(assets)

        if (st is None or st == "") and not images_list and not videos_list:
            raise ValueError(
                "Provide --state and/or --image / --video (Decision 3.0 is multimodal)."
            )

        kwargs: Dict[str, Any] = {}
        if images_list:
            kwargs["images"] = prepare_images_for_local(images_list)
        if videos_list:
            kwargs["videos"] = prepare_videos_for_local(videos_list)
        if asset_map:
            kwargs["assets"] = asset_map
        if long_context:
            kwargs["long_context"] = True

        model = self._load()
        result = model.system_one(None if st in (None, "") else st, qs, **kwargs)
        if isinstance(result, dict) and "answers" in result:
            answers = result.get("answers", {})
            usage = result.get("usage")
        else:
            answers = result if isinstance(result, dict) else {}
            usage = None
        return {"model": self.model_id, "answers": answers, "usage": usage}
