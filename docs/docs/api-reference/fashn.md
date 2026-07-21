---
sidebar_position: 9
title: FASHN AI Virtual Try-On
description: Fashion-focused virtual try-on using FASHN Try-On Max and Try-On v1.6
keywords:
  - fashn
  - tryon-max
  - tryon-v1.6
  - virtual try-on
  - fashion
---

# FASHN AI Virtual Try-On

The `FashnVTONAdapter` provides an interface to [FASHN](https://docs.fashn.ai/)'s fashion-focused virtual try-on endpoints.

## Overview

FASHN exposes a universal `POST /v1/run` + `GET /v1/status/{id}` API. This adapter covers the two primary try-on models:

| Model | Registry id | Best for |
|---|---|---|
| `tryon-max` | `fashn-tryon-max` | High-fidelity photoshoots / e-commerce catalogs (up to 4K, prompt-based styling) |
| `tryon-v1.6` | `fashn-tryon-v1.6` | Fast real-time try-on (1 credit/image, ~5–8s) |

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
