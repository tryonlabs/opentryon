"""
MiniMax Hailuo video API adapter (first-party).

Supports MiniMax-Hailuo-2.3 / 2.3-Fast text-to-video and image-to-video via
the official MiniMax Open Platform (async create → poll → file retrieve).

Docs:
  https://platform.minimax.io/docs/api-reference/video-generation-t2v
  https://platform.minimax.io/docs/api-reference/video-generation-i2v
  https://platform.minimax.io/docs/api-reference/video-generation-query

Env:
  MINIMAX_API_KEY
  MINIMAX_API_BASE_URL (default https://api.minimax.io)

Examples:
    >>> from tryon.api.minimax import HailuoVideoAdapter
    >>> adapter = HailuoVideoAdapter()
    >>> video = adapter.generate_text_to_video(
    ...     prompt="A fashion model walking a runway [Tracking shot]",
    ...     duration=6,
    ...     resolution="1080P",
    ... )
"""

from __future__ import annotations

import base64
import io
import os
import time
from typing import Any, Dict, Optional, Union

import requests
from PIL import Image

DEFAULT_BASE_URL = "https://api.minimax.io"

MODEL_ALIASES = {
    "hailuo-2.3": "MiniMax-Hailuo-2.3",
    "hailuo-2.3-fast": "MiniMax-Hailuo-2.3-Fast",
    "MiniMax-Hailuo-2.3": "MiniMax-Hailuo-2.3",
    "MiniMax-Hailuo-2.3-Fast": "MiniMax-Hailuo-2.3-Fast",
    "MiniMax-Hailuo-02": "MiniMax-Hailuo-02",
}


