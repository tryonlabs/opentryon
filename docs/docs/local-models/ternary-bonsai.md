---
sidebar_position: 11
title: Ternary Bonsai 2 27B (PrismML, local server)
description: Run PrismML's ternary-quantized Ternary Bonsai 2 27B on your own machine via its llama.cpp/MLX server, then call it from OpenTryOn as an OpenAI-compatible client.
---

# Ternary Bonsai 2 27B (PrismML, local server)

[Ternary-Bonsai-2-27B](https://docs.prismml.com/bonsai-2-27b) is a 27B-parameter
model (Apache 2.0) built on Qwen3.8-27B whose weights are quantized to
`{-1, 0, +1}` ("ternary"), retaining ~98% of full-precision benchmark
performance at a fraction of the footprint (5.9-8.5GB on disk depending on
quant, vs. ~54GB in FP16).

Unlike the other local models in OpenTryOn (`qwen3.8`, `kimi-vl`, ...), this
one does **not** load in-process via `transformers`/`diffusers` — there is no
rotated-weight ternary kernel for those stacks. Instead `TernaryBonsaiAdapter`
is a thin **OpenAI-compatible HTTP client**, the same shape as an LM Studio or
Ollama integration: you start the model's own server, and OpenTryOn just
calls it. No `opentryon[local]` / torch install is needed for this adapter.

## Capabilities

| Capability | `ternary-bonsai-2-27b` |
|---|---|
| Modalities | Text + image → text |
| Parameters | 27.36B, ternary-quantized (~1.76 bits/weight effective) |
| Context | Up to 262,144 tokens |
| Thinking | On by default; per-request budget via `thinking_budget_tokens`, or server-wide `--reasoning-budget` |
| License | Apache 2.0 |

## Why a separate server

GGUF variants require the **PrismML llama.cpp fork** (`prism-b10658` or
newer) — a stock llama.cpp build silently loads a Q2_0 fallback and produces
gibberish, since the rotated weight basis isn't in upstream. MLX weights work
with a stock `mlx-lm` install on Apple Silicon.

| Variant | Repo | Disk |
|---|---|---|
| GGUF (PTQ1_0) | [`prism-ml/Ternary-Bonsai-2-27B-gguf`](https://huggingface.co/prism-ml/Ternary-Bonsai-2-27B-gguf) | 5.93 GB |
| GGUF (PQ2_0, default) | same repo | 7.25 GB |
| MLX 2-bit | [`prism-ml/Ternary-Bonsai-2-27B-mlx-2bit`](https://huggingface.co/prism-ml/Ternary-Bonsai-2-27B-mlx-2bit) | 8.49 GB |

## Start the server

Follow PrismML's own instructions (llama.cpp fork, `prism-b10658`+):

```bash
# llama.cpp: OpenAI-compatible HTTP on :8080
./scripts/start_llama_server.sh

# or, on Apple Silicon:
mlx_lm.server --model prism-ml/Ternary-Bonsai-2-27B-mlx-2bit --port 8080
```

Full instructions: [docs.prismml.com/bonsai-2-27b](https://docs.prismml.com/bonsai-2-27b).

## Installation (OpenTryOn side)

```bash
# No opentryon[local] needed -- this adapter only uses `openai` + `requests`,
# both already core dependencies.
```

## Configuration

```bash
# BONSAI_BASE_URL=http://127.0.0.1:8080/v1  # default
# BONSAI_API_KEY=...                        # only if your server enforces auth
```

## Quick Start

```python
from tryon.models.ternary_bonsai import TernaryBonsaiAdapter

adapter = TernaryBonsaiAdapter()  # talks to http://127.0.0.1:8080/v1

result = adapter.understand(
    image="garment.jpg",
    prompt="Describe this outfit: color, pattern, style, fit, and material.",
    thinking_budget_tokens=512,
)
print(result["text"])
```

If the server isn't running, the adapter raises a `RuntimeError` pointing at
the PrismML docs instead of a raw connection-refused traceback.

## CLI

```bash
opentryon understand --model ternary-bonsai-2-27b \
  --image garment.jpg --prompt "Describe this outfit."

opentryon understand --model ternary-bonsai-2-27b \
  --prompt "Explain ternary quantization in two sentences." \
  --thinking-budget-tokens 256

# Point at a different local server
opentryon understand --model ternary-bonsai-2-27b \
  --prompt "hi" --base-url http://127.0.0.1:1234/v1
```

## MCP

Same registry model appears as an MCP tool (no extra wiring):

- `understand_ternary_bonsai_2_27b` — no cloud key needed; requires the local
  server to be running (see above)

## API Reference

### `TernaryBonsaiAdapter`

```python
class TernaryBonsaiAdapter:
    def __init__(
        self,
        api_key: Optional[str] = None,   # BONSAI_API_KEY, optional
        model: str = "Ternary-Bonsai-2-27B",
        base_url: Optional[str] = None,  # BONSAI_BASE_URL or http://127.0.0.1:8080/v1
    )
```

### Methods

- `understand(image=None, prompt=..., thinking_budget_tokens=None, max_tokens=None, temperature=None, model=None)`

Return dict keys: `text`, `reasoning`, `model`, `usage`.

## References

- [Ternary Bonsai 2 27B docs](https://docs.prismml.com/bonsai-2-27b)
- [PrismML announcement](https://prismml.com/news/bonsai-2-27b)
- [GGUF weights](https://huggingface.co/prism-ml/Ternary-Bonsai-2-27B-gguf)
- [MLX weights](https://huggingface.co/prism-ml/Ternary-Bonsai-2-27B-mlx-2bit)
