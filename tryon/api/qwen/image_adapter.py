"""
Qwen-Image (DashScope / Qwen Cloud) generation, edit, and try-on adapter.

First-party Alibaba Cloud Model Studio multimodal-generation API for the
Qwen-Image family. Text-to-image, image-to-image (1–3 refs), and a
virtual-try-on convenience wrapper that composes a person + garment pair.

This is the image counterpart to ``QwenUnderstandAdapter`` (Qwen3.8-Max).
Same ``DASHSCOPE_API_KEY``; different endpoint (DashScope ``/api/v1``
multimodal-generation, not OpenAI-compatible chat).

Docs:
    https://docs.qwencloud.com/api-reference/image-generation/qwen-text-to-image
    https://docs.qwencloud.com/api-reference/image-generation/qwen-image-editing
    https://help.aliyun.com/en/model-studio/qwen-image-generation-and-editing-api-reference

Models:
    qwen-image-3.0-pro (default), qwen-image-3.0,
    qwen-image-2.0-pro, qwen-image-2.0

Env:
    DASHSCOPE_API_KEY (required)
    QWEN_IMAGE_BASE_URL — default https://dashscope-intl.aliyuncs.com/api/v1
      China: https://dashscope.aliyuncs.com/api/v1
      Or a workspace URL:
        https://{WorkspaceId}.ap-southeast-1.maas.aliyuncs.com/api/v1

Examples:
    >>> from tryon.api.qwen import QwenImageAdapter
    >>> adapter = QwenImageAdapter()
    >>> images = adapter.generate_text_to_image("editorial lookbook, linen trench")
    >>> tryon = adapter.generate_virtual_tryon("person.jpg", "garment.jpg")
"""

from __future__ import annotations

import base64
import io
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import requests
from PIL import Image

DEFAULT_BASE_URL = "https://dashscope-intl.aliyuncs.com/api/v1"
GENERATION_PATH = "/services/aigc/multimodal-generation/generation"

VALID_MODELS = {
    "qwen-image-3.0-pro",
    "qwen-image-3.0",
    "qwen-image-2.0-pro",
    "qwen-image-2.0",
}
VALID_PROMPT_EXTEND_MODES = {"direct", "agent"}

DEFAULT_TRYON_PROMPT = (
    "The person in the first image, keeping their face, pose and background "
    "unchanged, wearing the garment shown in the second image. Preserve identity "
    "and lighting; match the garment's fabric, color, and details faithfully."
)

ImageInput = Union[str, Path, io.BytesIO, bytes, Image.Image]


