---
sidebar_position: 15
title: Inception Mercury 3
description: Inception Labs Mercury 3 diffusion LLM — OpenAI-compatible chat, 1M context, 1000+ tok/s.
keywords:
  - Mercury 3
  - Inception Labs
  - diffusion LLM
  - understand
  - chat completions
---

# Inception Mercury 3

[Mercury 3](https://www.inceptionlabs.ai/blog/introducing-mercury-3) is Inception
Labs' flagship **diffusion language model** — optimized for low-latency chat,
agents, and voice-adjacent workloads (1M-token context, up to 131K output tokens,
1000+ tokens/s on NVIDIA GPUs). OpenTryOn exposes the hosted **chat** path on
**`understand`** (text in, text out).

| | |
|---|---|
| **Registry id** | `mercury-3` |
| **Adapter** | `InceptionUnderstandAdapter` |
| **Auth** | `INCEPTION_API_KEY` |
| **Default base URL** | `https://api.inceptionlabs.ai/v1` |
| **Upstream model id** | `mercury-3` (also `--inception-model mercury-2.5`, `mercury-2`, `mercury-voice`) |

Mercury 3 on `v1/chat/completions` is **text-only** (no `--image`). For
high-volume classification with optional image input, Inception ships
**Mercury Decide** on `v1/decisions` — not wired in OpenTryOn yet.

## CLI

```bash
export INCEPTION_API_KEY="..."

opentryon understand --model mercury-3 \
  --prompt "Draft a 2-sentence product description for a merino crewneck." \
  --reasoning-effort medium --dry-run
```

`--reasoning-effort` accepts `instant`, `low`, `medium`, or `high`.
`--temperature` must stay between **0.5** and **1.0** when set.

## Python

```python
from tryon.api.inception import InceptionUnderstandAdapter

adapter = InceptionUnderstandAdapter()  # INCEPTION_API_KEY
result = adapter.understand(
    prompt="Summarize this merchandising brief in three bullets.",
    reasoning_effort="medium",
    max_tokens=2048,
)
print(result["text"])
```

## MCP

Tool: `understand_mercury_3`. Restart MCP so TryOn Studio lists it. Connect
saves `INCEPTION_API_KEY`.

## See also

- [Inception models & pricing](https://docs.inceptionlabs.ai/get-started/models)
- [Quick start](https://docs.inceptionlabs.ai/get-started)
- [Tool use](https://docs.inceptionlabs.ai/capabilities/tool-use)