class HailuoVideoAdapter:
    """Official MiniMax Hailuo video adapter (T2V / I2V)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "MiniMax-Hailuo-2.3",
        poll_interval: float = 5.0,
        timeout: float = 900.0,
    ):
        self.api_key = api_key or os.getenv("MINIMAX_API_KEY")
        if not self.api_key:
            raise ValueError(
                "MiniMax API key is required. Set MINIMAX_API_KEY "
                "(https://platform.minimax.io/user-center/basic-information/interface-key)."
            )
        self.base_url = (
            base_url or os.getenv("MINIMAX_API_BASE_URL") or DEFAULT_BASE_URL
        ).rstrip("/")
        self.model = self._resolve_model(model)
        self.poll_interval = float(poll_interval)
        self.timeout = float(timeout)

    @staticmethod
    def _resolve_model(model: str) -> str:
        key = (model or "").strip()
        return MODEL_ALIASES.get(key, key)

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _prepare_image_uri(
        self, image: Union[str, io.BytesIO, Image.Image, bytes]
    ) -> str:
        if isinstance(image, str):
            if image.startswith(("http://", "https://", "data:")):
                return image
            if os.path.exists(image):
                with open(image, "rb") as f:
                    raw = f.read()
                b64 = base64.b64encode(raw).decode("ascii")
                ext = os.path.splitext(image)[1].lower()
                mime = {
                    ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg",
                    ".png": "image/png",
                    ".webp": "image/webp",
                }.get(ext, "image/jpeg")
                return f"data:{mime};base64,{b64}"
            raise ValueError(f"Image path does not exist: {image}")
        if isinstance(image, Image.Image):
            buf = io.BytesIO()
            image.convert("RGB").save(buf, format="JPEG", quality=95)
            b64 = base64.b64encode(buf.getvalue()).decode("ascii")
            return f"data:image/jpeg;base64,{b64}"
        if isinstance(image, (bytes, bytearray)):
            b64 = base64.b64encode(bytes(image)).decode("ascii")
            return f"data:image/jpeg;base64,{b64}"
        if hasattr(image, "read"):
            image.seek(0)
            b64 = base64.b64encode(image.read()).decode("ascii")
            return f"data:image/jpeg;base64,{b64}"
        raise ValueError("Unsupported image input for Hailuo.")

    def _check_base_resp(self, data: Dict[str, Any], context: str) -> None:
        base = data.get("base_resp") or {}
        code = base.get("status_code", 0)
        if code not in (0, None):
            raise RuntimeError(
                f"MiniMax {context} failed ({code}): {base.get('status_msg') or data}"
            )

    def _create_task(self, payload: Dict[str, Any]) -> str:
        url = f"{self.base_url}/v1/video_generation"
        resp = requests.post(url, headers=self._headers(), json=payload, timeout=60)
        if resp.status_code >= 400:
            raise RuntimeError(
                f"MiniMax create failed ({resp.status_code}): {resp.text}"
            )
        data = resp.json()
        self._check_base_resp(data, "create")
        task_id = data.get("task_id")
        if not task_id:
            raise RuntimeError(f"MiniMax create missing task_id: {data}")
        return str(task_id)

    def _poll(self, task_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/v1/query/video_generation"
        deadline = time.time() + self.timeout
        while time.time() < deadline:
            resp = requests.get(
                url,
                headers=self._headers(),
                params={"task_id": task_id},
                timeout=60,
            )
            if resp.status_code >= 400:
                raise RuntimeError(
                    f"MiniMax poll failed ({resp.status_code}): {resp.text}"
                )
            data = resp.json()
            self._check_base_resp(data, "poll")
            status = (data.get("status") or "").lower()
            if status == "success":
                return data
            if status == "fail":
                raise RuntimeError(f"MiniMax task failed: {data}")
            time.sleep(self.poll_interval)
        raise TimeoutError(f"MiniMax task {task_id} timed out after {self.timeout}s")

    def _download_file(self, file_id: Union[str, int]) -> bytes:
        url = f"{self.base_url}/v1/files/retrieve"
        resp = requests.get(
            url,
            headers=self._headers(),
            params={"file_id": file_id},
            timeout=60,
        )
        if resp.status_code >= 400:
            raise RuntimeError(
                f"MiniMax file retrieve failed ({resp.status_code}): {resp.text}"
            )
        data = resp.json()
        self._check_base_resp(data, "file retrieve")
        file_obj = data.get("file") or {}
        download_url = file_obj.get("download_url")
        if not download_url:
            raise RuntimeError(f"MiniMax file missing download_url: {data}")
        if not download_url.startswith("http"):
            download_url = f"https://{download_url}"
        video_resp = requests.get(download_url, stream=True, timeout=180)
        if video_resp.status_code != 200:
            raise RuntimeError(
                f"Failed to download Hailuo video ({video_resp.status_code})"
            )
        return video_resp.content

    def _run(self, payload: Dict[str, Any]) -> bytes:
        task_id = self._create_task(payload)
        result = self._poll(task_id)
        file_id = result.get("file_id")
        if not file_id:
            raise RuntimeError(f"MiniMax success response missing file_id: {result}")
        return self._download_file(file_id)

    def generate_text_to_video(
        self,
        prompt: str,
        model: Optional[str] = None,
        duration: int = 6,
        resolution: str = "768P",
        prompt_optimizer: bool = True,
        fast_pretreatment: bool = False,
    ) -> bytes:
        if not prompt:
            raise ValueError("prompt is required.")
        payload: Dict[str, Any] = {
            "model": self._resolve_model(model) if model else self.model,
            "prompt": prompt,
            "duration": int(duration),
            "resolution": resolution,
            "prompt_optimizer": bool(prompt_optimizer),
            "fast_pretreatment": bool(fast_pretreatment),
        }
        return self._run(payload)

    def generate_image_to_video(
        self,
        image: Union[str, io.BytesIO, Image.Image, bytes],
        prompt: Optional[str] = None,
        model: Optional[str] = None,
        duration: int = 6,
        resolution: str = "768P",
        prompt_optimizer: bool = True,
        fast_pretreatment: bool = False,
    ) -> bytes:
        payload: Dict[str, Any] = {
            "model": self._resolve_model(model) if model else self.model,
            "first_frame_image": self._prepare_image_uri(image),
            "duration": int(duration),
            "resolution": resolution,
            "prompt_optimizer": bool(prompt_optimizer),
            "fast_pretreatment": bool(fast_pretreatment),
        }
        if prompt:
            payload["prompt"] = prompt
        return self._run(payload)
