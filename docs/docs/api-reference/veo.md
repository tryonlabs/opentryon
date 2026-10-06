---
sidebar_position: 7
title: Google Veo 3.1 (Video)
description: Text-to-video, image-to-video, first/last-frame and reference-image generation with Google Veo 3.1 (Generate, Fast, Lite).
keywords:
  - Veo 3.1
  - Veo 3.1 Lite
  - Google video generation
  - first and last frame
  - reference images
---

# Google Veo 3.1 (Video)

`VeoAdapter` wraps Google's Veo 3.1 family through the Gemini API (`models.generate_videos`, polled until done).

| Model id | Notes |
|----------|-------|
| `veo-3.1-generate-preview` (default) | Highest quality; 720p / 1080p / 4k |
| `veo-3.1-fast-generate-preview` | Faster, cheaper; 720p / 1080p / 4k |
| `veo-3.1-lite-generate-preview` | Lowest cost; **720p / 1080p only, no reference images** |

:::warning Veo 3.0 retired
`veo-3.0-generate-001` and `veo-3.0-fast-generate-001` were shut down on 30 Jun 2026. The adapter now rejects them with a clear error.
:::

## Authentication

```bash
export GEMINI_API_KEY="your_api_key"   # same key as Nano Banana / Gemini Omni
```

## Rules enforced by the adapter

- `duration_seconds`: `"4"`, `"6"` or `"8"`.
- 1080p and 4k require `duration_seconds="8"`.
- First + last frame and reference-image modes require 8 s; reference images also require 16:9, at most 3 images, and a non-Lite model.

## CLI / MCP

```bash
# Text-to-video
opentryon video-generate --model veo --prompt "A model walking a runway" --duration 8 --resolution 4k

# Image-to-video
opentryon video-generate --model veo --prompt "Slow push-in" --image look.jpg

# First + last frame
opentryon video-generate --model veo --prompt "Dress changes colour" \
  --image first.jpg --last-image last.jpg --duration 8

# Reference images (up to 3)
opentryon video-generate --model veo --prompt "Editorial walk" \
  --reference-image a.jpg b.jpg --duration 8 --aspect-ratio 16:9

# Cheaper Lite tier
opentryon video-generate --model veo --prompt "Lookbook loop" \
  --model-version veo-3.1-lite-generate-preview
```

MCP tool: `video_generate_veo`.

## Python

```python
from tryon.api.veo import VeoAdapter

adapter = VeoAdapter()
video = adapter.generate_text_to_video(
    prompt="A cinematic runway shot", duration_seconds="8", resolution="1080p",
)
open("veo.mp4", "wb").write(video)

video = adapter.generate_image_to_video(
    image="first.jpg", last_image="last.jpg", prompt="Smooth transition", duration_seconds="8",
)
```

Methods: `generate_text_to_video` (optionally `reference_images=`), `generate_image_to_video` (optionally `last_image=`), `generate_video_with_references`, `generate_video_with_frames`.

## See also

- [Gemini Omni 1.1 Flash](gemini-omni) · [Seedance](seedance-seedream) · [Official docs](https://ai.google.dev/gemini-api/docs/video)

Veo is cloud-only; there are no open weights.
