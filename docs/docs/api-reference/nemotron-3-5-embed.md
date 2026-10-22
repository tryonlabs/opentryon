---
title: Nemotron 3.5 Embed 1B
description: NVIDIA NIM multimodal embeddings for RAG (text + document images)
---

# Nemotron 3.5 Embed 1B

**Registry ids:** `nemotron-3.5-embed-1b` (hosted NIM), `nemotron-3.5-embed-1b-local` (self-hosted OpenAI `/v1/embeddings`).

Model id: `nvidia/nemotron-3.5-embed-1b` ([build.nvidia.com](https://build.nvidia.com/nvidia/nemotron-3_5-embed-1b)).

## Hosted (NIM)

```bash
export NVIDIA_API_KEY=...
opentryon embed --model nemotron-3.5-embed-1b \
  --text "linen trench coat" "wool blazer" \
  --query "lightweight outerwear"
```

```bash
opentryon embed --model nemotron-3.5-embed-1b \
  --image page1.png catalog.png \
  --input-type passage --query "summer dress SKU layout"
```

## Local (NeMo Retriever Embedding NIM / vLLM)

Serve the BF16 or NVFP4 checkpoint with NVIDIA’s Embedding NIM, then:

```bash
export NEMOTRON_EMBED_BASE_URL=http://127.0.0.1:8000/v1
opentryon embed --model nemotron-3.5-embed-1b-local --text "hello" --query "hi"
```

## CLI flags

| Flag | Purpose |
| --- | --- |
| `--input-type` | `query` vs `passage` (retrieval) |
| `--modality` | `text`, `image`, or `text_image` when mixing inputs |
| `--dim` | Optional dynamic embedding size |
| `--longest-edge` | Image resize cap (256–1540) |

Vectors are L2-normalized and saved to `.npz` like other `embed` models.
