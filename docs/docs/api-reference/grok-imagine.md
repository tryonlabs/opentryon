---
sidebar_position: 19
title: Grok Imagine (xAI)
description: xAI Grok Imagine Image Quality and Video 1.5 adapters.
keywords:
  - Grok Imagine
  - xAI
  - grok-imagine-video-1.5
  - grok-imagine-image-quality
---

# Grok Imagine (xAI)

| CLI model | API model | Service |
|---|---|---|
| `grok-imagine-image` | `grok-imagine-image-quality` (default) | `generate` |
| `grok-imagine-video` | `grok-imagine-video-1.5` | `video-generate` |

Docs: [Image](https://docs.x.ai/developers/model-capabilities/images/generation) · [Video 1.5](https://docs.x.ai/developers/models/grok-imagine-video-1.5)

## Environment

```bash
export XAI_API_KEY=...
```

## Image variants

| `--model-version` | Notes |
|---|---|
| `grok-imagine-image-quality` | Highest fidelity (default) |
| `grok-imagine-image` | Standard |
| `grok-imagine-image-pro` | Pro tier when available |

## Video

- Duration up to ~15s
- Resolutions: `480p`, `720p`, `1080p` (1080p on 1.5 for T2V/I2V)
- Optional start image for I2V

## CLI

```bash
opentryon generate --model grok-imagine-image \
  --prompt "Collage of London landmarks, stencil street-art style" \
  --aspect-ratio 16:9 --resolution 2k

opentryon video-generate --model grok-imagine-video \
  --prompt "Slow cinematic push-in across a battlefield helmet" \
  --duration 6 --resolution 720p

opentryon video-generate --model grok-imagine-video \
  --image still.png --prompt "Make the water crash and pan out" --duration 12
```
