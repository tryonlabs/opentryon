---
sidebar_position: 21
title: Recraft V3
description: Recraft V3 generate, image-to-image, and background removal
---

# Recraft V3

[Recraft V3](https://www.recraft.ai/docs/api-reference/models/recraft-v3) is Recraft’s raster model for photorealism, illustration, and on-image text. OpenTryOn calls the first-party API at `https://external.api.recraft.ai/v1`.

| Registry id | Service | Method | Auth |
|---|---|---|---|
| `recraft-v3` | `generate` | `POST /images/generations` | `RECRAFT_API_TOKEN` |
| `recraft-v3` | `edit` | `POST /images/imageToImage` | `RECRAFT_API_TOKEN` |
| `recraft-v3` | `bg-remove` | `POST /images/removeBackground` | `RECRAFT_API_TOKEN` |

`RECRAFT_API_KEY` is an alias. Override the host with `RECRAFT_BASE_URL`.

Styles: `Photorealism`, `Illustration`, `Vector art`, `Recraft V3 Raw` (default). `--size` is an aspect ratio (`1:1`, `16:9`, …) or a pixel size (`1024x1024`). `--n` is 1–6. Edit `--strength` is 0 (near the original) to 1 (least similar); default 0.2.

```bash
opentryon generate --model recraft-v3 \
  --prompt "linen trench on a sunlit terrace, lookbook still" \
  --style Photorealism --size 3:4

opentryon edit --model recraft-v3 \
  --image look.jpg --prompt "the same scene in winter" --strength 0.4

opentryon bg-remove --model recraft-v3 --image product.jpg
```

This adapter pins raster `recraftv3`. Recraft V4 / V4.1 and SVG `recraftv3_vector` are not registered.

MCP tools: `generate_recraft_v3`, `edit_recraft_v3`, `bg_remove_recraft_v3`.
