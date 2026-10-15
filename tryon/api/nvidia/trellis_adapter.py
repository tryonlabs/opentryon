"""
Microsoft TRELLIS via NVIDIA NIM (Path A) — text/image to 3D mesh (GLB/STL).

Hosted: ``POST https://ai.api.nvidia.com/v1/genai/microsoft/trellis``
Self-hosted NIM: ``TRELLIS_INFER_URL`` (``http://127.0.0.1:8000/v1/infer``).

Docs:
  https://docs.api.nvidia.com/nim/reference/microsoft-trellis-infer
  https://build.nvidia.com/microsoft/trellis
"""

from __future__ import annotations

import base64
import io
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

import requests
from PIL import Image

from .adapter import _load_bytes, _resolve_nvidia_key
from .cosmos_adapter import NVCF_STATUS_URL

DEFAULT_INFER_URL = "https://ai.api.nvidia.com/v1/genai/microsoft/trellis"

ImageInput = Union[str, Path, io.BytesIO, bytes, Image.Image]


class TrellisMeshAdapter:
    """TRELLIS 3D asset generation via NVIDIA genai / NIM infer."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        infer_url: Optional[str] = None,
        poll_interval: float = 5.0,
        timeout: float = 900.0,
    ):
        self.api_key = _resolve_nvidia_key(api_key)
        self.infer_url = (
            infer_url or os.getenv("TRELLIS_INFER_URL") or DEFAULT_INFER_URL
        ).rstrip("/")
        self.poll_interval = float(poll_interval)
        self.timeout = float(timeout)

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _image_payload(self, image: ImageInput) -> str:
        if isinstance(image, str) and image.startswith("data:image/png;example_id,"):
            return image
        data, ext = _load_bytes(image, default_ext="png")
        if ext not in {"png", "jpg", "jpeg"}:
            ext = "png"
        mime = "jpeg" if ext in {"jpg", "jpeg"} else "png"
        return f"data:image/{mime};base64,{base64.b64encode(data).decode('utf-8')}"

    def _raise_http(self, resp: requests.Response) -> None:
        try:
            payload = resp.json()
        except ValueError:
            payload = None
        if isinstance(payload, dict):
            detail = payload.get("detail") or payload.get("error") or payload.get("title")
            if detail:
                raise RuntimeError(f"TRELLIS HTTP {resp.status_code}: {detail}")
        snippet = (resp.text or "")[:500]
        raise RuntimeError(f"TRELLIS HTTP {resp.status_code}: {snippet}")

    def _poll_nvcf(self, resp: requests.Response) -> requests.Response:
        req_id = resp.headers.get("NVCF-REQID") or resp.headers.get("nvcf-reqid")
        if not req_id:
            self._raise_http(resp)
        url = NVCF_STATUS_URL.format(req_id=req_id)
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            time.sleep(self.poll_interval)
            poll = requests.get(url, headers=self._headers(), timeout=60)
            if poll.status_code == 202:
                continue
            if poll.status_code >= 400:
                self._raise_http(poll)
            return poll
        raise TimeoutError(
            f"TRELLIS timed out after {self.timeout:.0f}s (NVCF-REQID={req_id})."
        )

    def _post_infer(self, body: Dict[str, Any]) -> Dict[str, Any]:
        resp = requests.post(
            self.infer_url,
            json=body,
            headers=self._headers(),
            timeout=max(self.timeout, 120.0),
        )
        if resp.status_code == 202:
            resp = self._poll_nvcf(resp)
        if resp.status_code >= 400:
            self._raise_http(resp)
        try:
            data = resp.json()
        except ValueError as exc:
            raise RuntimeError("TRELLIS returned non-JSON.") from exc
        if isinstance(data, dict) and data.get("error"):
            raise RuntimeError(f"TRELLIS error: {data['error']}")
        return data if isinstance(data, dict) else {"raw": data}

    def _decode_mesh(self, data: Dict[str, Any], output_format: str) -> bytes:
        artifacts = data.get("artifacts")
        if isinstance(artifacts, list) and artifacts:
            item = artifacts[0]
            if isinstance(item, dict):
                b64 = item.get("base64") or item.get("content")
                if b64:
                    if isinstance(b64, str) and b64.startswith("data:"):
                        b64 = b64.split(",", 1)[-1]
                    return base64.b64decode(b64)
        b64 = data.get("base64") or data.get("model")
        if b64 and isinstance(b64, str):
            if b64.startswith("data:"):
                b64 = b64.split(",", 1)[-1]
            return base64.b64decode(b64)
        raise RuntimeError(
            f"TRELLIS response missing mesh artifacts (keys: {list(data.keys())})."
        )

    def _run(
        self,
        *,
        prompt: Optional[str] = None,
        image: Optional[ImageInput] = None,
        output_format: str = "glb",
        seed: int = 0,
        no_texture: bool = False,
        slat_cfg_scale: Optional[float] = None,
        ss_cfg_scale: Optional[float] = None,
        slat_sampling_steps: Optional[int] = None,
        ss_sampling_steps: Optional[int] = None,
    ) -> Tuple[bytes, str]:
        output_format = (output_format or "glb").lower()
        if output_format not in {"glb", "stl"}:
            raise ValueError("output_format must be glb or stl")
        if not prompt and image is None:
            raise ValueError("Provide --prompt (text-to-3D) or --image (image-to-3D).")
        if prompt and len(prompt) > 77:
            raise ValueError("TRELLIS prompt must be at most 77 characters.")
        body: Dict[str, Any] = {
            "output_format": output_format,
            "samples": 1,
            "seed": int(seed),
            "no_texture": bool(no_texture),
        }
        if prompt:
            body["prompt"] = prompt
        if image is not None:
            body["image"] = self._image_payload(image)
            body.setdefault("mode", "image")
        elif prompt:
            body.setdefault("mode", "text")
        if slat_cfg_scale is not None:
            body["slat_cfg_scale"] = float(slat_cfg_scale)
        if ss_cfg_scale is not None:
            body["ss_cfg_scale"] = float(ss_cfg_scale)
        if slat_sampling_steps is not None:
            body["slat_sampling_steps"] = int(slat_sampling_steps)
        if ss_sampling_steps is not None:
            body["ss_sampling_steps"] = int(ss_sampling_steps)
        data = self._post_infer(body)
        return self._decode_mesh(data, output_format), output_format

    def generate_text_to_3d(
        self,
        prompt: str,
        output_format: str = "glb",
        seed: int = 0,
        no_texture: bool = False,
        **kwargs,
    ) -> Tuple[bytes, str]:
        if not (prompt or "").strip():
            raise ValueError("prompt is required for text-to-3D.")
        mesh, fmt = self._run(
            prompt=prompt.strip(),
            output_format=output_format,
            seed=seed,
            no_texture=no_texture,
            **kwargs,
        )
        return mesh, fmt

    def generate_image_to_3d(
        self,
        image: ImageInput,
        prompt: str = "",
        output_format: str = "glb",
        seed: int = 0,
        no_texture: bool = False,
        **kwargs,
    ) -> Tuple[bytes, str]:
        if image is None:
            raise ValueError("image is required for image-to-3D.")
        mesh, fmt = self._run(
            prompt=prompt.strip() if prompt else None,
            image=image,
            output_format=output_format,
            seed=seed,
            no_texture=no_texture,
            **kwargs,
        )
        return mesh, fmt
