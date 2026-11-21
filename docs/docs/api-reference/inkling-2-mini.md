---
title: Inkling 2 Mini (Thinking Machines)
description: Multimodal hybrid MoE via Tinker API or local vLLM/SGLang/Ollama
---

# Inkling 2 Mini

**Registry ids:** `inkling-2-mini` (Tinker hosted), `inkling-2-mini-local` (self-hosted OpenAI-compatible server).

Inkling 2 Mini is Thinking Machines Lab’s 26B MoE multimodal model (~5.4B active, hybrid reasoning, image + text in). Apache 2.0 weights on [Hugging Face](https://huggingface.co/thinkingmachines/Inkling-2-Mini). Sampling context up to 1M tokens on Tinker.

## Hosted (Tinker)

```bash
export TINKER_API_KEY=...
opentryon understand --model inkling-2-mini \
  --image lookbook-page.png \
  --prompt "List garment types and styling notes." \
  --reasoning-effort high
```

Tinker OpenAI base URL (default):

`https://tinker.thinkingmachines.dev/services/tinker-prod/oai/api/v1`

Models:

| `--inkling-model` | Use |
| --- | --- |
| `thinkingmachines/Inkling-2-Mini` | 64K train / 1M sample (default) |
| `thinkingmachines/Inkling-2-Mini:peft:262144` | 256K train variant |

**Images on Tinker:** only `data:` URIs (OpenTryOn converts paths for you). Max **2 MiB** per image before base64. HTTP image URLs are downloaded then embedded.

Docs: [OpenAI-compatible overview](https://tinker-docs.thinkingmachines.ai/inference/openai/overview/)

## Local (Path B)

Serve `thinkingmachines/Inkling-2-Mini` with SGLang, vLLM, Ollama, or Exo (~20 GB checkpoint; DGX Spark or 32 GB+ Apple silicon per model card), then:

```bash
export INKLING_BASE_URL=http://127.0.0.1:8000/v1
opentryon understand --model inkling-2-mini-local \
  --image garment.jpg --prompt "Describe fabric and silhouette."
```

## CLI flags

| Flag | Notes |
| --- | --- |
| `--reasoning-effort` | `none` … `max` (Inkling hybrid reasoning on Tinker) |
| `--inkling-model` | Tinker / served model id |
| `--max-tokens` | Maps to `max_completion_tokens` on Tinker |

No video input. Production inference URL (`inference.thinkingmachines.dev`) is waitlisted separately from the beta Tinker OAI path.