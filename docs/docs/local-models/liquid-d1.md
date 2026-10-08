---
sidebar_position: 18
title: Liquid AI d1 (local)
description: Open-weight Liquid AI d1-3B and d1-omni-600M decision models — calibrated yes/no, choice and score answers about text, images and speech.
keywords:
  - Liquid AI
  - d1-3B
  - d1-omni-600M
  - decision model
  - System One
  - classification
  - local
---

# Liquid AI d1 (local)

[d1-3B](https://huggingface.co/LiquidAI/d1-3B) and [d1-omni-600M](https://huggingface.co/LiquidAI/d1-omni-600M) are open-weight **decision models**. They are not chat models: given a state (text, JSON, images, or speech for omni) and named typed questions, they return calibrated probabilities in **one forward pass with zero output tokens**. OpenTryOn exposes them through the `decide` service with `LiquidD1Adapter` (Path B, `extra="local"`).

Good fits: garment attribute classification from photos (neckline, sleeve, pattern), QC gating of generated try-on images, moderation, routing.

| | `d1-3b` | `d1-omni-600m` |
|---|---|---|
| Repo | `LiquidAI/d1-3B` | `LiquidAI/d1-omni-600M` |
| Size | 3.12B (bfloat16) | 587M (float16) |
| Input | text / JSON + images | text / JSON + images **or** one 16 kHz mono speech clip (≤ 30 s) |
| Context | 32,768 | 16,384 |
| Transformers | `>=5.14` | `>=5.15` |
| Decision Index 0.2.1 | 48.57 | 15.95 |
| License | LFM Open License v1.0 (`lfm1.0`) — review for commercial use | same |

Images and audio cannot be combined in one call. The omni card recommends float16 on GPU and advises against bfloat16.

Hosted, text-only twin: [Typesafe Jev](../api-reference/typesafe-jev.md) (`--model jev`).

## Requirements

```bash
pip install opentryon[local]
pip install "transformers>=5.15" torchvision pillow soundfile
```

The shared `opentryon[local]` pin is `transformers==4.42.4`, so use a separate environment for d1 (same situation as Limite and Ternary Bonsai). The adapter raises a clear error if the installed transformers is too old.

Optional override: `export LIQUID_D1_MODEL_ID=/path/to/snapshot`.

## CLI

Question schema (`noul` / `choice` / `score`) is documented on the [Jev page](../api-reference/typesafe-jev.md#question-schema).

```bash
# Image classification
opentryon decide --model d1-3b --questions neckline.json --image dress.jpg

# Text/JSON state
opentryon decide --model d1-3b --questions triage.json --state "Customer says the zip broke after one wear."

# Speech (omni only)
opentryon decide --model d1-omni-600m --questions intent.json --audio request.wav
```

Flags: `--questions/-q` (required), `--state/-s`, `--image/-i` (one or more), `--audio` (omni), `--variant`, `--model-id`, `--device`.

## Python

```python
from tryon.models.liquid_d1 import LiquidD1Adapter

adapter = LiquidD1Adapter(variant="d1-3B")
out = adapter.decide(
    questions={"neckline": {"type": "choice", "instructions": "Neckline style?",
                            "criteria": {"v-neck": "V-shaped opening", "crew": "round, high"}}},
    image="dress.jpg",
)
print(out["answers"]["neckline"])  # {'choice': ..., 'confidence': ..., 'probabilities': {...}}
```

## Notes

- MCP tools: `decide_d1_3b`, `decide_d1_omni_600m`.
- Audio must already be 16 kHz mono; the adapter errors (rather than resampling) otherwise.
- No GPU was available when this was integrated, so weight loading was not exercised end to end — same caveat as the other local adapters.
