---
sidebar_position: 13
title: Qwen3.8-Max Understanding
description: Multimodal text, image, and video understanding using Alibaba DashScope Qwen3.8-Max via the opentryon QwenUnderstandAdapter.
keywords:
  - Qwen
  - Qwen3.8
  - Qwen3.8-Max
  - DashScope
  - Alibaba Cloud
  - multimodal understanding
  - image understanding
  - video understanding
  - vision language model
  - reasoning
  - agents
---

# Qwen3.8-Max Understanding

[Qwen3.8-Max](https://docs.qwencloud.com/developer-guides/multimodal/vision) is
Alibaba's hosted flagship multimodal model on DashScope / Model Studio.
OpenTryOn integrates it via `QwenUnderstandAdapter` for **image and video
understanding** over the OpenAI-compatible Chat Completions API.

For local/GPU deployment, see the open-weight
[Qwen3.8-27B local model](../local-models/qwen3.8.md).

## Capabilities (Qwen3.8 series)

Qwen3.8 is a **native multimodal** generation (text + image + video → text),
designed for coding, professional work, research, and long-horizon agents —
not a separate “VL-only” model ID.

| Capability | Hosted Max (`qwen3.8-max`) | Notes |
|---|---|---|
| Modalities | Text, image, video in | Text out |
| Context | Up to ~**1M** tokens | Large docs / long multimodal sessions |
| Video | Up to ~**2 hours / 2GB** (vendor limits) | Many images per request also supported |
| Thinking | On by default | Toggle with `enable_thinking` / `--no-thinking` |
| Reasoning depth | `reasoning_effort`: `xhigh` (default), `medium`, `low` | Trades thoroughness vs latency/cost |
| Coding & agents | Strong long-horizon coding / tool use (vendor) | OpenTryOn exposes **understand**; use `chat()` or DashScope for full agent loops |
| Structured output / tools | Supported on DashScope | Function calling, built-in tools (search / code exec) on the hosted API |

**OpenTryOn surface today:** `understand` (image and/or video + prompt), plus
`chat()` as an escape hatch for multi-turn / tools. General-purpose — garments
and lookbooks, and equally documents, UI screenshots, product photography, and
runway/clips.

**Family lineup (vendor):**

| Variant | Role |
|---|---|
| **Qwen3.8-Max** | Hosted MoE flagship (~2.4T total / ~95B active) — CLI `qwen3.8-max` |
| **Qwen3.8-27B** | Dense open weights — CLI `qwen3.8` ([local docs](../local-models/qwen3.8.md)) |
| **Qwen3.8-2.4T-A95B** | Open MoE closest to Max — cluster / vLLM–SGLang only |

## Prerequisites

1. **Alibaba Cloud Model Studio** account and API key
2. Set `DASHSCOPE_API_KEY` (same key used for Wan video API)
3. Optional region override via `QWEN_BASE_URL`

```bash
DASHSCOPE_API_KEY=your_dashscope_api_key
# International (default):
# QWEN_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
# China:
# QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

## Installation

Uses the `openai` package (already a core `opentryon` dependency). No extra
install step.

## Quick Start

### Image Understanding

```python
from tryon.api import QwenUnderstandAdapter

adapter = QwenUnderstandAdapter()  # qwen3.8-max by default

result = adapter.understand_image(
    "garment.jpg",
    prompt="Describe this outfit: color, pattern, style, fit, and material.",
)
print(result["text"])
print(result["reasoning"])  # thinking content when enabled
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
opentryon understand --model qwen3.8-max \
  --image garment.jpg --prompt "Describe this outfit."

opentryon understand --model qwen3.8-max \
  --video runway_clip.mp4 --prompt "Summarize the styling." \
  --reasoning-effort medium

opentryon understand --model qwen3.8-max \
  --image garment.jpg --no-thinking
```

## MCP

Same registry models appear as MCP tools (no extra wiring):

- `understand_qwen3_8_max` — DashScope API (`DASHSCOPE_API_KEY`)
- `understand_qwen3_8` — local 27B ([local docs](../local-models/qwen3.8.md))

See [MCP Server](../getting-started/mcp.md) and
[`mcp-server/README.md`](https://github.com/tryonlabs/opentryon/blob/main/mcp-server/README.md).

## API Reference

### `QwenUnderstandAdapter`

```python
class QwenUnderstandAdapter:
    def __init__(
        self,
        api_key: Optional[str] = None,       # DASHSCOPE_API_KEY
        model: str = "qwen3.8-max",
        base_url: Optional[str] = None,      # QWEN_BASE_URL or intl default
    )
```

### Methods

- `understand_image(image, prompt, enable_thinking=None, reasoning_effort=None, ...)`
- `understand_video(video, prompt, ...)`
- `understand(image=None, video=None, prompt=..., ...)` — CLI / MCP entry point
- `chat(messages, ...)` — multi-turn / tools escape hatch (raw ChatCompletion)

Return dict keys: `text`, `reasoning`, `model`, `usage`.

## References

- [Qwen Cloud vision guide](https://docs.qwencloud.com/developer-guides/multimodal/vision)
- [Model Studio vision docs](https://www.alibabacloud.com/help/en/model-studio/vision)
- [Get API key](https://www.alibabacloud.com/help/en/model-studio/get-api-key)
- [Alibaba Qwen3.8-Max announcement](https://www.alibabacloud.com/press-room/alibaba-unveils-qwen3-8-max)
- [Open-weight Qwen3.8-27B](../local-models/qwen3.8.md)
