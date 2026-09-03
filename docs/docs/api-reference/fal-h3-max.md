---
sidebar_position: 24
title: MiniMax H3 Max (Fal)
description: Third-party Fal hoster for MiniMax H3 Max — text-to-video, image-to-video, and reference-to-video.
keywords:
  - Fal
  - MiniMax H3 Max
  - third-party
  - video generation
  - reference-to-video
---

# MiniMax H3 Max (Fal)

OpenTryOn’s **first third-party hoster** adapter. [Fal](https://fal.ai/minimax-h3-max) jointly released MiniMax H3 Max with MiniMax and hosts a post-trained stack with **T2V, I2V, and reference-to-video**.

This is **not** the MiniMax first-party V2 API. Official MiniMax H3 Max (`--model minimax-h3-max`, `MINIMAX_API_KEY`) is T2V / first-last I2V only. Use Fal when you want R2V or Fal’s queue.

| CLI model | Host | Modes | Key |
|---|---|---|---|
| `minimax-h3-max` | MiniMax V2 | T2V, I2V | `MINIMAX_API_KEY` |
| `fal-h3-max` | Fal queue | T2V, I2V, **R2V** | `FAL_KEY` |
| `minimax-h3` | MiniMax V2 | T2V, I2V, R2V (Python), 2K | `MINIMAX_API_KEY` |

No open weights for H3 Max. Local H3-Base is `--model minimax-h3-local`.

Docs: [T2V](https://fal.ai/models/minimax/h3-max/text-to-video/api), [I2V](https://fal.ai/models/minimax/h3-max/image-to-video/api), [R2V](https://fal.ai/models/minimax/h3-max/reference-to-video/api), [queue](https://docs.fal.ai/model-apis/inference/queue).

## Environment

```bash
export FAL_KEY=...          # https://fal.ai/dashboard/keys
# export FAL_API_KEY=...    # alias
# export FAL_QUEUE_BASE_URL=https://queue.fal.run
```

Auth header is `Authorization: Key {FAL_KEY}` (not Bearer).

## CLI

```bash
opentryon video-generate --model fal-h3-max \
  --prompt "A fashion model walking a runway at dusk, camera tracking" \
  --duration 5 --resolution 768P --ratio 16:9

opentryon video-generate --model fal-h3-max \
  --image look.jpg --prompt "Gentle fabric motion as the model turns" \
  --duration 6

opentryon video-generate --model fal-h3-max \
  --prompt "Walk toward camera, stop on the mark" \
  --last-frame end.jpg

opentryon video-generate --model fal-h3-max \
  --prompt "Image 1 is the model. Keep her identity while she walks the runway." \
  --reference-image look.jpg \
  --duration 5 --resolution 768P
```

| Flag | Notes |
|---|---|
| `--duration` | Integer **5–15** seconds (default 5) |
| `--resolution` | `480P` or `768P` (default **768P**) |
| `--ratio` | T2V: `21:9`, `16:9`, `4:3`, `1:1`, `3:4`, `9:16` (not `adaptive`). R2V may use `adaptive`. I2V follows the keyframe. |
| `--image` | First frame (switches to I2V) |
| `--last-frame` | Last frame (alone or with `--image`) |
| `--reference-image` / `--reference-video` / `--reference-audio` | R2V lists. At most 12 files total. Audio cannot be the only reference. Mutually exclusive with `--image`. |
| `--prompt-expansion` | `balanced` (default) or `quality` |
| `--no-safety-checker` | Disable Fal’s safety checker |
| `--seed` | Optional |

## Python

```python
from tryon.api.fal import FalH3MaxAdapter

adapter = FalH3MaxAdapter()
open("t2v.mp4", "wb").write(
    adapter.generate_text_to_video(
        prompt="A fashion model walking a runway at dusk",
        duration=5,
        resolution="768P",
        ratio="16:9",
    )
)
open("i2v.mp4", "wb").write(
    adapter.generate_image_to_video(
        image="look.jpg",
        prompt="Gentle turn toward the camera",
        last_frame="end.jpg",
    )
)
open("r2v.mp4", "wb").write(
    adapter.generate_text_to_video(
        prompt="Image 1 is the model. Keep her identity while she walks.",
        reference_image=["look.jpg"],
    )
)
```

## Notes

- Jobs go through Fal’s **queue** (`POST https://queue.fal.run/minimax/h3-max/...` → poll `status_url` → download `video.url`).
- MCP tool: `video_generate_fal_h3_max` (generated from the registry).
- Planner: `fal h3 max` / `fal-h3-max` pin this id. A bare `h3 max` still pins first-party `minimax-h3-max`.
