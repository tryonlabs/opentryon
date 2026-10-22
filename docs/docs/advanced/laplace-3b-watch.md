---
title: Laplace 3B (i14) — watch
description: Linear-attention 3B model; no public weights or API yet (Oct 2026)
---

# Laplace 3B (i14) — not integrated

**Laplace 3B** is i14’s 3B decoder with **gated linear attention** (fixed ~29.5 MB recurrent state per sequence, no growing KV cache). AWS and i14 published [Trainium2 training/serving results](https://aws.amazon.com/blogs/machine-learning/beyond-the-kv-cache-training-and-serving-i14s-laplace-3b-linear-attention-model-on-aws-trainium2-with-native-pytorch/) in October 2026.

## OpenTryOn status

| Path | Status |
| --- | --- |
| **Hosted API** | Not published |
| **Local weights** | Not released (contact i14 / AWS for evaluation) |
| **Registry** | **Not added** — nothing to call until weights or an endpoint ship |

When Hugging Face weights and a vLLM/SGLang recipe appear, integrate as Path B (`laplace-3b-local`) on `understand`, mirroring Hy4/Sage local clients.

Do not confuse with unrelated Hugging Face org **Laplaces-Red-Devils** — that is a different team.
