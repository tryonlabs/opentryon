---
sidebar_position: 21
title: LTX-2.5 (official API)
description: First-party LTX API for LTX-2.5 Fast / Pro text-to-video and image-to-video with synced audio.
keywords:
  - LTX
  - LTX-2.5
  - Lightricks
  - video generation
  - text-to-video
  - image-to-video
---

# LTX-2.5 (official API)

First-party [LTX API](https://docs.ltx.video/) for **LTX-2.5 Fast** and **Pro**. Generates video with synchronized audio. OpenTryOn defaults to the **async V2** job API (submit → poll → download).

| CLI model | API `model` | Best for |
|---|---|---|
| `ltx-2.5-api` | `ltx-2-5-pro` (default) or `ltx-2-5-fast` | Hosted T2V / I2V, up to 4K on Fast |

Local open weights: [LTX-2.5 (local Diffusers)](../local-models/ltx-2.5.md) (`--model ltx-2.5`).

## Environment

```bash
export LTX_API_KEY=...          # https://console.ltx.io
# export LTX_API_BASE_URL=https://api.ltx.io
```

## CLI

```bash
opentryon video-generate --model ltx-2.5-api \
  --prompt "A fashion model walking a runway, soft studio light, camera tracking" \
  --model-version ltx-2-5-pro \
  --duration 8 --resolution 1920x1080 --fps 24

# Fast tier + automatic duration
opentryon video-generate --model ltx-2.5-api \
  --prompt "Lookbook: wide establishing shot, then close-up of fabric detail" \
  --model-version ltx-2-5-fast \
  --duration auto --resolution 1280x720

# Image-to-video
opentryon video-generate --model ltx-2.5-api \
  --image look.jpg \
  --prompt "Gentle turn, fabric motion, ambient atelier sound" \
  --duration 8 --resolution 1280x720
```

## Python

```python
from tryon.api.ltx import LTXVideoAdapter

adapter = LTXVideoAdapter()  # reads LTX_API_KEY
video = adapter.generate_text_to_video(
    prompt="A majestic eagle soaring through clouds at sunset",
    model="ltx-2-5-pro",
    duration=8,
    resolution="1920x1080",
)
open("out.mp4", "wb").write(video)

video = adapter.generate_image_to_video(
    image="look.jpg",
    prompt="Subject turns and smiles, soft breeze",
    duration=8,
    resolution="1280x720",
)
```

## Notes

- Resolutions / FPS / duration limits differ by Fast vs Pro — see [LTX-2.5 support matrix](https://docs.ltx.video/models/ltx-2-5).
- `--duration auto` sends `duration: null` (automatic length from the prompt).
- `--no-audio` disables synced audio.
- Prefer async (default) for production; set `use_async=False` on the adapter for the sync V1 endpoints.
