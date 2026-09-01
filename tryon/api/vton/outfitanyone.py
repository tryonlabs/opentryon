"""Alibaba OutfitAnyone-Plus (``aitryon-plus``) virtual try-on.

First-party DashScope / Model Studio dedicated try-on. This is **not**
Qwen-Image composition I2I (``--model qwen-image``).

Official docs:
    https://www.alibabacloud.com/help/en/model-studio/aitryon-plus-api

The published API is **China (Beijing) only**. Use a Beijing-region
DashScope key. Async: ``POST .../image-synthesis`` with
``X-DashScope-Async: enable``, then poll ``GET /tasks/{task_id}``.

Images must be public HTTP(S) URLs. Local files, PIL images, and raw
bytes are uploaded to DashScope temporary OSS (48h) and passed as
``oss://`` URLs with ``X-DashScope-OssResourceResolve: enable``.

Env:
    DASHSCOPE_API_KEY (required)
    OUTFITANYONE_BASE_URL / AITRYON_PLUS_BASE_URL — default
      https://dashscope.aliyuncs.com/api/v1
      Workspace: https://{WorkspaceId}.cn-beijing.maas.aliyuncs.com/api/v1

Example:
    >>> from tryon.api.vton.outfitanyone import OutfitAnyonePlusAdapter
    >>> adapter = OutfitAnyonePlusAdapter()
    >>> images = adapter.generate_and_decode(
    ...     person="https://example.com/person.png",
    ...     garment="https://example.com/top.jpeg",
    ... )
    >>> images[0].save("worn.png")
"""

from __future__ import annotations

import io
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import requests
from PIL import Image as PILImage

ImageInput = Union[str, Path, io.BytesIO, bytes, PILImage.Image]

DEFAULT_MODEL = "aitryon-plus"
DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/api/v1"
DEFAULT_UPLOAD_BASE = "https://dashscope.aliyuncs.com/api/v1"
SYNTHESIS_PATH = "/services/aigc/image2image/image-synthesis"
MIN_IMAGE_BYTES = 5 * 1024
MAX_IMAGE_BYTES = 5 * 1024 * 1024
VALID_RESOLUTIONS = {-1, 1024, 1280}
TERMINAL_OK = {"SUCCEEDED", "SUCCESS"}
TERMINAL_FAIL = {"FAILED", "CANCELED", "CANCELLED", "UNKNOWN"}


