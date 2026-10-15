---
sidebar_position: 7
title: FLUX 3 Image Klein
description: Generate and edit images with Black Forest Labs FLUX 3 Image Klein — faster distilled API sibling to FLUX 3 Image.
keywords:
  - FLUX 3
  - FLUX 3 Image Klein
  - Klein
  - image generation
  - image editing
  - BFL AI
---

# FLUX 3 Image Klein

[FLUX 3 Image Klein](https://docs.bfl.ml/flux_3/flux3_image_klein) is Black Forest Labs' compact, open-weights sibling to [FLUX 3 Image](flux3-image). The hosted API uses the same unified contract: text-to-image, edits, multi-reference composition (up to **10** images), and bounding-box layout prompts — without the full model's **grounding** field. OpenTryOn exposes it as **`flux3-image-klein`** on `generate` and `edit` (same `BFL_API_KEY` as FLUX.2 / FLUX 3 Image / FLUX 3 Video).

## Prerequisites

```bash
BFL_API_KEY=your_bfl_api_key
```

Sign up and create a key in the [BFL dashboard](https://docs.bfl.ml/).

## CLI

```bash
# Text-to-image (distilled default ~16 steps on the API)
opentryon generate --model flux3-image-klein \
  --prompt "Editorial fashion still, soft window light" \
  --aspect-ratio 3:4 --resolution 2k

# Reproducible output
opentryon generate --model flux3-image-klein \
  --prompt "Lookbook flat lay" --seed 42 --steps 12

# Edit with one reference
opentryon edit --model flux3-image-klein \
  --image data/model-1.jpg \
  --prompt "Change the blazer to deep burgundy velvet"

# Dry-run (no API call)
opentryon generate --model flux3-image-klein --prompt "test" --dry-run
```

### Klein vs full FLUX 3 Image

| | `flux3-image-klein` | `flux3-image` |
|---|---|---|
| Endpoint | `/v1/flux-3-image-klein` | `/v1/flux-3-image` |
| Grounding | Not supported | Optional (`--no-grounding`) |
| Safety tolerance | 0–7 | 0–4 |
| Extra knobs | `--seed`, `--steps` (1–16), `--output-format` | — |
| Exact pixels | `--width` + `--height` (overrides resolution/ratio) | Resolution tiers only |

Layout control uses the same bounding-box JSON appended to the prompt; see the [BFL bounding-box tutorial](https://docs.bfl.ml/flux_3/flux3_image_bounding_boxes).

## Python

```python
from tryon.api import Flux3ImageKleinAdapter

adapter = Flux3ImageKleinAdapter()

images = adapter.generate_text_to_image(
    prompt="Editorial fashion still",
    aspect_ratio="3:4",
    resolution="2k",
    seed=0,
    steps=16,
)
images[0].save("outputs/flux3_klein_t2i.png")

edited = adapter.generate_image_edit(
    prompt="Change jacket to navy wool",
    input_image="data/model-1.jpg",
)
edited[0].save("outputs/flux3_klein_edit.png")
```

## MCP

After the OpenTryOn MCP server loads the registry:

- `generate_flux3_image_klein`
- `edit_flux3_image_klein`

## Local weights (GPU)

OpenTryOn registers local inference as **`flux3-image-klein-local`** on `generate` and `edit` (`Flux3ImageKleinLocalAdapter`, Diffusers `ModularPipeline`). See **[FLUX 3 Image Klein (local)](../local-models/flux3-image-klein)** for install, VRAM notes, and CLI examples. Default weights: `black-forest-labs/flux-3-image-klein`; base checkpoint via `--model-id black-forest-labs/flux-3-image-klein-base`.
