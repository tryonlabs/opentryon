---
sidebar_position: 16
title: Seedance & Seedream (BytePlus ModelArk)
description: ByteDance Seedance 2.5 video and Seedream 5.0 Pro image generation via BytePlus ModelArk.
keywords:
  - Seedance 2.5
  - Seedream 5.0 Pro
  - BytePlus
  - ModelArk
  - video generation
  - image generation
---

# Seedance & Seedream (BytePlus ModelArk)

Official ByteDance creative models through [BytePlus ModelArk](https://docs.byteplus.com/en/docs/ModelArk/):

| Model | Service | Variants |
|---|---|---|
| **Seedance 2.5** | `video-generate` | `seedance-2-5` (default); also Seedance 2.0 Standard / Fast / Mini |
| **Seedream 5.0 Pro** | `generate` / `edit` | `seedream-5-0-pro` (default); also Lite / 4.x |

Product pages: [Seedance 2.5](https://seed.bytedance.com/en/seedance2_5) · Seedream 5.0 Pro on ModelArk.

## Environment

```bash
export ARK_API_KEY=...
# optional:
# export BYTEPLUS_ARK_BASE_URL=https://ark.ap-southeast.bytepluses.com/api/v3
```

## Variants

### Seedance (video)

| `--model-version` | Notes |
|---|---|
| `seedance-2-5` / `dreamina-seedance-2-5-260628` | Up to ~30s storytelling (official ModelArk id) |
| `seedance-2-0` / `dreamina-seedance-2-0-260128` | Production 2.0 Standard |
| `seedance-2-0-fast` / `dreamina-seedance-2-0-fast-260128` | Faster 2.0 |
| `seedance-2-0-mini` / `dreamina-seedance-2-0-mini-260615` | Lightweight 2.0 |

### Seedream (image)

| `--model-version` | Notes |
|---|---|
| `seedream-5-0-pro` | Precision T2I / edit / multi-ref (default) |
| `seedream-5-0-lite` | Faster / cheaper 5.0 tier |
| `seedream-4-5` / `seedream-4-0` | Prior generation |

## CLI

```bash
# Seedance 2.5 text-to-video
opentryon video-generate --model seedance \
  --prompt "A 10-second runway walk in soft studio light" \
  --duration 10 --resolution 1080p --ratio 16:9

# Image-to-video
opentryon video-generate --model seedance \
  --image person.jpg --prompt "Slow cinematic push-in" --duration 5

# Seedream 5.0 Pro text-to-image
opentryon generate --model seedream \
  --prompt "Editorial product shot of matte black sneakers" --size 2K

# Multi-reference edit / fusion
opentryon edit --model seedream \
  --images person.jpg garment.jpg \
  --prompt "Dress the person in the garment, catalogue lighting"
```

## Python

```python
from tryon.api.byteplus import SeedanceAdapter, SeedreamAdapter

video = SeedanceAdapter().generate_text_to_video(
    prompt="Fashion model walking through a loft apartment",
    duration=8,
    resolution="1080p",
)
open("out.mp4", "wb").write(video)

images = SeedreamAdapter().generate_text_to_image(
    prompt="Minimalist lookbook still, soft daylight",
    size="2K",
)
images[0].save("out.png")
```

## Notes

- Seedance 2.5 public ModelArk id is `dreamina-seedance-2-5-260628` (CLI `--model-version seedance-2-5` maps to it). Activate the model in the BytePlus console before calling.
- Auth uses `Authorization: Bearer $ARK_API_KEY`.
- Async video tasks are polled until completion, then the MP4 is downloaded.
