---
sidebar_position: 19
title: EmbeddingGemma 2 (local)
description: Google's open-weight EmbeddingGemma 2 — text, code, image, video and audio embeddings in one shared 768-d space.
keywords:
  - EmbeddingGemma 2
  - embeddings
  - multimodal retrieval
  - sentence-transformers
  - local
---

# EmbeddingGemma 2 (local)

[`google/embeddinggemma-2`](https://huggingface.co/google/embeddinggemma-2) (740M parameters; Apache-2.0 tag — the card also links the Gemma terms, so review them for commercial use) maps **text, code, images, video and audio into one shared 768-d space**, Matryoshka-truncatable to 512 / 256 / 128. OpenTryOn exposes it through the new `embed` service with `EmbeddingGemma2Adapter` (Path B).

Fashion uses: embed catalogue photos *and* garment descriptions in one space, then search by text or by image; cluster lookbooks; deduplicate product shots.

| Modalities (`--modalities`) | Loaded size |
|---|---|
| `text` | 270M |
| `text+image` | 440M |
| `text+audio` | 570M |
| `full` (default) | 740M |

8,192-token context shared across modalities. Use bfloat16 or float32 — **not** float16. Audio should be mono 16 kHz; video is sampled at 1 fps.

## Requirements

```bash
pip install opentryon[local]
pip install -U sentence-transformers transformers
```

Optional override: `export EMBEDDINGGEMMA_MODEL_ID=/path/to/snapshot`.

## CLI

```bash
# Embed text + an image, and score both against a query (cosine)
opentryon embed --model embeddinggemma-2 \
  --text "red satin evening gown" --image dress.jpg \
  --query "formal red dress" --modalities text+image

# Smaller vectors
opentryon embed --model embeddinggemma-2 --text "linen shirt" --dim 256
```

Vectors are written to `outputs/embed_embeddinggemma-2.npz` (keys `emb_0 … emb_{n-1}`, one row per input in text → image → audio → video order). The command also prints shapes, a short preview, and — with `--query` — a cosine score per input. Text uses `--task` prompts (`Document` default; `SearchQuery`, `Classification`, `Clustering`, …); images, audio and video are unprefixed.

## Python

```python
from tryon.models.embeddinggemma import EmbeddingGemma2Adapter

adapter = EmbeddingGemma2Adapter(modalities="text+image")
out = adapter.embed(text=["red satin evening gown"], image=["dress.jpg"], query="formal red dress", dim=256)
print(out["embeddings"].shape, out["scores"])
```

## Notes

- MCP tool: `embed_embeddinggemma_2`. The response carries the `.npz` path, shapes, labels and scores — not the raw vectors.
- Truncated vectors are re-normalised, as the model card requires.
- Late-interaction alternative with page-level image retrieval: [pplx-embed-v2-late](pplx-embed.md).
- No GPU was available when this was integrated; the encode path is covered by option-validation and packaging tests, not a real weight load.
