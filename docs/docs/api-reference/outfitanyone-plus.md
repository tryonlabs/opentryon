---
sidebar_position: 9
title: OutfitAnyone-Plus
description: Alibaba DashScope aitryon-plus — dedicated person + garment try-on (Beijing region)
---

# OutfitAnyone-Plus (`aitryon-plus`)

First-party Alibaba Cloud Model Studio dedicated try-on. Person photo + flat-lay garment(s) → one try-on still. Supports a single top (random bottoms), single bottoms (random top), top+bottoms combo, or a dress/jumpsuit on `top_garment_url`.

This is **not** Qwen-Image composition (`--model qwen-image`). Same `DASHSCOPE_API_KEY` family, but the published API is **China (Beijing) only**.

| CLI `--model` | MCP tool | Adapter | Upstream id |
|---|---|---|---|
| `outfitanyone-plus` | `vton_outfitanyone_plus` | `OutfitAnyonePlusAdapter` | `aitryon-plus` |

Official docs: [aitryon-plus API](https://www.alibabacloud.com/help/en/model-studio/aitryon-plus-api)

## Auth

A Beijing-region Model Studio key.

```bash
export DASHSCOPE_API_KEY=sk-...
# Optional host (default is China DashScope):
# export OUTFITANYONE_BASE_URL=https://dashscope.aliyuncs.com/api/v1
# Workspace:
# export OUTFITANYONE_BASE_URL=https://{WorkspaceId}.cn-beijing.maas.aliyuncs.com/api/v1
```

International DashScope keys used for Qwen-Image / Wan will **not** unlock this model. Create a Beijing key from [Model Studio](https://www.alibabacloud.com/help/en/model-studio/get-api-key).

## Inputs

- Person: one complete, full-body, front-facing subject. 5 KB–5 MB, 150–4096 px, JPG/PNG/BMP/HEIC.
- Garment: flat-lay, one item, clean background. Same size limits.
- At least one of top (or dress) / bottoms.
- Public HTTP(S) URLs are passed through. Local files, PIL images, and bytes are uploaded to DashScope temporary OSS (48h) and sent as `oss://` with `X-DashScope-OssResourceResolve: enable`.

Keep-original-bottoms (or top) is a two-step vendor flow using companion `aitryon-parsing-v1`. OpenTryOn does not wrap that parsing API yet — pass the segmented URL as `--bottom-garment-image` (or `--garment-image`) yourself.

## CLI

```bash
opentryon vton --model outfitanyone-plus \
  --person-image person.jpg \
  --garment-image top.jpeg

opentryon vton --model outfitanyone-plus \
  --person-image person.jpg \
  --garment-image top.jpeg \
  --bottom-garment-image pants.jpeg \
  --resolution -1

opentryon vton --model outfitanyone-plus \
  --person-image person.jpg \
  --garment-image dress.jpg \
  --dry-run
```

`--resolution -1` (default) matches the person image; `1024` is 576×1024; `1280` is 720×1280. `--no-restore-face` generates a random face.

## Python

```python
from tryon.api import OutfitAnyonePlusAdapter

adapter = OutfitAnyonePlusAdapter()  # DASHSCOPE_API_KEY
images = adapter.generate_and_decode(
    person="person.jpg",
    garment="top.jpeg",
    restore_face=True,
    resolution=-1,
)
images[0].save("worn.png")
```

## Planner / Studio

Name **`outfitanyone-plus`**, **`aitryon-plus`**, or **OutfitAnyone** in chat to pin this model. The VTON default stays `kling-ai`. After MCP restart, Connect lists it under **Alibaba DashScope** (`DASHSCOPE_API_KEY`).
