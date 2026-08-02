---
sidebar_position: 8
title: Pruna AI
description: Pruna P-Image, P-Image-Edit, P-Image-Upscale, P-Image-Try-On, P-Video, P-Video-Replace, P-Video-Avatar, and P-Video-Animate
keywords:
  - pruna
  - p-image
  - p-image-edit
  - p-image-upscale
  - p-image-try-on
  - p-video
  - p-video-replace
  - p-video-avatar
  - p-video-animate
  - virtual try-on
---

# Pruna AI

OpenTryOn integrates Pruna's unified predictions API (`POST /v1/predictions` with a `Model` header) through a shared client in `tryon.api.pruna.client.PrunaClient`.

| Model | CLI | Adapter | Role |
|---|---|---|---|
| `p-image` | `generate --model p-image` | `PImageAdapter` | Ultra-fast text-to-image |
| `p-image-edit` | `edit --model p-image-edit` | `PImageEditAdapter` | Edit / compose 1–5 images |
| `p-image-upscale` | `edit --model p-image-upscale` | `PImageUpscaleAdapter` | Upscale to 1–128 MP |
| `p-image-try-on` | `vton --model p-image-tryon` | `PImageTryOnAdapter` | Multi-garment virtual try-on |
| `p-video` | `video-generate --model p-video` | `PVideoAdapter` | T2V / I2V (+ optional audio) |
| `p-video-replace` | `video-generate --model p-video-replace` | `PVideoReplaceAdapter` | Identity swap in a source clip |
| `p-video-avatar` | `video-generate --model p-video-avatar` | `PVideoAvatarAdapter` | Talking-head from portrait + script/audio |
| `p-video-animate` | `video-generate --model p-video-animate` | `PVideoAnimateAdapter` | Animate a subject with source motion |

**Auth:** `PRUNA_API_KEY` (optional `PRUNA_BASE_URL`). Key is sent as the `apikey` header.

**Docs:** [Pruna model guides](https://docs.api.pruna.ai/guides/models)

Ideogram-via-Pruna is skipped — use `opentryon generate --model ideogram` instead.

## Shared client

All adapters upload local files via `/v1/files`, create predictions with `Try-Sync: true` by default, and poll `/v1/predictions/status/{id}` when needed. Try-on lives under `tryon.api.vton` for historical reasons but reuses the same client; image/video models live in `tryon.api.pruna`.

## Authentication

```bash
export PRUNA_API_KEY="your_api_key"
# optional:
# export PRUNA_BASE_URL="https://api.pruna.ai"
```

## CLI examples

```bash
# Text-to-image
opentryon generate --model p-image \
  --prompt "editorial fashion still, soft window light" \
  --aspect-ratio 3:4

# Multi-image edit
opentryon edit --model p-image-edit \
  --images person.jpg garment.jpg \
  --prompt "Dress the person in the garment, studio lighting"

# Upscale
opentryon edit --model p-image-upscale \
  --image result.jpg --target 8 --enhance-details

# Multi-garment try-on
opentryon vton --model p-image-tryon \
  --person-image person.jpg \
  --garment-image top.jpg --garment-image bottoms.jpg

# Text / image to video
opentryon video-generate --model p-video \
  --prompt "model walks toward camera, soft breeze" \
  --duration 5 --resolution 720p

opentryon video-generate --model p-video \
  --prompt "gentle head turn and smile" \
  --image still.jpg --duration 5

# Identity replace in video
opentryon video-generate --model p-video-replace \
  --video source.mp4 \
  --images identity.jpg \
  --instruction-prompt "Place the reference person into the video"

# Talking-head avatar (script or audio)
opentryon video-generate --model p-video-avatar \
  --image portrait.jpg \
  --voice-script "Welcome to our spring collection." \
  --voice "Zephyr (Female)"

opentryon video-generate --model p-video-avatar \
  --image portrait.jpg \
  --audio speech.mp3

# Animate subject with source motion
opentryon video-generate --model p-video-animate \
  --video driver.mp4 \
  --image subject.jpg \
  --instruction-prompt "Keep the subject’s outfit and lighting"
```

## Python quick start

```python
from dotenv import load_dotenv
load_dotenv()

from tryon.api.pruna import (
    PImageAdapter,
    PImageEditAdapter,
    PImageUpscaleAdapter,
    PVideoAdapter,
    PVideoAnimateAdapter,
    PVideoAvatarAdapter,
    PVideoReplaceAdapter,
)
from tryon.api.vton import PImageTryOnAdapter

# Generate
images = PImageAdapter().generate_text_to_image(
    prompt="luxury knitwear flatlay on marble",
    aspect_ratio="1:1",
)
images[0].save("out.png")

# Edit
edited = PImageEditAdapter().generate_image_edit(
    prompt="Replace the background with a clean studio",
    image=["photo.jpg"],
)

# Upscale
hires = PImageUpscaleAdapter().upscale(image="out.png", target=8)

# Try-on
tryon = PImageTryOnAdapter().generate_and_decode(
    person_image="person.jpg",
    garment_images=["top.jpg", "bottoms.jpg"],
)

# Video
mp4 = PVideoAdapter().generate_text_to_video(
    prompt="runway walk, cinematic tracking shot",
    duration=5,
    resolution="720p",
)
open("clip.mp4", "wb").write(mp4)

replaced = PVideoReplaceAdapter().generate_video_replace(
    video="source.mp4",
    images=["identity.jpg"],
)

avatar = PVideoAvatarAdapter().generate_video_avatar(
    image="portrait.jpg",
    voice_script="Welcome to our spring collection.",
)

animated = PVideoAnimateAdapter().generate_video_animate(
    video="driver.mp4",
    image="subject.jpg",
)
```

## Parameter notes

### P-Image
- Required: `prompt`
- Optional: `aspect_ratio` (incl. `custom` + `width`/`height`), `seed`, `prompt_upsampling`, LoRA fields

### P-Image-Edit
- Required: `prompt`, 1–5 images
- Optional: `aspect_ratio` (default `match_input_image`), `turbo` (default `True`), `seed`

### P-Image-Upscale
- Required: `image`
- Optional: `target` MP (1–128, default 4), `output_format`, `enhance_details`, `enhance_realism`

### P-Image-Try-On
- Required: person image + ≥1 garment image (up to 11; 6 recommended)
- Optional: `prompt`, `turbo`, `reference_pose`, `output_format` / `output_quality`
- Pricing (per Pruna): $0.015 first garment + $0.008 each additional

### P-Video
- Required: `prompt`
- Optional: `image` (I2V), `audio` (duration follows audio), `duration` 1–20s, `resolution` 720p/1080p, `fps` 24/48, `draft`, `prompt_upsampling`

### P-Video-Replace
- Required: source `video`, 1–3 identity `images`
- Optional: `instruction_prompt`, `resolution`, `target_fps`, `turbo`, audio flags

### P-Video-Avatar
- Required: portrait `image`, plus `voice_script` and/or `audio` (audio wins if both)
- Optional: `voice`, `voice_language`, `resolution`, `video_prompt`, `voice_prompt`, negative-prompt fields

### P-Video-Animate
- Required: source `video`, subject `image`
- Optional: `instruction_prompt`, `resolution`, `target_fps`, `turbo`, audio flags

## See Also

- [API Reference Overview](overview)
- [Unified CLI](../getting-started/cli)
- [Pruna docs](https://docs.api.pruna.ai/guides/models)
