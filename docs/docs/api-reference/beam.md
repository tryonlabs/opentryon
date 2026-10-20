---
sidebar_position: 50
title: Beam
description: Reflection Beam 1.0 text chat on the understand service
---

# Beam

[Beam 1.0](https://developers.reflection.ai/models) is Reflection's 501B / 23B-active MoE. OpenTryOn calls the first-party OpenAI-compatible chat API. The model is text in, text out.

| Registry id | Service | Upstream id | Auth |
|---|---|---|---|
| `beam` | `understand` | `Beam-1.0-501B-A23B` | `REFLECTION_API_KEY` |

Base URL is `https://api.reflection.ai/openai/v1`. Override with `REFLECTION_BASE_URL` or `--base-url`.

Reasoning is always on. `--reasoning-effort` accepts `low`, `medium`, `high`, `xhigh`, or `max`. Omit it to use the default your Reflection org reports.

```bash
opentryon understand --model beam \
  --prompt "Write a 3-sentence lookbook caption for a linen trench."

opentryon understand --model beam \
  --prompt "Tighten this PDP copy." \
  --system "You edit fashion product copy. Keep claims factual." \
  --reasoning-effort high
```

Images and video are rejected. Use `kimi-k2.6`, `moondream-3.1`, or `nemotron-omni` for media.

The Apache-2.0 weights are on Hugging Face (`reflection/Beam-1.0-501B-A23B`). Reflection's serve guide asks for four B300 GPUs and a few hundred gigabytes of NVFP4 weights, so there is no local registry id.

MCP tool: `understand_beam`. Named-model-only — the understand default stays `kimi-k2.6`.
