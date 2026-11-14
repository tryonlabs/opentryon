---
sidebar_position: 52
title: Trinity
description: Arcee Trinity Large (400B), Mini, and Nano text chat on the understand service
---

# Trinity

[Trinity](https://www.arcee.ai/trinity) is Arcee’s Apache-2.0 MoE family. OpenTryOn calls the first-party OpenAI-compatible Platform API for hosted ids. The models are text in, text out.

| Registry id | Service | Upstream id | Auth |
|---|---|---|---|
| `trinity-large` | `understand` | `Trinity-Large-Preview` | `ARCEE_API_KEY` |
| `trinity-large-thinking` | `understand` | `Trinity-Large-Thinking` | `ARCEE_API_KEY` |
| `trinity-mini` | `understand` | `trinity-mini` | `ARCEE_API_KEY` |
| `trinity-nano` | `understand` | `Trinity-Nano` | local server (`TRINITY_BASE_URL`) |

**Trinity Large Preview** is 400B / 13B-active, hosted at 128K context (weights support 512K). **Trinity Large Thinking** is the reasoning-optimised Large; responses may include `reasoning_content`. **Trinity Mini** is 26B / 3B-active. **Trinity Nano** (6B / 1B-active) is **not hosted** on the Arcee Platform — point `--model trinity-nano` at your own vLLM/SGLang server.

Base URL is `https://api.arcee.ai/api/v1`. Override with `ARCEE_BASE_URL` or `--base-url`. `ARCEEAI_API_KEY` is an alias for `ARCEE_API_KEY`. Nano uses `TRINITY_BASE_URL` (default `http://127.0.0.1:8000/v1`).

```bash
opentryon understand --model trinity-large \
  --prompt "Write a 3-sentence lookbook caption for a linen trench."

opentryon understand --model trinity-large-thinking \
  --prompt "Plan a three-look campaign around one linen trench." \
  --system "You are a fashion editor."

opentryon understand --model trinity-nano \
  --prompt "Tighten this PDP copy."
```

Images and video are rejected. Use `kimi-k2.6`, `moondream-3.1`, or `nemotron-omni` for media.

Large self-host needs multi-GPU; there is no in-process GPU registry id.

MCP tools: `understand_trinity_large`, `understand_trinity_large_thinking`, `understand_trinity_mini`, `understand_trinity_nano`. Named-model-only — the understand default stays `kimi-k2.6`.
