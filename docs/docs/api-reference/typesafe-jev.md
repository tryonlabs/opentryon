---
sidebar_position: 29
title: Typesafe AI Jev (Decisions)
description: Calibrated yes/no, choice and score decisions from Typesafe AI's Jev "System One" model via the opentryon decide service.
keywords:
  - Typesafe AI
  - Jev
  - System One
  - decision model
  - classification
  - routing
  - calibrated probabilities
---

# Typesafe AI Jev (Decisions)

**Jev** is TypeSafe AI's first "System One" model. It does not write text: you send a *state* (text or JSON) and a set of named, typed *questions*, and it returns calibrated answers to all of them in one call (reported 70–500 ms, 32K context, output tokens free). OpenTryOn exposes it through the new `decide` service with `JevAdapter`.

Use it for routing, moderation, attribute classification and QC gating over text or structured data (for example product copy, order notes or VLM captions). It has **no image, audio or video input** — for images use the open-weight [Liquid d1](../local-models/liquid-d1.md) models.

:::warning Early access
Jev is waitlisted. TypeSafe paused new sign-ups on 22 Sep 2026; check [console.typesafe.ai](https://console.typesafe.ai) for current status. The model is also served through OpenRouter (`typesafe/jev-1.13`), Vercel AI Gateway and DigitalOcean Inference — set `TYPESAFE_BASE_URL` to a compatible gateway if you use one. Endpoint and field names here follow the published System One API (`POST /v1/systemone`); confirm against your account's docs.
:::

## Authentication

```bash
export TYPESAFE_API_KEY="..."
# export TYPESAFE_BASE_URL="https://api.typesafe.ai"   # default
```

## Question schema

Shared by every `decide` model:

| `type` | Answer | `criteria` |
|---|---|---|
| `noul` | yes/no — returns P(yes), 0–1 | not used |
| `choice` | one option + `probabilities` + `confidence` | object: option → when it applies (≥ 2 options) |
| `score` | probability-weighted level + `legend` | ordered list of 2–10 levels, lowest first |

`questions.json`:

```json
{
  "formal": {"type": "noul", "instructions": "Is this garment formal wear?"},
  "category": {
    "type": "choice",
    "instructions": "Which category is the garment?",
    "criteria": {"dress": "one-piece gowns and dresses", "top": "shirts and blouses", "outerwear": "coats and jackets"}
  },
  "quality": {
    "type": "score",
    "instructions": "How complete is this product description?",
    "criteria": ["missing key facts", "adequate", "complete"]
  }
}
```

## CLI

```bash
opentryon decide --model jev \
  --questions questions.json \
  --state "Red satin evening gown, floor length, size 6, shown with heels"
```

Output is JSON (also saved under `outputs/`): `{"model": ..., "answers": {"formal": {"type": "noul", "noul": 0.93}, "category": {"choice": "dress", "confidence": ..., "probabilities": {...}}, ...}, "usage": {...}}`.

| Flag | Notes |
|---|---|
| `--questions`, `-q` | JSON string or path to a JSON file — required |
| `--state`, `-s` | Text, JSON, or path to a file — required |
| `--jev-model` | `jev-latest` (default), `jev-preview`, `jev-1.13.0` |

## Python

```python
from tryon.api.typesafe import JevAdapter

out = JevAdapter().decide(
    state={"title": "Linen shirt", "description": "Relaxed fit, short sleeve"},
    questions={"season": {"type": "choice", "instructions": "Best season?",
                          "criteria": {"summer": "warm weather", "winter": "cold weather"}}},
)
print(out["answers"]["season"]["choice"])
```

## Notes

- MCP tool: `decide_jev`; key: `TYPESAFE_API_KEY` (shown in the Connect rail as **Typesafe AI (Jev)**).
- "Zero hallucinations" means guaranteed schema-valid answers, not guaranteed-correct ones; the probabilities are calibrated but vendor-reported.
- The `decide` service is named-model-only in the planner: no chat intent routes to it and no defaults change.

See also: [Liquid d1 (local)](../local-models/liquid-d1.md).
