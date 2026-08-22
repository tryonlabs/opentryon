# Qwen-Image (Open-Weight)

Qwen-Image is Alibaba's open-weight image foundation family on Hugging Face —
the open counterpart to the hosted
[Qwen-Image DashScope API](../api-reference/qwen-image.md). Use this for
**text-to-image**, **image editing**, and **virtual try-on** on your own GPU
(privacy, no per-request cost, offline).

Apache-2.0 weights. OpenTryOn uses Hugging Face **Diffusers** (not ComfyUI).

Hosted twin: `opentryon generate|edit|vton --model qwen-image`.

## Capabilities

| Task | CLI | Default weights | Pipeline |
|---|---|---|---|
| Generate (T2I) | `--model qwen-image-local` | [`Qwen/Qwen-Image-2512`](https://huggingface.co/Qwen/Qwen-Image-2512) | `QwenImagePipeline` |
| Edit / I2I (1–3 refs) | `--model qwen-image-local` | [`Qwen/Qwen-Image-Edit-2511`](https://huggingface.co/Qwen/Qwen-Image-Edit-2511) | `QwenImageEditPlusPipeline` |
| VTON | `--model qwen-image-local` | same Edit-Plus | person + garment (up to 3 refs) |

Earlier open checkpoints still work via env overrides:

| Role | Other official ids |
|---|---|
| T2I | `Qwen/Qwen-Image` (original 20B) |
| Single-image edit | `Qwen/Qwen-Image-Edit` (`QwenImageEditPipeline`, 1 ref only) |
| Multi-image edit | `Qwen/Qwen-Image-Edit-2509` |

Qwen-Image **2.0 / 3.0** are the hosted DashScope ids (`qwen-image-2.0`,
`qwen-image-3.0-pro`). There are no matching open Diffusers weights for those
hosted SKUs yet — local OpenTryOn tracks the official HF open series (2512 T2I,
2511 Edit).

## Overview

| Feature | Value |
|---|---|
| **License** | Apache 2.0 |
| **Architecture** | ~20B MMDiT + Qwen2.5-VL text encoder |
| **Packed sizes** | Official aspect map, e.g. `1:1` → 1328×1328 |
| **Min VRAM** | ~40GB+ bf16 full load; **cpu_offload on by default** for smaller cards |
| **OpenTryOn id** | `qwen-image-local` (`extra="local"`) |

VTON is **person + product composition** (Edit-Plus was trained on combinations
like person+product / person+scene), not a dedicated garment-fit model.

## Installation

```bash
pip install opentryon[local]
pip install -U diffusers transformers accelerate
# Qwen-Image needs transformers>=4.51.3 (Qwen2.5-VL) and a Diffusers
# build that ships QwenImagePipeline / QwenImageEditPlusPipeline.
```

CUDA GPU required. First run downloads tens of GB of weights.

## Environment

```bash
# Optional overrides (defaults shown)
# QWEN_IMAGE_LOCAL_MODEL_ID=Qwen/Qwen-Image-2512
# QWEN_IMAGE_EDIT_MODEL_ID=Qwen/Qwen-Image-Edit-2511
# QWEN_IMAGE_LOCAL_PATH=/path/to/local/t2i-snapshot
# QWEN_IMAGE_EDIT_PATH=/path/to/local/edit-snapshot
# HF_TOKEN=...   # only if the Hub repo is gated for your account
```

## CLI

```bash
opentryon generate --model qwen-image-local \
  --prompt "editorial lookbook, linen trench on a sunlit terrace" \
  --aspect-ratio 16:9 --seed 42
# Optional: --model-id Qwen/Qwen-Image  (original 20B T2I)

opentryon edit --model qwen-image-local \
  --images person.jpg \
  --prompt "Change the jacket to black leather, keep the face and pose."

opentryon vton --model qwen-image-local \
  --person-image model.jpg --garment-image garment.jpg \
  --garment-description "olive green bomber jacket"
```

Pair with local or hosted understand:

```bash
opentryon understand --model qwen3.8 --image garment.jpg \
  --prompt "Describe this garment: category, color, fabric, cut."
```

## MCP

- `generate_qwen_image_local`
- `edit_qwen_image_local`
- `vton_qwen_image_local`

Requires `pip install opentryon[local]` on the machine running the MCP server.

## Python

```python
from tryon.models import QwenImageLocalAdapter

adapter = QwenImageLocalAdapter()  # downloads 2512 / 2511 on first use

images = adapter.generate_text_to_image(
    "editorial lookbook, linen trench on a sunlit terrace",
    aspect_ratio="16:9",
    seed=42,
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
tryon[0].save("qwen_tryon_local.png")
```

Use original T2I weights and Edit-Plus 2509:

```python
adapter = QwenImageLocalAdapter(
    model_id="Qwen/Qwen-Image",
    edit_model_id="Qwen/Qwen-Image-Edit-2509",
)
```

### `QwenImageLocalAdapter`

```python
class QwenImageLocalAdapter:
    def __init__(
        self,
        model_id: Optional[str] = None,       # T2I HF id / path
        edit_model_id: Optional[str] = None,  # Edit HF id / path
        device: Optional[str] = None,         # cuda required
        dtype: str = "bfloat16",
        cpu_offload: bool = True,
    )
```

### Methods

- `generate_text_to_image(prompt, aspect_ratio="1:1", width=None, height=None, num_inference_steps=50, true_cfg_scale=4.0, ...)`
- `generate_image_edit(image, prompt, num_inference_steps=40, ...)`
- `generate_multi_image(images, prompt, ...)` — 1–3 refs on Edit-Plus
- `generate_virtual_tryon(person, garment, prompt=None, garment_description=None, ...)`

Pipelines load lazily (T2I vs edit) so a generate-only run does not download
the edit weights.

## Hardware notes

- Full bf16 load is datacenter-class (~40GB+). `cpu_offload=True` (default)
  trades speed for VRAM.
- Community FP8 / Nunchaku / Lightning LoRA stacks exist; OpenTryOn stays on
  official Diffusers pipelines. Pass a local quantized snapshot via
  `model_id=` / `edit_model_id=` if you already have one that loads with the
  same pipeline classes.
- Do not expect Qwen-Image-2.0/3.0 DashScope quality from the 2512 open T2I
  checkpoint — they are different hosted SKUs.
- [`Qwen/Qwen-Image-Layered`](https://huggingface.co/Qwen/Qwen-Image-Layered)
  (RGBA layer decomposition) is a separate Diffusers pipeline and is **not**
  registered in OpenTryOn yet. Pass a custom snapshot only if it loads with
  `QwenImagePipeline` / `QwenImageEditPlusPipeline`.

## References

- [Qwen-Image-2512](https://huggingface.co/Qwen/Qwen-Image-2512)
- [Qwen-Image-Edit-2511](https://huggingface.co/Qwen/Qwen-Image-Edit-2511)
- [Diffusers QwenImage pipelines](https://huggingface.co/docs/diffusers/main/en/api/pipelines/qwenimage)
- [QwenLM/Qwen-Image](https://github.com/QwenLM/Qwen-Image)
- [Hosted Qwen-Image API](../api-reference/qwen-image.md)
