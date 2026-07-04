# Kimi-VL (Open-Weight)

Kimi-VL is Moonshot AI's open-weight multimodal model family on Hugging
Face -- the open-weight counterpart to the hosted
[Kimi K2.6 / K2.7 Code API](../api-reference/kimi.md). Use this when you
need image/video understanding running entirely on your own GPU (privacy,
no per-request costs, offline capability) instead of calling Moonshot's API.

## Overview

| Feature | Value |
|---|---|
| **Default model** | [moonshotai/Kimi-VL-A3B-Thinking-2506](https://huggingface.co/moonshotai/Kimi-VL-A3B-Thinking-2506) |
| **Architecture** | Mixture-of-Experts VLM, 16B total / ~3B activated params |
| **Context length** | 128K |
| **Capabilities** | Image, multi-image, and (via frame sampling) video understanding, with visible "thinking" chain-of-thought |
| **Min VRAM** | 24GB+ recommended (bf16) |

Because only ~3B parameters are activated per token, Kimi-VL-A3B is
practical to run on a single high-end GPU, unlike the much larger
open-weight [Kimi-K2.5](https://huggingface.co/moonshotai/Kimi-K2.5)
(1T total / 32B activated params), which needs distributed serving
(vLLM/SGLang across multiple GPUs). Pass `model_id="moonshotai/Kimi-K2.5"`
if you have that kind of cluster infrastructure and want a model closer in
scale to the hosted `kimi-k2.6`/`kimi-k2.7-code` APIs.

## Installation

```bash
pip install opentryon[local]   # torch, transformers, etc.
pip install decord             # only needed for understand_video()
```

:::note
Kimi-VL's model card recommends `transformers>=4.48.2`. The `local` extra
pins an older version shared across all local models (BEN2, LLaVA-NeXT,
FLUX.2-dev Turbo). If you hit `trust_remote_code` loading errors, upgrade
transformers in a dedicated environment: `pip install -U transformers`.
:::

## Quick Start

### Image Understanding

```python
from tryon.models import KimiVLAdapter

adapter = KimiVLAdapter()  # downloads model on first use

result = adapter.understand_image(
    "garment.jpg",
    prompt="Describe this outfit: color, pattern, style, fit, and material.",
)
print(result["text"])
print(result["thinking"])  # visible chain-of-thought, if any
```

### Video Understanding

Video is handled by uniformly sampling frames and passing them to the model
as a multi-image prompt (the official recipe uses vLLM for native video
token handling; this is a `transformers`-only fallback):

```python
result = adapter.understand_video(
    "runway_clip.mp4",
    prompt="Summarize the styling shown in this video.",
    num_frames=8,
)
print(result["text"])
```

## API Reference

### `KimiVLAdapter`

```python
class KimiVLAdapter:
    def __init__(
        self,
        model_id: str = "moonshotai/Kimi-VL-A3B-Thinking-2506",
        device: Optional[str] = None,          # passed as device_map, defaults to "auto"
        torch_dtype: str = "auto",
        trust_remote_code: bool = True,         # required for Kimi-VL's custom modeling code
    )
```

### `understand_image`

```python
def understand_image(
    self,
    image: Union[str, Path, Image.Image, List[...]],
    prompt: str = "Describe the content of the image in detail.",
    max_new_tokens: int = 4096,
    temperature: float = 0.8,
) -> Dict[str, Any]  # {"thinking": ..., "text": ..., "model": ...}
```

### `understand_video`

```python
def understand_video(
    self,
    video: Union[str, Path],
    prompt: str = "Describe what happens in this video.",
    num_frames: int = 8,
    max_new_tokens: int = 4096,
    temperature: float = 0.8,
) -> Dict[str, Any]
```

### `understand`

```python
def understand(
    self,
    image=None,
    video=None,
    prompt: str = "Describe the content in detail.",
    num_frames: int = 8,
    max_new_tokens: int = 4096,
    temperature: float = 0.8,
) -> Dict[str, Any]
```

Single entry point that accepts `image` and/or `video` (at least one
required) -- this is what the `opentryon understand --model kimi-vl` CLI
command calls.

## Using the `opentryon` CLI

```bash
# Image understanding (downloads the model on first run)
opentryon understand --model kimi-vl --image garment.jpg \
  --prompt "Describe this outfit."

# Video understanding, sampling 12 frames
opentryon understand --model kimi-vl --video runway_clip.mp4 --num-frames 12
```

The CLI checks that `torch` is installed before attempting to load the
model, and will print an install hint (`pip install opentryon[local]`) if
it's missing.

## Choosing a Model Variant

| Model | Params | Use Case |
|---|---|---|
| `moonshotai/Kimi-VL-A3B-Thinking-2506` (default) | 16B / 3B active | Best general reasoning + video/OCR/agent grounding |
| `moonshotai/Kimi-VL-A3B-Instruct` | 16B / 3B active | Faster, non-thinking variant for simple captioning |
| `moonshotai/Kimi-K2.5` | 1T / 32B active | Cluster-scale, closest to the hosted K2.6 API; needs vLLM/SGLang |

```python
adapter = KimiVLAdapter(model_id="moonshotai/Kimi-VL-A3B-Instruct")
```

## Troubleshooting

### Out of Memory (OOM)
- Use the default `Kimi-VL-A3B-*` model (only ~3B activated params) rather than `Kimi-K2.5`.
- Reduce `max_new_tokens`.

### `ImportError` for `decord`
- Video understanding needs frame sampling: `pip install decord`.

### `trust_remote_code` errors
- Kimi-VL ships custom modeling code on the Hub; ensure `trust_remote_code=True` (the default) and consider upgrading `transformers` (see note above).

## References

- [Kimi-VL-A3B-Thinking-2506 on Hugging Face](https://huggingface.co/moonshotai/Kimi-VL-A3B-Thinking-2506)
- [Kimi-VL GitHub](https://github.com/MoonshotAI/Kimi-VL)
- [Kimi-K2.5 on Hugging Face](https://huggingface.co/moonshotai/Kimi-K2.5)
- [Hosted Kimi K2.6 / K2.7 Code API adapter](../api-reference/kimi.md)
