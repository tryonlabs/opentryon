---
sidebar_position: 12
title: Kimi K2.6 / K2.7 Code Understanding
description: Multimodal text, image, and video understanding using Moonshot AI's Kimi K2.6 and K2.7 Code models via the opentryon KimiUnderstandAdapter.
keywords:
  - Kimi
  - Kimi K2.6
  - Kimi K2.7 Code
  - Moonshot AI
  - multimodal understanding
  - image understanding
  - video understanding
  - vision language model
---

# Kimi K2.6 / K2.7 Code Understanding

[Kimi](https://platform.kimi.ai/docs/overview) is Moonshot AI's family of
natively multimodal models. OpenTryOn integrates two variants via a single
adapter, `KimiUnderstandAdapter`, for **image and video understanding**:

- **Kimi K2.6** (`kimi-k2.6`): General-purpose multimodal model with
  optional "thinking" mode and a 256K context window.
- **Kimi K2.7 Code** (`kimi-k2.7-code` / `kimi-k2.7-code-highspeed`):
  Coding-focused variant built on K2.6 with the same vision/video
  understanding, tuned for long-horizon agentic coding and tool use.
  Thinking mode is always on for this variant.

Unlike most other adapters in this repo, Kimi's understanding capability is
**general-purpose** -- useful for describing garments, outfits, and
lookbook/runway videos in the fashion domain, but equally capable on
documents, UI screenshots, product photography, or any other visual content.

For local/GPU deployment instead of the hosted API, see the open-weight
[Kimi-VL local model](../local-models/kimi-vl.md).

## Prerequisites

1. **Moonshot AI Account**: Sign up at [platform.kimi.ai](https://platform.kimi.ai/)
2. **API Key**: Get one from the [API Keys console](https://platform.kimi.ai/console/api-keys)
3. **Environment Variable**: Set `MOONSHOT_API_KEY` in your `.env` file

```bash
MOONSHOT_API_KEY=your_moonshot_api_key
```

## Installation

The Kimi adapter reuses the `openai` package (already a core dependency of
`opentryon`, since the Kimi API is fully OpenAI-SDK compatible). No
additional installation is required.

## Quick Start

### Image Understanding

```python
from tryon.api import KimiUnderstandAdapter

adapter = KimiUnderstandAdapter()  # uses kimi-k2.6 by default

result = adapter.understand_image(
    "garment.jpg",
    prompt="Describe this outfit: color, pattern, style, fit, and material.",
)
print(result["text"])
```

### Video Understanding

```python
result = adapter.understand_video(
    "runway_clip.mp4",
    prompt="Summarize the styling and garments shown in this video.",
)
print(result["text"])
```

### Kimi K2.7 Code (coding-focused, still multimodal)

```python
adapter = KimiUnderstandAdapter(model="kimi-k2.7-code")

result = adapter.understand_image(
    "ui_mockup.png",
    prompt="Write the HTML/CSS for this design.",
)
print(result["text"])
```

## API Reference

### `KimiUnderstandAdapter`

#### `__init__(api_key=None, model="kimi-k2.6", base_url=None)`

**Parameters:**
- `api_key` (str, optional): Moonshot API key. Defaults to `MOONSHOT_API_KEY` environment variable.
- `model` (str, optional): Default model for calls that don't override it. One of `kimi-k2.6`, `kimi-k2.7-code`, `kimi-k2.7-code-highspeed`, `kimi-k2.5`. Default: `"kimi-k2.6"`.
- `base_url` (str, optional): Defaults to `KIMI_BASE_URL` env var or `https://api.moonshot.ai/v1`.

**Raises:**
- `ValueError`: If the API key is missing.
- `ImportError`: If the `openai` package isn't installed.

#### `understand_image(image, prompt=..., model=None, thinking=None, max_tokens=None)`

Understand one or more images.

**Parameters:**
- `image`: A single image or list of images. Each may be a file path, URL, `PIL.Image`, raw bytes, or `BytesIO`. Supported formats: png, jpeg, webp, gif.
- `prompt` (str): Question/instruction about the image(s).
- `model` (str, optional): Override the default model for this call.
- `thinking` (bool, optional): Force-enable/disable thinking mode. Only `kimi-k2.6` supports disabling it; `kimi-k2.7-code*` always thinks.
- `max_tokens` (int, optional): Max output tokens (server default: 32768).

**Returns:** `dict` with keys `text`, `reasoning`, `model`, `usage`.

#### `understand_video(video, prompt=..., model=None, thinking=None, max_tokens=None, use_file_upload=None, max_inline_mb=20.0)`

Understand video content.

**Parameters:**
- `video`: File path, URL, raw bytes, or `BytesIO`. Supported formats: mp4, mpeg, mov, avi, x-flv, mpg, webm, wmv, 3gpp.
- `use_file_upload` (bool, optional): Upload to Moonshot storage (`ms://` reference) instead of inlining as base64. Defaults to auto-enabled above `max_inline_mb`.
- Other parameters same as `understand_image`.

**Returns:** `dict` with keys `text`, `reasoning`, `model`, `usage`.

#### `understand(image=None, video=None, prompt=..., model=None, thinking=None, max_tokens=None)`

Single entry point that accepts `image` and/or `video` (at least one
required) -- this is what the `opentryon understand --model kimi-k2.6`
CLI command calls.

#### `chat(messages, model=None, thinking=None, max_tokens=None, tools=None, tool_choice=None)`

Escape hatch for full multi-turn conversations or tool-calling agents (e.g.
Kimi's "watch a video clip" tool-use pattern). Returns the raw OpenAI SDK
`ChatCompletion` object.

## Parameter Notes

Kimi's `k2.5`/`k2.6`/`k2.7-code` models fix `temperature`, `top_p`, `n`,
`presence_penalty`, and `frequency_penalty` server-side -- non-default
values raise an API error, so this adapter doesn't expose those knobs. Only
`thinking` and `max_tokens` are configurable.

| Field | Behavior |
|---|---|
| `thinking` | Default enabled. `kimi-k2.7-code*` cannot disable it. |
| `max_tokens` | Default 32768. |
| `temperature` / `top_p` / `n` / `presence_penalty` / `frequency_penalty` | Fixed by the API; not exposed. |

## Using the `opentryon` CLI

```bash
# Kimi K2.6 -- image understanding
opentryon understand --model kimi-k2.6 --image garment.jpg \
  --prompt "Describe this outfit."

# Kimi K2.6 -- video understanding, disable thinking mode
opentryon understand --model kimi-k2.6 --video runway_clip.mp4 --no-thinking

# Kimi K2.7 Code -- coding-focused multimodal understanding
opentryon understand --model kimi-k2.7-code --image ui_mockup.png \
  --prompt "Write the HTML/CSS for this design."

# High-speed K2.7 Code variant
opentryon understand --model kimi-k2.7-code --kimi-model kimi-k2.7-code-highspeed \
  --image garment.jpg
```

Results are printed to stdout and saved as JSON under `outputs/`.

## Error Handling

The adapter raises `ValueError` for:
- Missing API key
- Neither `image` nor `video` provided to `understand()`
- Invalid `model`
- Attempting to disable `thinking` on `kimi-k2.7-code*`

## References

- [Kimi API Overview](https://platform.kimi.ai/docs/overview)
- [Kimi K2.6 Quickstart](https://platform.kimi.ai/docs/guide/kimi-k2-6-quickstart)
- [Kimi K2.7 Code Quickstart](https://platform.kimi.ai/docs/guide/kimi-k2-7-code-quickstart)
- [Using the Kimi Vision Model](https://platform.kimi.ai/docs/guide/use-kimi-vision-model)