class OutfitAnyonePlusAdapter:
    """DashScope OutfitAnyone-Plus adapter (``aitryon-plus``)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        poll_interval: float = 3.0,
        timeout: float = 300.0,
    ):
        """
        Args:
            api_key: DashScope / Model Studio key. Defaults to
                ``DASHSCOPE_API_KEY``.
            base_url: DashScope ``/api/v1`` host. Defaults to
                ``OUTFITANYONE_BASE_URL`` / ``AITRYON_PLUS_BASE_URL``,
                then the China Beijing endpoint.
            model: Upstream model id. Defaults to ``aitryon-plus``.
            poll_interval: Seconds between task polls.
            timeout: Max seconds to wait for a task.
        """
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "DashScope API key is required for OutfitAnyone-Plus. "
                "Set DASHSCOPE_API_KEY (China / Beijing Model Studio key). "
                "This is not Qwen-Image composition — see "
                "https://www.alibabacloud.com/help/en/model-studio/aitryon-plus-api"
            )
        self.base_url = (
            base_url
            or os.getenv("OUTFITANYONE_BASE_URL")
            or os.getenv("AITRYON_PLUS_BASE_URL")
            or DEFAULT_BASE_URL
        ).rstrip("/")
        self.upload_base = (
            os.getenv("DASHSCOPE_UPLOAD_URL") or DEFAULT_UPLOAD_BASE
        ).rstrip("/")
        self.model = model or DEFAULT_MODEL
        self.poll_interval = float(poll_interval)
        self.timeout = float(timeout)

    def _headers(self, *, async_enable: bool = False, resolve_oss: bool = False) -> Dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if async_enable:
            headers["X-DashScope-Async"] = "enable"
        if resolve_oss:
            headers["X-DashScope-OssResourceResolve"] = "enable"
        return headers

    def _load_bytes(self, image_input: ImageInput) -> tuple[bytes, str]:
        if isinstance(image_input, PILImage.Image):
            return self._pil_to_png_or_jpeg(image_input)
        if isinstance(image_input, (bytes, bytearray)):
            return self._as_png_or_jpeg(bytes(image_input))
        if hasattr(image_input, "read"):
            image_input.seek(0)
            data = image_input.read()
            image_input.seek(0)
            return self._as_png_or_jpeg(data)
        if isinstance(image_input, Path):
            image_input = str(image_input)
        if isinstance(image_input, str):
            if image_input.startswith(("http://", "https://")):
                response = requests.get(image_input, timeout=60)
                response.raise_for_status()
                return self._as_png_or_jpeg(response.content)
            with open(image_input, "rb") as fh:
                return self._as_png_or_jpeg(fh.read())
        raise ValueError(
            "Invalid image input: must be a file path, URL, PIL Image, "
            "bytes, or file-like object."
        )

    @staticmethod
    def _pil_to_png_or_jpeg(image: PILImage.Image) -> tuple[bytes, str]:
        fmt = (image.format or "PNG").upper()
        buf = io.BytesIO()
        if fmt in ("JPEG", "JPG"):
            image.convert("RGB").save(buf, format="JPEG")
            return buf.getvalue(), "image/jpeg"
        image.save(buf, format="PNG")
        return buf.getvalue(), "image/png"

    @classmethod
    def _as_png_or_jpeg(cls, data: bytes) -> tuple[bytes, str]:
        if data.startswith(b"\x89PNG"):
            return data, "image/png"
        if data.startswith(b"\xff\xd8"):
            return data, "image/jpeg"
        return cls._pil_to_png_or_jpeg(PILImage.open(io.BytesIO(data)))

    def _to_url(self, image_input: ImageInput, label: str) -> str:
        """Return an HTTP(S) or oss:// URL the synthesis API can fetch."""
        if isinstance(image_input, str) and image_input.startswith(
            ("http://", "https://", "oss://")
        ):
            return image_input
        data, mime = self._load_bytes(image_input)
        if not (MIN_IMAGE_BYTES <= len(data) <= MAX_IMAGE_BYTES):
            raise ValueError(
                f"{label} is {len(data):,} bytes; OutfitAnyone-Plus allows "
                f"{MIN_IMAGE_BYTES:,}–{MAX_IMAGE_BYTES:,} bytes (5 KB–5 MB)."
            )
        ext = ".png" if mime == "image/png" else ".jpg"
        fd, path = tempfile.mkstemp(suffix=ext, prefix=f"aitryon-{label}-")
        try:
            with os.fdopen(fd, "wb") as fh:
                fh.write(data)
            return self._upload_temp(path)
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass

    def _upload_temp(self, file_path: str) -> str:
        """Upload to DashScope temporary OSS and return an ``oss://`` URL."""
        policy_url = f"{self.upload_base}/uploads"
        policy_resp = requests.get(
            policy_url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            params={"action": "getPolicy", "model": self.model},
            timeout=60,
        )
        if policy_resp.status_code >= 400:
            raise ValueError(
                "OutfitAnyone-Plus needs a public HTTP(S) image URL, or a "
                "Beijing-region DashScope key so local files can be uploaded. "
                f"Upload policy failed ({policy_resp.status_code}): {policy_resp.text}"
            )
        policy = (policy_resp.json() or {}).get("data") or {}
        file_name = Path(file_path).name
        upload_dir = policy.get("upload_dir")
        if not upload_dir or not policy.get("upload_host"):
            raise ValueError(
                f"DashScope upload policy missing fields: {policy_resp.text}"
            )
        key = f"{upload_dir}/{file_name}"
        with open(file_path, "rb") as fh:
            files = {
                "OSSAccessKeyId": (None, policy["oss_access_key_id"]),
                "Signature": (None, policy["signature"]),
                "policy": (None, policy["policy"]),
                "x-oss-object-acl": (None, policy["x_oss_object_acl"]),
                "x-oss-forbid-overwrite": (None, policy["x_oss_forbid_overwrite"]),
                "key": (None, key),
                "success_action_status": (None, "200"),
                "file": (file_name, fh),
            }
            upload_resp = requests.post(policy["upload_host"], files=files, timeout=120)
        if upload_resp.status_code >= 400:
            raise ValueError(
                f"DashScope temp upload failed ({upload_resp.status_code}): "
                f"{upload_resp.text}"
            )
        return f"oss://{key}"

    def _submit(self, payload: Dict[str, Any], resolve_oss: bool) -> str:
        url = f"{self.base_url}{SYNTHESIS_PATH}"
        resp = requests.post(
            url,
            headers=self._headers(async_enable=True, resolve_oss=resolve_oss),
            json=payload,
            timeout=60,
        )
        if resp.status_code >= 400:
            raise ValueError(
                f"OutfitAnyone-Plus create failed ({resp.status_code}): {resp.text}"
            )
        data = resp.json()
        if data.get("code") and not (data.get("output") or {}).get("task_id"):
            raise ValueError(
                f"OutfitAnyone-Plus create error: {data.get('code')} "
                f"{data.get('message') or data}"
            )
        output = data.get("output") or data
        task_id = output.get("task_id") or data.get("task_id")
        if not task_id:
            raise ValueError(f"OutfitAnyone-Plus create missing task_id: {data}")
        return str(task_id)

    def _poll(self, task_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/tasks/{task_id}"
        deadline = time.time() + self.timeout
        while time.time() < deadline:
            resp = requests.get(url, headers=self._headers(), timeout=60)
            if resp.status_code >= 400:
                raise ValueError(
                    f"OutfitAnyone-Plus poll failed ({resp.status_code}): {resp.text}"
                )
            data = resp.json()
            output = data.get("output") or data
            status = (
                output.get("task_status")
                or output.get("status")
                or data.get("task_status")
                or ""
            ).upper()
            if status in TERMINAL_OK:
                return output
            if status in TERMINAL_FAIL:
                raise ValueError(
                    f"OutfitAnyone-Plus task failed: "
                    f"{output.get('code') or ''} {output.get('message') or output}"
                )
            time.sleep(self.poll_interval)
        raise TimeoutError(
            f"OutfitAnyone-Plus task {task_id} timed out after {self.timeout}s"
        )

    @staticmethod
    def _download_image(output: Dict[str, Any]) -> PILImage.Image:
        image_url = output.get("image_url")
        if not image_url:
            results = output.get("results")
            if isinstance(results, list) and results:
                image_url = (results[0] or {}).get("url") or (results[0] or {}).get(
                    "image_url"
                )
        if not image_url:
            raise ValueError(
                f"OutfitAnyone-Plus success response missing image_url: {output}"
            )
        resp = requests.get(image_url, timeout=120)
        if resp.status_code != 200:
            raise ValueError(
                f"Failed to download OutfitAnyone-Plus result ({resp.status_code})"
            )
        return PILImage.open(io.BytesIO(resp.content))

    def generate_and_decode(
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
        top_garment: Optional[ImageInput] = None,
        bottom_garment: Optional[ImageInput] = None,
        restore_face: bool = True,
        resolution: int = -1,
        **kwargs,
    ) -> List[PILImage.Image]:
        """Generate a try-on still and return PIL Images.

        Pass a person photo plus at least one garment. A single garment
        (or dress/jumpsuit) goes to ``top_garment_url``. Combo outfits
        can set both ``top_garment`` and ``bottom_garment``.

        Args:
            person / garment: Person and primary garment (path, URL, PIL, bytes).
            top_garment / bottom_garment: Explicit top and bottoms URLs/files.
            restore_face: Keep the original face (default True).
            resolution: ``-1`` (match person), ``1024`` (576x1024), or
                ``1280`` (720x1280).
        """
        resolved_person = person or source_image or person_image or model_image
        resolved_top = (
            top_garment or garment or reference_image or garment_image or cloth_image
        )
        resolved_bottom = bottom_garment or kwargs.get("bottom_garment_image")
        if resolved_person is None:
            raise ValueError(
                "Person image is required. Pass person, source_image, "
                "person_image, or model_image."
            )
        if resolved_top is None and resolved_bottom is None:
            raise ValueError(
                "At least one garment is required (top/dress via garment or "
                "top_garment, and/or bottoms via bottom_garment)."
            )
        res = int(resolution if resolution is not None else -1)
        if res not in VALID_RESOLUTIONS:
            raise ValueError(
                f"resolution must be one of {sorted(VALID_RESOLUTIONS)} "
                "(-1 matches the person image)."
            )

        person_url = self._to_url(resolved_person, "person")
        input_obj: Dict[str, str] = {"person_image_url": person_url}
        if resolved_top is not None:
            input_obj["top_garment_url"] = self._to_url(resolved_top, "top_garment")
        if resolved_bottom is not None:
            input_obj["bottom_garment_url"] = self._to_url(
                resolved_bottom, "bottom_garment"
            )
        resolve_oss = any(value.startswith("oss://") for value in input_obj.values())
        payload = {
            "model": self.model,
            "input": input_obj,
            "parameters": {
                "resolution": res,
                "restore_face": bool(restore_face),
            },
        }
        task_id = self._submit(payload, resolve_oss=resolve_oss)
        output = self._poll(task_id)
        return [self._download_image(output)]
