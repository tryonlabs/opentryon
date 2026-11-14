---
title: GAIA-2 (Wayve) — watch
description: Latent diffusion driving world model; no public weights or API
---

# GAIA-2 — not integrated

**GAIA-2** is Wayve’s latent-diffusion world model for controllable multi-camera driving video (successor to GAIA-1). The [technical report](https://wayve.ai/thinking/gaia-2/) describes an 8.4B space-time transformer trained with flow matching, a video tokenizer, and structured conditioning (ego dynamics, agents, weather, road semantics). Wayve later discussed a larger **GAIA-3** research line.

## OpenTryOn status

| Path | Status |
| --- | --- |
| **Hosted API** | Not published. Wayve has no public developer API |
| **Local weights** | Not released |
| **Registry** | **Not added** — nothing to call until weights or an endpoint ship |

When a first-party inference API or Hugging Face weights plus a Diffusers/vLLM recipe appear, integrate as Path A (`gaia-2`) on `video-generate` and/or Path B (`gaia-2-local`). Conditioning is driving-specific (multi-camera, ego action), so it is out of the fashion/media default until a usable interface exists.

Do not confuse with unrelated “Gaia” LLM or earth-observation models.
