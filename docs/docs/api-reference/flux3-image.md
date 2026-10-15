---
sidebar_position: 6
title: FLUX 3 Image
description: Generate and edit images with Black Forest Labs FLUX 3 Image — resolution tiers, multi-reference composition, and optional grounding.
keywords:
  - FLUX 3
  - FLUX 3 Image
  - image generation
  - image editing
  - BFL AI
  - grounding
---

# FLUX 3 Image

[FLUX 3 Image](https://docs.bfl.ml/flux_3/flux3_image_overview) is Black Forest Labs' unified still-image endpoint: one model handles text-to-image, edits, and compositions from up to **10** reference images. OpenTryOn exposes it as **`flux3-image`** on the `generate` and `edit` services (same adapter class, same `BFL_API_KEY`). For video, see **[FLUX 3 Video](flux3-video)** (`flux3-video`).

## Prerequisites

```bash
BFL_API_KEY=your_bfl_api_key
```

Sign up and create a key in the [BFL dashboard](https://docs.bfl.ml/).

## CLI

```bash
# Text-to-image
opentryon generate --model flux3-image \
  --prompt "Editorial fashion still, soft window light" \
  --aspect-ratio 3:4 --resolution 2k

# Edit with one reference
opentryon edit --model flux3-image \
  --image data/model-1.jpg \
  --prompt "Change the blazer to deep burgundy velvet"

# Dry-run (no API call)
opentryon generate --model flux3-image --prompt "test" --dry-run
```

### Notable flags

| Flag | Default | Notes |
| --- | --- | --- |
| `--aspect-ratio` | `auto` | Many ratios plus `auto` (follows first reference or prompt) |
| `--resolution` | `1k` | `768sq`, `1k`, `1.5k`, `2k`, `4k` |
| `--safety-tolerance` | `2` | `0` (strictest) through `4` |
| `--no-grounding` | grounding on | Skip web/image search pre-step for faster runs |
| `--reference-images` | — | **Edit only** — extra refs beyond `--image` (10 total) |

Layout control uses **bounding boxes in the prompt** (JSON on a 0–1000 grid); see the [BFL bounding-box tutorial](https://docs.bfl.ml/flux_3/flux3_image_bounding_boxes).

## Python

```python
from tryon.api import Flux3ImageAdapter

adapter = Flux3ImageAdapter()

images = adapter.generate_text_to_image(
    prompt="Minimal product photo on warm stone",
    aspect_ratio="16:9",
    resolution="1k",
)

images[0].save("outputs/flux3_t2i.png")

edited = adapter.generate_image_edit(
    prompt="Replace the background with a runway set",
    input_image="data/model-1.jpg",
    resolution="2k",
)
edited[0].save("outputs/flux3_edit.png")
```

## MCP

After registry changes, restart the MCP server. Tools are generated from the registry:

- `generate_flux3_image`
- `edit_flux3_image`

Both unlock when `BFL_API_KEY` is set in the OpenTryOn `.env` (Studio Connect passthrough).

## API details

- **Submit:** `POST https://api.bfl.ai/v1/flux-3-image` with `x-key`
- **Poll:** use the returned `polling_url` until `status` is `Ready`
- **Download:** `result.sample` (signed URL; download within about one hour)
- **Rejected fields:** FLUX.2-only fields such as `width`, `height`, and `seed` return HTTP 422 on this endpoint

## Related

- [FLUX.2 Image Generation](./flux2) — separate PRO/FLEX endpoints with pixel width/height
- Virtual try-on remains on the dedicated `flux-vto` model (`vton` service); see [CLI](../getting-started/cli.md).
