---
sidebar_position: 24
title: MiniMax H3-Image (official API)
description: First-party MiniMax H3-Image text-to-image and 1–16 reference editing via the Open Platform image API.
keywords:
  - MiniMax H3-Image
  - MiniMax
  - image generation
  - image edit
---

# MiniMax H3-Image (official API)

First-party [MiniMax H3-Image](https://platform.minimax.io/docs/guides/image-generation) — text-to-image and reference-image editing (1–16 images). Same **`MINIMAX_API_KEY`** as [Hailuo 2.3](./hailuo.md), [MiniMax H3 video](./minimax-h3.md), and `minimax-h3-max`.

| CLI model | API `model` | Services |
|---|---|---|
| `minimax-h3-image` | `MiniMax-H3-Image` (default) or `MiniMax-H3-Image-Highspeed` (`--model-version h3-image-highspeed` or `MiniMax-H3-Image-Highspeed`) | `generate`, `edit` |

Local open weights: [MiniMax H3-Image (local)](../local-models/minimax-h3-image.md) (`--model minimax-h3-image-local`).

**Not** the same product as [MiniMax H3 video](./minimax-h3.md) (`--model minimax-h3` on `video-generate`).

## Environment

```bash
export MINIMAX_API_KEY=...
# Global (default): https://api.minimax.io
# Mainland China keys: export MINIMAX_API_BASE_URL=https://api.minimax.cn
```

With the default URL response, the adapter downloads successful images before links expire. Mixed batches: successful images are saved and per-image failures are reported as warnings (see #171).

## CLI

Text-to-image (prompt enhancement on by default):

```bash
opentryon generate --model minimax-h3-image \
  --prompt "Editorial flat lay of a linen blazer on stone, soft window light" \
  --aspect-ratio 3:4 --area 2K

opentryon generate --model minimax-h3-image \
  --prompt "Exact brand color swatch layout" \
  --disable-prompt-enhanced --size 2048x2048
```

Highspeed tier:

```bash
opentryon generate --model minimax-h3-image \
  --model-version h3-image-highspeed \
  --prompt "Quick moodboard frame, neutral backdrop"
```

Multi-reference edit (prompt enhancement always on):

```bash
opentryon edit --model minimax-h3-image \
  --images model.jpg garment.png \
  --prompt "Put the garment from image 2 on the person in image 1, keep the studio background"
```

## API notes

| Topic | Detail |
|------|--------|
| Endpoints | `POST /v1/images/generations`, `POST /v1/images/edits` |
| Timeout | Server waits up to **600s** — set the HTTP client timeout ≥ 600s |
| Retries | **Not idempotent** — failed retries can double-bill; adapter uses `allow_redirects=False` on POST |
| `n` | Up to **10** images per request (T2I and edit) |
| `size` | `auto`, `WIDTHxHEIGHT`, or `aspect_ratio` + `area` (`1K` / `2K` / `4K`) |
| Partial failures | Response `data[]` may mix successes and per-image errors |

## Python

```python
from tryon.api.minimax import MiniMaxH3ImageAdapter

adapter = MiniMaxH3ImageAdapter()
images = adapter.generate_text_to_image(
    prompt="A fashion still life with ceramic vase and silk scarf",
    aspect_ratio="16:9",
    area="4K",
)
images[0].save("out.png")
```

## See also

- [MiniMax H3 (video API)](./minimax-h3.md)
- [Hailuo 2.3](./hailuo.md)
- [Global API reference](https://platform.minimax.io/docs/api-reference/image-generation-h3-generations)
- [Mainland China API reference](https://platform.minimax.cn/docs/api-reference/image-generation-h3-generations)
- Planner pins: `minimax h3 image`, `h3 image` → `minimax-h3-image` (distinct from `minimax h3` video)