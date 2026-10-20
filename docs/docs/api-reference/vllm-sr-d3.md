---
sidebar_position: 12
title: vLLM-SR Decision 3.0 (hosted)
description: Multimodal System One decision models — d3-turbo through d3-edge on the free Decision 3.0 API.
keywords:
  - Decision 3.0
  - d3-turbo
  - vLLM Semantic Router
  - System One
  - box
  - track
---

# vLLM-SR Decision 3.0 (hosted)

[Decision 3.0](https://decision.vllm-sr.ai/) models from **vLLM Semantic Router** are multimodal **decision** models: they do not generate chat text. You send a **state** (text/JSON) plus optional **images** and **video**, and a map of typed **questions**; the model returns calibrated probabilities (and boxes/tracks when asked).

OpenTryOn exposes the hosted API on the `decide` service with **`D3ApiAdapter`** and **`DECISION_API_KEY`**.

| Registry id | HF model id | Size |
|---|---|---|
| `d3-turbo` | `vllm-sr/d3-turbo` | 27B |
| `d3-flash` | `vllm-sr/d3-flash` | 9B |
| `d3-mini` | `vllm-sr/d3-mini` | 4B |
| `d3-nano` | `vllm-sr/d3-nano` | 2B |
| `d3-lite` | `vllm-sr/d3-lite` | 0.8B |
| `d3-edge` | `vllm-sr/d3-edge` | 0.6B |

On the API, `vllm-sr/d3` aliases **`d3-turbo`**. Local Apache-2.0 weights: [Decision 3.0 (local)](../local-models/d3.md).

## Prerequisites

```bash
# Free key (one click, no account): https://decision.vllm-sr.ai
export DECISION_API_KEY=your_key
# optional:
# export DECISION_BASE_URL=https://decision.vllm-sr.ai
```

Limits and model readiness: `GET https://decision.vllm-sr.ai/api/info`.

## Question schema

Shared with Jev / Liquid d1 for **`noul`**, **`choice`**, and **`score`**. Decision 3.0 adds:

| type | Purpose |
|---|---|
| `box` | One bounding box + confidence (`top`/`bottom`/`left`/`right` as fractions 0–1) |
| `track` | Box trajectory over a video (`rate` = updates per second) |

Use **`--assets`** when images appear inside questions or options (placeholder map). See the [d3-turbo model card](https://huggingface.co/vllm-sr/d3-turbo) for examples.

## CLI

```bash
# Text routing (fashion support triage)
opentryon decide --model d3-turbo \
  --state "Customer photo: wrong size tag on linen shirt order" \
  --questions triage.json

# Product photo: where is the logo?
opentryon decide --model d3-turbo \
  --state "E-commerce packshot" \
  --image product.jpg \
  --questions box_logo.json

# Video: track a garment through a clip
opentryon decide --model d3-turbo \
  --state "Runway clip" \
  --video walk.mp4 \
  --questions track.json

opentryon decide --model d3-flash --questions q.json --state "..." --dry-run
```

## Python

```python
from tryon.api.vllm_sr import D3ApiAdapter

adapter = D3ApiAdapter(model_id="vllm-sr/d3-turbo")
out = adapter.decide(
    state="Red satin evening gown on mannequin",
    questions={
        "formal": {"type": "noul", "instructions": "Is this formal wear?"},
    },
    image="dress.jpg",
)
print(out["answers"])
```

## MCP

Tools are generated from the registry, e.g. `decide_d3_turbo`, `decide_d3_flash`, … Restart MCP after registry changes. Key: **`DECISION_API_KEY`** (Connect rail: **vLLM Semantic Router (Decision 3.0)**).

## API details

- **Endpoint:** `POST https://decision.vllm-sr.ai/v1/systemone`
- **Auth:** `Authorization: Bearer $DECISION_API_KEY`
- **Body:** `model`, `questions`, optional `state`, `images`, `videos`, `assets`, `long_context`

Compare with [Typesafe Jev](typesafe-jev.md) (text-only hosted) and [Liquid d1](../local-models/liquid-d1.md) (local, no box/track).
