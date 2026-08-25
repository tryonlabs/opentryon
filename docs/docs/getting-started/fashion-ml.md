---
sidebar_position: 7
title: Fashion ML Engineer Path
description: Outline of the train → eval → invoke → workflow path OpenTryOn is building toward v0.1.0
keywords:
  - fashion ML
  - fine-tune
  - LoRA
  - evaluation
  - Fashion Bench
  - MCP
  - agents
---

# Fashion ML Engineer Path

This page is the **outline** for AI/ML engineers who want to train, evaluate, and operate fashion models with OpenTryOn — not only call cloud APIs.

**Status:** target path for **v0.1.0 (Fashion ML Toolkit Core)**. Invoke-layer pieces below work today on **v0.0.4**; train/eval/workflow sections are planned. See the [Roadmap](../community/roadmap).

## Who this is for

- Fashion ML engineers (LoRA / local VTON / VLM finetunes)
- Fashion agent builders (MCP + CLI workflows)
- Fashion companies customizing models for brand style and catalog quality

If you only need to call providers, start with [Installation](installation) → [CLI](cli) → [MCP](mcp) instead.

## Path overview (target)

```
data / prompts  →  train (LoRA)  →  eval / bench  →  invoke (CLI/MCP)  →  fashion workflow
```

| Step | Goal | Today (v0.0.4) | Toward v0.1.0 |
|---|---|---|---|
| **1. Data & prompts** | Train packs + versioned prompt packs | Dataset loaders (VITON-HD, …) | Schema, validate CLI, prompt packs |
| **2. Train** | Brand-style / VTON LoRA | TryOnDiffusion research code | `opentryon train` + recipes/notebooks |
| **3. Eval** | Garment/identity quality | Manual / ad-hoc | Fashion Bench v0 + `opentryon eval` |
| **4. Invoke** | Same path for cloud & local | CLI + MCP registry | + productized local OSS VTON |
| **5. Workflow** | Task agents, not chatbots | Planner over live MCP registry | Try-On QA or Fine-Tune Coach via MCP |

## What you can do now

```bash
pip install -U opentryon
# local/GPU models when needed:
pip install -U "opentryon[local]"

opentryon vton --model flux-vto --help
opentryon generate --model p-image --help
# MCP: see getting-started/mcp
```

- Cloud try-on / generate / edit / video / understand via one registry  
- Local extras: FLUX.2-dev Turbo, Kimi-VL, LLaVA-NeXT, BEN2  
- Docs per provider under [API Reference](../api-reference/overview)

## Planned package layout

```
tryon/train/       # recipes, configs, runners
tryon/eval/        # metrics, Fashion Bench, reports
tryon/workflows/   # agentic fashion graphs
tryon/prompts/     # versioned prompt packs
tryon/datasets/    # loaders + train packs / cards
```

## Suggested reading order

1. [Roadmap — next slices A–F](../community/roadmap)  
2. [CLI](cli) · [MCP](mcp) · [Configuration](configuration)  
3. [New model checklist](../advanced/new-model-checklist) (when adding local/train adapters)  
4. [`VISION.md`](https://github.com/tryonlabs/opentryon/blob/main/VISION.md) (product system)

## Contribute

High-value PRs for this path: prompt packs, bench pairs, LoRA recipe hardening, first local VTON adapter, Try-On QA / Fine-Tune Coach workflow.

Join [Discord](https://discord.gg/T5mPpZHxkY) or open a GitHub issue tagged for train/eval/workflows.
