---
sidebar_position: 9
title: FASHN AI Virtual Try-On
description: FASHN virtual try-on (Try-On Max, v1.6) plus the catalogue endpoints — product-to-model, model-create, model-swap, face-to-model, reframe, edit, image-to-video and background-remove
keywords:
  - fashn
  - tryon-max
  - tryon-v1.6
  - virtual try-on
  - fashion
  - product to model
  - model swap
  - model create
  - face to model
---

# FASHN AI Virtual Try-On

The `FashnVTONAdapter` provides an interface to [FASHN](https://docs.fashn.ai/)'s fashion-focused virtual try-on endpoints.

## Overview

FASHN exposes a universal `POST /v1/run` + `GET /v1/status/{id}` API. This adapter covers the two primary try-on models:

| Model | Registry id | Best for |
|---|---|---|
| `tryon-max` | `fashn-tryon-max` | High-fidelity photoshoots / e-commerce catalogs (up to 4K, prompt-based styling) |
| `tryon-v1.6` | `fashn-tryon-v1.6` | Fast real-time try-on (1 credit/image, ~5–8s) |

**Open-weight twin:** FASHN open-sourced VTON v1.5 (Apache-2.0). Run it on your own GPU with `--model fashn-vton-1.5` — see [FASHN VTON v1.5 (local)](../local-models/fashn-vton.md).

**Location note:** like Pruna's P-Image-Try-On, this adapter lives under `tryon.api.vton` (a use-case directory) rather than a dedicated `tryon.api.fashn/` package -- see [Adding a New Model Integration](../advanced/new-model-checklist.md#1-decide-where-the-adapter-lives).

**References:**
- [FASHN docs](https://docs.fashn.ai/)
- [Try-On Max](https://docs.fashn.ai/api-reference/tryon-max)
- [Try-On v1.6](https://docs.fashn.ai/api-reference/tryon-v1-6)
- [Python SDK](https://docs.fashn.ai/sdk/python) (optional; this adapter uses `requests` directly)

## Authentication

```bash
export FASHN_API_KEY="your_api_key"
```

Or pass `api_key=` to the constructor. Keys are created in the [FASHN Developer API dashboard](https://app.fashn.ai/api).

## Quick Start

```python
from dotenv import load_dotenv
load_dotenv()

from tryon.api.vton import FashnVTONAdapter

adapter = FashnVTONAdapter()

# Try-On Max (recommended)
images = adapter.generate_and_decode(
    model_image="data/model-1.jpg",
    product_image="data/garment.png",
    model_name="tryon-max",
    resolution="2k",
    generation_mode="quality",
)
images[0].save("outputs/fashn_max.png")

# Try-On v1.6 (fast)
images = adapter.generate_and_decode(
    model_image="data/model-1.jpg",
    product_image="data/garment.png",
    model_name="tryon-v1.6",
    mode="performance",
)
images[0].save("outputs/fashn_v16.png")
```

## API Reference

### Class: `FashnVTONAdapter`

#### Constructor

```python
FashnVTONAdapter(api_key: Optional[str] = None, base_url: Optional[str] = None)
```

#### Methods

##### `generate(...)` / `generate_and_decode(...)`

Common person/garment aliases: `model_image` / `person` / `source_image` and
`product_image` / `garment` / `garment_image`. The adapter maps the garment
field to `product_image` (`tryon-max`) or `garment_image` (`tryon-v1.6`)
automatically.

**Shared options:** `seed`, `output_format` (`png`|`jpeg`), `return_base64`,
`max_wait_time`.

**`tryon-max` options:** `prompt`, `resolution` (`1k`|`2k`|`4k`),
`generation_mode` (`fast`|`balanced`|`quality`), `num_images` (1–4).

**`tryon-v1.6` options:** `category`, `mode`, `garment_photo_type`,
`moderation_level`, `segmentation_free`, `num_samples` (1–4).

`generate()` returns a list of CDN URLs (or data URIs when `return_base64=True`).
`generate_and_decode()` returns `List[PIL.Image.Image]`.

After a successful call, `adapter.last_prediction_id` and
`adapter.last_credits_used` are set from the response.

## Catalogue endpoints (product-to-model, model swap, …)

Beyond try-on, FASHN exposes the e-commerce photo workflow. `tryon.api.fashn.FashnAdapter` (it extends `FashnVTONAdapter`, so it uses the same `FASHN_API_KEY`, `/v1/run` + `/v1/status` protocol and image handling) wraps them:

| CLI model | Service | FASHN endpoint | What it does | Lifecycle |
|---|---|---|---|---|
| `fashn-product-to-model` | `edit` | `product-to-model` | Product photo → a person wearing it. Optional `--image-prompt` (pose/lighting), `--background-reference`, `--face-reference` | Preview |
| `fashn-model-create` | `generate` | `model-create` | Prompt (+ optional reference) → a new fashion model photo | Experimental |
| `fashn-model-swap` | `edit` | `model-swap` | Change the model's face / skin / hair, keep outfit and pose | Experimental |
| `fashn-face-to-model` | `edit` | `face-to-model` | Headshot → try-on-ready upper-body avatar (vertical ratios only) | Experimental |
| `fashn-reframe` | `edit` | `reframe` | Expand or crop to a target aspect ratio | Experimental |
| `fashn-edit` | `edit` | `edit` | Prompt edit with optional `--mask` and `--image-context` | — |
| `fashn-image-to-video` | `video-generate` | `image-to-video` | Animate a still, 5 or 10 s, 480p–1080p, optional `--end-image` | — |
| `fashn-bg-remove` | `bg-remove` | `background-remove` | Transparent-background cut-out, 1 credit | — |

**Product-to-model is not try-on.** It generates a *new* person wearing the product and does not keep an existing photo's pose or background; use `fashn-tryon-max` with a person photo for that. The usual chain for a catalogue with no studio shots is `fashn-face-to-model` → `fashn-tryon-max`, or `fashn-product-to-model` directly.

**Credits** (as published by FASHN): the image endpoints cost `generation_mode` × `resolution` (fast / balanced / quality × 1k / 2k / 4k = 1–5 credits), `--face-reference` adds +3 per image, and `--num-images` multiplies the total. Video is 1 / 3 / 6 credits for 5 s and 2 / 6 / 12 for 10 s at 480p / 720p / 1080p. Background remove is 1. If `--generation-mode` is omitted FASHN picks one and bills accordingly.

```bash
opentryon edit --model fashn-product-to-model \
  --image jacket.jpg --prompt "tucked-in, studio background" \
  --aspect-ratio 4:5 --resolution 2k --generation-mode balanced

opentryon edit --model fashn-model-swap --model-image look.jpg \
  --face-reference campaign_face.jpg --face-reference-mode match_base

opentryon generate --model fashn-model-create \
  --prompt "Full body shot, woman in a white t-shirt and dark blue biker shorts"

opentryon edit --model fashn-reframe --image look.jpg --aspect-ratio 9:16
opentryon video-generate --model fashn-image-to-video --image look.jpg --duration 5 --resolution 720p
opentryon bg-remove --model fashn-bg-remove --image product.jpg
```

```python
from tryon.api.fashn import FashnAdapter

adapter = FashnAdapter()
images = adapter.generate_product_to_model("jacket.jpg", prompt="studio background", resolution="2k")
video = adapter.generate_image_to_video("look.jpg", duration=5, resolution="720p")  # MP4 bytes
```

Image endpoints return decoded PIL images (the adapter requests base64 output, so results do not depend on CDN expiry). The adapter validates resolution tier, quality mode, `num_images` (1–4), per-endpoint aspect ratios, and that `--face-reference-mode` is only used with `--face-reference`. Pricing and parameters come from FASHN's docs (checked 13 Oct 2026); these endpoints were integrated without live calls, so confirm credit costs on your account. MCP tools: `edit_fashn_product_to_model`, `generate_fashn_model_create`, `edit_fashn_model_swap`, `edit_fashn_face_to_model`, `edit_fashn_reframe`, `edit_fashn_edit`, `video_generate_fashn_image_to_video`, `bg_remove_fashn_bg_remove`. Planner pins: `fashn product to model`, `fashn model swap`, `fashn model create`, `fashn face to model`, `fashn reframe`, `fashn edit`, `fashn image to video`.

## opentryon CLI / MCP Server

```bash
opentryon vton --model fashn-tryon-max \
  --model-image model.png --garment-image garment.png \
  --resolution 2k --generation-mode quality

opentryon vton --model fashn-tryon-v1.6 \
  --model-image model.png --garment-image garment.png --mode performance
```

MCP tools: `vton_fashn_tryon_max`, `vton_fashn_tryon_v1_6`.

## See Also

- [API Reference Overview](overview)
- [Pruna P-Image-Try-On](pruna) -- multi-garment alternative
- [FASHN documentation](https://docs.fashn.ai/)
