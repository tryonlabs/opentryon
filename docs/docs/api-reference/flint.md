---
title: Recursive Flint
description: Local or OpenRouter coding agent LLM (text understand)
---

# Recursive Flint

**Registry ids:** `flint-local` (SGLang), `flint-openrouter` (hosted free tier via OpenRouter).

Flint is Recursive’s ~40B MoE coding agent (~2.5B active). OpenTryOn exposes it on **`understand`** (text only, not vision).

## Local (recommended)

Follow [RecursiveSI/flint](https://huggingface.co/RecursiveSI/flint) SGLang kit, then:

```bash
export FLINT_BASE_URL=http://127.0.0.1:30000/v1
opentryon understand --model flint-local --prompt "Summarize how virtual try-on pipelines are structured."
```

## OpenRouter

```bash
export OPENROUTER_API_KEY=...
opentryon understand --model flint-openrouter --prompt "Draft a pytest for image resize utilities."
```

There is **no** first-party Flint HTTP API; OpenRouter is a third-party aggregator.
