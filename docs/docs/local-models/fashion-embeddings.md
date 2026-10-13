---
sidebar_position: 21
title: Fashion embeddings (local)
description: Fashion-specific retrieval encoders — Marqo-FashionSigLIP, MODA and ZooClaw-FashionSigLIP2 — for catalogue search by text or by photo.
keywords:
  - fashion embeddings
  - Marqo-FashionSigLIP
  - MODA
  - ZooClaw-FashionSigLIP2
  - fashion retrieval
  - catalogue search
  - open_clip
---

# Fashion embeddings (local)

General-purpose embedders are not tuned for catalogue photos and product titles. These **fashion-specific** encoders are, and they plug into the `embed` service next to [EmbeddingGemma 2](embeddinggemma.md) and [pplx-embed-v2-late](pplx-embed.md). Typical uses: search a catalogue by description or by photo, find "more like this", deduplicate product shots, group lookbooks.

| CLI model | Repo | Modes | Licence | Notes |
|---|---|---|---|---|
| `marqo-fashionsiglip` | [`Marqo/marqo-fashionSigLIP`](https://huggingface.co/Marqo/marqo-fashionSigLIP) | text + image | Apache-2.0 | ViT-B/16 SigLIP, ~0.2B, 768-d. Marqo reports up to +57% MRR / recall over FashionCLIP (vendor-reported). The most-downloaded fashion encoder. |
| `moda-fashion-distilled` | [`HopitAI/moda-fashion-distilled`](https://huggingface.co/HopitAI/moda-fashion-distilled) | **image only** | MIT | MODA's image-to-image checkpoint, distilled from a 3-model ensemble. 67.63 fine R@1 on LookBench vs 63.84 for FashionSigLIP (vendor-reported). The card documents no text usage, so text is blocked here. |
| `moda-pro-lite` | [`HopitAI/moda-pro-lite`](https://huggingface.co/HopitAI/moda-pro-lite) | text + image | Apache-2.0 | 213M text-to-image encoder for catalogue and title search. Bare encoder only — MODA's "Plus" multi-view recipe and ANN helpers are not wired. |
| `zooclaw-fashionsiglip2` | [`srpone/zooclaw-fashionsiglip2`](https://huggingface.co/srpone/zooclaw-fashionsiglip2) | text + image | Apache-2.0 | SigLIP2-base fine-tune (~375M), 384 px images, 64 text tokens, arXiv 2606.27708. The card lists no benchmarks. |

All vectors are L2-normalised, so cosine similarity is a dot product. Benchmark numbers above come from the model authors and were not reproduced here.

## Requirements

```bash
pip install opentryon[local]
pip install open_clip_torch      # Marqo and MODA (ZooClaw uses plain transformers)
```

Pass `--model-id` to point at a local snapshot or a different repo.

## CLI

```bash
# Catalogue search by text
opentryon embed --model marqo-fashionsiglip \
  --image boot1.jpg boot2.jpg boot3.jpg --query "black leather ankle boots"

# "More like this" by photo
opentryon embed --model moda-fashion-distilled \
  --image catalogue/*.jpg --query-image customer_photo.jpg

# Embed product titles and photos into one space
opentryon embed --model zooclaw-fashionsiglip2 \
  --text "linen wrap dress" "wool overcoat" --image dress.jpg
```

Vectors are saved to `outputs/embed_<model>.npz` (`emb_0 … emb_{n-1}`, text first, then images). With `--query` or `--query-image` the command also prints a cosine score per input. `--query` and `--query-image` are mutually exclusive.

## Python

```python
from tryon.models.fashion_embed import FashionOpenCLIPAdapter, ZooClawFashionSigLIP2Adapter

adapter = FashionOpenCLIPAdapter(variant="marqo-fashionsiglip")   # or moda-fashion-distilled / moda-pro-lite
out = adapter.embed(image=["a.jpg", "b.jpg"], query="red satin evening gown")
print(out["scores"], out["embeddings"].shape)

zoo = ZooClawFashionSigLIP2Adapter()
out = zoo.embed(text=["linen shirt"], image=["shirt.jpg"], query_image="query.jpg")
```

## Notes

- MCP tools: `embed_marqo_fashionsiglip`, `embed_moda_fashion_distilled`, `embed_moda_pro_lite`, `embed_zooclaw_fashionsiglip2`.
- Planner pins: `marqo fashionsiglip`, `moda pro lite`, `moda fashion`, `zooclaw`. `embed` stays named-model-only.
- No GPU was available when these were integrated; the adapters are tested against stubbed `open_clip` / `transformers` models, not real weights. Run a quick sanity retrieval on your own catalogue before relying on any of them.
- Not integrated: the MODA multi-view "Plus" recipe, `moda-fashion-matryoshka` / `-vision-fp16` variants, and the Trendyol e-commerce DINOv2 embedder (CC BY-SA). See [Integrate next](../community/integrate-next.md).
