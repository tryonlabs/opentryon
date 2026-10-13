---
sidebar_position: 22
title: Fashion Florence (local)
description: Self-hosted garment tagging — Florence-2-large fine-tuned to return category, colour, material and style tags as JSON.
keywords:
  - Fashion Florence
  - Florence-2
  - fashion attribute extraction
  - garment tagging
  - catalogue tagging
  - local
---

# Fashion Florence (local)

[`anushreeberlia/fashion-florence`](https://huggingface.co/anushreeberlia/fashion-florence) is a LoRA fine-tune of Microsoft's Florence-2-large (0.77B parameters, MIT, LoRA merged into the base weights) trained on about 78k [Marqo/iMaterialist](https://huggingface.co/datasets/Marqo/iMaterialist) examples. One clothing photo in, structured JSON out — cheap, deterministic, self-hosted catalogue tagging instead of a per-image VLM call. OpenTryOn exposes it through the `understand` service as `fashion-florence` (Path B, `extra="local"`).

| Field | Values |
|---|---|
| `category` | `top`, `bottom`, `dress`, `layer`, `shoes`, `accessory` |
| `primary_color` | dominant colour, e.g. `navy blue` |
| `material` | fabric, e.g. `cotton` |
| `style_tags` | list of descriptors, e.g. `["casual", "minimalist"]` |

## How well does it work?

From the model card, on 3,915 held-out iMaterialist examples: 100% JSON parse rate, **89.5% category accuracy**, 52.7% colour and 42.6% material exact-match (near-synonyms such as "navy" vs "navy blue" count as misses), style-tag macro F1 0.888. Shoes (F1 0.61) and accessories (0.29, six test examples) are weak. The authors' paper ([arXiv 2605.09827](https://arxiv.org/abs/2605.09827)) reports higher category and material accuracy (94.6% / 63.0%) on a different, smaller test set and claims it beats GPT-4o-mini and Gemini 2.5 Flash on that fixed schema. These are the authors' numbers; **measure on your own catalogue** before relying on colour and material.

It is a narrow tagger, not a chat model: it ignores free-form questions. For those use a VLM such as [`gemini-3.8-flash`](../api-reference/gemini-3-8.md) or [`claude-haiku-5-5`](../api-reference/claude.md).

## Requirements

```bash
pip install opentryon[local]
```

The model loads with `trust_remote_code=True` (Florence-2 ships custom modelling code). That code targets the transformers 4.4x line pinned by `opentryon[local]` and may break on much newer transformers — use the pinned environment. CPU works (slow); a GPU runs in float16. Optional override: `export FASHION_FLORENCE_MODEL_ID=/path/to/snapshot`.

## CLI

```bash
opentryon understand --model fashion-florence --image dress.jpg
```

```json
{
  "model": "anushreeberlia/fashion-florence",
  "tags": {"category": "dress", "primary_color": "navy blue", "material": "cotton", "style_tags": ["casual", "minimalist"]},
  "raw": "{\"category\": \"dress\", ...}"
}
```

Several images return `{"model": ..., "results": [{"image", "tags", "raw"}, ...]}`. `tags` is `null` only if the model produced no JSON object; `raw` always holds the generated text. Flags: `--image` (one or more), `--prompt` (overrides the tagging instruction; the fine-tune expects the default), `--max-new-tokens`, `--num-beams`, `--model-id`, `--device`.

## Python

```python
from tryon.models.fashion_florence import FashionFlorenceAdapter

adapter = FashionFlorenceAdapter()
print(adapter.understand("dress.jpg")["tags"])
```

## Notes

- MCP tool: `understand_fashion_florence`. Planner pin: `fashion florence`; the `understand` default stays `kimi-k2.6`.
- Training labels were collapsed into this four-field schema, so it will not return fit, pattern, neckline or occasion. For richer attributes use a general VLM with a JSON prompt.
- No GPU was available when this was integrated; the adapter is tested against a stubbed Florence model (JSON parsing, single vs. batch output, validation), not real weights.
