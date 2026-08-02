---
sidebar_position: 17
title: Kling Video (3.0 / Omni / Turbo)
description: Kling AI Open Platform video generation — Kling 3.0, 3.0 Omni, and 2.5 Turbo.
keywords:
  - Kling 3.0
  - Kling Omni
  - Kling Turbo
  - video generation
  - Kuaishou
---

# Kling Video (3.0 / Omni / Turbo)

Official [Kling AI Open Platform](https://kling.ai/document-api/guides/get-started/overview) video models (JWT auth, same keys as Kolors VTON).

| CLI model | API `model_name` | Best for |
|---|---|---|
| `kling-v3` | `kling-v3` | High-quality T2V / I2V, 3–15s, audio |
| `kling-v3-omni` | `kling-v3-omni` | Multimodal refs, elements, Omni workflows |
| `kling-v2-5-turbo` | `kling-v2-5-turbo` | Fast previews |

## Environment

```bash
export KLING_AI_API_KEY=...
export KLING_AI_SECRET_KEY=...
# export KLING_AI_BASE_URL=https://api-singapore.klingai.com
```

## CLI

```bash
opentryon video-generate --model kling-v3 \
  --prompt "Slow pan across a couture atelier" \
  --duration 5 --mode pro --aspect-ratio 16:9 --sound on

opentryon video-generate --model kling-v3-omni \
  --prompt "Multi-shot lookbook" --duration 8 --mode pro

opentryon video-generate --model kling-v2-5-turbo \
  --prompt "Quick product spin" --duration 5 --mode std

# Image-to-video
opentryon video-generate --model kling-v3 \
  --image start.jpg --prompt "Subject turns and smiles" --duration 5
```

## Python

```python
from tryon.api.kling_video import KlingVideoAdapter

adapter = KlingVideoAdapter(model="kling-v3")
video = adapter.generate_text_to_video(
    prompt="A model walking a marble corridor",
    duration="5",
    mode="pro",
    sound="on",
)
open("kling.mp4", "wb").write(video)
```

## Endpoints used

- `POST /v1/videos/text2video`
- `POST /v1/videos/image2video`
- `POST /v1/videos/omni-video` (Omni)
- Task polling via `GET /v1/videos/{kind}/{task_id}`
