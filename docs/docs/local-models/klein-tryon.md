---
sidebar_position: 24
title: FLUX.2-klein-4B try-on LoRA (local)
description: Community try-on LoRA on FLUX.2 klein 4B — an Apache-2.0 base and LoRA, so a commercially clean local try-on stack.
keywords:
  - FLUX.2 klein
  - klein-4B
  - virtual try-on
  - LoRA
  - Apache-2.0
  - local
---

# FLUX.2-klein-4B try-on LoRA (local)

[`xocialize/tryon-FLUX.2-klein-4B-lora`](https://huggingface.co/xocialize/tryon-FLUX.2-klein-4B-lora) is a rank-32 edit LoRA for [`black-forest-labs/FLUX.2-klein-4B`](https://huggingface.co/black-forest-labs/FLUX.2-klein-4B) that dresses a person in a specified top and bottom, preserving identity, pose and background. OpenTryOn runs it as `klein-4b-tryon` in the `vton` service (Path B, `extra="local"`).

**Why it matters:** the base (FLUX.2 klein 4B, distilled, about 13 GB VRAM) and the LoRA are both **Apache-2.0**. The more popular klein *9B* try-on LoRAs (for example `fal/flux-klein-9b-virtual-tryon-lora`) sit on a base released under the FLUX Non-Commercial License, which blocks commercial use. Compare with [FASHN VTON 1.5](fashn-vton.md) (Apache-2.0, maskless, single garment), [Leffa](leffa.md) and [CatVTON](catvton.md).

:::caution v1 community LoRA — validate before relying on it
Trained on only 273 full-body tuples (Pexels frames, step-2000 checkpoint) with **no published metrics**. Known limits from the card: nearby objects can leak into the bottom garment crop (faint artifacts) and all-dark outfits are the weakest case. The card gives no sampler settings, so the defaults here are BFL's klein-4B defaults (4 steps, guidance 1.0) — tune them on your data. No GPU was available when this was integrated; the adapter is tested against a stubbed pipeline (reference order, masking, LoRA load order), not real weights.
:::

## Inputs (order is load-bearing)

| Slot | Flag | What to pass |
|---|---|---|
| 1 — person | `--person-image` | Full-body photo, **clothing-agnostic** (outfit region greyed) |
| 2 — top | `--top-image` | Isolated upper-body garment, product-style |
| 3 — bottom | `--bottom-image` | Isolated lower-body garment |
| (one-piece) | `--dress-image` | A dress or jumpsuit: used for **both** the top and bottom slots |

**This adapter does not segment clothing.** Either pass an already clothing-agnostic person image, or pass `--mask-image` (white = the clothing region to replace) and the adapter greys that area (RGB 128) before inference. Any parser can produce the mask; note that `fashn-human-parser` and `segformer_b2_clothes` (the one the LoRA author used) carry their own licences — check them before commercial use. The garments must be isolated crops; the LoRA was trained on both a top and a bottom, so both (or a dress) are required.

## Requirements

```bash
pip install opentryon[local]
pip install git+https://github.com/huggingface/diffusers.git peft accelerate
```

`Flux2KleinPipeline` is not in a stable diffusers release yet. CUDA GPU, about 13 GB+ VRAM (CPU offload is on by default). Overrides: `KLEIN_TRYON_LORA_ID`, `KLEIN_TRYON_BASE_ID` (or `--lora-id` / `--base-model-id`).

## CLI

```bash
# Separate top and bottom, person already agnostic
opentryon vton --model klein-4b-tryon \
  --person-image person_agnostic.png --top-image shirt.png --bottom-image jeans.png

# Let the adapter grey out the clothing region from a mask
opentryon vton --model klein-4b-tryon \
  --person-image person.jpg --mask-image clothing_mask.png \
  --top-image shirt.png --bottom-image jeans.png --seed 7

# One-piece garment
opentryon vton --model klein-4b-tryon --person-image person_agnostic.png --dress-image dress.png
```

Output size defaults to the person image's size, with the long side capped at 1024 and snapped to multiples of 16 (`--height` / `--width` override). Other flags: `--prompt` (must start with `TRYON`; the default is the LoRA's trigger prompt), `--steps` (default 4), `--guidance-scale` (default 1.0), `--seed`, `--num-images`, `--dtype`, `--no-cpu-offload`.

## Python

```python
from tryon.models.klein_tryon import Klein4BTryOnAdapter

adapter = Klein4BTryOnAdapter()
images = adapter.generate_and_decode(person="person.jpg", mask="mask.png", top="shirt.png", bottom="jeans.png")
images[0].save("tryon.png")
```

## Notes

- MCP tool: `vton_klein_4b_tryon`. Planner pins: `klein 4b tryon`, `klein-4b-tryon`. The `vton` default stays `kling-ai`.
- The weight file is `tryon-klein-4b.safetensors` (rank 32, "BFL-fused" dialect); if your diffusers build cannot load it, update diffusers from GitHub.
