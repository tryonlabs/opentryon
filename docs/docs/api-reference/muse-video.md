---
sidebar_position: 25
title: Muse Video (not available)
description: Why OpenTryOn cannot ship Muse Video yet — no first-party API and no open weights.
keywords:
  - Muse Video
  - Meta
  - video generation
---

# Muse Video (not available)

[Muse Video](https://ai.meta.com/blog/introducing-muse-image-muse-video-msl/) was announced as an **early preview** alongside Muse Image. Meta’s public post says it is *coming soon* to creators and Meta AI. It is **not** in [Meta Model API](https://ai.developer.meta.com/docs/models/).

| Path | Status |
|---|---|
| **Path A — first-party API** | No `video_generation` (or equivalent) endpoint. Model API video APIs are **understanding** only (Muse Spark reads video → text). |
| **Path B — local / open weights** | No Hugging Face / Diffusers checkpoint. Muse Glimmer is open-weight but outputs **text**, not video. |
| **Third-party hosters** | Not wired. OpenTryOn only adds Fal/Replicate/etc. when you explicitly ask. |

There is no `--model muse-video` (or local twin) in the registry. Do not confuse Muse Spark video **understanding** with video **generation**.

When Meta ships a first-party generate/edit video API or open weights, follow [Model Integration Guidelines](../advanced/model-integration-guidelines.md) the same way as [MiniMax H3](./minimax-h3.md): two `ModelSpec` ids if both paths exist, never one adapter that mixes HTTP and GPU.

Until then, use existing video models (`sora`, `ltx-2.5-api`, `minimax-h3`, `wan-3.0`, …). Image twin: [Muse Image](./muse-image.md).
