---
sidebar_position: 13
title: DeepSeek-OCR (Open-Weight)
description: Run DeepSeek's open-weight DeepSeek-OCR document/image OCR model locally -- no first-party hosted API exists for this model.
---

# DeepSeek-OCR (Open-Weight)

DeepSeek-OCR is DeepSeek's open-weight document/image OCR model --
["Contexts Optical Compression"](https://github.com/deepseek-ai/DeepSeek-OCR):
it reads scans, screenshots, and photographed documents and returns
markdown or plain text. **No first-party hosted API exists for it** --
DeepSeek's own Platform API ([`deepseek-flash`](../api-reference/deepseek.md))
only serves `deepseek-flash` / `deepseek-v4-pro`, so this local adapter is
the only way to use DeepSeek-OCR today.

Real fashion fit: garment care labels, size tags, SKU/product-copy sheets,
receipts -- distinct value from general captioning
([Kimi](../api-reference/kimi.md) / [Qwen3.8](../api-reference/qwen3.8.md) /
[GLM-5.3-FlashX](../api-reference/glm.md) /
[DeepSeek-V4.1-Flash](../api-reference/deepseek.md)) even though it shares
the same `understand` CLI service.

## Overview

| Feature | Value |
|---|---|
| **Default model** | [deepseek-ai/DeepSeek-OCR](https://huggingface.co/deepseek-ai/DeepSeek-OCR) |
| **Parameters** | 3B |
| **License** | MIT |
| **Capabilities** | Document -> markdown, or plain free-form OCR text |
| **Requires** | `flash-attn` (`_attn_implementation='flash_attention_2'`) |

DeepSeek also publishes `deepseek-ai/DeepSeek-OCR-2` ("Visual Causal
Flow"), which may have a different `model.infer()` call shape. This
adapter follows the v1 API documented on the `DeepSeek-OCR` model card --
check `DeepSeek-OCR-2`'s own card before pointing `DEEPSEEK_OCR_MODEL_ID`
at it.

## Installation

```bash
pip install opentryon[local]   # torch, transformers, etc.
pip install flash-attn
```

:::note
DeepSeek-OCR's model card pins `torch==2.6.0`, `transformers==4.46.3`, and
`flash-attn==2.7.3` -- newer than this repo's shared `opentryon[local]`
pin (`transformers==4.42.4`). If loading fails (for example a `tokenizers`
error while loading the tokenizer), upgrade in a dedicated environment to
match DeepSeek's pins.
:::

## Quick Start

```python
from tryon.models.deepseek_ocr import DeepSeekOCRAdapter

adapter = DeepSeekOCRAdapter()  # downloads DeepSeek-OCR on first use

# Document -> markdown (default)
result = adapter.understand_image("care_label.jpg", mode="markdown")
print(result["text"])

# Plain free-form OCR
result = adapter.understand_image("receipt.jpg", mode="free")
print(result["text"])
```

## API Reference

### `DeepSeekOCRAdapter`

```python
class DeepSeekOCRAdapter:
    def __init__(
        self,
        model_id: Optional[str] = None,   # DEEPSEEK_OCR_MODEL_ID or deepseek-ai/DeepSeek-OCR
        device: Optional[str] = None,     # "cpu" to force CPU; otherwise CUDA if available
    )
```

### `understand_image` / `understand`

```python
def understand_image(
    self,
    image,                       # path, URL, PIL.Image, or bytes
    prompt: Optional[str] = None,   # raw DeepSeek-OCR prompt; overrides `mode`
    mode: str = "markdown",         # "markdown" or "free"
    base_size: int = 1024,
    image_size: int = 640,
    crop_mode: bool = True,
) -> Dict[str, Any]  # {"text": ..., "model": ..., "mode": ...}

def understand(
    self, image=None, prompt=None, mode="markdown",
    base_size=1024, image_size=640, crop_mode=True,
) -> Dict[str, Any]
```

`understand` requires `image` -- there is no text-only or video path for
OCR. This is what `opentryon understand --model deepseek-ocr` calls.

Under the hood this wraps DeepSeek's documented `model.infer(...)` recipe:
the input image is saved to a temp file (`model.infer` needs a real file
path), inference runs with `save_results=True, eval_mode=True`, and the
adapter reads the returned text (falling back to the markdown/text file
`model.infer` writes to a temp output directory if the return value isn't
directly usable -- the exact output contract has drifted across DeepSeek-OCR
releases).

## Using the `opentryon` CLI

```bash
opentryon understand --model deepseek-ocr --image care_label.jpg

opentryon understand --model deepseek-ocr --image receipt.jpg --ocr-mode free

# Not --mode: that flag name collides with the CLI's own --model selector.
```

The CLI checks that `torch` is installed before attempting to load the
model, and will print an install hint (`pip install opentryon[local]`) if
it's missing.

## Troubleshooting

### `tokenizers` / loading errors
- Usually a version mismatch: install DeepSeek's pinned `torch==2.6.0` / `transformers==4.46.3` in a dedicated environment (see note above).

### `RuntimeError: DeepSeek-OCR ran but produced no readable output`
- The upstream `model.infer()` return-value/output-file contract changed. Check the current [DeepSeek-OCR model card](https://huggingface.co/deepseek-ai/DeepSeek-OCR) for the latest recipe.

### Out of memory / no GPU
- DeepSeek-OCR's official recipe requires CUDA (`.cuda()`); there is no supported CPU path.

## References

- [DeepSeek-OCR GitHub](https://github.com/deepseek-ai/DeepSeek-OCR)
- [DeepSeek-OCR on Hugging Face](https://huggingface.co/deepseek-ai/DeepSeek-OCR)
- [DeepSeek-OCR-2 on Hugging Face](https://huggingface.co/deepseek-ai/DeepSeek-OCR-2)
- [Hosted DeepSeek-V4.1-Flash API adapter](../api-reference/deepseek.md)
