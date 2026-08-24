"""
Alibaba Wan video API adapter (first-party DashScope / Model Studio).

Async video-synthesis for Wan 2.x and Wan 3.0: submit with
``X-DashScope-Async: enable``, poll ``/tasks/{id}``, download ``video_url``.

Wan 3.0 (``wan3.0-video``) uses ``input.media[]`` (first/last frame, file,
link) instead of Wan 2.x ``img_url``. There are no official Wan 3.0 open
weights; local inference stays on ``--model wan-2.2``.

Docs:
  https://www.alibabacloud.com/help/en/model-studio/text-to-video-guide
  https://help.aliyun.com/en/model-studio/wan3-video-generation-api-reference
  Legacy T2V: https://www.alibabacloud.com/help/en/model-studio/legacy-wan-text-to-video-api-reference

Env:
  DASHSCOPE_API_KEY (or WAN_API_KEY)
  WAN_API_BASE_URL — default https://dashscope-intl.aliyuncs.com/api/v1
    China: https://dashscope.aliyuncs.com/api/v1
    Or a workspace URL:
      https://{WorkspaceId}.ap-southeast-1.maas.aliyuncs.com/api/v1

Examples:
    >>> from tryon.api.wan import WanVideoAdapter
    >>> adapter = WanVideoAdapter()
    >>> video = adapter.generate_text_to_video(
    ...     prompt="A fashion model walking a runway, soft light",
    ...     model="wan2.6-t2v",
    ...     duration=5,
    ...     resolution="720P",
    ... )
"""

from __future__ import annotations

import base64
import io
import os
import time
from typing import Any, Dict, List, Optional, Union

import requests
from PIL import Image

DEFAULT_BASE_URL = "https://dashscope-intl.aliyuncs.com/api/v1"

MODEL_ALIASES = {
    "wan2.6": "wan2.6-t2v",
    "wan2.6-t2v": "wan2.6-t2v",
    "wan2.7": "wan2.7-t2v",
    "wan2.7-t2v": "wan2.7-t2v",
    "wan2.2": "wan2.2-t2v-plus",
    "wan2.2-t2v-plus": "wan2.2-t2v-plus",
    "wan2.6-i2v": "wan2.6-i2v",
    "wan2.6-i2v-flash": "wan2.6-i2v-flash",
    "wan2.2-i2v-plus": "wan2.2-i2v-plus",
    "wan3": "wan3.0-video",
    "wan3.0": "wan3.0-video",
    "wan-3": "wan3.0-video",
    "wan-3.0": "wan3.0-video",
    "wan3.0-video": "wan3.0-video",
}

WAN3_MODEL_IDS = {"wan3.0-video"}


