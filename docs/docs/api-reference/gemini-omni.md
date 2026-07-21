---
sidebar_position: 10
title: Gemini Omni Flash (Video)
description: Multimodal video generation and conversational editing with Gemini Omni Flash
keywords:
  - gemini omni
  - gemini-omni-flash-preview
  - video generation
  - conversational editing
  - interactions api
---

# Gemini Omni Flash (Video)

The `GeminiOmniAdapter` wraps Google's [Gemini Omni Flash](https://ai.google.dev/gemini-api/docs/omni)
preview model (`gemini-omni-flash-preview`) for fast multimodal video generation
and conversational video editing via the Interactions API.

## Overview

Unlike Veo (which uses `models.generate_videos`), Omni uses
`client.interactions.create(...)`. It accepts text, images (and in the broader
Omni family, audio/video inputs) and returns short clips (about 3–10s at 720p /
24 FPS) with natively generated audio. Prior generations can be refined with
natural-language edit turns using `previous_interaction_id`.

**References:**
- [Generate and edit videos with Gemini Omni Flash](https://ai.google.dev/gemini-api/docs/omni)
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

- `generate_text_to_video(prompt, aspect_ratio="16:9", previous_interaction_id=None)` → `bytes`
- `generate_image_to_video(image, prompt, aspect_ratio="16:9", reference_images=None, previous_interaction_id=None)` → `bytes`
- `edit_video(prompt, previous_interaction_id=None, aspect_ratio=None)` → `bytes`

`aspect_ratio` supports `16:9` and `9:16`. After each successful call,
`adapter.last_interaction_id` is updated so you can chain edits without
re-uploading the prior clip.

When `previous_interaction_id` is passed to `generate_text_to_video` /
`generate_image_to_video`, the request is treated as an `edit` task.

## opentryon CLI / MCP Server

```bash
# Text-to-video
opentryon video-generate --model gemini-omni \
  --prompt "A fashion model walking a runway" --aspect-ratio 9:16

# Image-to-video (passing --image switches the method)
opentryon video-generate --model gemini-omni \
  --prompt "Animate a slow walk toward camera" --image photo.jpg

# Conversational edit
opentryon video-generate --model gemini-omni \
  --prompt "Dim the lights" --previous-interaction-id <id>
```

MCP tool: `video_generate_gemini_omni`.

## See Also

- [Sora Video](sora-video)
- [API Reference Overview](overview)
- [Official Omni docs](https://ai.google.dev/gemini-api/docs/omni)