class QwenImageAdapter:
    """
    Adapter for Qwen-Image T2I / I2I / virtual try-on via DashScope.

    Args:
        api_key: DashScope / Model Studio key. Defaults to ``DASHSCOPE_API_KEY``.
        model: Default model id. Defaults to ``"qwen-image-3.0-pro"``.
        base_url: DashScope ``/api/v1`` host. Defaults to ``QWEN_IMAGE_BASE_URL``,
            then ``WAN_API_BASE_URL``, then the international endpoint.
        timeout: HTTP timeout in seconds for a single generation call.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "qwen-image-3.0-pro",
        base_url: Optional[str] = None,
        timeout: float = 300.0,
    ):
        if model not in VALID_MODELS:
            raise ValueError(
                f"Invalid model: {model!r}. Supported models: {sorted(VALID_MODELS)}"
            )

        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "DashScope API key must be provided either as a parameter or "
                "through the DASHSCOPE_API_KEY environment variable."
            )

        self.model = model
        self.base_url = (
            base_url
            or os.getenv("QWEN_IMAGE_BASE_URL")
            or os.getenv("WAN_API_BASE_URL")
            or DEFAULT_BASE_URL
        ).rstrip("/")
        self.timeout = float(timeout)

    # -- input loading --------------------------------------------------

    @staticmethod
    def _load_bytes(source, default_ext: str = "png"):
        if isinstance(source, Image.Image):
            buf = io.BytesIO()
            source.convert("RGB").save(buf, format="PNG")
            return buf.getvalue(), "png"

        if isinstance(source, (bytes, bytearray)):
            return bytes(source), default_ext

        if isinstance(source, io.BytesIO):
            source.seek(0)
            return source.read(), default_ext

        source_str = str(source)
        if source_str.startswith("http://") or source_str.startswith("https://"):
            resp = requests.get(source_str, timeout=60)
            resp.raise_for_status()
            ext = Path(source_str.split("?")[0]).suffix.lstrip(".").lower() or default_ext
            return resp.content, ext

        path = Path(source_str)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {source_str}")
        ext = path.suffix.lstrip(".").lower() or default_ext
        with open(path, "rb") as f:
            return f.read(), ext

    def _image_uri(self, image: ImageInput) -> str:
        """Pass through http(s)/data/oss URIs; otherwise encode as a data URI."""
        if isinstance(image, (str, Path)):
            source = str(image)
            if source.startswith(("http://", "https://", "data:", "oss://")):
                return source
        data, ext = self._load_bytes(image, default_ext="png")
        mime = "jpeg" if ext in {"jpg", "jpeg"} else (ext or "png")
        return f"data:image/{mime};base64,{base64.b64encode(data).decode('utf-8')}"

    @staticmethod
    def _normalize_size(size: Optional[str]) -> Optional[str]:
        if not size:
            return None
        return size.strip().replace("x", "*").replace("X", "*").replace("×", "*")

    def _resolve_model(self, model: Optional[str]) -> str:
        resolved = model or self.model
        if resolved not in VALID_MODELS:
            raise ValueError(
                f"Invalid model: {resolved!r}. Supported models: {sorted(VALID_MODELS)}"
            )
        return resolved

    # -- core call --------------------------------------------------------

    def _generate(
        self,
        content: List[Dict[str, Any]],
        model: Optional[str] = None,
        size: Optional[str] = None,
        n: int = 1,
        negative_prompt: Optional[str] = None,
        prompt_extend: bool = True,
        prompt_extend_mode: Optional[str] = None,
        enable_thinking: bool = True,
        watermark: bool = False,
        seed: Optional[int] = None,
    ) -> List[Image.Image]:
        parameters: Dict[str, Any] = {
            "n": int(n),
            "prompt_extend": bool(prompt_extend),
            "enable_thinking": bool(enable_thinking),
            "watermark": bool(watermark),
        }
        normalized_size = self._normalize_size(size)
        if normalized_size:
            parameters["size"] = normalized_size
        if negative_prompt:
            parameters["negative_prompt"] = negative_prompt
        if prompt_extend_mode is not None:
            if prompt_extend_mode not in VALID_PROMPT_EXTEND_MODES:
                raise ValueError(
                    f"Invalid prompt_extend_mode: {prompt_extend_mode!r}. "
                    f"Supported values: {sorted(VALID_PROMPT_EXTEND_MODES)}"
                )
            parameters["prompt_extend_mode"] = prompt_extend_mode
        if seed is not None:
            parameters["seed"] = int(seed)

        payload = {
            "model": self._resolve_model(model),
            "input": {"messages": [{"role": "user", "content": content}]},
            "parameters": parameters,
        }
        url = f"{self.base_url}{GENERATION_PATH}"
        resp = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=self.timeout,
        )
        try:
            data = resp.json()
        except ValueError as exc:
            raise RuntimeError(
                f"Qwen-Image returned non-JSON ({resp.status_code}): {resp.text[:500]}"
            ) from exc

        err_code = data.get("code")
        if resp.status_code >= 400 or err_code:
            message = data.get("message") or resp.text
            raise RuntimeError(
                f"Qwen-Image request failed ({resp.status_code}"
                f"{', ' + err_code if err_code else ''}): {message}"
            )

        images = self._images_from_response(data)
        if not images:
            raise RuntimeError(f"Qwen-Image returned no images: {data}")
        return images

    def _images_from_response(self, data: Dict[str, Any]) -> List[Image.Image]:
        choices = (data.get("output") or {}).get("choices") or []
        urls: List[str] = []
        for choice in choices:
            content = ((choice.get("message") or {}).get("content")) or []
            for part in content:
                if isinstance(part, dict) and part.get("image"):
                    urls.append(part["image"])
        images: List[Image.Image] = []
        for image_url in urls:
            r = requests.get(image_url, timeout=60)
            r.raise_for_status()
            images.append(Image.open(io.BytesIO(r.content)).convert("RGB"))
        return images

    def _i2i(
        self,
        images: List[ImageInput],
        prompt: str,
        **kwargs,
    ) -> List[Image.Image]:
        if not prompt:
            raise ValueError("prompt is required.")
        if not images:
            raise ValueError("At least one input image is required.")
        if len(images) > 3:
            raise ValueError("Qwen-Image I2I accepts at most 3 reference images.")
        content: List[Dict[str, Any]] = [
            {"image": self._image_uri(img)} for img in images
        ]
        content.append({"text": prompt})
        return self._generate(content, **kwargs)

    # -- public API ---------------------------------------------------------

    def generate_text_to_image(
        self,
        prompt: str,
        size: Optional[str] = None,
        n: int = 1,
        negative_prompt: Optional[str] = None,
        prompt_extend: bool = True,
        prompt_extend_mode: str = "direct",
        enable_thinking: bool = True,
        watermark: bool = False,
        seed: Optional[int] = None,
        model: Optional[str] = None,
    ) -> List[Image.Image]:
        """Generate image(s) from a text prompt (T2I)."""
        if not prompt:
            raise ValueError("prompt is required.")
        return self._generate(
            [{"text": prompt}],
            model=model,
            size=size,
            n=n,
            negative_prompt=negative_prompt,
            prompt_extend=prompt_extend,
            prompt_extend_mode=prompt_extend_mode,
            enable_thinking=enable_thinking,
            watermark=watermark,
            seed=seed,
        )

    def generate_image_edit(
        self,
        image: Union[ImageInput, List[ImageInput]],
        prompt: str,
        size: Optional[str] = None,
        n: int = 1,
        negative_prompt: Optional[str] = None,
        prompt_extend: bool = True,
        prompt_extend_mode: str = "direct",
        enable_thinking: bool = True,
        watermark: bool = False,
        seed: Optional[int] = None,
        model: Optional[str] = None,
    ) -> List[Image.Image]:
        """Edit or restyle one image (I2I). Pass a list for 1–3 refs."""
        images = image if isinstance(image, list) else [image]
        return self._i2i(
            images,
            prompt,
            model=model,
            size=size,
            n=n,
            negative_prompt=negative_prompt,
            prompt_extend=prompt_extend,
            prompt_extend_mode=prompt_extend_mode,
            enable_thinking=enable_thinking,
            watermark=watermark,
            seed=seed,
        )

    def generate_multi_image(
        self,
        images: List[ImageInput],
        prompt: str,
        size: Optional[str] = None,
        n: int = 1,
        negative_prompt: Optional[str] = None,
        prompt_extend: bool = True,
        prompt_extend_mode: str = "direct",
        enable_thinking: bool = True,
        watermark: bool = False,
        seed: Optional[int] = None,
        model: Optional[str] = None,
    ) -> List[Image.Image]:
        """Compose 1–3 reference images with a text instruction (I2I)."""
        return self._i2i(
            images,
            prompt,
            model=model,
            size=size,
            n=n,
            negative_prompt=negative_prompt,
            prompt_extend=prompt_extend,
            prompt_extend_mode=prompt_extend_mode,
            enable_thinking=enable_thinking,
            watermark=watermark,
            seed=seed,
        )

    def build_tryon_prompt(
        self,
        prompt: Optional[str] = None,
        garment_description: Optional[str] = None,
    ) -> str:
        """Build the styling prompt for a virtual try-on composition."""
        if prompt:
            return prompt
        if garment_description:
            return (
                "The person in the first image, keeping their face, pose and "
                f"background unchanged, wearing the {garment_description} shown "
                "in the second image. Preserve identity and lighting; match the "
                "garment's fabric, color, and details faithfully."
            )
        return DEFAULT_TRYON_PROMPT

    def generate_virtual_tryon(
        self,
        person: Optional[ImageInput] = None,
        garment: Optional[ImageInput] = None,
        *,
        source_image: Optional[ImageInput] = None,
        reference_image: Optional[ImageInput] = None,
        model_image: Optional[ImageInput] = None,
        cloth_image: Optional[ImageInput] = None,
        person_image: Optional[ImageInput] = None,
        garment_image: Optional[ImageInput] = None,
        prompt: Optional[str] = None,
        garment_description: Optional[str] = None,
        size: Optional[str] = None,
        n: int = 1,
        negative_prompt: Optional[str] = None,
        prompt_extend: bool = True,
        prompt_extend_mode: str = "direct",
        enable_thinking: bool = True,
        watermark: bool = False,
        seed: Optional[int] = None,
        model: Optional[str] = None,
    ) -> List[Image.Image]:
        """
        Virtual try-on via Qwen-Image I2I: person (first) + garment (second).

        Convenience wrapper around ``generate_multi_image``. Not a dedicated
        garment-fit model — prefer FLUX VTO / FASHN when drape accuracy
        matters more than a single DashScope workflow.
        """
        resolved_person = person or source_image or person_image or model_image
        resolved_garment = garment or reference_image or garment_image or cloth_image

        if resolved_person is None:
            raise ValueError(
                "Person image is required. Pass person, source_image, person_image, "
                "or model_image."
            )
        if resolved_garment is None:
            raise ValueError(
                "Garment image is required. Pass garment, reference_image, "
                "garment_image, or cloth_image."
            )

        styling_prompt = self.build_tryon_prompt(
            prompt=prompt, garment_description=garment_description
        )
        return self.generate_multi_image(
            images=[resolved_person, resolved_garment],
            prompt=styling_prompt,
            size=size,
            n=n,
            negative_prompt=negative_prompt,
            prompt_extend=prompt_extend,
            prompt_extend_mode=prompt_extend_mode,
            enable_thinking=enable_thinking,
            watermark=watermark,
            seed=seed,
            model=model,
        )
