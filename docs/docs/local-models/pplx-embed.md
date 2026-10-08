---
sidebar_position: 20
title: pplx-embed-v2-late (local)
description: Perplexity's open-weight multimodal late-interaction (multi-vector) retrievers pplx-embed-v2-late 0.6B and 9B.
keywords:
  - pplx-embed-v2-late
  - Perplexity
  - late interaction
  - ColBERT
  - MaxSim
  - multi-vector embeddings
  - local
---

# pplx-embed-v2-late (local)

`pplx-embed-v2-late` is a pair of MIT-licensed, multimodal **late-interaction** (ColBERT-style) retrievers from Perplexity, built on Qwen3.5 with bidirectional attention. Instead of one vector per document they emit **one 128-d vector per token** and score a query against a document with **MaxSim**. They retrieve text, images and rendered pages without OCR, and the 0.6B and 9B models share an embedding space — a 0.6B query encoder can search an index built with 9B.

OpenTryOn exposes them through the `embed` service with `PplxEmbedLateAdapter` (Path B).

| CLI model | Repo | Active params |
|---|---|---|
| `pplx-embed-v2-late-0.6b` | `perplexity-ai/pplx-embed-v2-late-0.6b` | 340M |
| `pplx-embed-v2-late-9b` | `perplexity-ai/pplx-embed-v2-late-9b` | 7.4B |

Vendor-reported ViDoRe v3 image retrieval (nDCG@10): 62.3 (0.6B), 65.2 (9B).

:::note Local only
Perplexity's hosted Embeddings API serves the v1 dense models (`pplx-embed-v1-*`, `pplx-embed-context-v1-*`; `PERPLEXITY_API_KEY`), not v2-late, and Hugging Face lists no inference provider for it. There is therefore no hosted v2-late integration to add. The text-only `pplx-embed-v2-context-9b-preview` is a separate preview model and is not integrated.
:::

## Requirements

```bash
pip install opentryon[local]
pip install "sentence-transformers>=6.0.0" "transformers>=5.4.0"
```

Optional override: `export PPLX_EMBED_MODEL_ID=/path/to/snapshot`. Encode **text and image batches separately** — mixed text+image batches are unsupported (the adapter does this for you). To index a PDF, render its pages to images first.

## CLI

```bash
# Index two lookbook pages and rank them against a query
opentryon embed --model pplx-embed-v2-late-0.6b \
  --image page1.png page2.png --query "red wool coat with oversized lapels"

# Text passages
opentryon embed --model pplx-embed-v2-late-9b --text "Care: dry clean only" "Machine wash cold"
```

Each input becomes a `(tokens, 128)` matrix stored in `outputs/embed_<model>.npz` (`emb_0 …`). With `--query` the command prints the MaxSim score per input.

## Python

```python
from tryon.models.pplx_embed import PplxEmbedLateAdapter

adapter = PplxEmbedLateAdapter(variant="0.6b")
out = adapter.embed(image=["page1.png", "page2.png"], query="red wool coat")
print(out["scores"], [m.shape for m in out["embeddings"]])
```

## Notes

- MCP tools: `embed_pplx_embed_v2_late_0_6b`, `embed_pplx_embed_v2_late_9b`.
- Planner pins: `pplx-embed-v2-late` (→ 0.6B), `pplx-embed-v2-late-9b`.
- Benchmark figures are vendor-reported. The 9B stores F32 safetensors — plan for a large GPU.
- No GPU was available when this was integrated; weight loading was not exercised end to end.

See also: [EmbeddingGemma 2](embeddinggemma.md) (single dense vector, adds audio/video).
