# Qwen3.8 (Open-Weight)

Qwen3.8 is Alibaba's open-weight multimodal family on Hugging Face — the
open counterpart to the hosted
[Qwen3.8-Max DashScope API](../api-reference/qwen3.8.md). Use this for
image/video understanding on your own GPUs (privacy, no per-request cost,
offline).

## Capabilities

Same **series strengths** as hosted Max, at open-weight scale:

| Capability | OpenTryOn local (`qwen3.8`) |
|---|---|
| Modalities | Text + image (+ video via frame sampling) → text |
| Default weights | Dense **Qwen3.8-27B** (~27B VLM) |
| Context | **262K** native; toward 1M with YaRN in vLLM/SGLang |
| Thinking | On by default; `--no-thinking` / `enable_thinking=False` |
| Coding / agents / tools | Strong in the model family; local adapter focuses on **understand** (use a serving stack for full agent loops) |
| Cluster Max-class | `Qwen/Qwen3.8-2.4T-A95B` MoE — not single-GPU Transformers |

Useful for garments, lookbooks, documents, UI screenshots, product photos, and
sampled video — the same general-purpose understand path as the API adapter.

## Overview

| Feature | Value |
|---|---|
| **Default model** | [Qwen/Qwen3.8-27B](https://huggingface.co/Qwen/Qwen3.8-27B) |
| **Architecture** | Dense VLM (~27B), hybrid attention + vision encoder |
| **Context length** | 262K native (extensible toward 1M with YaRN in serving stacks) |
| **OpenTryOn focus** | Image, multi-image, and frame-sampled video understanding; thinking mode |
| **Min VRAM** | ~50GB+ recommended for bf16; community quantized checkpoints for smaller cards |

The flagship open MoE [Qwen/Qwen3.8-2.4T-A95B](https://huggingface.co/Qwen/Qwen3.8-2.4T-A95B)
is datacenter-scale — pass `model_id="Qwen/Qwen3.8-2.4T-A95B"` only with
cluster serving (vLLM / SGLang), not single-GPU Transformers.

## Installation

```bash
pip install opentryon[local]
pip install -U transformers   # Qwen3.8 needs a recent transformers
pip install decord            # only for understand_video()
```

## Quick Start

### Image Understanding

```python
from tryon.models import Qwen38Adapter

adapter = Qwen38Adapter()  # downloads Qwen/Qwen3.8-27B on first use

result = adapter.understand_image(
    "garment.jpg",
    prompt="Describe this outfit: color, pattern, style, fit, and material.",
)
print(result["text"])
print(result["thinking"])
```

### Video Understanding

Video uses uniform frame sampling as a multi-image prompt (transformers
fallback; native video IO is better under vLLM/SGLang):

```python
result = adapter.understand_video(
    "runway_clip.mp4",
    prompt="Summarize the styling shown in this video.",
    num_frames=8,
)
print(result["text"])
```

## API Reference

### `Qwen38Adapter`

```python
class Qwen38Adapter:
    def __init__(
        self,
        model_id: Optional[str] = None,     # or QWEN38_MODEL_ID / Qwen/Qwen3.8-27B
        device: Optional[str] = None,       # device_map, default "auto"
        torch_dtype: str = "auto",
        trust_remote_code: bool = True,
    )
```

### Methods

- `understand_image(image, prompt, max_new_tokens=4096, temperature=0.8, enable_thinking=True)`
- `understand_video(video, prompt, num_frames=8, ...)`
- `understand(image=None, video=None, ...)` — CLI / MCP entry point

Returns `{"thinking": ..., "text": ..., "model": ...}`.

## CLI

```bash
opentryon understand --model qwen3.8 --image garment.jpg \
  --prompt "Describe this outfit."

opentryon understand --model qwen3.8 --video runway_clip.mp4 --num-frames 12

opentryon understand --model qwen3.8 --image garment.jpg --no-thinking
```

## MCP

Local registry id `qwen3.8` → tool `understand_qwen3_8` (requires
`pip install opentryon[local]`). Hosted Max is `understand_qwen3_8_max`.
See [MCP Server](../getting-started/mcp.md).

## Choosing a Variant

| Model | Scale | Use case |
|---|---|---|
| `Qwen/Qwen3.8-27B` (default) | Dense 27B | Practical open multimodal reasoning |
| `Qwen/Qwen3.8-2.4T-A95B` | MoE ~2.4T / 95B active | Cluster-scale; closest to hosted Max |
| Community AWQ/NVFP4 quants | Smaller VRAM | Single-GPU when bf16 does not fit |

```python
adapter = Qwen38Adapter(model_id="barrydeen/Qwen3.8-27B-AWQ-4bit")
```

## Troubleshooting

### Out of Memory
- Prefer a quantized Hub checkpoint, or serve 27B with vLLM/SGLang.
- Do not load `Qwen3.8-2.4T-A95B` on a single GPU.

### `AutoModelForImageTextToText` / architecture errors
- Upgrade transformers: `pip install -U transformers`.

### `ImportError` for `decord`
- Needed only for video frame sampling: `pip install decord`.

## References

- [Qwen3.8-27B on Hugging Face](https://huggingface.co/Qwen/Qwen3.8-27B)
- [Qwen3.8 collection](https://huggingface.co/collections/Qwen/qwen38)
- [Hosted Qwen3.8-Max API](../api-reference/qwen3.8.md)
