"""
Adapter for Black Forest Labs FLUX 3 Video API.

Modes: t2v, i2v (keyframes), v2v (start_video), draft_enhance (draft_cache).

Reference: https://docs.bfl.ml/flux_3/flux3_video
API: POST https://api.bfl.ai/v1/flux-3-video
Auth: BFL_API_KEY via x-key header.
"""

from __future__ import annotations

import base64
import io
import mimetypes
import os
import time
from typing import Any, List, Optional, Union

import requests
from PIL import Image


class Flux3VideoAdapter:
    BASE_URL = "https://api.bfl.ai"
    ENDPOINT = "/v1/flux-3-video"

    _IN_PROGRESS_STATUSES = frozenset(
        {
            "pending",
            "processing",
            "submitted",
            "reasoning",
            "generating",
            "request moderated",
            "content moderated",
        }
    )

    _ASPECT_RATIOS = frozenset(
        {"auto", "21:9", "2:1", "16:9", "4:3", "1:1", "3:4", "9:16", "9:21"}
    )
    _RESOLUTIONS = frozenset({"hd", "fhd", "qhd", "uhd"})

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or os.getenv("BFL_API_KEY")
        if not self.api_key:
            raise ValueError(
                "BFL API key is required. Set BFL_API_KEY environment variable "
                "or pass api_key parameter."
            )
        self.base_url = base_url or self.BASE_URL
        self.endpoint = f"{self.base_url}{self.ENDPOINT}"
        self.headers = {
            "x-key": self.api_key,
            "Content-Type": "application/json",
        }

    @staticmethod
    def _normalize_duration(duration: Any) -> Any:
        if duration is None:
            return "auto"
        if isinstance(duration, str):
            key = duration.strip().lower()
            if key == "auto":
                return "auto"
            if key.isdigit():
                return int(key)
            raise ValueError('duration must be "auto" or a whole number of seconds (5–20 for t2v/i2v)')
        if isinstance(duration, (int, float)):
            return int(duration)
        return duration

    def _prepare_image_input(self, image_input: Union[str, io.BytesIO, Image.Image]) -> str:
        if isinstance(image_input, Image.Image):
            buffer = io.BytesIO()
            image_input.save(buffer, format="PNG")
            buffer.seek(0)
            return base64.b64encode(buffer.read()).decode("utf-8")

        if hasattr(image_input, "read"):
            image_file = image_input
            image_file.seek(0)
            image_bytes = image_file.read()
            image_file.seek(0)
            return base64.b64encode(image_bytes).decode("utf-8")

        if isinstance(image_input, str):
            if image_input.startswith(("http://", "https://", "data:")):
                return image_input
            if len(image_input) > 100 and not os.path.exists(image_input):
                try:
                    base64.b64decode(image_input[:100])
                    return image_input
                except Exception:
                    pass
            with open(image_input, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode("utf-8")

        raise ValueError(
            "Invalid image input: must be a file path, URL, file-like object, "
            "PIL Image, or base64 string"
        )

    def _prepare_video_input(self, video_input: str) -> str:
        if not video_input:
            raise ValueError("video input is required")
        if video_input.startswith(("http://", "https://", "data:")):
            return video_input
        if len(video_input) > 200 and not os.path.exists(video_input):
            try:
                base64.b64decode(video_input[:100])
                return video_input
            except Exception:
                pass
        if not os.path.exists(video_input):
            raise ValueError(f"Video path does not exist: {video_input}")
        mime, _ = mimetypes.guess_type(video_input)
        if not mime:
            mime = "video/mp4"
        with open(video_input, "rb") as f:
            raw = base64.b64encode(f.read()).decode("ascii")
        return f"data:{mime};base64,{raw}"

    def _poll_task(self, task_id: str, polling_url: str, max_wait_time: int = 1800) -> dict:
        start_time = time.time()
        while True:
            elapsed_time = time.time() - start_time
            if elapsed_time > max_wait_time:
                raise ValueError(f"Task {task_id} timed out after {max_wait_time} seconds.")

            try:
                response = requests.get(
                    polling_url,
                    headers={"accept": "application/json", "x-key": self.api_key},
                    timeout=60,
                )
                if response.status_code in (502, 503):
                    time.sleep(1.5)
                    continue
                response.raise_for_status()
                task_data = response.json()
            except requests.exceptions.RequestException as e:
                raise ValueError(f"Failed to poll task status: {str(e)}")

            status_raw = task_data.get("status", "")
            status = status_raw.lower()

            if status_raw == "Ready" or status in {"completed", "succeed", "ready"}:
                return task_data

            if status_raw in {"Error", "Failed"} or status in {"failed", "fail", "error"}:
                error_msg = task_data.get("error", {})
                if isinstance(error_msg, dict):
                    error_msg = error_msg.get("message", status_raw)
                if not error_msg:
                    error_msg = task_data.get("message", str(task_data))
                raise ValueError(f"Task {task_id} failed: {error_msg}")

            if status in self._IN_PROGRESS_STATUSES:
                time.sleep(1.5)
                continue

            if status == "task not found":
                raise ValueError(f"Task {task_id} not found. It may have expired or been deleted.")

            raise ValueError(f"Unknown task status: {status_raw}. Response data: {task_data}")

    def _extract_sample(self, response_data: dict) -> str:
        result = response_data.get("result", {})
        if isinstance(result, dict) and "sample" in result:
            return result["sample"]
        if "sample" in response_data:
            return response_data["sample"]
        raise ValueError(f"No result sample in FLUX 3 Video response: {response_data}")

    def _download_sample(self, sample: str) -> bytes:
        if sample.startswith(("http://", "https://")):
            response = requests.get(sample, timeout=300)
            response.raise_for_status()
            return response.content
        return base64.b64decode(sample)

    def _submit(self, payload: dict) -> dict:
        try:
            response = requests.post(
                self.endpoint,
                headers=self.headers,
                json=payload,
                timeout=120,
            )
            response.raise_for_status()
            response_data = response.json()
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP {e.response.status_code}"
            try:
                error_data = e.response.json()
                error_msg = error_data.get("detail", str(error_data))
            except Exception:
                error_msg = e.response.text or str(e)
            raise ValueError(
                f"BFL FLUX 3 Video API HTTP error ({e.response.status_code}): {error_msg}"
            )
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Failed to connect to BFL FLUX 3 Video API: {str(e)}")

        if "polling_url" in response_data:
            task_id = response_data.get("id", "unknown")
            response_data = self._poll_task(task_id, response_data["polling_url"])
        return response_data

    def _run_and_download(self, payload: dict) -> bytes:
        response_data = self._submit(payload)
        sample = self._extract_sample(response_data)
        return self._download_sample(sample)

    def _common_video_fields(
        self,
        *,
        aspect_ratio: str,
        duration: Any,
        resolution: str,
        generate_audio: bool,
        safety_tolerance: int,
        draft: bool,
        version: str,
    ) -> dict:
        if aspect_ratio not in self._ASPECT_RATIOS:
            raise ValueError(f"aspect_ratio must be one of {sorted(self._ASPECT_RATIOS)}")
        if resolution not in self._RESOLUTIONS:
            raise ValueError(f"resolution must be one of {sorted(self._RESOLUTIONS)}")
        if safety_tolerance < 0 or safety_tolerance > 7:
            raise ValueError("safety_tolerance must be between 0 and 7")
        return {
            "aspect_ratio": aspect_ratio,
            "duration": self._normalize_duration(duration),
            "resolution": resolution,
            "generate_audio": generate_audio,
            "safety_tolerance": safety_tolerance,
            "draft": draft,
            "version": version,
        }

    def generate_text_to_video(
        self,
        prompt: str,
        aspect_ratio: str = "auto",
        duration: Any = "auto",
        resolution: str = "hd",
        generate_audio: bool = True,
        safety_tolerance: int = 2,
        draft: bool = False,
        version: str = "latest",
        video: Optional[str] = None,
        draft_cache: Optional[str] = None,
        **kwargs,
    ) -> bytes:
        if draft_cache:
            return self.enhance_draft(
                draft_cache,
                resolution=resolution if resolution != "hd" else "fhd",
                safety_tolerance=safety_tolerance,
                **kwargs,
            )
        if video:
            if not prompt:
                raise ValueError("prompt is required for video continuation (v2v)")
            payload = {
                "mode": "v2v",
                "prompt": prompt,
                "start_video": self._prepare_video_input(video),
                **self._common_video_fields(
                    aspect_ratio=aspect_ratio,
                    duration=duration,
                    resolution=resolution,
                    generate_audio=generate_audio,
                    safety_tolerance=safety_tolerance,
                    draft=draft,
                    version=version,
                ),
            }
            payload.update(kwargs)
            return self._run_and_download(payload)

        if not prompt:
            raise ValueError("prompt is required for text-to-video")
        payload = {
            "mode": "t2v",
            "prompt": prompt,
            **self._common_video_fields(
                aspect_ratio=aspect_ratio,
                duration=duration,
                resolution=resolution,
                generate_audio=generate_audio,
                safety_tolerance=safety_tolerance,
                draft=draft,
                version=version,
            ),
        }
        payload.update(kwargs)
        return self._run_and_download(payload)

    def generate_image_to_video(
        self,
        image: Union[str, io.BytesIO, Image.Image],
        prompt: str,
        end_image: Optional[Union[str, io.BytesIO, Image.Image]] = None,
        aspect_ratio: str = "auto",
        duration: Any = "auto",
        resolution: str = "hd",
        generate_audio: bool = True,
        safety_tolerance: int = 2,
        draft: bool = False,
        version: str = "latest",
        **kwargs,
    ) -> bytes:
        if not prompt:
            raise ValueError("prompt is required for image-to-video")
        start = self._prepare_image_input(image)
        if end_image is not None:
            keyframes: List[str] = [start, self._prepare_image_input(end_image)]
        else:
            keyframes = start
        payload = {
            "mode": "i2v",
            "prompt": prompt,
            "keyframes": keyframes,
            **self._common_video_fields(
                aspect_ratio=aspect_ratio,
                duration=duration,
                resolution=resolution,
                generate_audio=generate_audio,
                safety_tolerance=safety_tolerance,
                draft=draft,
                version=version,
            ),
        }
        payload.update(kwargs)
        return self._run_and_download(payload)

    def enhance_draft(
        self,
        draft_cache: str,
        resolution: str = "fhd",
        safety_tolerance: int = 2,
        **kwargs,
    ) -> bytes:
        if not draft_cache:
            raise ValueError("draft_cache is required for draft_enhance")
        if resolution not in self._RESOLUTIONS:
            raise ValueError(f"resolution must be one of {sorted(self._RESOLUTIONS)}")
        payload = {
            "mode": "draft_enhance",
            "draft_cache": draft_cache,
            "resolution": resolution,
            "safety_tolerance": safety_tolerance,
        }
        payload.update(kwargs)
        return self._run_and_download(payload)
