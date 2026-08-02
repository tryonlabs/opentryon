"""
Kling AI video generation adapter (official Open Platform).

Supports:
  - Kling 3.0          (kling-v3)         — T2V / I2V, multi-shot, audio
  - Kling 3.0 Omni     (kling-v3-omni)    — unified multimodal / omni-video
  - Kling 2.5 Turbo    (kling-v2-5-turbo) — fast T2V / I2V

Auth: JWT (HS256) via Access Key + Secret Key — same credentials as VTON.
Docs: https://kling.ai/document-api/guides/get-started/overview

Env:
  KLING_AI_API_KEY / KLING_AI_SECRET_KEY
  KLING_AI_BASE_URL (default https://api-singapore.klingai.com)
"""

from __future__ import annotations

import base64
import io
import os
import time
from typing import Any, Dict, Optional, Union

import requests
from PIL import Image

from tryon.api.kling_ai import generate_api_token

DEFAULT_BASE_URL = "https://api-singapore.klingai.com"

KLING_VIDEO_MODELS = {
    "kling-v3": "kling-v3",
    "kling-3.0": "kling-v3",
    "kling-v3-omni": "kling-v3-omni",
    "kling-3.0-omni": "kling-v3-omni",
    "kling-v2-5-turbo": "kling-v2-5-turbo",
    "kling-2.5-turbo": "kling-v2-5-turbo",
}

T2V_MODELS = {"kling-v3", "kling-v2-5-turbo"}
OMNI_MODELS = {"kling-v3-omni"}


