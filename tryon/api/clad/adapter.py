"""
Clad Body Model API (Path A) — photo or questionnaire → ISO 8559-1 measurements (+ GLB mesh).

Docs: https://api.clad.you/ (OpenAPI on root)
Keys: https://clad.you/developers
"""

from __future__ import annotations

import io
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional, Union

import requests

DEFAULT_BASE_URL = "https://api.clad.you"

PhotoInput = Union[str, Path, io.BytesIO, bytes]


def _resolve_clad_key(api_key: Optional[str]) -> str:
    key = api_key or os.getenv("CLAD_API_KEY")
    if not key:
        raise ValueError(
            "Clad API key is required. Set CLAD_API_KEY "
            "(https://clad.you/developers)."
        )
    return key


def _photo_bytes(photo: PhotoInput) -> tuple[bytes, str]:
    if isinstance(photo, (bytes, bytearray)):
        return bytes(photo), "photo.jpg"
    if isinstance(photo, io.BytesIO):
        photo.seek(0)
        return photo.read(), "photo.jpg"
    path = Path(str(photo))
    if not path.exists():
        raise FileNotFoundError(f"Photo not found: {photo}")
    return path.read_bytes(), path.name


def _strip_mesh(payload: Dict[str, Any], include_mesh: bool) -> Dict[str, Any]:
    if include_mesh:
        return payload
    out = dict(payload)
    out.pop("mesh", None)
    return out


class CladBodyApiAdapter:
    """Clad hosted body model API (measurements + optional GLB mesh)."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = _resolve_clad_key(api_key)
        self.base_url = (base_url or os.getenv("CLAD_API_BASE_URL") or DEFAULT_BASE_URL).rstrip(
            "/"
        )

    def _auth_headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}

    def _poll_job(
        self,
        job_id: str,
        poll_url: Optional[str] = None,
        max_wait_time: int = 300,
    ) -> Dict[str, Any]:
        if poll_url and poll_url.startswith("http"):
            url = poll_url
        elif poll_url:
            url = f"{self.base_url}/{poll_url.lstrip('/')}"
        else:
            url = f"{self.base_url}/v1/jobs/{job_id}"

        deadline = time.time() + max_wait_time
        while time.time() < deadline:
            resp = requests.get(url, headers=self._auth_headers(), timeout=60)
            resp.raise_for_status()
            data = resp.json()
            status = data.get("status")
            if status == "completed":
                result = data.get("result")
                if not result:
                    raise ValueError(f"Job {job_id} completed without result: {data}")
                return {
                    "job_id": job_id,
                    "measurements": result.get("measurements", {}),
                    "params": result.get("params"),
                    "mae": result.get("mae"),
                    "mesh": result.get("mesh"),
                    "source": "photo",
                }
            if status == "failed":
                err = data.get("error") or data
                raise ValueError(f"Clad photo job {job_id} failed: {err}")
            if status in ("queued", "running"):
                time.sleep(2.0)
                continue
            raise ValueError(f"Unknown Clad job status {status!r}: {data}")
        raise ValueError(f"Clad job {job_id} timed out after {max_wait_time}s")

    def measure_from_photo(
        self,
        photo: PhotoInput,
        height_cm: float,
        max_wait_time: int = 300,
        include_mesh: bool = False,
    ) -> Dict[str, Any]:
        if height_cm < 140 or height_cm > 220:
            raise ValueError("height_cm must be between 140 and 220 (Clad API limits).")
        raw, filename = _photo_bytes(photo)
        resp = requests.post(
            f"{self.base_url}/v1/body/from-photo",
            headers=self._auth_headers(),
            files={"photo": (filename, raw, "application/octet-stream")},
            data={"height_cm": str(height_cm)},
            timeout=120,
        )
        if resp.status_code == 401:
            raise ValueError("Clad API unauthorized — check CLAD_API_KEY.")
        resp.raise_for_status()
        job = resp.json()
        job_id = job["job_id"]
        polled = self._poll_job(job_id, job.get("poll_url"), max_wait_time=max_wait_time)
        polled["quota"] = job.get("quota")
        return _strip_mesh(polled, include_mesh)

    def measure_from_questionnaire(
        self,
        height_cm: float,
        mass_kg: float,
        gender: str,
        body_shape: str,
        belly: int,
        build: int,
        legs: int = 2,
        arms: int = 2,
        cupsize: Optional[str] = None,
        ancestry: Optional[str] = "mixed",
        include_mesh: bool = False,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "height_cm": height_cm,
            "mass_kg": mass_kg,
            "gender": gender,
            "body_shape": body_shape,
            "belly": belly,
            "build": build,
            "legs": legs,
            "arms": arms,
        }
        if cupsize is not None:
            payload["cupsize"] = cupsize
        if ancestry is not None:
            payload["ancestry"] = ancestry

        resp = requests.post(
            f"{self.base_url}/v1/body/from-questionnaire",
            headers={**self._auth_headers(), "Content-Type": "application/json"},
            json=payload,
            timeout=120,
        )
        if resp.status_code == 401:
            raise ValueError("Clad API unauthorized — check CLAD_API_KEY.")
        resp.raise_for_status()
        data = resp.json()
        out = {
            "measurements": data.get("measurements", {}),
            "params": data.get("params"),
            "mesh": data.get("mesh"),
            "quota": data.get("quota"),
            "source": "questionnaire",
        }
        return _strip_mesh(out, include_mesh)
