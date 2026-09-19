---
sidebar_position: 26
title: GLM-5.3-FlashX Understanding
description: Multimodal text, image, and video understanding using Zhipu's GLM-5.3-FlashX via the opentryon GLMUnderstandAdapter.
keywords:
  - GLM
  - GLM-5.3
  - GLM-5.3-FlashX
  - Zhipu
  - Z.ai
  - multimodal understanding
  - image understanding
  - video understanding
  - vision language model
  - reasoning
---

# GLM-5.3-FlashX Understanding

[GLM-5.3-FlashX](https://docs.z.ai/guides/vlm/glm-5.3-flash) is Zhipu's
high-speed serving tier of GLM-5.3-Flash (up to 200 tokens/s, launched
18 Sep 2026) via [Z.ai](https://z.ai)'s OpenAI-compatible Chat Completions
API. OpenTryOn integrates it via `GLMUnderstandAdapter` for **image and
video understanding**.

Unlike Zhipu's text-only GLM-5.3 flagship, the Flash/FlashX branch is a
vision-language model. Like Kimi and Qwen3.8, it is **general-purpose** --
useful for describing garments, outfits, and lookbook/runway videos in the
fashion domain, but equally capable on documents, UI screenshots, product
photography, or any other visual content.

## Capabilities

| Capability | `glm-5.3-flashx` | Notes |
|---|---|---|
| Modalities | Text, image, video in | Text out |
| Context | 1M tokens | 128K max output |
| Thinking | Always on | `thinking.type` only supports `enabled`; use `reasoning_effort` to control depth instead |
| Reasoning depth | `reasoning_effort`: `low`, `high`, `max` (default `max`) | Trades thoroughness vs latency/cost |
| Serving | Same weights as GLM-5.3-Flash, faster inference tier | ~100K domestic accelerators behind the speedup |

## Prerequisites

1. **Z.ai account** and API key
2. Set `ZAI_API_KEY` in your `.env` file
3. Optional base URL override via `ZAI_BASE_URL`

```bash
ZAI_API_KEY=your_zai_api_key
# ZAI_BASE_URL=https://api.z.ai/api/paas/v4  # default
```

## Installation

The GLM adapter reuses the `openai` package (already a core dependency of
`opentryon`, since the Z.ai API is OpenAI-SDK compatible). No additional
installation is required.

## Quick Start

### Image Understanding

```python
from tryon.api.zai import GLMUnderstandAdapter

adapter = GLMUnderstandAdapter()  # glm-5.3-flashx by default

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

Public `https://` media URLs are passed through; local files are inlined as
base64 data URIs.

## CLI

```bash
opentryon understand --model glm-5.3-flashx \
  --image garment.jpg --prompt "Describe this outfit."

opentryon understand --model glm-5.3-flashx \
  --video runway_clip.mp4 --prompt "Summarize the styling." \
  --reasoning-effort low
```

## MCP

Same registry model appears as an MCP tool (no extra wiring):

- `understand_glm_5_3_flashx` — Z.ai API (`ZAI_API_KEY`)

See [MCP Server](../getting-started/mcp.md) and
[`mcp-server/README.md`](https://github.com/tryonlabs/opentryon/blob/main/mcp-server/README.md).

## API Reference

### `GLMUnderstandAdapter`

```python
class GLMUnderstandAdapter:
    def __init__(
        self,
        api_key: Optional[str] = None,       # ZAI_API_KEY
        model: str = "glm-5.3-flashx",
        base_url: Optional[str] = None,      # ZAI_BASE_URL or the Z.ai default
    )
```

### Methods

- `understand_image(image, prompt, reasoning_effort=None, max_tokens=None, temperature=None, top_p=None)`
- `understand_video(video, prompt, ...)`
- `understand(image=None, video=None, prompt=..., ...)` — CLI / MCP entry point

Return dict keys: `text`, `reasoning`, `model`, `usage`.

## References

- [GLM-5.3-Flash/FlashX guide](https://docs.z.ai/guides/vlm/glm-5.3-flash)
- [Z.ai API reference](https://docs.z.ai/api-reference/introduction)
