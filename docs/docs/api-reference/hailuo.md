---
sidebar_position: 22
title: Hailuo 2.3 (MiniMax API)
description: First-party MiniMax Hailuo 2.3 text-to-video and image-to-video.
---

# Hailuo 2.3 (MiniMax official API)

First-party [MiniMax](https://platform.minimax.io/) Hailuo 2.3 video generation. **API only for this model** — Hailuo 2.3 has no open weights. MiniMax **H3** (Hailuo 3) is a separate dual-path: [API](./minimax-h3.md) (`--model minimax-h3`, plus fast `--model minimax-h3-max`) and [local Diffusers](../local-models/minimax-h3.md) (`--model minimax-h3-local`). Fal-hosted H3 Max (T2V / I2V / R2V) is `--model fal-h3-max`.

| CLI model | API model | Modes |
|---|---|---|
| `hailuo-2.3` | `MiniMax-Hailuo-2.3` (default) or `MiniMax-Hailuo-2.3-Fast` | T2V / I2V |

## Environment

```bash
export MINIMAX_API_KEY=...
```

## CLI

```bash
opentryon video-generate --model hailuo-2.3 \
  --prompt "A fashion model walking a runway [Tracking shot]" \
  --duration 6 --resolution 1080P

opentryon video-generate --model hailuo-2.3 \
  --image look.jpg --prompt "Gentle turn [Push in]" --duration 6
```

## Python

```python
from tryon.api.minimax import HailuoVideoAdapter

adapter = HailuoVideoAdapter()
video = adapter.generate_text_to_video(
    prompt="A mouse runs toward the camera, smiling",
    duration=6,
    resolution="1080P",
)
open("out.mp4", "wb").write(video)
```
