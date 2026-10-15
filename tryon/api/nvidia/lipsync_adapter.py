"""
NVIDIA Maxine LipSync NIM (Path A, self-hosted gRPC).

There is no public ``ai.api.nvidia.com`` REST endpoint for LipSync (unlike TRELLIS).
Run the NIM container locally or on your cluster, then point
``LIPSYNC_GRPC_TARGET`` at ``host:port`` (default gRPC port ``8001``).

This adapter shells out to NVIDIA's sample client script from
`NVIDIA-Maxine/nim-clients` (``lipsync/python/scripts/lipsync.py``), configured via
``LIPSYNC_CLIENT_SCRIPT``. Set ``NGC_API_KEY`` / ``NVIDIA_API_KEY`` when pulling the NIM image.

Docs:
  https://docs.nvidia.com/nim/maxine/lipsync/latest/basic-inference.html
  https://build.nvidia.com/nvidia/lipsync
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional


class LipSyncAdapter:
    """Lip-sync a video's mouth movements to a speech audio track (gRPC NIM)."""

    def __init__(
        self,
        grpc_target: Optional[str] = None,
        client_script: Optional[str] = None,
    ):
        self.grpc_target = (
            grpc_target or os.getenv("LIPSYNC_GRPC_TARGET") or "127.0.0.1:8001"
        )
        self.client_script = client_script or os.getenv("LIPSYNC_CLIENT_SCRIPT")

    def _resolve_media(self, path: str, label: str) -> str:
        if not path:
            raise ValueError(f"{label} is required.")
        if path.startswith(("http://", "https://")):
            raise ValueError(
                f"LipSync NIM client expects local files for {label}; download URLs first."
            )
        if not os.path.isfile(path):
            raise ValueError(f"{label} path does not exist: {path}")
        return path

    def generate_audio_to_video(
        self,
        video: str,
        audio: str,
        **kwargs,
    ) -> bytes:
        """
        Dub lip movements in ``video`` (H.264 CFR MP4) to match ``audio`` (WAV/MP3).

        Returns MP4 bytes.
        """
        video_path = self._resolve_media(video, "video")
        audio_path = self._resolve_media(audio, "audio")
        if not self.client_script or not os.path.isfile(self.client_script):
            raise ValueError(
                "LipSync requires a local gRPC NIM and NVIDIA's sample client script. "
                "Clone https://github.com/NVIDIA-Maxine/nim-clients, install "
                "lipsync/requirements.txt, and set LIPSYNC_CLIENT_SCRIPT to "
                "lipsync/python/scripts/lipsync.py. Hosted REST is not available; "
                "for cloud lip-sync without self-hosting, use --model fal-h3-max-lipsync."
            )
        with tempfile.TemporaryDirectory(prefix="opentryon-lipsync-") as tmp:
            out_path = os.path.join(tmp, "lipsync_out.mp4")
            cmd = [
                sys.executable,
                self.client_script,
                "--target",
                self.grpc_target,
                "--video-input",
                video_path,
                "--audio-input",
                audio_path,
                "--output",
                out_path,
            ]
            for key, value in kwargs.items():
                if value is None:
                    continue
                flag = "--" + key.replace("_", "-")
                cmd.extend([flag, str(value)])
            try:
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=int(os.getenv("LIPSYNC_TIMEOUT_SECONDS", "600")),
                    check=False,
                )
            except subprocess.TimeoutExpired as exc:
                raise TimeoutError(
                    f"LipSync client timed out after {exc.timeout}s."
                ) from exc
            if proc.returncode != 0:
                err = (proc.stderr or proc.stdout or "").strip()[:2000]
                raise RuntimeError(
                    f"LipSync client failed (exit {proc.returncode}): {err or 'no output'}"
                )
            if not os.path.isfile(out_path):
                raise RuntimeError("LipSync client did not write output video.")
            return Path(out_path).read_bytes()
