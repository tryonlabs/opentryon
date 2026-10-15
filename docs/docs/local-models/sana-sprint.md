---
sidebar_position: 20
title: SANA-Sprint (local)
description: Ultra-fast 1–4 step text-to-image with NVLabs SANA-Sprint via Diffusers.
keywords:
  - SANA-Sprint
  - NVLabs
  - text-to-image
  - local
  - diffusers
---

# SANA-Sprint (local)

[SANA-Sprint](https://nvlabs.github.io/Sana/Sprint/) is NVIDIA/MIT HAN Lab’s distilled flow-matching T2I model: **1–4 steps** at 1024×1024 with strong speed/quality tradeoffs. OpenTryOn exposes **`sana-sprint`** on `generate` (Path B, `extra="local"`).

## Requirements

```bash
pip install opentryon[local]
pip install "git+https://github.com/huggingface/diffusers"
```

Default weights: `Efficient-Large-Model/Sana_Sprint_1.6B_1024px_diffusers`. Override with `SANA_SPRINT_MODEL_ID`.

## CLI

```bash
opentryon generate --model sana-sprint \
  --prompt "Editorial fashion still, soft window light" \
  --steps 2 --width 1024 --height 1024

opentryon generate --model sana-sprint --prompt "test" --dry-run
```

## MCP

Restart MCP after registry changes. Tool: `generate_sana_sprint`.

## Notes

- No first-party hosted API in OpenTryOn — local only (integrate-next listed SANA-Sprint as Path B `next`).
- For cloud T2I, use existing registry models (FLUX, Nano Banana, Seedream, etc.).
