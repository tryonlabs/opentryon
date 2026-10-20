---
sidebar_position: 7
title: FLUX 3 Video
description: Generate and continue video with Black Forest Labs FLUX 3 — t2v, keyframe i2v, v2v, draft preview, and draft enhance.
keywords:
  - FLUX 3
  - FLUX 3 Video
  - video generation
  - BFL AI
  - image to video
---

# FLUX 3 Video

[FLUX 3 Video](https://docs.bfl.ml/flux_3/flux3_video) is Black Forest Labs' unified async video endpoint: text-to-video, image keyframes, continuation from an existing clip, and a draft → enhance workflow. OpenTryOn exposes it as **`flux3-video`** on `video-generate` (same `BFL_API_KEY` as FLUX 3 Image and FLUX.2). For the **Max** speed/quality tier (`version=max`), see **[FLUX 3 Max](flux3-max)** (`flux3-max`).

## Prerequisites

```bash
BFL_API_KEY=your_bfl_api_key
```

## CLI

```bash
# Text-to-video
opentryon video-generate --model flux3-video \
  --prompt "Runway walk under soft key light, camera tracking" \
  --aspect-ratio 9:16 --duration 8 --resolution fhd

# Image-to-video (optional end frame)
opentryon video-generate --model flux3-video \
  --prompt "She turns slowly toward camera" \
  --image data/model-1.jpg --end-image data/model-2.jpg

# Continue from an existing clip
opentryon video-generate --model flux3-video \
  --prompt "They step into a crowded night market" \
  --video outputs/prior_clip.mp4

# Draft preview, then full-quality enhance (use draft_cache URL or file from the draft result)
opentryon video-generate --model flux3-video \
  --prompt "Fox running through dawn mist" --draft
opentryon video-generate --model flux3-video \
  --draft-cache path/to/draft_cache.bin --resolution fhd

# Dry-run
opentryon video-generate --model flux3-video --prompt "test" --dry-run
```

### Notable flags

| Flag | Default | Notes |
| --- | --- | --- |
| `--aspect-ratio` | `auto` | `21:9` … `9:21` or `auto` |
| `--duration` | `auto` | Whole seconds 5–20 (`auto`); v2v caps at 15 |
| `--resolution` | `hd` | `hd`, `fhd`, `qhd`, `uhd` |
| `--safety-tolerance` | `2` | `0` (strictest) through `7` |
| `--draft` | off | Fast preview; save `draft_cache` from the API result |
| `--no-audio` | audio on | Silent clip |
| `--video` | — | v2v continuation from local path or URL |
| `--draft-cache` | — | `draft_enhance` from a prior draft bundle |
| `--version` | `latest` | `latest` or `max` (Max is also available as `--model flux3-max`) |

**Out of scope here:** [FLUX Video Edit](https://docs.bfl.ml/) at `POST /v1/flux-tools/video-edit-v1` (separate BFL tool; not wired in OpenTryOn yet).

## Python

```python
from tryon.api import Flux3VideoAdapter

adapter = Flux3VideoAdapter()

mp4 = adapter.generate_text_to_video(
    prompt="Editorial runway walk, soft window light",
    aspect_ratio="16:9",
    duration=8,
    resolution="fhd",
)
with open("outputs/flux3_t2v.mp4", "wb") as f:
    f.write(mp4)

mp4 = adapter.generate_image_to_video(
    image="data/model-1.jpg",
    prompt="Gentle turn, fabric motion",
    duration=10,
)
```

## MCP

After registry changes, restart the MCP server. Tools are generated from the registry:

- `video_generate_flux3_video`

## API summary

- **Submit:** `POST https://api.bfl.ai/v1/flux-3-video` with `x-key`
- **Poll:** `polling_url` until `status` is `Ready`
- **Result:** `result.sample` — signed MP4 URL (or base64)

See the [BFL API reference](https://docs.bfl.ml/api-reference/utility/generate-a-video-with-flux-3) for the full request schema.
