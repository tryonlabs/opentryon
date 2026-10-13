---
sidebar_position: 25
title: Try-on safety classifier (local)
description: Gate garments before a virtual try-on — Genlook's Apache-2.0 classifier of what a try-on would show, via the new classify service.
keywords:
  - try-on safety
  - content moderation
  - Genlook
  - SigLIP 2
  - classify
  - local
---

# Try-on safety classifier (local)

[`Genlook/tryon-safety-classifier`](https://huggingface.co/Genlook/tryon-safety-classifier) (Apache-2.0, SigLIP 2 so400m) answers one question about a product: **if a shopper tries this on, how much skin or sexual content ends up in the result?** Use it to gate garments **before** they are rendered onto a shopper's photo. It is not a generic NSFW detector: a lingerie flat lay has no nudity, but its try-on would, and a fetish mask on a mannequin is not explicit but is still a sexual product.

OpenTryOn exposes it as `tryon-safety-classifier` in the new **`classify`** service — fixed-label image classifiers with calibrated probabilities (the labels are fixed by the model, so it does not fit the free-form questions of [`decide`](../api-reference/typesafe-jev.md#question-schema)). `classify` is named-model-only in the planner and returns JSON like `decide` and `understand` do.

## Outputs

One prediction per **product**, computed over all the photos you pass:

| Field | Values |
|---|---|
| `level` | `ok`, `revealing`, `lingerie`, `adult` (by severity) |
| `blocked` | `P(adult) >= adult_threshold` (default 0.3). **Use this for the gate**: it catches more adult products than the top `level` for a small rise in false blocks |
| `probs` | probability of each level |
| `subject` | `human_clothing`, `pet`, `not_clothing` |
| `swimwear` | `not_swimwear`, `regular`, `near_micro`, `micro` |
| `ravewear` | `true` / `false` (does not change the level) |

Levels: **ok** (everyday wear, sportswear, costumes, accessories), **revealing** (swimwear-level coverage, men's underwear, micro skirts, most festival wear), **lingerie** (bras, panties, bodysuits, corsets), **adult** (intimate areas exposed, or a sexual product: BDSM and fetish wear, crotchless or open-cup designs, sex toys, …). The full policy is in the model's [LABELLING_POLICY.md](https://huggingface.co/Genlook/tryon-safety-classifier/blob/main/LABELLING_POLICY.md).

## How reliable is it?

From the model card (5-fold cross-validation over 2,596 products, ~5,000 photos): **94.6%** four-level accuracy (finetuned); at the 0.3 threshold it misses 34 of 534 adult products with 52 false blocks; lingerie recall 90%; subject accuracy 99.2%. Hardest cases are sheer lingerie vs adult and festival / rave wear (85% accuracy). It was trained mostly on western e-commerce photography, so accuracy may drop on very different photo styles. The labels came from an LLM with human correction on boundary cases, and the dataset is not released. **The right gate depends on your audience** (some stores allow `lingerie`, some block `revealing`), and it classifies products — never use it to make decisions about people. Treat it as one layer of moderation, not a guarantee.

## Requirements

```bash
pip install opentryon[local]
pip install open_clip_torch safetensors huggingface_hub
```

Variants: `finetuned` (default, ~0.9 GB, best at catching adult products) and `frozen` (~120 KB of heads over the public SigLIP 2 weights; misses slightly more). Both also download the SigLIP 2 base through `open_clip`. Optional override: `TRYON_SAFETY_MODEL_ID` (a Hub repo or a local folder).

**No remote code is executed.** The model repo ships a `tryon_safety.py`; this adapter instead re-implements the same ~40-line inference path and only downloads `config.json` and `model.safetensors` (tensors, no code), pinned to the `v1.0` tag by default (`--revision`).

## CLI

```bash
# Pass ALL photos of ONE product
opentryon classify --model tryon-safety-classifier --image front.jpg back.jpg detail.jpg

# Stricter gate
opentryon classify --model tryon-safety-classifier --image front.jpg --adult-threshold 0.15
```

```json
{
  "model": "Genlook/tryon-safety-classifier", "variant": "finetuned",
  "level": "ok", "blocked": false, "adult_threshold": 0.3,
  "probs": {"ok": 0.97, "revealing": 0.02, "lingerie": 0.01, "adult": 0.0},
  "subject": "human_clothing", "swimwear": "not_swimwear", "ravewear": false, "n_images": 3
}
```

## Python

```python
from tryon.models.tryon_safety import TryOnSafetyAdapter

result = TryOnSafetyAdapter().classify(["front.jpg", "back.jpg"])
if result["blocked"]:
    ...  # do not render this garment onto the shopper's photo
```

## Notes

- MCP tool: `classify_tryon_safety_classifier`. Planner pins: `tryon safety classifier`, `tryon safety`, `genlook safety`. No chat intent routes to `classify`, and no defaults change.
- Studio has no screen for `classify` yet; the tool works from any MCP client.
- No GPU or real weights were used when this was integrated; the adapter is tested against real safetensors files in a temp folder with a stubbed SigLIP tower (heads, thresholds, variants, pinned download).
