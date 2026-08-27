---
sidebar_position: 20
title: Ideogram 4.0
description: Ideogram 4.0 text-to-image with Turbo / Default / Quality rendering speeds.
keywords:
  - Ideogram 4.0
  - typography
  - text to image
---

# Ideogram 4.0

Hosted Ideogram 4.0 via [`POST /v1/ideogram-v4/generate`](https://developer.ideogram.ai/ideogram-api/api-overview).

For **P-Image-Ideogram** (Pruna × Ideogram, five `thinking` levels), use [`generate --model p-image-ideogram`](p-image-ideogram) and `PRUNA_API_KEY` — that is a different model, not this Ideogram 4.0 adapter.

## Environment

```bash
export IDEOGRAM_API_KEY=...
```

## Rendering speeds

| Speed | Typical use |
|---|---|
| `TURBO` | Fast / cheapest |
| `DEFAULT` | Balanced (default) |
| `QUALITY` | Highest fidelity |

## CLI

```bash
opentryon generate --model ideogram \
  --prompt 'Poster reading "SUMMER LOOKBOOK 2026"' \
  --rendering-speed QUALITY --aspect-ratio 3:4
```

## Python

```python
from tryon.api.ideogram import IdeogramAdapter

images = IdeogramAdapter().generate_text_to_image(
    prompt='Logo mark "TryOn Labs" on linen texture',
    rendering_speed="QUALITY",
)
images[0].save("ideogram.png")
```
