"""
Shared Pruna AI HTTP client.

All Pruna models use the same surface:
  POST /v1/files                     -- upload local media, get a temp URL
  POST /v1/predictions               -- create a prediction (Model header)
  GET  /v1/predictions/status/{id}   -- poll an async prediction
  GET  <generation_url>              -- download the result

Auth: ``apikey`` header from ``PRUNA_API_KEY`` (optional ``PRUNA_BASE_URL``).
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

DEFAULT_BASE_URL = "https://api.pruna.ai"
TERMINAL_STATUSES = {"succeeded", "failed", "canceled"}

MediaInput = Union[str, io.BytesIO, Image.Image, bytes, bytearray]


class PrunaClient:
    """Low-level Pruna API helper shared by every Pruna adapter."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.api_key = api_key or os.getenv("PRUNA_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Pruna API key is required. Set PRUNA_API_KEY environment "
                "variable or pass api_key parameter."
            )
        self.base_url = (
            base_url or os.getenv("PRUNA_BASE_URL") or DEFAULT_BASE_URL
        ).rstrip("/")
        self.headers = {"apikey": self.api_key}

    def resolve_url(self, url: str) -> str:
        """Pruna sometimes returns a relative path for generation_url."""
        if url.startswith(("http://", "https://")):
            return url
        return f"{self.base_url}{url if url.startswith('/') else '/' + url}"

    def upload_bytes(self, data: bytes, filename: str = "upload.bin") -> str:
        """Upload raw bytes to Pruna's temporary file store; return hosted URL."""
        response = requests.post(
            f"{self.base_url}/v1/files",
            headers=self.headers,
            files={"content": (filename, data)},
            timeout=120,
        )
        response.raise_for_status()
        data_json = response.json()
        try:
            return data_json["urls"]["get"]
        except (KeyError, TypeError):
            raise ValueError(f"Unexpected file upload response from Pruna: {data_json}")

    def prepare_url(
        self,
        media_input: MediaInput,
        *,
        default_filename: str = "upload.bin",
    ) -> str:
        """
        Resolve any supported media input to a URL Pruna can fetch.

        Already-http(s) URLs are passed through; everything else is uploaded
        via ``/v1/files``.
        """
        if isinstance(media_input, Image.Image):
            buffer = io.BytesIO()
            media_input.save(buffer, format="PNG")
            return self.upload_bytes(buffer.getvalue(), filename="image.png")

        if isinstance(media_input, (bytes, bytearray)):
            return self.upload_bytes(bytes(media_input), filename=default_filename)

        if hasattr(media_input, "read"):
            media_input.seek(0)
            return self.upload_bytes(media_input.read(), filename=default_filename)

        if isinstance(media_input, str):
            if media_input.startswith(("http://", "https://")):
                return media_input

            if os.path.exists(media_input):
                with open(media_input, "rb") as f:
                    return self.upload_bytes(
                        f.read(), filename=Path(media_input).name or default_filename
                    )

            if len(media_input) > 100:
                try:
                    return self.upload_bytes(
                        base64.b64decode(media_input), filename=default_filename
                    )
                except Exception:
                    pass

            raise ValueError(f"Media path does not exist: {media_input}")

        raise ValueError(
            "Invalid media input: must be a file path, URL, PIL Image, bytes, "
            "file-like object, or base64 string"
        )

    def poll_prediction(
        self,
        get_url: str,
        max_wait_time: int = 120,
        poll_interval: float = 1.0,
    ) -> Dict[str, Any]:
        """Poll until a terminal status; return the completed payload."""
        start_time = time.time()
        while True:
            elapsed = time.time() - start_time
            if elapsed > max_wait_time:
                raise ValueError(f"Prediction timed out after {max_wait_time} seconds.")

            response = requests.get(get_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            status = data.get("status")

            if status == "succeeded":
                return data
            if status in ("failed", "canceled"):
                raise ValueError(
                    f"Prediction {status}: {data.get('error') or data.get('message') or data}"
                )

            time.sleep(poll_interval)

    def predict(
        self,
        model: str,
        input_payload: Dict[str, Any],
        *,
        wait: bool = True,
        max_wait_time: int = 120,
        poll_interval: float = 1.0,
        label: Optional[str] = None,
    ) -> str:
        """
        Create a prediction and return the absolute ``generation_url``.

        When ``wait`` is True, sends ``Try-Sync: true`` and falls back to
        polling if the sync window expires unfinished.
        """
        headers = {
            **self.headers,
            "Content-Type": "application/json",
            "Model": model,
        }
        if wait:
            headers["Try-Sync"] = "true"

        name = label or model
        try:
            response = requests.post(
                f"{self.base_url}/v1/predictions",
                headers=headers,
                json={"input": input_payload},
                timeout=90,
            )
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.HTTPError as e:
            error_msg = e.response.text
            try:
                error_msg = e.response.json().get("error", error_msg)
            except Exception:
                pass
            raise ValueError(
                f"Pruna {name} API HTTP error ({e.response.status_code}): {error_msg}"
            )
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Failed to connect to Pruna {name} API: {str(e)}")

        status = data.get("status")
        if status == "succeeded":
            return self.resolve_url(data["generation_url"])
        if status == "failed":
            raise ValueError(
                f"Prediction failed: {data.get('error') or data.get('message') or data}"
            )

        get_url = data.get("get_url") or (
            f"{self.base_url}/v1/predictions/status/{data.get('id')}"
        )
        completed = self.poll_prediction(
            get_url, max_wait_time=max_wait_time, poll_interval=poll_interval
        )
        return self.resolve_url(completed["generation_url"])

    def download(self, url: str, timeout: int = 120) -> bytes:
        """Download generation bytes (auth header included for delivery URLs)."""
        response = requests.get(
            self.resolve_url(url), headers=self.headers, timeout=timeout
        )
        response.raise_for_status()
        return response.content
