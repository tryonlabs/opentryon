---
sidebar_position: 14
title: Limite 1B - Violetto (Paradigma Inc, local)
description: A 1B math-reasoning LLM from Paradigma Inc -- out of OpenTryOn's fashion/media scope, added as a reference point for a possible future generic model gateway.
---

# Limite 1B - Violetto (Paradigma Inc, local)

:::note Out of scope, added deliberately
Every other model in this registry targets fashion/media (try-on, image,
video, understanding, speech). **Limite 1B - Violetto does not** -- it is a
math-reasoning-only text LLM with no image/video/audio capability. It was
added on request as a reference point for a possible future "generic model
gateway" direction, not because it fits the current OpenTryOn roadmap. If
you're looking for a fashion-domain text/VLM model, see
[Kimi-VL](kimi-vl.md), [Qwen3.8](qwen3.8.md), [DeepSeek-VL2](deepseek-vl2.md),
or [Ternary Bonsai 2 27B](ternary-bonsai.md) instead.
:::

[Limite 1B - Violetto](https://huggingface.co/paradigma-inc/limite-1b-violetto)
is Paradigma Inc's first model: a dense 1B-parameter autoregressive
transformer trained from scratch on under 300B curated tokens specifically
for **high-throughput mathematical reasoning**. No first-party hosted API
exists -- Paradigma publishes weights only -- so local is the only path.

## Overview

| Feature | Value |
|---|---|
| **Model** | [paradigma-inc/limite-1b-violetto](https://huggingface.co/paradigma-inc/limite-1b-violetto) |
| **Parameters** | 1B, dense |
| **License** | Apache-2.0 |
| **Context** | Up to 131K tokens |
| **Disk / VRAM** | ~2.1GB -- the lightest local model in this registry |
| **Capability** | Text-only math reasoning. **No image, video, or audio input.** |
| **Usage pattern** | Single-turn only (system prompt + current user message) -- the model card warns multi-turn history may get reinterpreted as a different math problem |

## Installation

```bash
pip install opentryon[local]   # torch, transformers, etc.
```

:::note
The model card recommends Python 3.12 / torch 2.11 (CUDA 13) / transformers
5.6.2 and `attn_implementation="sdpa"` (FlashAttention2 + StaticCache is
explicitly called out upstream as numerically incorrect for this model --
this adapter always uses `sdpa`). This repo's shared `opentryon[local]` pin
is older (`transformers==4.42.4`) -- upgrade in a separate env if loading
fails with a `trust_remote_code` error.
:::

## Quick Start

```python
from tryon.models.limite import LimiteAdapter

adapter = LimiteAdapter()  # downloads paradigma-inc/limite-1b-violetto on first use

result = adapter.understand(prompt="If x + 3 = 8, what is x?")
print(result["text"])
```

## Using the `opentryon` CLI

```bash
opentryon understand --model limite-1b-violetto \
  --prompt "A train travels 60 miles in 1.5 hours. What is its average speed?"
```

The CLI checks that `torch` is installed before attempting to load the
model (`pip install opentryon[local]` hint if missing).

## API Reference

### `LimiteAdapter`

```python
class LimiteAdapter:
    def __init__(
        self,
        model_id: Optional[str] = None,   # LIMITE_MODEL_ID or paradigma-inc/limite-1b-violetto
        device: Optional[str] = None,     # passed as device_map, defaults to "auto"
        torch_dtype: str = "auto",
        trust_remote_code: bool = True,   # required for Limite's custom modeling code
    )
```

### `understand`

```python
def understand(
    self,
    prompt: str,
    system_prompt: Optional[str] = None,
    max_new_tokens: int = 512,
    temperature: Optional[float] = None,  # default 0.6 from generation_config.json if omitted
    top_p: Optional[float] = None,        # default 0.95 from generation_config.json if omitted
) -> Dict[str, Any]  # {"text": ..., "model": ...}
```

Only `prompt` (and optionally `system_prompt`) are sent per call -- no chat
history -- matching the model card's recommended usage.

## MCP

Same registry model appears as an MCP tool (no extra wiring):

- `understand_limite_1b_violetto` -- local GPU, no cloud key

Not wired into the planner's capability defaults or a new intent (it stays
named-model-only: `--model limite-1b-violetto` or "use limite-1b-violetto"
in chat) since it doesn't fit any fashion/media intent as a default.

## References

- [Limite 1B - Violetto on Hugging Face](https://huggingface.co/paradigma-inc/limite-1b-violetto)
- [Limite GitHub](https://github.com/paradigma-inc/limite-violetto)
