"""
Dream Labs Dream-1 World Action Model (hosted policy API).

Dream-1 controls bimanual parallel-gripper robots via the public Dream API
(``POST /v1/get_action``). There is no self-hosted Dream-1 checkpoint for
this policy path; use the official ``dreamlabs-client`` package.

Reference: https://dreamlabs.ai/research/dream-1/
SDK: https://pypi.org/project/dreamlabs-client/

Env:
  DREAM_API_KEY (required)
  DREAM_GATEWAY_URL, DREAM_API_URL, DREAM_DATA_URL (optional; see ~/.dreamlabs/credentials)
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional, Union

FramesInput = Union[Dict[str, str], str]
ObservationInput = Union[Dict[str, Any], str]
PolicyConfigInput = Union[Dict[str, Any], str]

DEFAULT_CHECKPOINTS = {
    "dream-1": "dreamlabs/dream-1",
    "dream-1-flash": "dreamlabs/dream-1-flash",
}


def _load_json(value: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    text = value.strip()
    if os.path.isfile(text):
        with open(text, "r", encoding="utf-8") as f:
            text = f.read()
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise ValueError("Expected a JSON object.")
    return parsed


class Dream1Adapter:
    """Thin wrapper around ``dream.DreamClient`` for one policy step."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        checkpoint: str = "dreamlabs/dream-1",
    ):
        self.api_key = api_key or os.getenv("DREAM_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Dream Labs API key is required. Set DREAM_API_KEY (mint at "
                "https://decision.vllm-sr.ai or the Dream Labs platform) or pass api_key."
            )
        self.checkpoint = checkpoint

    def _import_dream(self):
        try:
            import dream  # dreamlabs-client on PyPI
        except ImportError as exc:
            raise ImportError(
                "Dream-1 requires the official Dream Labs client. Install with:\n"
                "  pip install dreamlabs-client\n"
                "Or the full library: pip install dreamlabs\n"
                f"Original error: {exc}"
            ) from exc
        return dream

    def get_action(
        self,
        frames: FramesInput,
        observation: ObservationInput,
        policy_config: Optional[PolicyConfigInput] = None,
        checkpoint: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run one ``set_observation`` + ``get_action`` cycle and return the action chunk.

        ``frames`` maps ``video.<role>`` keys to base64 JPEG strings (no ``data:`` prefix).
        ``observation`` carries ``state.*`` arrays, ``prompt``, etc. See the dreamlabs-client docs.
        """
        frames_dict = _load_json(frames)
        obs_dict = _load_json(observation)
        policy: Dict[str, Any] = {}
        if policy_config is not None:
            policy = _load_json(policy_config)
        use_checkpoint = checkpoint or self.checkpoint
        policy = {**policy, "checkpoint": use_checkpoint}

        dream = self._import_dream()
        client = dream.DreamClient(api_key=self.api_key)
        try:
            client.policy(policy)
            client.set_observation(frames_dict, obs_dict)
            action = client.get_action()
            timing = getattr(client, "last_timing", None)
            return {
                "checkpoint": use_checkpoint,
                "action": action,
                "session_id": getattr(client, "session_id", None),
                "last_timing": timing,
            }
        finally:
            client.close()

    @staticmethod
    def list_checkpoints(*, api_key: Optional[str] = None) -> list[Dict[str, Any]]:
        """List servable checkpoints for the account (requires dreamlabs-client)."""
        dream = Dream1Adapter(api_key=api_key)._import_dream()
        models = dream.models.list_models(api_key=api_key or os.getenv("DREAM_API_KEY"))
        return [
            {
                "id": m.id,
                "servable": m.servable,
                "embodiment": m.embodiment,
                "owner": m.owner,
            }
            for m in models
        ]
