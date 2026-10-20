---
sidebar_position: 30
title: Inception Mercury Decide
description: Calibrated noul, choice, and score decisions from Inception Labs Mercury Decide via POST /v1/decisions.
keywords:
  - Mercury Decide
  - Inception Labs
  - decision model
  - classification
  - routing
  - noul
---

# Inception Mercury Decide

**Mercury Decide** evaluates named questions against shared **state** and returns
typed, calibrated answers (`noul`, `choice`, `score`) in one call. OpenTryOn
exposes it on the **`decide`** service with `MercuryDecideAdapter`.

Unlike Mercury 3 chat, Decide uses **`POST /v1/decisions`** with model
`mercury-decide` — no streaming, no tool calling. Only **input tokens** are
billed; output tokens appear in `usage` but are free.

| | |
|---|---|
| **Registry id** | `mercury-decide` |
| **Adapter** | `MercuryDecideAdapter` |
| **Auth** | `INCEPTION_API_KEY` (same key as [Mercury 3](mercury-3)) |
| **Endpoint** | `https://api.inceptionlabs.ai/v1/decisions` |

## Question schema

Same `noul` / `choice` / `score` shape as other `decide` models (see
[Typesafe Jev](typesafe-jev.md)). OpenTryOn validates questions with
`load_questions` — each question needs a non-empty `instructions` field even
though the upstream API allows `null`.

## CLI

```bash
export INCEPTION_API_KEY="..."

opentryon decide --model mercury-decide \
  --questions questions.json \
  --state "Customer message: duplicate charge on my card." \
  --dry-run

opentryon decide --model mercury-decide \
  --questions questions.json \
  --state "Screenshot of checkout after Pay." \
  --image checkout.png
```

`--image` paths are converted to **base64 data URLs** (PNG/JPEG/WebP/GIF). Remote
`http(s)` image URLs are **not** supported by Mercury Decide — use local files.

## Python

```python
from tryon.api.inception import MercuryDecideAdapter

adapter = MercuryDecideAdapter()
out = adapter.decide(
    state={"message": "Please refund the duplicate charge."},
    questions={
        "billing": {"type": "noul", "instructions": "Is this about billing?"},
        "team": {
            "type": "choice",
            "instructions": "Which team owns this?",
            "criteria": {"billing": "payments", "support": "other"},
        },
    },
)
print(out["answers"])
```

## MCP

Tool: `decide_mercury_decide`. Restart MCP after upgrading OpenTryOn.

## See also

- [Decisions capability](https://docs.inceptionlabs.ai/capabilities/decisions)
- [Create a decision (API)](https://docs.inceptionlabs.ai/api-reference/decisions/create-a-decision)
- [Mercury 3 chat](mercury-3.md)
