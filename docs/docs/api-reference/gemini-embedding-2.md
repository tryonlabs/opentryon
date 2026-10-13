---
sidebar_position: 31
title: Gemini Embedding 2 (Multimodal Embeddings)
description: Google's hosted gemini-embedding-2 maps text, images, audio, video and PDFs into one embedding space, via the opentryon GeminiEmbeddingAdapter and the embed service.
keywords:
  - Gemini Embedding 2
  - gemini-embedding-2
  - multimodal embeddings
  - embeddings API
  - catalogue search
  - Matryoshka embeddings
---

# Gemini Embedding 2 (Multimodal Embeddings)

`gemini-embedding-2` is Google's hosted multimodal embedding model. **Text, images, audio, video and PDFs land in one shared space** (100+ languages), so one index serves text-to-image, image-to-image and video/audio search. It uses the same `GEMINI_API_KEY` as Nano Banana, Veo and Gemini understanding.

```bash
export GEMINI_API_KEY="your_api_key"
```

| Item | Value |
|---|---|
| CLI model | `gemini-embedding-2` (service `embed`) |
| Adapter | `tryon.api.gemini.GeminiEmbeddingAdapter` |
| Output | `3072`-d by default; `--dim` 128–3072 (768 / 1536 / 3072 recommended), re-normalised |
| Not comparable with | `gemini-embedding-001` (text-only, different space) or other models; re-embed if you switch |

## Input limits

| Modality | Limit |
|---|---|
| Text | 8,192 tokens |
| Image | PNG / JPEG, up to 6 per aggregated request |
| Audio | MP3 / WAV, up to 180 s |
| Video | MP4 / MOV, up to 120 s (≤32 sampled frames; audio track not processed) |
| PDF | 1 file, up to 6 pages |

Files above ~18 MB are sent through the Gemini Files API automatically.

## CLI

```bash
# One vector per input, plus cosine scores against a text query
opentryon embed --model gemini-embedding-2 --image boot1.jpg boot2.jpg --query "black leather ankle boots"

# "More like this": image query
opentryon embed --model gemini-embedding-2 --image catalogue/*.jpg --query-image reference.jpg

# One fused vector for a product (title + photo), smaller dimension
opentryon embed --model gemini-embedding-2 --text "Linen shirt" --image shirt.jpg --aggregate --dim 768
```

Vectors are written to an `.npz` file in the output directory (`emb_0`, `emb_1`, …); the call returns its path, shapes, labels and, with a query, the scores.

### Flags

| Flag | Meaning |
|---|---|
| `--text`, `--image`, `--audio`, `--video`, `--pdf` | Inputs (any mix) |
| `--query`, `--query-image` | Optional query; adds cosine `scores` (use one of the two) |
| `--task` | Text task prefix: `search result` (default), `question answering`, `fact checking`, `code retrieval`, `classification`, `clustering`, `sentence similarity` |
| `--role` | `document` (default) or `query` for `--text` items (retrieval tasks) |
| `--dim` | Output dimensionality, 128–3072 |
| `--aggregate` | Fuse all inputs into **one** embedding |

## Semantics worth knowing

- **Separate vs aggregated.** Gemini collapses several parts in one request into a single embedding. By default OpenTryOn wraps each input separately (one vector each, batched); `--aggregate` sends them together.
- **No `task_type`.** The model ignores task types, so for text OpenTryOn adds the prompt prefix itself: queries use `task: search result | query: …`, documents `title: none | text: …`, and symmetric tasks `task: clustering | query: …`. Media is never prefixed, and text inside an aggregated multimodal embedding is left unprefixed (Google's guidance).
- Truncated dimensions are re-normalised client-side, so cosine similarity stays valid.

## Python

```python
from tryon.api.gemini import GeminiEmbeddingAdapter

adapter = GeminiEmbeddingAdapter()
out = adapter.embed(image=["boot1.jpg", "boot2.jpg"], query="black leather ankle boots", output_dimensionality=768)
print(out["scores"])          # cosine similarity to the query
vectors = out["embeddings"]   # numpy array, L2-normalised
```

Related: the open-weight alternatives [EmbeddingGemma 2](../local-models/embeddinggemma.md) and the [fashion embedders](../local-models/fashion-embeddings.md). Official docs: [ai.google.dev/gemini-api/docs/embeddings](https://ai.google.dev/gemini-api/docs/embeddings).