class KlingVideoAdapter:
    """Official Kling Open Platform video adapter."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "kling-v3",
        poll_interval: float = 3.0,
        timeout: float = 900.0,
    ):
        self.api_key = api_key or os.getenv("KLING_AI_API_KEY")
        self.secret_key = secret_key or os.getenv("KLING_AI_SECRET_KEY")
        if not self.api_key or not self.secret_key:
            raise ValueError(
                "Kling AI API key and secret key are required. "
                "Set KLING_AI_API_KEY and KLING_AI_SECRET_KEY."
            )
        self.base_url = (
            base_url or os.getenv("KLING_AI_BASE_URL") or DEFAULT_BASE_URL
        ).rstrip("/")
        self.model = self._resolve_model(model)
        self.poll_interval = poll_interval
        self.timeout = timeout

    @staticmethod
    def _resolve_model(model: str) -> str:
        key = model.strip()
        return KLING_VIDEO_MODELS.get(key, key)

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {generate_api_token(self.api_key, self.secret_key)}",
            "Content-Type": "application/json",
        }

    def _prepare_image(self, image: Union[str, io.BytesIO, Image.Image, bytes]) -> str:
        if isinstance(image, str):
            if image.startswith(("http://", "https://")):
                return image
            if image.startswith("data:"):
                # strip data URI prefix if present for Kling base64 fields
                if "," in image:
                    return image.split(",", 1)[1]
                return image
            if os.path.exists(image):
                with open(image, "rb") as f:
                    return base64.b64encode(f.read()).decode("ascii")
            raise ValueError(f"Image path does not exist: {image}")
        if isinstance(image, Image.Image):
            buf = io.BytesIO()
            image.save(buf, format="PNG")
            return base64.b64encode(buf.getvalue()).decode("ascii")
        if isinstance(image, (bytes, bytearray)):
            return base64.b64encode(bytes(image)).decode("ascii")
        if hasattr(image, "read"):
            image.seek(0)
            return base64.b64encode(image.read()).decode("ascii")
        raise ValueError("Unsupported image input for Kling video.")

    def _post(self, path: str, payload: Dict[str, Any]) -> str:
        url = f"{self.base_url}{path}"
        resp = requests.post(url, headers=self._headers(), json=payload, timeout=60)
        if resp.status_code >= 400:
            raise RuntimeError(f"Kling video create failed ({resp.status_code}): {resp.text}")
        data = resp.json()
        if data.get("code") not in (0, None, "0"):
            # Some responses use code=0 for success; others omit it.
            if data.get("code") not in (0, "0") and "data" not in data:
                raise RuntimeError(f"Kling video create error: {data}")
        task = data.get("data") or data
        task_id = task.get("task_id") or task.get("id")
        if not task_id:
            raise RuntimeError(f"Kling video create missing task_id: {data}")
        return task_id

    def _poll(self, kind: str, task_id: str) -> Dict[str, Any]:
        path = f"/v1/videos/{kind}/{task_id}"
        url = f"{self.base_url}{path}"
        deadline = time.time() + self.timeout
        while time.time() < deadline:
            resp = requests.get(url, headers=self._headers(), timeout=60)
            if resp.status_code >= 400:
                raise RuntimeError(f"Kling poll failed ({resp.status_code}): {resp.text}")
            data = resp.json()
            body = data.get("data") or data
            status = (body.get("task_status") or body.get("status") or "").lower()
            if status in {"succeed", "succeeded", "success", "completed"}:
                return body
            if status in {"failed", "error"}:
                raise RuntimeError(
                    f"Kling task failed: {body.get('task_status_msg') or body}"
                )
            time.sleep(self.poll_interval)
        raise TimeoutError(f"Kling task {task_id} timed out after {self.timeout}s")

    def _extract_video_bytes(self, body: Dict[str, Any]) -> bytes:
        result = body.get("task_result") or body.get("result") or {}
        videos = result.get("videos") or []
        if not videos:
            # Some shapes nest differently
            if result.get("url"):
                videos = [result]
            else:
                raise RuntimeError(f"Kling response missing videos: {body}")
        video_url = videos[0].get("url") or videos[0].get("video_url")
        if not video_url:
            raise RuntimeError(f"Kling video entry missing url: {videos[0]}")
        resp = requests.get(video_url, stream=True, timeout=120)
        if resp.status_code != 200:
            raise RuntimeError(f"Failed to download Kling video ({resp.status_code})")
        return resp.content

    def generate_text_to_video(
        self,
        prompt: str,
        model: Optional[str] = None,
        duration: Union[str, int] = "5",
        mode: str = "pro",
        aspect_ratio: str = "16:9",
        negative_prompt: Optional[str] = None,
        sound: str = "off",
        cfg_scale: Optional[float] = None,
    ) -> bytes:
        if not prompt:
            raise ValueError("prompt is required.")
        resolved = self._resolve_model(model) if model else self.model
        payload: Dict[str, Any] = {
            "model_name": resolved,
            "prompt": prompt,
            "duration": str(duration),
            "mode": mode,
            "aspect_ratio": aspect_ratio,
            "sound": sound,
        }
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt
        if cfg_scale is not None:
            payload["cfg_scale"] = float(cfg_scale)

        if resolved in OMNI_MODELS:
            task_id = self._post("/v1/videos/omni-video", payload)
            body = self._poll("omni-video", task_id)
        else:
            task_id = self._post("/v1/videos/text2video", payload)
            body = self._poll("text2video", task_id)
        return self._extract_video_bytes(body)

    def generate_image_to_video(
        self,
        image: Union[str, io.BytesIO, Image.Image, bytes],
        prompt: Optional[str] = None,
        model: Optional[str] = None,
        duration: Union[str, int] = "5",
        mode: str = "pro",
        aspect_ratio: str = "16:9",
        negative_prompt: Optional[str] = None,
        sound: str = "off",
        end_image: Optional[Union[str, io.BytesIO, Image.Image, bytes]] = None,
        cfg_scale: Optional[float] = None,
    ) -> bytes:
        resolved = self._resolve_model(model) if model else self.model
        image_payload = self._prepare_image(image)

        if resolved in OMNI_MODELS:
            payload: Dict[str, Any] = {
                "model_name": resolved,
                "prompt": prompt or "",
                "duration": str(duration),
                "mode": mode,
                "aspect_ratio": aspect_ratio,
                "sound": sound,
                "image_list": [{"image": image_payload}],
            }
            if end_image is not None:
                payload["image_list"].append({
                    "image": self._prepare_image(end_image),
                    "type": "end",
                })
            if negative_prompt:
                payload["negative_prompt"] = negative_prompt
            task_id = self._post("/v1/videos/omni-video", payload)
            body = self._poll("omni-video", task_id)
            return self._extract_video_bytes(body)

        payload = {
            "model_name": resolved,
            "image": image_payload,
            "prompt": prompt or "",
            "duration": str(duration),
            "mode": mode,
            "aspect_ratio": aspect_ratio,
            "sound": sound,
        }
        if end_image is not None:
            payload["image_tail"] = self._prepare_image(end_image)
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt
        if cfg_scale is not None:
            payload["cfg_scale"] = float(cfg_scale)
        task_id = self._post("/v1/videos/image2video", payload)
        body = self._poll("image2video", task_id)
        return self._extract_video_bytes(body)


