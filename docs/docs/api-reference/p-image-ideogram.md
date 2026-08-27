---
sidebar_position: 9
title: P-Image-Ideogram
description: Pruna × Ideogram text-to-image via Pruna predictions (thinking levels, 1K/2K).
keywords:
  - P-Image-Ideogram
  - Pruna
  - Ideogram
  - text to image
  - thinking
---

# P-Image-Ideogram

[P-Image-Ideogram](https://ideogram.ai/tools/p-image-ideogram/) is a fast text-to-image model from **Pruna × Ideogram**. OpenTryOn integrates the **Pruna predictions API** (`Model: p-image-ideogram`) — the same client as the rest of the P-Image family.

| CLI model | MCP tool | Adapter | Auth |
|---|---|---|---|
| `p-image-ideogram` | `generate_p_image_ideogram` | `PImageIdeogramAdapter` | `PRUNA_API_KEY` |

**No open weights.** Studio Image → Generate picks it up from the live MCP catalog after an MCP restart.

This is **not** Ideogram 4.0 (`generate --model ideogram` / `IDEOGRAM_API_KEY`). Ideogram also publishes a first-party `POST /v1/text-to-image/p-image-ideogram` (four Quality levels, no Very High). We did not add a second hoster id; use Pruna for the five-level `thinking` surface.

## Environment

```bash
export PRUNA_API_KEY=...
# export PRUNA_BASE_URL=https://api.pruna.ai
```

Key from the [Pruna dashboard](https://dashboard.pruna.ai/login). Sent as the `apikey` header.

## Thinking vs resolution

Pruna `thinking` values (CLI uses hyphens; the adapter maps them to the API strings):

| CLI / MCP | API `thinking` | 1K price (list) | Typical use |
|---|---|---|---|
| `very-low` | `"very low"` | $0.003 | Drafts, A/B, high volume |
| `low` | `"low"` | $0.0075 | Simple prompts at scale |
| `medium` | `"medium"` | $0.01 | Balanced production |
| `high` (default) | `"high"` | $0.015 | Complex prompts, everyday production |
| `very-high` | `"very high"` | $0.033 | Hero assets; slowest (~5.5s+ at 1K) |

`image_size` is `1K` (default) or `2K` (ignored when `--aspect-ratio custom`). **Typography:** use `high` or `very-high` at **2K**, keep copy short, and add an `Exact visible text only:` / `CRITICAL TYPOGRAPHY:` block. Difficult text does not work well at `very-low` / `low`.

Prompt upsampling is **on** by default. Pass `--no-prompt-upsampling` (MCP `prompt_upsampling: false`) for final JSON specs or exact on-image text.

JSON prompts follow the [Ideogram 4.0 structured-caption schema](https://docs.ideogram.ai/) (`high_level_description` + `compositional_deconstruction`).

## CLI

```bash
opentryon generate --model p-image-ideogram \
  --prompt 'Lookbook cover. Exact visible text only: "ATELIER NOIR"' \
  --thinking high --image-size 2K --aspect-ratio 3:4

# Fast draft
opentryon generate --model p-image-ideogram \
  --prompt "editorial street style, no logos, no text" \
  --thinking very-low --no-prompt-upsampling
```

## Python

```python
from tryon.api.pruna import PImageIdeogramAdapter

images = PImageIdeogramAdapter().generate_text_to_image(
    prompt='Lookbook cover. Exact visible text only: "ATELIER NOIR"',
    thinking="high",
    image_size="2K",
    aspect_ratio="3:4",
)
images[0].save("p-image-ideogram.jpg")
```

## Notes

- Endpoint: `POST https://api.pruna.ai/v1/predictions` with headers `Model: p-image-ideogram` and `Try-Sync: true` (poll if needed). Rate limit: 500 rpm.
- Defaults match Pruna: `thinking=high`, `aspect_ratio=1:1`, `image_size=1K`, `prompt_upsampling=true`, `output_format=jpg`.
- Custom size: `--aspect-ratio custom --width … --height …` (0–2560, multiple of 16).
- TryOn Studio: Connect → Pruna (`PRUNA_API_KEY`); Image generate model `p-image-ideogram`. Chat: name `p-image-ideogram` (otherwise generate defaults to `nano-banana-pro`). Saying only “ideogram” still pins Ideogram 4.0.
- Provider docs: [Pruna P-Image-Ideogram](https://docs.pruna.ai/en/stable/docs_pruna_endpoints/performance_models/p-image-ideogram.html)

## See also

- [Pruna AI family](pruna)
- [Ideogram 4.0](ideogram)
- [Unified CLI](../getting-started/cli)
