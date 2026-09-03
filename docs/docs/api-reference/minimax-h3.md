---
sidebar_position: 23
title: MiniMax H3 (official API)
description: First-party MiniMax H3 and H3 Max text-to-video and image-to-video via the V2 video_generation API.
keywords:
  - MiniMax H3
  - MiniMax H3 Max
  - Hailuo 3
  - MiniMax
  - video generation
  - text-to-video
  - image-to-video
---

# MiniMax H3 (official API)

First-party [MiniMax](https://platform.minimax.io/) **H3** (also marketed as Hailuo 3 / Hailuo-03) video generation with native stereo audio. Uses the **V2** endpoints (`POST /v2/video_generation`, `GET /v2/query/video_generation/{task_id}`). This is a different surface from [Hailuo 2.3](./hailuo.md), which stays on V1.

Switch H3 vs **H3 Max** (fast variant) with the CLI model id. Same adapter class, same `MINIMAX_API_KEY`. H3 Max has no open-weight twin.

| CLI model | API `model` | Modes | Resolution | Duration |
|---|---|---|---|---|
| `minimax-h3` | `MiniMax-H3` | T2V, first/last-frame I2V, reference-to-video (Python) | `768P`, `2K` (default 2K) | 4–15s |
| `minimax-h3-max` | `MiniMax-H3-Max` | T2V, first/last-frame I2V only (no R2V) | `480P`, `768P` (default 768P; **no 2K**) | 5–15s |

Local open weights: [MiniMax H3 (local Diffusers)](../local-models/minimax-h3.md) (`--model minimax-h3-local`). Local is 768p H3-Base only; this API path is the hosted 2K workflow. H3 Max is API-only.

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

# Fast variant (H3 Max) — 768P default, no 2K / no reference-to-video
opentryon video-generate --model minimax-h3-max \
  --prompt "A fashion model walking a runway at dusk, camera tracking" \
  --duration 5 --resolution 768P --ratio 16:9
```

| Flag | H3 (`minimax-h3`) | H3 Max (`minimax-h3-max`) |
|---|---|---|
| `--duration` | Integer **4–15** seconds (default 5) | Integer **5–15** seconds (default 5; **4s invalid**) |
| `--resolution` | `768P` or `2K` (default **2K**) | `480P` or `768P` (default **768P**) |
| `--ratio` | Required for T2V: `21:9`, `16:9`, `4:3`, `1:1`, `3:4`, `9:16`. **Cannot** be `adaptive`. I2V ignores ratio (always adaptive from the keyframe). | Same |
| `--image` | First frame (switches to I2V) | Same |
| `--last-frame` | Last frame (alone or with `--image`) | Same |

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

# Reference-to-video (H3 only; mutually exclusive with first/last frames)
video = adapter.generate_text_to_video(
    prompt="Character speaks: follow the wind. Voice follows reference audio 1.",
    reference_image=["subject.jpg"],
    reference_audio=["voice.mp3"],
    duration=5,
    resolution="2K",
)

# Fast variant
fast = MiniMaxH3Adapter(model="MiniMax-H3-Max")
open("h3-max.mp4", "wb").write(
    fast.generate_text_to_video(
        prompt="Runway walk at dusk",
        duration=5,
        resolution="768P",
    )
)
```

## Notes

- Auth is `Authorization: Bearer {MINIMAX_API_KEY}`.
- Jobs are async: create returns `task_id`, poll until `succeeded`, then download `task.content.url` (time-limited).
- Image-to-video and reference-to-video cannot be mixed in one request.
- H3 Max on MiniMax does not support reference image / video / audio — use `--model minimax-h3`, or Fal `--model fal-h3-max` ([Fal H3 Max](./fal-h3-max.md)).
- MCP tools: `video_generate_minimax_h3`, `video_generate_minimax_h3_max` (generated from the registry — no hand-written wrappers).
