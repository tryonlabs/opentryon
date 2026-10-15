---
sidebar_position: 19
title: VideoJev (local)
description: Open-weight video System One models — temporal grounding and multiple-choice video QA without text generation.
keywords:
  - VideoJev
  - System One
  - video grounding
  - video QA
  - MCG-NJU
  - local
---

# VideoJev (local)

[VideoJev](https://mcg-nju.github.io/VideoJev/) (MCG-NJU, Apache-2.0) is a **video System One** model family: it scores temporal intervals and multiple-choice options directly against video evidence, without autoregressive answer decoding. OpenTryOn exposes it on the **`decide`** service as **`videojev-4b`** and **`videojev-35b-a3b`** (Path B, `extra="local"`).

## Hosted API?

**There is no first-party VideoJev HTTP API today.**

| Provider | Video input? | Notes |
| --- | --- | --- |
| [Typesafe Jev](../api-reference/typesafe-jev.md) (`jev`) | No | `POST /v1/systemone`, text/JSON `state` only |
| [HAL-X THX-01](../api-reference/hal-x-thx01.md) (`thx-01`) | No | Same System One shape, text/JSON |
| **VideoJev** | Yes (local) | HF weights + `predict_video` |

Workarounds (frame captions → text `state` → Jev) are possible but are **not** VideoJev integration.

## Models

| Registry id | HF checkpoint | Backbone |
| --- | --- | --- |
| `videojev-4b` | `ZhuYuhan/VideoJev-4B` | Qwen3.5-4B |
| `videojev-35b-a3b` | `ZhuYuhan/VideoJev-35B-A3B` | Qwen3.6-35B-A3B |

Paper: [arXiv:2610.18615](https://arxiv.org/abs/2610.18615) · Code: [MCG-NJU/VideoJev](https://github.com/MCG-NJU/VideoJev)

## Requirements

VideoJev upstream targets **Python 3.12**, **PyTorch 2.8 + CUDA 12.8**, **FlashAttention 2**, and `trust_remote_code` checkpoints. Use a dedicated GPU environment (same pattern as Liquid d1 / LTX local):

```bash
pip install opentryon[local]
pip install "transformers>=4.51" torch torchvision
# FlashAttention 2 per VideoJev requirements.txt / scripts/env.sh
```

Optional env overrides:

- `VIDEOJEV_MODEL_ID` — default checkpoint for both tiers
- `VIDEOJEV_MODEL_ID_4B` / `VIDEOJEV_MODEL_ID_35B_A3B`
- `VIDEOJEV_BASE_4B` / `VIDEOJEV_BASE_35B` — local Qwen base paths (see upstream repo)

## Question schema (VideoJev-native)

Unlike Jev/d1 **`noul` / `choice` / `score`** maps, VideoJev expects a **JSON array** of tasks:

```json
[
  {
    "id": "grounding-1",
    "task": "grounding",
    "query": "The model walks the runway."
  },
  {
    "id": "qa-1",
    "task": "choice",
    "query": "What is she wearing?",
    "options": ["A. Evening gown.", "B. Denim jacket.", "C. Activewear."]
  }
]
```

Grounding returns a time **`interval`** in seconds; choice returns **`answer_index`** and **`answer`**.

## CLI

```bash
opentryon decide --model videojev-4b \
  --video clip.mp4 \
  --questions videojev_tasks.json \
  --fps 2.0 --max-frames 2048 --context 8192

opentryon decide --model videojev-35b-a3b \
  --video https://example.com/clip.mp4 \
  --questions videojev_tasks.json \
  --context 262144

opentryon decide --model videojev-4b --video clip.mp4 --questions tasks.json --dry-run
```

## Python

```python
from tryon.models.videojev import VideoJevAdapter

adapter = VideoJevAdapter(variant="4b")
out = adapter.decide(
    questions="videojev_tasks.json",
    video="clip.mp4",
)
print(out["results"])
```

## MCP

Restart MCP after registry changes. Tools:

- `decide_videojev_4b`
- `decide_videojev_35b_a3b`

## When to use

- **Temporal grounding** — “when does X happen?” with scored intervals
- **Multiple-choice video QA** — fast structured labels for agents (QC, routing, dataset filtering)
- **Repeated queries on one clip** — upstream supports cached/joint inference for many questions per video

For text/image **noul/choice/score** without video, use [Jev](../api-reference/typesafe-jev.md), [d1](liquid-d1.md), or [THX-01](../api-reference/hal-x-thx01.md).
