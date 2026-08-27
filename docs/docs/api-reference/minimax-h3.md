---
sidebar_position: 23
title: MiniMax H3 (official API)
description: First-party MiniMax H3 (Hailuo 3) text-to-video and image-to-video via the V2 video_generation API.
keywords:
  - MiniMax H3
  - Hailuo 3
  - MiniMax
  - video generation
  - text-to-video
  - image-to-video
---

# MiniMax H3 (official API)

First-party [MiniMax](https://platform.minimax.io/) **H3** (also marketed as Hailuo 3 / Hailuo-03) video generation with native stereo audio. Uses the **V2** endpoints (`POST /v2/video_generation`, `GET /v2/query/video_generation/{task_id}`). This is a different surface from [Hailuo 2.3](./hailuo.md), which stays on V1.

| CLI model | API `model` | Modes |
|---|---|---|
| `minimax-h3` | `MiniMax-H3` | T2V, first/last-frame I2V, reference-to-video (Python) |

Local open weights: [MiniMax H3 (local Diffusers)](../local-models/minimax-h3.md) (`--model minimax-h3-local`). Local is 768p H3-Base only; this API path is the hosted 2K workflow.

H3 on the API is billed as [pay-as-you-go video](https://platform.minimax.io/docs/guides/pricing-paygo).

## Environment

```bash
export MINIMAX_API_KEY=...   # same key as hailuo-2.3
# export MINIMAX_API_BASE_URL=https://api.minimax.io
```

## CLI

```bash
opentryon video-generate --model minimax-h3 \
  --prompt "A fashion model walking a runway at dusk, camera tracking" \
  --duration 5 --resolution 2K --ratio 16:9

opentryon video-generate --model minimax-h3 \
  --image look.jpg --prompt "Gentle fabric motion as the model turns" \
  --duration 6 --resolution 2K

# Last-frame only, or first + last
opentryon video-generate --model minimax-h3 \
  --prompt "Walk toward camera, stop on the mark" \
  --last-frame end.jpg --duration 5
```

| Flag | Notes |
|---|---|
| `--duration` | Integer **4–15** seconds (default 5) |
| `--resolution` | `768P` or `2K` (default **2K**) |
| `--ratio` | Required for T2V: `21:9`, `16:9`, `4:3`, `1:1`, `3:4`, `9:16`. **Cannot** be `adaptive`. I2V ignores ratio (always adaptive from the keyframe). |
| `--image` | First frame (switches to I2V) |
| `--last-frame` | Last frame (alone or with `--image`) |

Prompt is required (max 7000 characters).

## Python

```python
from tryon.api.minimax import MiniMaxH3Adapter

adapter = MiniMaxH3Adapter()
video = adapter.generate_text_to_video(
    prompt="A fashion model walking a runway at dusk, camera tracking",
    duration=5,
    resolution="2K",
    ratio="16:9",
)
open("h3.mp4", "wb").write(video)

# First + last frame
video = adapter.generate_image_to_video(
    image="look.jpg",
    prompt="Gentle turn toward the camera",
    last_frame="end.jpg",
    duration=6,
)

# Reference-to-video (mutually exclusive with first/last frames)
video = adapter.generate_text_to_video(
    prompt="Character speaks: follow the wind. Voice follows reference audio 1.",
    reference_image=["subject.jpg"],
    reference_audio=["voice.mp3"],
    duration=5,
    resolution="2K",
)
```

## Notes

- Auth is `Authorization: Bearer {MINIMAX_API_KEY}`.
- Jobs are async: create returns `task_id`, poll until `succeeded`, then download `task.content.url` (time-limited).
- Image-to-video and reference-to-video cannot be mixed in one request.
- MCP tool: `video_generate_minimax_h3` (generated from the registry — no hand-written wrapper).
