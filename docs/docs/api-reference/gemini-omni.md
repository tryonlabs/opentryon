---
sidebar_position: 10
title: Gemini Omni 1.2 Flash (Video)
description: Multimodal video generation, conversational editing and clip extension with Gemini Omni 1.2 Flash
keywords:
  - gemini omni
  - gemini-omni-1.2-flash
  - gemini-omni-1.1-flash
  - video extension
  - video generation
  - conversational editing
  - interactions api
---

# Gemini Omni 1.2 Flash (Video)

The `GeminiOmniAdapter` wraps Google's [Gemini Omni 1.2 Flash](https://ai.google.dev/gemini-api/docs/omni)
model (`gemini-omni-1.2-flash`, GA 5 Nov 2026) for fast multimodal video generation,
conversational video editing and clip extension via the Interactions API.

| | `gemini-omni-1.2-flash` (default) | `gemini-omni-1.1-flash` |
|---|---|---|
| Clip length | 3–15s (`duration`, default 10s) | 3–10s |
| Output | Video with native audio | Video with native audio |
| Video output price | $12.00 per 1M tokens | $17.50 per 1M tokens |
| Status | Stable | Stable, routed to 1.2 from 3 Dec 2026 |

Select 1.1 with `--omni-model gemini-omni-1.1-flash` (or `GeminiOmniAdapter(model=...)`). Prices are Google's published paid-tier rates at the time of writing.

:::warning Preview endpoint deprecated
The earlier `gemini-omni-flash-preview` endpoint was deprecated on 30 Sep 2026.
The adapter defaults to `gemini-omni-1.2-flash` and rejects the old id.
:::

## Overview

Unlike Veo (which uses `models.generate_videos`), Omni uses
`client.interactions.create(...)`. It accepts text, images (and in the broader
Omni family, audio/video inputs) and returns short clips (about 3–15s; 360p / 720p / 1080p / 4k via `resolution`, 720p by default) with natively generated audio. Prior generations can be refined with
natural-language edit turns using `previous_interaction_id`.

**References:**
- [Generate and edit videos with Gemini Omni](https://ai.google.dev/gemini-api/docs/omni)
- [Model card](https://ai.google.dev/gemini-api/docs/models/gemini-omni-flash)
- [DeepMind Gemini Omni](https://deepmind.google/models/gemini-omni/)
- [Launch blog](https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-omni/)

## Authentication

Uses the same key as Nano Banana / Veo:

```bash
export GEMINI_API_KEY="your_api_key"
```

## Quick Start

```python
from dotenv import load_dotenv
load_dotenv()

from tryon.api.omni import GeminiOmniAdapter

adapter = GeminiOmniAdapter()

# Text-to-video
video = adapter.generate_text_to_video(
    prompt="A fashion model walking a runway under soft studio lights",
    aspect_ratio="9:16",
)
with open("outputs/omni_t2v.mp4", "wb") as f:
    f.write(video)

# Image-to-video
video = adapter.generate_image_to_video(
    image="data/model-1.jpg",
    prompt="The model begins walking toward the camera, soft cinematic motion",
    aspect_ratio="16:9",
)

# Conversational edit (reuse the prior interaction id)
edited = adapter.edit_video(
    prompt="Dim the lights and add a slow dolly-in",
    previous_interaction_id=adapter.last_interaction_id,
)
with open("outputs/omni_edit.mp4", "wb") as f:
    f.write(edited)
```

## API Reference

### Class: `GeminiOmniAdapter`

#### Methods

- `generate_text_to_video(prompt, aspect_ratio="16:9", resolution=None, previous_interaction_id=None, video=None, duration=None)` → `bytes`
- `generate_image_to_video(image, prompt, aspect_ratio="16:9", resolution=None, reference_images=None, previous_interaction_id=None, duration=None)` → `bytes`
- `edit_video(prompt, previous_interaction_id=None, aspect_ratio=None, resolution=None)` → `bytes`
- `extend_video(video, prompt, aspect_ratio=None, resolution=None, duration=None)` → `bytes` — extends a clip by 3–10s. `video` may be a local path (uploaded via the Files API), a Files/`gs://`/http(s) URI.

`aspect_ratio` supports `16:9` and `9:16`. `duration` accepts `3`–`15` seconds (`8` or `"8s"`; 1.1 caps at 10, and extension turns cap at 10). It is sent as `response_format.duration`. After each successful call,
`adapter.last_interaction_id` is updated so you can chain edits without
re-uploading the prior clip.

When `previous_interaction_id` is passed to `generate_text_to_video` /
`generate_image_to_video`, the request is treated as an `edit` task.

## opentryon CLI / MCP Server

```bash
# Text-to-video
opentryon video-generate --model gemini-omni \
  --prompt "A fashion model walking a runway" --aspect-ratio 9:16

# Longer clip (1.2 supports up to 15s)
opentryon video-generate --model gemini-omni \
  --prompt "Slow tracking shot down a runway" --duration 15 --resolution 1080p

# Image-to-video (passing --image switches the method)
opentryon video-generate --model gemini-omni \
  --prompt "Animate a slow walk toward camera" --image photo.jpg

# Conversational edit
opentryon video-generate --model gemini-omni \
  --prompt "Dim the lights" --previous-interaction-id <id>

# Extend an existing clip at 1080p
opentryon video-generate --model gemini-omni \
  --prompt "Continue as the model turns and smiles" --video clip.mp4 --resolution 1080p
```

MCP tool: `video_generate_gemini_omni`.

## See Also

- [Veo](veo)
- [Sora Video](sora-video)
- [API Reference Overview](overview)
- [Official Omni docs](https://ai.google.dev/gemini-api/docs/omni)
