---
sidebar_position: 24
title: Runway Gen-4.5
description: First-party Runway Gen-4.5 text-to-video and image-to-video API.
---

# Runway Gen-4.5 (official API)

First-party [Runway](https://docs.dev.runwayml.com/) Gen-4.5 video generation. **API only** — Gen-4.5 weights are not publicly released for local deployment.

| CLI model | API `model` |
|---|---|
| `runway-gen4.5` | `gen4.5` |

## Environment

```bash
export RUNWAYML_API_SECRET=...   # https://dev.runwayml.com/
# export RUNWAY_API_BASE_URL=https://api.dev.runwayml.com
```

## CLI

```bash
opentryon video-generate --model runway-gen4.5 \
  --prompt "A golden retriever running through wildflowers at sunset" \
  --duration 5 --ratio 1280:720

opentryon video-generate --model runway-gen4.5 \
  --image cover.jpg --prompt "A slow dolly-in shot" --duration 5
```

## Python

```python
from tryon.api.runway import RunwayVideoAdapter

adapter = RunwayVideoAdapter()
video = adapter.generate_text_to_video(
    prompt="A fashion model walking through mist",
    duration=5,
    ratio="1280:720",
)
open("out.mp4", "wb").write(video)
```
