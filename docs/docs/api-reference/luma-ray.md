---
sidebar_position: 18
title: Luma Ray 3.2
description: Luma Agents API video generation with Ray 3.2 (T2V, I2V, HDR).
keywords:
  - Luma
  - Ray 3.2
  - Agents API
  - video generation
---

# Luma Ray 3.2

[Ray 3.2](https://lumalabs.ai/news/introducing-ray-3-2) via the [Luma Agents API](https://docs.agents.lumalabs.ai/guides/videos/).

Legacy Dream Machine Ray 2 models remain under `opentryon video-generate --model luma-video`.

## Environment

```bash
export LUMA_AGENTS_API_KEY=...   # preferred
# falls back to LUMA_AI_API_KEY if Agents key unset
```

## Variants

| Model | Notes |
|---|---|
| `ray-3.2` | Current Agents API model (default) |

Resolutions: `360p`, `540p`, `720p`, `1080p`. Durations: `5s`, `10s`.

## CLI

```bash
opentryon video-generate --model luma-ray-3.2 \
  --prompt "Slow dolly through a misty greenhouse" \
  --resolution 720p --duration 5s --aspect-ratio 16:9

opentryon video-generate --model luma-ray-3.2 \
  --image start.jpg --end-image end.jpg \
  --prompt "Character turns toward camera" --hdr
```

## Python

```python
from tryon.api.lumaAI import LumaRay32Adapter

adapter = LumaRay32Adapter()
video = adapter.generate_text_to_video(
    prompt="Cinematic tracking shot of a runway",
    resolution="1080p",
    duration="5s",
)
open("ray32.mp4", "wb").write(video)
```
