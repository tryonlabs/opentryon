---
sidebar_position: 13
title: Dream Labs Dream-1
description: Hosted World Action Model API for bimanual robot control (dream-1 and dream-1-flash).
keywords:
  - Dream-1
  - Dream Labs
  - World Action Model
  - robotics
  - robot policy
---

# Dream Labs Dream-1

[Dream-1](https://dreamlabs.ai/research/dream-1/) is Dream Labs' **World Action Model (WAM)**: a hosted policy that maps camera frames + robot state to short action chunks (~1.6 seconds). It targets **bimanual parallel-gripper** arms and is meant for zero-shot control of unseen embodiments (research beta — not safety-validated).

OpenTryOn exposes it on the **`robot-act`** service (API only). There is **no local Dream-1 policy checkpoint** to run on your GPU; inference is through Dream Labs' gateway (`POST /v1/get_action`).

| Registry id | Checkpoint | Notes |
|---|---|---|
| `dream-1` | `dreamlabs/dream-1` | Full model (~$3/hr on Dream Labs pricing) |
| `dream-1-flash` | `dreamlabs/dream-1-flash` | Faster tier (~$2/hr) |

Video world models (DreamDojo / GR-1) use a separate **`dream-engine`** SDK — not wired here.

## Prerequisites

```bash
pip install dreamlabs-client   # import dream

export DREAM_API_KEY=dl_live_...   # platform / Dream Labs setup
```

Optional credentials file (`~/.dreamlabs/credentials`):

```
DREAM_GATEWAY_URL=https://api.dreamlabs.ai
DREAM_API_URL=https://platform.dreamlabs.ai
DREAM_DATA_URL=https://data.dreamlabs.ai
DREAM_API_KEY=dl_live_...
```

## One policy step (CLI)

Each CLI call performs **`policy` → `set_observation` → `get_action` → `close`** (one action chunk). Production loops call `set_observation` every camera tick and `get_action` on a worker thread — see the [dreamlabs-client README](https://pypi.org/project/dreamlabs-client/).

```bash
opentryon robot-act --model dream-1 \
  --frames frames.json \
  --observation obs.json \
  --policy-config yam_policy.json

opentryon robot-act --model dream-1-flash --frames frames.json --observation obs.json --dry-run
```

### `frames.json` (example)

```json
{
  "video.overhead": "<base64 JPEG, no data: prefix>",
  "video.wrist_l": "<base64 JPEG>",
  "video.wrist_r": "<base64 JPEG>"
}
```

### `obs.json` (example)

```json
{
  "state.right_arm": [0, 0, 0, 0, 0, 0],
  "state.right_gripper": [0.5],
  "state.left_arm": [0, 0, 0, 0, 0, 0],
  "state.left_gripper": [0.5],
  "prompt": "fold the towel"
}
```

Use float arrays compatible with your embodiment; YAM examples and `ik` / `embodiment` blocks are in the official client docs.

## Python

```python
from tryon.api.dream_labs import Dream1Adapter

adapter = Dream1Adapter(checkpoint="dreamlabs/dream-1")
out = adapter.get_action(
    frames="frames.json",
    observation="obs.json",
    policy_config={"strict": True, "ik": {"arm": "yam", "head": "joint"}},
)
print(out["action"])
```

## MCP

Tools: `robot_act_dream_1`, `robot_act_dream_1_flash` (generated from the registry). Key: **`DREAM_API_KEY`**.

## Local weights

**Not available** for Dream-1 policy inference. Dream Labs serves the model; you integrate via `dreamlabs-client`. For open-weight **decision** models (fashion QA / routing), see [vLLM-SR d3](vllm-sr-d3.md) or [Liquid d1](../local-models/liquid-d1.md).
