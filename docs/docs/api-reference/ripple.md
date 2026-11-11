---
title: Ricursive Ripple-65B Preview
description: Open-weight 65B coding and agent LLM (text only) via OpenRouter or a local OpenAI-compatible server
---

# Ricursive Ripple-65B Preview

**Registry ids:** `ripple-65b-openrouter` (hosted via OpenRouter), `ripple-65b-local` (your own OpenAI-compatible server).

[Ripple-65B Preview](https://www.ricursive.com/ripple) is an Apache-2.0, 65B dense Transformer from Ricursive Intelligence with a 1M-token context, tuned for agentic coding. Ricursive reports 80.5 on Terminal-Bench 2.1 (vendor-reported, not independently verified). It is **text only**, so it sits on **`understand`** as a named-model-only entry, alongside [Flint](flint). It has no fashion or media capability and is not a planner default.

## OpenRouter

Ricursive has no first-party API. The launch post lists OpenRouter, Together AI, GMI Cloud and Fireworks as hosts; OpenTryOn uses OpenRouter (`ricursiveai/ripple-65b-preview`).

```bash
export OPENROUTER_API_KEY=...
opentryon understand --model ripple-65b-openrouter --prompt "Write a pytest for an image resize helper." --max-tokens 1024
```

## Local

Serve `ricursiveAI/Ripple-65B-Preview` (BF16) or `ricursiveAI/Ripple-65B-Preview-NVFP4` with vLLM or SGLang, then point OpenTryOn at it. The model card does not give a serve command, so the server setup is yours.

```bash
export RIPPLE_BASE_URL=http://127.0.0.1:8000/v1   # default
export RIPPLE_MODEL=ricursiveAI/Ripple-65B-Preview   # name your server exposes
opentryon understand --model ripple-65b-local --prompt "Summarise this diff." --served-model ricursiveAI/Ripple-65B-Preview
```

## Python

```python
from tryon.api.ricursive import RippleAdapter

ripple = RippleAdapter(endpoint="openrouter")   # or endpoint="local"
print(ripple.understand("Refactor this function.", system="Be concise.", max_tokens=512)["text"])
```

`understand` returns `{"text", "model", "endpoint", "usage"}`. An empty prompt raises `ValueError`.

Links: [model card](https://huggingface.co/ricursiveAI/Ripple-65B-Preview) · [OpenRouter listing](https://openrouter.ai/ricursiveai/ripple-65b-preview)
