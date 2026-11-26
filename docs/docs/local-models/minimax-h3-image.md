---
sidebar_position: 6
title: MiniMax H3-Image (local)
description: Open-weight MiniMax H3-Image text-to-image and multi-reference edit via Hugging Face Diffusers ModularPipeline.
keywords:
  - MiniMax H3-Image
  - Diffusers
  - local image
  - open weights
---

# MiniMax H3-Image (local Diffusers)

Open-weight [MiniMax H3-Image](https://huggingface.co/MiniMaxAI/MiniMax-H3-Image) via Hugging Face Diffusers `ModularPipeline` (`text2image` / `image_conditioned`). Distilled **6-step** sampling (no `num_inference_steps` knob). Hosted twin: [MiniMax H3-Image (API)](../api-reference/minimax-h3-image.md) (`--model minimax-h3-image`).

This is **image only** — [MiniMax H3 (local video)](./minimax-h3.md) is a separate checkpoint for `video-generate`.

## License

Same **MiniMax H3 Community License** regional limits as [MiniMax H3 video](./minimax-h3.md) for local weights. The hosted image API is globally available.

## Requirements

| Item | Notes |
|------|--------|
| GPU | CUDA strongly recommended. Transformer ~62GB bf16; text encoder shares MiniMax-H3's Qwen3-VL stack (~62GB). |
| Host RAM | ~75GB+ typical with `ComponentsManager` auto CPU offload (default in the adapter). |
| Diffusers | `diffusers>=0.43.0` with `MiniMaxH3ImageModularPipeline` |
| Disk | Large HF snapshot; text encoder may dedupe with an existing `MiniMaxAI/MiniMax-H3` download |

```bash
pip install opentryon[local]
pip install -U 'diffusers>=0.43.0'
export HF_TOKEN=hf_...   # if needed
```

Optional:

```bash
export MINIMAX_H3_IMAGE_MODEL_ID=MiniMaxAI/MiniMax-H3-Image
```

## CLI

```bash
opentryon generate --model minimax-h3-image-local \
  --prompt "Overhead farm-to-table spread on weathered wood, film grain" \
  --width 2048 --height 1536 --seed 42

opentryon edit --model minimax-h3-image-local \
  --images reference.png \
  --prompt "Keep everything in <Picture 1>, remove the headphones" \
  --width 2048 --height 2048
```

Multi-reference: pass several `--images` and refer to `<Picture 1>`, `<Picture 2>`, … in the prompt (see [Diffusers docs](https://huggingface.co/docs/diffusers/api/pipelines/minimax_h3_image)).

## Python

```python
from tryon.models import MiniMaxH3ImageLocalAdapter

adapter = MiniMaxH3ImageLocalAdapter()
images = adapter.generate_text_to_image(
    prompt="Editorial sneaker on concrete, hard shadow",
    width=2048,
    height=1536,
    seed=0,
)
images[0].save("out.png")
```

## Prompting

- Long, explicit descriptions work best; there is no chat template.
- Edits: state what to preserve, what to change, then describe the target scene. Reference pictures by index in natural language or `<Picture N>`.