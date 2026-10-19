---
sidebar_position: 3
title: Roadmap
description: OpenTryOn roadmap — v0.0.8 invoke-layer expansion shipped; next is Fashion ML Toolkit Core toward v0.1.0
---

# Roadmap

> **Last Updated**: 19 October 2026 · **Current release**: [v0.0.8](https://pypi.org/project/opentryon/0.0.8/) · **Next**: **v0.1.0 Fashion ML Toolkit Core**

Canonical file: [`ROADMAP.md`](https://github.com/tryonlabs/opentryon/blob/main/ROADMAP.md) · Strategy: [`VISION.md`](https://github.com/tryonlabs/opentryon/blob/main/VISION.md)

**Audience priority:** fashion AI/ML engineers · agent builders · app builders · fashion companies (train + MCP) · CLI-first developers.

**v0.1.0 exit criteria:** train pack → LoRA finetune → garment/identity eval + Fashion Bench v0 → invoke via CLI/MCP → one agentic fashion workflow — without assembling five research repos. Outline: [Fashion ML Engineer Path](../getting-started/fashion-ml).

## Shipped — v0.0.3 – v0.0.8 (Phase 0: invoke layer)

- Unified **CLI** + **FastMCP** (shared registry / `invoke_model`)
- Broad cloud try-on / generate / edit / video / understand adapters
- **v0.0.4:** LTX-2.5 (API + local), Hailuo 2.3, Wan (API + local 2.2), Runway Gen-4.5, Qwen3.8 (API + local)
- **v0.0.5:** dedicated VTON (Google Vertex, OutfitAnyone-Plus, Photoroom, Leffa, CatVTON), ChatGPT Images 2.5, MiniMax H3 / H3 Max + Fal H3 Max, NVIDIA NIM, Hy4, Muse Image, Qwen-Image, Wan 3.0, planner as registry super-agent
- **v0.0.6:** new `decide` (Jev, Liquid d1, THX-01) and `embed` (EmbeddingGemma 2, pplx-embed-v2-late) services, `tts` (ElevenLabs, Gemini), Gemini 3.8 Flash, Claude Haiku 5.5, Nano Banana 2.1, FLUX 3 Image, Qwen-Image-2.1, FASHN VTON 1.5 (local, Apache-2.0), Veo 3.1 / Omni 1.1 / Seedance references, Cosmos 3 local, DeepSeek
- **v0.0.7:** FASHN catalogue endpoints (product-to-model, model swap, face-to-model, reframe, image-to-video), fashion retrieval embeddings (Marqo-FashionSigLIP, MODA, ZooClaw), Fashion Florence tagger, Extract-Outfit, klein-4B try-on (Apache-2.0 stack), try-on safety classifier (new `classify` service); root wrapper scripts removed
- **v0.0.8:** Clad body measurement (new `measure` service), FLUX 3 Image Klein (API + local) and FLUX 3 Video, NVIDIA LipSync (`audio-to-video`), TRELLIS (`generate-3d`), SANA-Sprint, Nemotron 3.5 Super VL, VideoJev, Gemini Embedding 2
- **OpenAPI / Postman** media snapshots, docs, Gradio demos
- Local extras (FLUX.2 Turbo, Kimi-VL, LLaVA-NeXT, BEN2, LTX-2.5, Wan 2.2, Qwen3.8, Qwen-Image, Leffa, CatVTON, MiniMax H3)
- Web UI in **[TryOn Studio](../getting-started/tryon-studio)** over **[MCP](../getting-started/mcp)**

## Next — Fashion ML Toolkit Core → v0.1.0

| Slice | Focus |
|---|---|
| **A — Data & prompts** | Versioned prompt packs, train-pack schema, `data` CLI helpers |
| **B — Train** | Brand-style LoRA + one VTON/local LoRA path; `opentryon train` |
| **C — Eval** | Fashion Bench v0, side-by-side reports; `opentryon eval` |
| **D — Local VTON** | **Leffa** + **CatVTON** shipped in v0.0.5 (`opentryon[local]`) |
| **E — Workflows** | MCP-native Try-On QA *or* Fine-Tune Coach (task agent, not chatbot) |
| **F — Efficiency card** | VRAM/latency table for the path we actually ship |

**v0.0.4** – **v0.0.8** shipped as intermediate tags; **v0.1.0** when A–E work end-to-end.

Fashion-only for this phase. Prompt datasets, fashion datasets, workflows, and agentic fashion workflows are **in scope**. Generic multi-domain / full LLM–VLM platform work waits until fashion patterns prove out.

## Later

- Broader quantization / distillation / serving recipes
- Full fashion agents suite (PDP, lookbook, router, return-risk, …)
- Async / batch / caching DX · video VTON / 3D VTON
- Adjacent domains only after fashion train/eval/agent recipes are solid

## Contribute

Good first issues: prompt packs, bench pairs, docs, dry-run tests.  
High-value: LoRA recipes, Fashion Bench metrics, first local VTON, first MCP workflow.

Vendor / model queue (separate from these slices): [Integrate next](integrate-next).

Follow the [new-model checklist](../advanced/new-model-checklist) or join [Discord](https://discord.gg/T5mPpZHxkY).
