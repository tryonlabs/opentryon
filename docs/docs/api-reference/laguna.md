---
sidebar_position: 51
title: Laguna
description: Poolside Laguna XS.2 / XS 2.1 / M.1 text chat on the understand service
---

# Laguna

[Laguna](https://docs.poolside.ai/get-started/supported-models) is Poolside’s agentic coding family. OpenTryOn calls the first-party OpenAI-compatible chat API. The models are text in, text out.

| Registry id | Service | Upstream id | Auth |
|---|---|---|---|
| `laguna-xs.2` | `understand` | `poolside/laguna-xs.2` | `POOLSIDE_API_KEY` |
| `laguna-xs.2.1` | `understand` | `poolside/laguna-xs.2.1` | `POOLSIDE_API_KEY` |
| `laguna-m.1` | `understand` | `poolside/laguna-m.1` | `POOLSIDE_API_KEY` |

XS.2 is 33B / 3B-active (Apache-2.0). XS 2.1 is the successor (OpenMDW-1.1) with native reasoning. M.1 is 225B / 23B-active (Apache-2.0). Pass `--laguna-model poolside/laguna-xs-2.1` as an alias for XS 2.1.

Base URL is `https://inference.poolside.ai/v1`. Override with `POOLSIDE_BASE_URL` or `--base-url`.

Thinking is **on by default**. `--no-thinking` sends `chat_template_kwargs.enable_thinking: false`.

```bash
opentryon understand --model laguna-m.1 \
  --prompt "Write a 3-sentence lookbook caption for a linen trench."

opentryon understand --model laguna-xs.2 \
  --prompt "Tighten this PDP copy." \
  --system "You edit fashion product copy. Keep claims factual." \
  --no-thinking
```

Images and video are rejected. Use `kimi-k2.6`, `moondream-3.1`, or `nemotron-omni` for media.

Open weights exist, but hosted inference is the Path A integration. There is no local registry id.

MCP tools: `understand_laguna_xs_2`, `understand_laguna_xs_2_1`, `understand_laguna_m_1`. Named-model-only — the understand default stays `kimi-k2.6`.
