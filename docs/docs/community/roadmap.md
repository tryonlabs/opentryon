---
sidebar_position: 3
title: Roadmap
description: What shipped in OpenTryOn v0.0.3 and what remains on the toolkit roadmap
---

# Roadmap

> **Last Updated**: 2 August 2026 · **Current release**: [v0.0.3](https://pypi.org/project/opentryon/0.0.3/)

The canonical roadmap file in the repo is [`ROADMAP.md`](https://github.com/tryonlabs/opentryon/blob/main/ROADMAP.md). Product strategy: [`VISION.md`](https://github.com/tryonlabs/opentryon/blob/main/VISION.md).

## Shipped — v0.0.3

- Unified **`opentryon` CLI** and **FastMCP server** (same registry + `invoke_model()`)
- **OpenAPI / Swagger** snapshot and **Postman** collection for upstream media APIs
- Broad cloud coverage: try-on, generate/edit, video, understanding, bg-remove
- Providers including Pruna (full image/video suite), Seedance/Seedream, Kling 3, Luma Ray 3.2, Grok Imagine, Ideogram, FASHN, Gemini Omni, Kimi, Nano Banana family, FLUX / GPT / Sora / Veo, and more
- Local extras: FLUX.2-dev Turbo, Kimi-VL, LLaVA-NeXT, BEN2
- Web UI moved to [`tryon-studio`](https://github.com/tryonlabs/tryon-studio) (MCP client)

## Remaining — near term

- Local OSS VTON (CatVTON / IDM-VTON / OOTDiffusion or FLUX-fill paths)
- Train / LoRA recipes and fashion fine-tune notebooks
- Prompt packs + lightweight garment/identity evals
- Deeper Studio features over MCP
- Additional datasets (DeepFashion, FashionGen, …)

## Remaining — later

- Quantization / distillation / serving recipes for local models
- Fashion agents v1 (PDP, try-on QA, lookbook, model-swap, prompts)
- Async / batch / caching DX improvements
- Video VTON / 3D VTON exploration
- Additional providers (Qwen-Image, more open weights)

## Contribute

Pick up a `good first issue`, follow the [new-model checklist](../advanced/new-model-checklist), or join [Discord](https://discord.gg/T5mPpZHxkY).
