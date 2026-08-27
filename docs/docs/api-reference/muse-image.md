---
sidebar_position: 24
title: Muse Image (Meta Model API)
description: First-party Meta Muse Image generate, edit, and multi-reference composition via Meta Model API.
keywords:
  - Muse Image
  - Meta
  - Meta Model API
  - image generation
  - image editing
---

# Muse Image (Meta Model API)

First-party [Muse Image](https://ai.meta.com/blog/introducing-muse-image-muse-video-msl/) from Meta Superintelligence Labs, served on [Meta Model API](https://ai.developer.meta.com/docs/overview/). One model (`muse-image-1.0`) does text-to-image, precise edits, and multi-reference composition. Agentic search/code tools run by default and are included in the per-image price.

There is **no open-weight / local path** for Muse Image. (Muse Glimmer is a separate open-weight **text** VLM, not an image generator.)

| CLI model | API `model` | Services |
|---|---|---|
| `muse-image` | `muse-image-1.0` | `generate`, `edit`, `vton` (composition) |

[Muse Video](./muse-video.md) is a consumer preview only — no developer API or weights yet.

## Environment

```bash
export MODEL_API_KEY=...          # official Meta name (dashboard → API keys)
# export META_MODEL_API_KEY=...   # OpenTryOn alias
# export META_MODEL_API_BASE_URL=https://api.meta.ai/v1
```

Create a key at the [Model API dashboard](https://dev.meta.ai/docs/authentication). Keys look like `LLM|…|…`.

## CLI

```bash
opentryon generate --model muse-image \
  --prompt "A fashion model walking a runway at dusk, editorial lighting" \
  --size 1024x1536 --output-format png

opentryon edit --model muse-image \
  --images look.jpg --prompt "Change the jacket to black leather, keep pose and face"

opentryon vton --model muse-image \
  --person-image model.jpg --garment-image garment.png \
  --garment-description "olive green bomber jacket"
```

`--size` is an **aspect hint** (`WxH`), not exact pixels. `--reasoning-strength low` skips self-refinement (faster, same $0.01/image). `--no-web-search` / `--no-image-search` / `--no-shell` turn off built-in tools.

## Python

```python
from tryon.api.muse import MuseImageAdapter

adapter = MuseImageAdapter()
images = adapter.generate_text_to_image(
    prompt="A watercolor editorial still of a red fox in snow",
    size="1536x1024",
    output_format="png",
)
images[0].save("muse.png")

edited = adapter.generate_image_edit(
    image=["look.jpg", "palette.jpg"],
    prompt="Keep the person from the first image; restyle using the second palette.",
)
```

## Notes

- Auth: `Authorization: Bearer {MODEL_API_KEY}` against `https://api.meta.ai/v1`.
- Endpoints: `POST /v1/images/generations`, `POST /v1/images/edits` (JSON `images[].image_url`).
- VTON here is **multi-image composition**, not a dedicated garment-fit model — prefer FLUX VTO / FASHN when fit accuracy matters.
- MCP tools: `generate_muse_image`, `edit_muse_image`, `vton_muse_image`.
