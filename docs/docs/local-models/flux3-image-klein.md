---
sidebar_position: 21
title: FLUX 3 Image Klein (local)
description: Text-to-image and multi-reference edits with open FLUX.3 Klein weights via Diffusers ModularPipeline.
keywords:
  - FLUX 3
  - Klein
  - local
  - diffusers
  - ModularPipeline
---

# FLUX 3 Image Klein (local)

[FLUX 3 Image Klein](https://docs.bfl.ml/flux_3/flux3_image_klein) ships open weights on Hugging Face. OpenTryOn exposes **`flux3-image-klein-local`** on `generate` and `edit` (Path B, `extra="local"`). For the BFL hosted API, use **[FLUX 3 Image Klein (API)](../api-reference/flux3-image-klein)** (`flux3-image-klein`, `BFL_API_KEY`).

## Requirements

```bash
pip install opentryon[local]
pip install -U diffusers transformers
```

Accept the FLUX Kommunity License on Hugging Face for the checkpoint you use.

| Checkpoint | HF id | Typical use |
|---|---|---|
| Distilled (default) | `black-forest-labs/flux-3-image-klein` | Fast T2I / edit (~16 steps, no CFG) |
| Base | `black-forest-labs/flux-3-image-klein-base` | Fine-tuning / LoRA (~50 steps, CFG) |

Override with `--model-id` or `FLUX3_IMAGE_KLEIN_MODEL_ID`.

**VRAM:** BFL targets consumer GPUs (e.g. RTX 3090+). Quantized single-file variants (`fp8r`, `nvfp4`) are documented on [Hugging Face](https://huggingface.co/blog/flux-3) but not auto-selected by this adapter yet.

## CLI

```bash
# Text-to-image (1024×1024 default)
opentryon generate --model flux3-image-klein-local \
  --prompt "Editorial fashion still, soft window light" \
  --seed 0

# Base checkpoint with CFG
opentryon generate --model flux3-image-klein-local \
  --model-id black-forest-labs/flux-3-image-klein-base \
  --guidance-scale 3.5 --steps 50 \
  --prompt "Lookbook flat lay on white seamless"

# Edit / restyle
opentryon edit --model flux3-image-klein-local \
  --image data/model-1.jpg \
  --prompt "Change the blazer to deep burgundy velvet"

# Multi-reference (order matches <ref_image_0>, <ref_image_1>, … in prompt)
opentryon edit --model flux3-image-klein-local \
  --image person.jpg --reference-images garment.jpg \
  --prompt "Dress the person from <ref_image_0> in the outfit from <ref_image_1>"

opentryon generate --model flux3-image-klein-local --prompt "test" --dry-run
```

Layout control uses the same bounding-box JSON appended to the prompt as the [BFL Klein guide](https://docs.bfl.ml/flux_3/flux3_image_klein).

## Python

```python
from tryon.models import Flux3ImageKleinLocalAdapter

adapter = Flux3ImageKleinLocalAdapter()
images = adapter.generate_text_to_image(
    prompt="Editorial fashion still",
    width=1024,
    height=1024,
    seed=0,
)
images[0].save("klein_local.png")
```

## MCP

Restart MCP after registry changes. Tools: `generate_flux3_image_klein_local`, `edit_flux3_image_klein_local`.
