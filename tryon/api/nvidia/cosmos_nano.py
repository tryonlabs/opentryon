"""
Cosmos 3 Nano certified NIM (self-hosted) — modes the hosted catalog API does not expose.

The build.nvidia.com ``cosmos3`` adapter is text-to-video and image-to-video only.
This client talks to a local Cosmos3 certified NIM (``NIM_MODEL_VARIANT=nano`` or
``nano-droid``) at ``POST /v1/infer`` with an explicit ``model_mode``.

Docs: https://github.com/NVIDIA/cosmos/blob/main/cookbooks/cosmos3/nim/api-reference.md
Env: COSMOS3_NIM_URL (default http://127.0.0.1:8010/v1/infer). Bearer token is sent
only when NVIDIA_API_KEY or NGC_API_KEY is set.
"""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

import requests

DEFAULT_NIM_URL = "http://127.0.0.1:8010/v1/infer"

MediaInput = Union[str, Path, bytes]


def _data_url(media: MediaInput, kind: str) -> str:
    if isinstance(media, str) and (
        media.startswith("http://") or media.startswith("https://") or media.startswith("data:")
    ):
        return media
    if isinstance(media, bytes):
        raw = media
        mime = "image/png" if kind == "image" else "video/mp4"
    else:
        path = Path(media)
        raw = path.read_bytes()
        suffix = path.suffix.lower().lstrip(".")
        if kind == "image":
            mime = "image/jpeg" if suffix in {"jpg", "jpeg"} else f"image/{suffix or 'png'}"
        else:
            mime = "video/mp4"
    encoded = base64.b64encode(raw).decode("ascii")
    return f"data:{mime};base64,{encoded}"


class Cosmos3NanoNimAdapter:
    """Certified NIM client for Nano text-to-image, video-to-video, and Nano-DROID policy."""

    def __init__(self, infer_url: Optional[str] = None, timeout: float = 900.0):
        self.infer_url = (infer_url or os.getenv("COSMOS3_NIM_URL") or DEFAULT_NIM_URL).rstrip("/")
        self.timeout = float(timeout)

    def _post(self, body: Dict[str, Any]) -> Dict[str, Any]:
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        key = os.getenv("NVIDIA_API_KEY") or os.getenv("NGC_API_KEY")
        if key:
            headers["Authorization"] = f"Bearer {key}"
        response = requests.post(self.infer_url, headers=headers, json=body, timeout=self.timeout)
        try:
            payload = response.json()
        except ValueError:
            payload = None
        if response.status_code >= 400:
            detail = payload if isinstance(payload, dict) else (response.text or "")[:500]
            raise RuntimeError(f"Cosmos 3 Nano NIM HTTP {response.status_code}: {detail}")
        if not isinstance(payload, dict):
            raise RuntimeError("Cosmos 3 Nano NIM returned a non-object response")
        return payload

    def generate_text_to_image(
        self,
        prompt: str,
        seed: Optional[int] = None,
        guidance_scale: Optional[float] = None,
        num_inference_steps: Optional[int] = None,
        resolution: Optional[str] = None,
    ) -> bytes:
        if not (prompt and prompt.strip()):
            raise ValueError("text-to-image requires --prompt")
        body: Dict[str, Any] = {"model_mode": "text2image", "prompt": prompt}
        if seed is not None:
            body["seed"] = seed
        if guidance_scale is not None:
            body["guidance_scale"] = guidance_scale
        if num_inference_steps is not None:
            body["num_inference_steps"] = num_inference_steps
        if resolution:
            body["resolution"] = resolution
        payload = self._post(body)
        encoded = payload.get("b64_image")
        if not isinstance(encoded, str) or not encoded:
            raise RuntimeError(f"Cosmos 3 Nano NIM text2image missing b64_image: {list(payload)}")
        return base64.b64decode(encoded)

    def generate_video_to_video(
        self,
        video: MediaInput,
        prompt: Optional[str] = None,
        seed: Optional[int] = None,
        guidance_scale: Optional[float] = None,
        num_inference_steps: Optional[int] = None,
        resolution: Optional[str] = None,
    ) -> bytes:
        if video is None or video == "":
            raise ValueError("video-to-video requires --video")
        body: Dict[str, Any] = {
            "model_mode": "video2video",
            "input_reference": _data_url(video, "video"),
        }
        if prompt:
            body["prompt"] = prompt
        if seed is not None:
            body["seed"] = seed
        if guidance_scale is not None:
            body["guidance_scale"] = guidance_scale
        if num_inference_steps is not None:
            body["num_inference_steps"] = num_inference_steps
        if resolution:
            body["resolution"] = resolution
        payload = self._post(body)
        encoded = payload.get("b64_video")
        if not isinstance(encoded, str) or not encoded:
            raise RuntimeError(f"Cosmos 3 Nano NIM video2video missing b64_video: {list(payload)}")
        return base64.b64decode(encoded)

    def get_action(
        self,
        image: MediaInput,
        prompt: str,
        observation: Union[str, Dict[str, Any]],
        action_chunk_size: int = 32,
        seed: Optional[int] = None,
    ) -> Dict[str, Any]:
        if not (prompt and prompt.strip()):
            raise ValueError("Nano-DROID policy requires --prompt")
        if image is None or image == "":
            raise ValueError("Nano-DROID policy requires --image")
        obs = _load_observation(observation)
        body: Dict[str, Any] = {
            "model_mode": "policy",
            "prompt": prompt,
            "input_reference": _data_url(image, "image"),
            "action_params": {
                "domain_name": "droid_lerobot",
                "action_chunk_size": int(action_chunk_size),
                "observation": obs,
            },
        }
        if seed is not None:
            body["seed"] = seed
        payload = self._post(body)
        action = payload.get("action")
        if not isinstance(action, dict):
            raise RuntimeError(f"Cosmos 3 Nano-DROID response missing action: {list(payload)}")
        return {"model_mode": "policy", "variant": "nano-droid", "action": action}


def _load_observation(value: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
    if isinstance(value, dict):
        obs = value
    else:
        text = value.strip()
        if os.path.isfile(text):
            text = Path(text).read_text(encoding="utf-8")
        parsed = json.loads(text)
        if not isinstance(parsed, dict):
            raise ValueError("--observation must be a JSON object")
        obs = parsed
    joints = obs.get("observation/joint_position")
    gripper = obs.get("observation/gripper_position")
    if not isinstance(joints, list) or len(joints) != 7:
        raise ValueError("observation/joint_position must be 7 numbers")
    if isinstance(gripper, bool) or not isinstance(gripper, (int, float)):
        raise ValueError("observation/gripper_position must be one number")
    return obs