class WanVideoAdapter:
    """Alibaba Model Studio / DashScope Wan video adapter."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "wan2.6-t2v",
        poll_interval: float = 5.0,
        timeout: float = 900.0,
    ):
        self.api_key = (
            api_key
            or os.getenv("DASHSCOPE_API_KEY")
            or os.getenv("WAN_API_KEY")
        )
        if not self.api_key:
            raise ValueError(
                "DashScope / Wan API key is required. Set DASHSCOPE_API_KEY "
                "(Alibaba Cloud Model Studio)."
            )
        self.base_url = (
            base_url or os.getenv("WAN_API_BASE_URL") or DEFAULT_BASE_URL
        ).rstrip("/")
        self.model = self._resolve_model(model)
        self.poll_interval = float(poll_interval)
        self.timeout = float(timeout)

    @staticmethod
    def _resolve_model(model: str) -> str:
        key = (model or "").strip()
        return MODEL_ALIASES.get(key, key)

    @classmethod
    def _is_wan3_model(cls, model: str) -> bool:
        resolved = cls._resolve_model(model)
        return resolved in WAN3_MODEL_IDS or resolved.startswith("wan3")

    def _headers(self, async_enable: bool = False) -> Dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if async_enable:
            headers["X-DashScope-Async"] = "enable"
        return headers

    def _prepare_image_uri(
        self, image: Union[str, io.BytesIO, Image.Image, bytes]
    ) -> str:
        if isinstance(image, str):
            if image.startswith(("http://", "https://", "data:", "oss://")):
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
        raise ValueError("Unsupported image input for Wan.")

    @staticmethod
    def _prepare_remote_url(value: str, kind: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Wan 3.0 {kind} must be a public HTTP(S) or OSS URL.")
        url = value.strip()
        if url.startswith(("http://", "https://", "oss://")):
            return url
        raise ValueError(
            f"Wan 3.0 {kind} must be a public HTTP(S) or OSS URL, not a local path."
        )

    def _wan3_parameters(
        self,
        *,
        duration: int,
        resolution: str,
        ratio: Optional[str],
        prompt_extend: bool,
        watermark: bool,
        audio: bool,
        seed: Optional[int],
    ) -> Dict[str, Any]:
        parameters: Dict[str, Any] = {
            "duration": int(duration),
            "resolution": resolution,
            "ratio": ratio or "adaptive",
            "prompt_extend": bool(prompt_extend),
            "watermark": bool(watermark),
            "audio": bool(audio),
        }
        if seed is not None:
            parameters["seed"] = int(seed)
        return parameters

    def _generate_wan3(
        self,
        *,
        prompt: Optional[str],
        model: str,
        image: Optional[Union[str, io.BytesIO, Image.Image, bytes]] = None,
        last_frame: Optional[Union[str, io.BytesIO, Image.Image, bytes]] = None,
        file: Optional[str] = None,
        link: Optional[str] = None,
        media: Optional[List[Dict[str, Any]]] = None,
        duration: int = 5,
        resolution: str = "720P",
        ratio: Optional[str] = None,
        prompt_extend: bool = True,
        watermark: bool = False,
        audio: bool = True,
        seed: Optional[int] = None,
    ) -> bytes:
        if media is not None:
            media_items = list(media)
        else:
            media_items = []
            if image is not None:
                media_items.append(
                    {"type": "first_frame", "url": self._prepare_image_uri(image)}
                )
            if last_frame is not None:
                if image is None:
                    raise ValueError(
                        "Wan 3.0 last_frame requires a first-frame image "
                        "(CLI: --image plus --last-frame)."
                    )
                media_items.append(
                    {"type": "last_frame", "url": self._prepare_image_uri(last_frame)}
                )
            if file and link:
                raise ValueError("Wan 3.0 file and link are mutually exclusive.")
            if (file or link) and (image is not None or last_frame is not None):
                raise ValueError(
                    "Wan 3.0 file/link cannot be combined with first_frame/last_frame."
                )
            if file:
                media_items.append(
                    {"type": "file", "url": self._prepare_remote_url(file, "file")}
                )
            if link:
                media_items.append(
                    {"type": "link", "url": self._prepare_remote_url(link, "link")}
                )

        if not (prompt or "").strip() and not media_items:
            raise ValueError("Wan 3.0 requires a prompt and/or media input.")

        input_obj: Dict[str, Any] = {}
        if prompt and prompt.strip():
            input_obj["prompt"] = prompt.strip()
        if media_items:
            input_obj["media"] = media_items

        payload: Dict[str, Any] = {
            "model": model,
            "input": input_obj,
            "parameters": self._wan3_parameters(
                duration=duration,
                resolution=resolution,
                ratio=ratio,
                prompt_extend=prompt_extend,
                watermark=watermark,
                audio=audio,
                seed=seed,
            ),
        }
        task_id = self._submit(payload)
        return self._download(self._poll(task_id))

    def _submit(self, payload: Dict[str, Any]) -> str:
        url = f"{self.base_url}/services/aigc/video-generation/video-synthesis"
        resp = requests.post(
            url, headers=self._headers(async_enable=True), json=payload, timeout=60
        )
        if resp.status_code >= 400:
            raise RuntimeError(
                f"Wan create failed ({resp.status_code}): {resp.text}"
            )
        data = resp.json()
        # Async create usually returns {output: {task_id}, request_id}
        output = data.get("output") or data
        task_id = output.get("task_id") or data.get("task_id")
        if not task_id:
            code = data.get("code")
            message = data.get("message")
            raise RuntimeError(
                f"Wan create missing task_id: code={code} message={message} body={data}"
            )
        return task_id

    def _poll(self, task_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/tasks/{task_id}"
        deadline = time.time() + self.timeout
        while time.time() < deadline:
            resp = requests.get(url, headers=self._headers(), timeout=60)
            if resp.status_code >= 400:
                raise RuntimeError(
                    f"Wan poll failed ({resp.status_code}): {resp.text}"
                )
            data = resp.json()
            output = data.get("output") or data
            status = (
                output.get("task_status")
                or output.get("status")
                or data.get("task_status")
                or ""
            ).upper()
            if status in {"SUCCEEDED", "SUCCESS"}:
                return output
            if status in {"FAILED", "CANCELED", "CANCELLED", "UNKNOWN"}:
                raise RuntimeError(
                    f"Wan task failed: {output.get('message') or output or data}"
                )
            time.sleep(self.poll_interval)
        raise TimeoutError(f"Wan task {task_id} timed out after {self.timeout}s")

    def _download(self, output: Dict[str, Any]) -> bytes:
        video_url = output.get("video_url")
        if not video_url:
            results = output.get("results")
            if isinstance(results, list) and results:
                first = results[0] or {}
                video_url = first.get("url") or first.get("video_url")
            elif isinstance(results, dict):
                video_url = results.get("video_url") or results.get("url")
        if not video_url:
            raise RuntimeError(f"Wan success response missing video_url: {output}")
        resp = requests.get(video_url, stream=True, timeout=180)
        if resp.status_code != 200:
            raise RuntimeError(f"Failed to download Wan video ({resp.status_code})")
        return resp.content

    def generate_text_to_video(
        self,
        prompt: str,
        model: Optional[str] = None,
        duration: int = 5,
        resolution: str = "720P",
        size: Optional[str] = None,
        ratio: Optional[str] = None,
        prompt_extend: bool = True,
        watermark: bool = False,
        negative_prompt: Optional[str] = None,
        last_frame: Optional[Union[str, io.BytesIO, Image.Image, bytes]] = None,
        file: Optional[str] = None,
        link: Optional[str] = None,
        media: Optional[List[Dict[str, Any]]] = None,
        audio: bool = True,
        seed: Optional[int] = None,
    ) -> bytes:
        resolved = self._resolve_model(model) if model else self.model
        if self._is_wan3_model(resolved):
            return self._generate_wan3(
                prompt=prompt,
                model=resolved,
                last_frame=last_frame,
                file=file,
                link=link,
                media=media,
                duration=duration,
                resolution=resolution,
                ratio=ratio,
                prompt_extend=prompt_extend,
                watermark=watermark,
                audio=audio,
                seed=seed,
            )
        if not prompt:
            raise ValueError("prompt is required.")
        payload: Dict[str, Any] = {
            "model": resolved,
            "input": {"prompt": prompt},
            "parameters": {
                "duration": int(duration),
                "prompt_extend": bool(prompt_extend),
                "watermark": bool(watermark),
            },
        }
        if negative_prompt:
            payload["input"]["negative_prompt"] = negative_prompt
        # Newer models prefer resolution+ratio; older prefer size WxH.
        if size:
            payload["parameters"]["size"] = size
        else:
            payload["parameters"]["resolution"] = resolution
            if ratio:
                payload["parameters"]["ratio"] = ratio
        task_id = self._submit(payload)
        return self._download(self._poll(task_id))

    def generate_image_to_video(
        self,
        image: Union[str, io.BytesIO, Image.Image, bytes],
        prompt: Optional[str] = None,
        model: Optional[str] = None,
        duration: int = 5,
        resolution: str = "720P",
        size: Optional[str] = None,
        ratio: Optional[str] = None,
        prompt_extend: bool = True,
        watermark: bool = False,
        negative_prompt: Optional[str] = None,
        last_frame: Optional[Union[str, io.BytesIO, Image.Image, bytes]] = None,
        file: Optional[str] = None,
        link: Optional[str] = None,
        media: Optional[List[Dict[str, Any]]] = None,
        audio: bool = True,
        seed: Optional[int] = None,
    ) -> bytes:
        resolved = self._resolve_model(model) if model else self.model
        if self._is_wan3_model(resolved):
            return self._generate_wan3(
                prompt=prompt,
                model=resolved,
                image=image,
                last_frame=last_frame,
                file=file,
                link=link,
                media=media,
                duration=duration,
                resolution=resolution,
                ratio=ratio,
                prompt_extend=prompt_extend,
                watermark=watermark,
                audio=audio,
                seed=seed,
            )
        # Prefer an i2v model id when caller left the default t2v id.
        if resolved.endswith("-t2v") or resolved.endswith("-t2v-plus"):
            resolved = resolved.replace("-t2v-plus", "-i2v-plus").replace("-t2v", "-i2v")
        img_uri = self._prepare_image_uri(image)
        input_obj: Dict[str, Any] = {"img_url": img_uri}
        if prompt:
            input_obj["prompt"] = prompt
        if negative_prompt:
            input_obj["negative_prompt"] = negative_prompt
        payload: Dict[str, Any] = {
            "model": resolved,
            "input": input_obj,
            "parameters": {
                "duration": int(duration),
                "prompt_extend": bool(prompt_extend),
                "watermark": bool(watermark),
            },
        }
        if size:
            payload["parameters"]["size"] = size
        else:
            payload["parameters"]["resolution"] = resolution
        task_id = self._submit(payload)
        return self._download(self._poll(task_id))
