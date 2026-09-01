---
sidebar_position: 14
title: Qwen-Image Generation & Try-On
description: Text-to-image, image editing, and virtual try-on using Alibaba DashScope Qwen-Image 3.0 via QwenImageAdapter.
keywords:
  - Qwen
  - Qwen-Image
  - Qwen-Image 3.0
  - Qwen3.8
  - DashScope
  - Alibaba Cloud
  - text to image
  - image editing
  - virtual try-on
---

# Qwen-Image Generation & Try-On

[Qwen-Image 3.0](https://docs.qwencloud.com/api-reference/image-generation/qwen-text-to-image)
is Alibaba's hosted image model on DashScope / Model Studio. OpenTryOn
integrates it via `QwenImageAdapter` for **text-to-image**, **image editing
(I2I, 1–3 refs)**, and **virtual try-on** (person + garment composition).

This is **composition** I2I, not Alibaba's dedicated try-on. Dedicated
OutfitAnyone-Plus is `--model outfitanyone-plus` (`aitryon-plus`, Beijing
region). See [OutfitAnyone-Plus](outfitanyone-plus).

Qwen3.8 (understand) and Qwen-Image (generate / edit / vton) share
`DASHSCOPE_API_KEY` but use different endpoints:

| Task | CLI | Adapter | Endpoint |
|---|---|---|---|
| Understand | `opentryon understand --model qwen3.8-max` | `QwenUnderstandAdapter` | OpenAI-compatible chat ([docs](qwen3.8.md)) |
| Generate | `opentryon generate --model qwen-image` | `QwenImageAdapter` | `/api/v1/.../multimodal-generation` |
| Edit | `opentryon edit --model qwen-image` | `QwenImageAdapter` | same image API, I2I |
| VTON | `opentryon vton --model qwen-image` | `QwenImageAdapter.generate_virtual_tryon` | I2I with person + garment |
| Local generate / edit / VTON | `opentryon … --model qwen-image-local` | `QwenImageLocalAdapter` | Diffusers ([local docs](../local-models/qwen-image.md)) |

For local Qwen3.8-27B understanding, see [Qwen3.8 local](../local-models/qwen3.8.md).
For local Qwen-Image T2I / edit / VTON, see [Qwen-Image local](../local-models/qwen-image.md)
(`--model qwen-image-local`).

## Understand → generate / VTON workflow

Qwen3.8 captions; Qwen-Image paints. Typical fashion loop:

```bash
# 1. Describe the garment (Qwen3.8-Max)
opentryon understand --model qwen3.8-max \
  --image garment.jpg \
  --prompt "Describe this garment: category, color, fabric, cut, and notable details."

# 2a. Text-to-image from that description
opentryon generate --model qwen-image \
  --prompt "editorial lookbook photo of a model wearing <paste description>"

# 2b. Or compose the garment onto a person photo
opentryon vton --model qwen-image \
  --person-image model.jpg --garment-image garment.jpg \
  --garment-description "<paste description>"
```

VTON here is **multi-image composition**, not a dedicated garment-fit model.
Prefer FLUX VTO or FASHN when drape/fit accuracy matters more than staying on
one DashScope key.

## Prerequisites

1. **Alibaba Cloud Model Studio** account and API key
2. Set `DASHSCOPE_API_KEY` (same key as Wan video and Qwen3.8-Max)
3. Optional region override via `QWEN_IMAGE_BASE_URL`

```bash
DASHSCOPE_API_KEY=your_dashscope_api_key
# International (default):
# QWEN_IMAGE_BASE_URL=https://dashscope-intl.aliyuncs.com/api/v1
# China:
# QWEN_IMAGE_BASE_URL=https://dashscope.aliyuncs.com/api/v1
```

## Models

| `--model-version` | Role |
|---|---|
| `qwen-image-3.0-pro` (default) | Flagship T2I + I2I |
| `qwen-image-3.0` | Standard 3.0 (quality / speed balance) |
| `qwen-image-2.0-pro` / `qwen-image-2.0` | Previous generation |

Thinking and prompt rewriting are **on by default**. `--no-thinking` and
`--no-prompt-extend` disable them. `--prompt-extend-mode agent` is T2I-only.

`--size` is `width*height` (e.g. `1024*1024`). If omitted, 3.0 auto-picks a
resolution from the prompt. `--n` is 1–6.

## CLI

```bash
opentryon generate --model qwen-image \
  --prompt "editorial lookbook, linen trench on a sunlit terrace" \
  --size 1024*1024

opentryon edit --model qwen-image \
  --images person.jpg \
  --prompt "Change the jacket to black leather, keep the face and pose."

opentryon vton --model qwen-image \
  --person-image model.jpg --garment-image garment.jpg \
  --garment-description "olive green bomber jacket"
```

## MCP

Same registry models appear as MCP tools (no extra wiring):

- `generate_qwen_image` — T2I (`DASHSCOPE_API_KEY`)
- `edit_qwen_image` — I2I, 1–3 images
- `vton_qwen_image` — person + garment composition

Pair with `understand_qwen3_8_max` for the caption → generate / try-on loop.

## Python

```python
from tryon.api import QwenImageAdapter

adapter = QwenImageAdapter()  # qwen-image-3.0-pro by default

images = adapter.generate_text_to_image(
    "editorial lookbook, linen trench on a sunlit terrace",
    size="1024*1024",
)

edited = adapter.generate_image_edit(
    "person.jpg",
    prompt="Change the jacket to black leather, keep the face and pose.",
)

tryon = adapter.generate_virtual_tryon(
    person="model.jpg",
    garment="garment.jpg",
    garment_description="olive green bomber jacket",
)
tryon[0].save("qwen_tryon.png")
```

## API Reference

### `QwenImageAdapter`

```python
class QwenImageAdapter:
    def __init__(
        self,
        api_key: Optional[str] = None,       # DASHSCOPE_API_KEY
        model: str = "qwen-image-3.0-pro",
        base_url: Optional[str] = None,      # QWEN_IMAGE_BASE_URL or intl /api/v1
        timeout: float = 300.0,
    )
```

### Methods

- `generate_text_to_image(prompt, size=None, n=1, ...)` → `List[Image.Image]`
- `generate_image_edit(image, prompt, ...)` — one image or a list of 1–3
- `generate_multi_image(images, prompt, ...)` — I2I composition
- `generate_virtual_tryon(person, garment, prompt=None, garment_description=None, ...)`
- `build_tryon_prompt(prompt=None, garment_description=None)`

Shared kwargs: `negative_prompt`, `prompt_extend`, `prompt_extend_mode`
(`direct` / `agent`), `enable_thinking`, `watermark`, `seed`, `model`.

## References

- [Qwen-Image T2I API](https://docs.qwencloud.com/api-reference/image-generation/qwen-text-to-image)
- [Qwen-Image editing API](https://docs.qwencloud.com/api-reference/image-generation/qwen-image-editing)
- [Model Studio generation & editing](https://help.aliyun.com/en/model-studio/qwen-image-generation-and-editing-api-reference)
- [Get API key](https://www.alibabacloud.com/help/en/model-studio/get-api-key)
- [Qwen3.8-Max understanding](qwen3.8.md)
- [Open-weight Qwen-Image local](../local-models/qwen-image.md)
