---
sidebar_position: 3
title: Roadmap
description: OpenTryOn roadmap — v0.0.4 media expansion shipped; next is Fashion ML Toolkit Core toward v0.1.0
---

# Roadmap

> **Last Updated**: 17 August 2026 · **Current release**: [v0.0.4](https://pypi.org/project/opentryon/0.0.4/) · **Next**: **v0.1.0 Fashion ML Toolkit Core**

Canonical file: [`ROADMAP.md`](https://github.com/tryonlabs/opentryon/blob/main/ROADMAP.md) · Strategy: [`VISION.md`](https://github.com/tryonlabs/opentryon/blob/main/VISION.md)

**Audience priority:** fashion AI/ML engineers · agent builders · app builders · fashion companies (train + MCP) · CLI-first developers.

**v0.1.0 exit criteria:** train pack → LoRA finetune → garment/identity eval + Fashion Bench v0 → invoke via CLI/MCP → one agentic fashion workflow — without assembling five research repos. Outline: [Fashion ML Engineer Path](../getting-started/fashion-ml).

## Shipped — v0.0.3 / v0.0.4 (Phase 0: invoke layer)

- Unified **CLI** + **FastMCP** (shared registry / `invoke_model`)
- Broad cloud try-on / generate / edit / video / understand adapters
- **v0.0.4:** LTX-2.5 (API + local), Hailuo 2.3, Wan (API + local 2.2), Runway Gen-4.5, Qwen3.8 (API + local)
- **OpenAPI / Postman** media snapshots, docs, Gradio demos
- Local extras (FLUX.2 Turbo, Kimi-VL, LLaVA-NeXT, BEN2, LTX-2.5, Wan 2.2, Qwen3.8)
- Web UI in [`tryon-studio`](https://github.com/tryonlabs/tryon-studio) over MCP

## Next — Fashion ML Toolkit Core → v0.1.0

| Slice | Focus |
|---|---|
| **A — Data & prompts** | Versioned prompt packs, train-pack schema, `data` CLI helpers |
| **B — Train** | Brand-style LoRA + one VTON/local LoRA path; `opentryon train` |
| **C — Eval** | Fashion Bench v0, side-by-side reports; `opentryon eval` |
| **D — Local VTON** | Productize **one** of CatVTON / IDM-VTON / OOTDiffusion |
| **E — Workflows** | MCP-native Try-On QA *or* Fine-Tune Coach (task agent, not chatbot) |
| **F — Efficiency card** | VRAM/latency table for the path we actually ship |

Intermediate tags `0.0.4` / `0.0.5` as slices land; **v0.1.0** when A–E work end-to-end.

Fashion-only for this phase. Prompt datasets, fashion datasets, workflows, and agentic fashion workflows are **in scope**. Generic multi-domain / full LLM–VLM platform work waits until fashion patterns prove out.

## Later

- Broader quantization / distillation / serving recipes
- Full fashion agents suite (PDP, lookbook, router, return-risk, …)
- Async / batch / caching DX · video VTON / 3D VTON
- Adjacent domains only after fashion train/eval/agent recipes are solid

## Contribute

Good first issues: prompt packs, bench pairs, docs, dry-run tests.  
High-value: LoRA recipes, Fashion Bench metrics, first local VTON, first MCP workflow.

Follow the [new-model checklist](../advanced/new-model-checklist) or join [Discord](https://discord.gg/T5mPpZHxkY).
