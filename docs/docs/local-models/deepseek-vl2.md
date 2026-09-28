---
sidebar_position: 12
title: DeepSeek-VL2 (Open-Weight)
description: Run DeepSeek's open-weight DeepSeek-VL2 multimodal family locally -- no first-party hosted API exists for this model.
---

# DeepSeek-VL2 (Open-Weight)

DeepSeek-VL2 is DeepSeek's open-weight multimodal model family on Hugging
Face. **No first-party hosted API exists for it** -- DeepSeek's own Platform
API ([`deepseek-flash`](../api-reference/deepseek.md)) only serves
`deepseek-flash` / `deepseek-v4-pro`, so this local adapter is the only way
to use DeepSeek-VL2 today.

Unlike this repo's other local VLMs (Kimi-VL, Qwen3.8), DeepSeek-VL2 does
**not** load via plain `trust_remote_code=True` + `AutoProcessor` -- it
needs DeepSeek's own `deepseek_vl2` Python package (not on PyPI) for the
processor and `<|User|>`/`<|Assistant|>` conversation format.

## Overview

| Feature | Value |
|---|---|
| **Default model** | [deepseek-ai/deepseek-vl2-tiny](https://huggingface.co/deepseek-ai/deepseek-vl2-tiny) |
| **Architecture** | MoE VLM, 27B total base, per-variant activated params below |
| **License** | Code: MIT. Weights: DeepSeek Model License (commercial use permitted) |
| **Capabilities** | Image, multi-image, and (via frame sampling) video understanding |
| **Min VRAM** | Reported figures vary a lot by source -- single-GPU friendly for tiny; budget 40GB+ for small, more for the full model. Check the model card before picking a variant. |

| Model | Total / Activated | Use Case |
|---|---|---|
| `deepseek-ai/deepseek-vl2-tiny` (default) | 3.37B / 1.0B active | Practical single-GPU default |
| `deepseek-ai/deepseek-vl2-small` | 16.1B / 2.8B active | Better quality, more VRAM |
| `deepseek-ai/deepseek-vl2` ("base") | 27B / 4.5B active | Heaviest, best quality |

## Installation

```bash
pip install opentryon[local]   # torch, transformers, etc.
pip install "git+https://github.com/deepseek-ai/DeepSeek-VL2.git"   # deepseek_vl2 (not on PyPI)
pip install decord             # only needed for understand_video()
```

:::note
DeepSeek-VL2's model card documents `transformers==4.38.2`. The `local`
extra pins a different version shared across all local models. If you hit
loading errors, install the exact version DeepSeek recommends in a
dedicated environment.
:::

## Quick Start

### Image Understanding

```python
from tryon.models.deepseek_vl2 import DeepSeekVL2Adapter

adapter = DeepSeekVL2Adapter()  # downloads deepseek-vl2-tiny on first use

result = adapter.understand_image(
    "garment.jpg",
    prompt="Describe this outfit: color, pattern, style, fit, and material.",
)
print(result["text"])
```

### Video Understanding

DeepSeek-VL2 has no official video recipe -- video is handled the same way
as Kimi-VL/Qwen3.8 local: uniformly sample frames and pass them as a
multi-image prompt.

```python
result = adapter.understand_video(
    "runway_clip.mp4",
    prompt="Summarize the styling shown in this video.",
    num_frames=8,
)
print(result["text"])
```

## API Reference

### `DeepSeekVL2Adapter`

```python
class DeepSeekVL2Adapter:
    def __init__(
        self,
        model_id: Optional[str] = None,   # DEEPSEEK_VL2_MODEL_ID or deepseek-ai/deepseek-vl2-tiny
        device: Optional[str] = None,     # defaults to CUDA if available, else CPU
        torch_dtype: str = "auto",        # bf16 on CUDA
    )
```

### `understand_image` / `understand_video` / `understand`

```python
def understand_image(
    self, image, prompt="Describe the content of the image in detail.",
    max_new_tokens=512, do_sample=False, temperature=0.8,
) -> Dict[str, Any]  # {"text": ..., "model": ...}

def understand_video(
    self, video, prompt="Describe what happens in this video.",
    num_frames=8, max_new_tokens=512, do_sample=False, temperature=0.8,
) -> Dict[str, Any]

def understand(
    self, image=None, video=None, prompt="Describe the content in detail.",
    num_frames=8, max_new_tokens=512, do_sample=False, temperature=0.8,
) -> Dict[str, Any]
```

`understand` is the single entry point that accepts `image` and/or `video`
(at least one required) -- this is what
`opentryon understand --model deepseek-vl2` calls.

## Using the `opentryon` CLI

```bash
opentryon understand --model deepseek-vl2 --image garment.jpg \
  --prompt "Describe this outfit."

opentryon understand --model deepseek-vl2 --video runway_clip.mp4 --num-frames 12
```

The CLI checks that `torch` is installed before attempting to load the
model (`pip install opentryon[local]` hint if missing) -- it does **not**
check for the separate `deepseek_vl2` package, which raises its own
`ImportError` with the git install command if missing.

## Choosing a Model Variant

```python
adapter = DeepSeekVL2Adapter(model_id="deepseek-ai/deepseek-vl2-small")
# or: export DEEPSEEK_VL2_MODEL_ID=deepseek-ai/deepseek-vl2-small
```

## Troubleshooting

### `ImportError: DeepSeek-VL2 needs DeepSeek's own 'deepseek_vl2' package`
- Install it from GitHub: `pip install "git+https://github.com/deepseek-ai/DeepSeek-VL2.git"`. It is intentionally **not** part of `opentryon[local]` (not on PyPI, maintained by DeepSeek).

### `ImportError` for `decord`
- Video understanding needs frame sampling: `pip install decord`.

### `trust_remote_code` / loading errors
- Try DeepSeek's exact pinned `transformers==4.38.2` in a dedicated environment (see note above).

## References

- [DeepSeek-VL2 GitHub](https://github.com/deepseek-ai/DeepSeek-VL2)
- [deepseek-vl2 on Hugging Face](https://huggingface.co/deepseek-ai/deepseek-vl2)
- [Hosted DeepSeek-V4.1-Flash API adapter](../api-reference/deepseek.md)
