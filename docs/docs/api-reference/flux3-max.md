---
sidebar_position: 8
title: FLUX 3 Max
description: Black Forest Labs FLUX 3 Max — fastest FLUX 3 video tier on the unified BFL video API (version=max).
keywords:
  - FLUX 3 Max
  - FLUX 3 Video
  - video generation
  - BFL AI
---

# FLUX 3 Max

[FLUX 3 Max](https://bfl.ai/models/flux-3-video#flux-3-max) is Black Forest Labs' fastest, highest-quality **video** tier in the FLUX 3 family. It uses the same async endpoint as [FLUX 3 Video](flux3-video) (`POST https://api.bfl.ai/v1/flux-3-video`) with the harness **`version`** field set to **`max`**.

OpenTryOn exposes it as **`flux3-max`** on `video-generate` (same `BFL_API_KEY` as `flux3-image`, `flux3-video`, and FLUX.2).

This is **not** FLUX 3 Image (still frames) and not FLUX.2 [max] (the previous-generation image model). For general-purpose FLUX 3 video with stylistic range and draft preview, use **`flux3-video`** (`version=latest` by default).

## Prerequisites

```bash
BFL_API_KEY=your_bfl_api_key
# Optional if BFL renames the harness tag:
# BFL_FLUX3_MAX_VERSION=max
```

## CLI

Same flags as [FLUX 3 Video](flux3-video) except there is no `--version` flag (Max is pinned).

```bash
opentryon video-generate --model flux3-max \
  --prompt "Runway walk, soft key light, camera tracking" \
  --aspect-ratio 9:16 --duration 10 --resolution fhd

opentryon video-generate --model flux3-max \
  --prompt "She turns slowly toward camera" \
  --image data/model-1.jpg

opentryon video-generate --model flux3-max --prompt "test" --dry-run
```

On **`flux3-video`** you can opt into Max explicitly with `--version max`.

## Python

```python
from tryon.api import Flux3MaxVideoAdapter

adapter = Flux3MaxVideoAdapter()
mp4 = adapter.generate_text_to_video(
    prompt="Editorial runway walk, synchronized ambience",
    aspect_ratio="16:9",
    duration=10,
    resolution="fhd",
)
with open("outputs/flux3_max.mp4", "wb") as f:
    f.write(mp4)
```

## MCP

After registry changes, restart the MCP server. Tools are generated from the registry:

- `video_generate_flux3_max`

Unlocks with `BFL_API_KEY` in the OpenTryOn `.env`.

## API summary

- **Submit:** `POST https://api.bfl.ai/v1/flux-3-video` with `version: "max"` plus the usual `mode` / `prompt` / media fields
- **Poll:** `polling_url` until `status` is `Ready`
- **Result:** `result.sample` — signed MP4 URL

See the [BFL FLUX 3 video docs](https://docs.bfl.ml/flux_3/flux3_video) and [API reference](https://docs.bfl.ml/api-reference/utility/generate-a-video-with-flux-3).
