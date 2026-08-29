"""
NVIDIA Cosmos 3 Generator (Path A) — text-to-video and image-to-video.

The Generator NIM contract is ``POST /v1/infer`` with JSON
``{prompt, image?, seed, resolution, num_output_frames, fps, steps,
guidance_scale, negative_prompt}`` and a ``b64_video`` MP4 in the response.

Hosted preview (build.nvidia.com) and a self-hosted NIM share that body.
Default infer URL is the NVIDIA genai catalog; override with
``COSMOS3_INFER_URL`` for a local container (``http://127.0.0.1:8000/v1/infer``).

Docs:
  https://docs.nvidia.com/nim/cosmos/latest/api-reference.html
  https://build.nvidia.com/nvidia/cosmos3-nano/modelcard

Env:
  NVIDIA_API_KEY
  COSMOS3_INFER_URL (optional)

Examples:
    >>> from tryon.api.nvidia import Cosmos3VideoAdapter
    >>> adapter = Cosmos3VideoAdapter()
    >>> mp4 = adapter.generate_text_to_video("A model walks a concrete runway.")
"""

from __future__ import annotations

import base64
import io
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional, Union

import requests
from PIL import Image

from .adapter import _load_bytes, _resolve_nvidia_key

DEFAULT_INFER_URL = "https://ai.api.nvidia.com/v1/genai/nvidia/cosmos3-nano"
NVCF_STATUS_URL = "https://api.nvcf.nvidia.com/v2/nvcf/pexec/status/{req_id}"

COSMOS3_RESOLUTIONS = [
    "256",
    "480",
    "720",
    "256_16_9",
    "480_16_9",
    "720_16_9",
    "256_1_1",
    "480_1_1",
    "720_1_1",
    "256_9_16",
    "480_9_16",
    "720_9_16",
    "256_4_3",
    "480_4_3",
    "720_4_3",
    "256_3_4",
    "480_3_4",
    "720_3_4",
]

ImageInput = Union[str, Path, io.BytesIO, bytes, Image.Image]


class Cosmos3VideoAdapter:
    """Cosmos 3 Generator nano — T2V / I2V via NIM ``POST /v1/infer``."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        infer_url: Optional[str] = None,
        poll_interval: float = 5.0,
        timeout: float = 900.0,
    ):
        self.api_key = _resolve_nvidia_key(api_key)
        self.infer_url = (
            infer_url
            or os.getenv("COSMOS3_INFER_URL")
            or DEFAULT_INFER_URL
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
        if isinstance(image, (str, Path)):
            source = str(image)
            if source.startswith("http://") or source.startswith("https://") or source.startswith("data:"):
                return source
        data, ext = _load_bytes(image, default_ext="png")
        mime = "jpeg" if ext in {"jpg", "jpeg"} else ext
        return f"data:image/{mime};base64,{base64.b64encode(data).decode('utf-8')}"

    def _raise_http(self, resp: requests.Response) -> None:
        try:
            payload = resp.json()
        except ValueError:
            payload = None
        if isinstance(payload, dict):
            detail = payload.get("detail") or payload.get("error") or payload.get("title")
            if detail:
                raise RuntimeError(f"Cosmos 3 Generator HTTP {resp.status_code}: {detail}")
        snippet = (resp.text or "")[:500]
        raise RuntimeError(f"Cosmos 3 Generator HTTP {resp.status_code}: {snippet}")

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
            f"Cosmos 3 Generator timed out after {self.timeout:.0f}s (NVCF-REQID={req_id})."
        )

    def _post_infer(self, body: Dict[str, Any]) -> Dict[str, Any]:
        resp = requests.post(
            self.infer_url,
            json=body,
            headers=self._headers(),
            timeout=max(self.timeout, 60.0),
        )
        if resp.status_code == 202:
            resp = self._poll_nvcf(resp)
        if resp.status_code >= 400:
            self._raise_http(resp)
        try:
            data = resp.json()
        except ValueError as exc:
            raise RuntimeError("Cosmos 3 Generator returned non-JSON.") from exc
        if isinstance(data, dict) and data.get("error"):
            raise RuntimeError(f"Cosmos 3 Generator error: {data['error']}")
        return data if isinstance(data, dict) else {"raw": data}

    def _decode_video(self, data: Dict[str, Any]) -> bytes:
        b64 = data.get("b64_video") or data.get("video") or data.get("output")
        if not b64 or not isinstance(b64, str):
            raise RuntimeError(
                f"Cosmos 3 Generator response missing b64_video: {list(data.keys())}"
            )
        if b64.startswith("data:"):
            b64 = b64.split(",", 1)[-1]
        try:
            return base64.b64decode(b64)
        except Exception as exc:
            raise RuntimeError("Cosmos 3 Generator returned invalid base64 video.") from exc

    def _infer(
        self,
        prompt: str,
        image: Optional[ImageInput] = None,
        seed: Optional[int] = None,
        resolution: str = "720",
        num_output_frames: int = 121,
        fps: float = 24.0,
        steps: int = 35,
        guidance_scale: float = 6.0,
        negative_prompt: Optional[str] = None,
    ) -> bytes:
        if not (prompt or "").strip() and image is None:
            raise ValueError("Provide a prompt (T2V) or an image (I2V).")
        body: Dict[str, Any] = {
            "prompt": prompt or "",
            "resolution": resolution,
            "num_output_frames": int(num_output_frames),
            "fps": float(fps),
            "steps": int(steps),
            "guidance_scale": float(guidance_scale),
        }
        if seed is not None:
            body["seed"] = int(seed)
        if negative_prompt:
            body["negative_prompt"] = negative_prompt
        if image is not None:
            body["image"] = self._image_payload(image)
        return self._decode_video(self._post_infer(body))

    def generate_text_to_video(
        self,
        prompt: str,
        seed: Optional[int] = None,
        resolution: str = "720",
        num_output_frames: int = 121,
        fps: float = 24.0,
        steps: int = 35,
        guidance_scale: float = 6.0,
        negative_prompt: Optional[str] = None,
    ) -> bytes:
        if not (prompt or "").strip():
            raise ValueError("prompt is required for text-to-video.")
        return self._infer(
            prompt=prompt,
            image=None,
            seed=seed,
            resolution=resolution,
            num_output_frames=num_output_frames,
            fps=fps,
            steps=steps,
            guidance_scale=guidance_scale,
            negative_prompt=negative_prompt,
        )

    def generate_image_to_video(
        self,
        image: ImageInput,
        prompt: str = "",
        seed: Optional[int] = None,
        resolution: str = "720",
        num_output_frames: int = 121,
        fps: float = 24.0,
        steps: int = 35,
        guidance_scale: float = 6.0,
        negative_prompt: Optional[str] = None,
    ) -> bytes:
        if image is None:
            raise ValueError("image is required for image-to-video.")
        return self._infer(
            prompt=prompt or "",
            image=image,
            seed=seed,
            resolution=resolution,
            num_output_frames=num_output_frames,
            fps=fps,
            steps=steps,
            guidance_scale=guidance_scale,
            negative_prompt=negative_prompt,
        )
