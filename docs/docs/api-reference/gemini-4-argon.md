---
sidebar_position: 31
title: Gemini 4 Argon (Understanding)
description: Google Gemini 4 Argon flagship multimodal reasoning — long decode, agentic video, Interactions background jobs.
keywords:
  - Gemini 4 Argon
  - gemini-4-argon
  - long decode
  - agentic video
  - understand
---

# Gemini 4 Argon (Understanding)

**Gemini 4 Argon** (`gemini-4-argon`) is Google’s flagship **reasoning** multimodal model on the
Gemini API (stable since Oct 2026). OpenTryOn exposes it on **`understand`** via the same
`GeminiUnderstandAdapter` as [Gemini 3.8 Flash](gemini-3-8.md), with Argon-specific flags.

| | |
|---|---|
| **Registry id** | `gemini-4-argon` |
| **Auth** | `GEMINI_API_KEY` |
| **SDK** | `google-genai>=2.30.1` |
| **Tier** | Paid (not free tier) |

**When to use which Gemini understand model**

| Task | Model |
|---|---|
| Fast, cost-efficient multimodal QA | `gemini-3.8-flash` |
| Hard reasoning, long outputs, agentic video on long clips | `gemini-4-argon` |

## CLI (multimodal)

```bash
export GEMINI_API_KEY="..."

opentryon understand --model gemini-4-argon \
  --video runway.mp4 --prompt "List each look and call out fabric changes." \
  --video-processing agentic --thinking-level medium --dry-run
```

## Long decode (>64K tokens)

**Multimodal (recommended):** set a high `--max-tokens` (e.g. `131072`). The adapter enables
`automatic_continuation` on `generateContent` (SDK ≥2.30.1).

```bash
opentryon understand --model gemini-4-argon \
  --pdf spec.pdf --prompt "Extract every measurement table as JSON." \
  --max-tokens 131072 --thinking-level high
```

**Text-only background job (Interactions API):** `--background` polls a server-side interaction
(up to 24h). Requires `--max-tokens` **greater than 65536** and **no** `--image`/`--video`/etc.

```bash
opentryon understand --model gemini-4-argon \
  --prompt "Write a detailed technical spec for a sizing API." \
  --max-tokens 262144 --background --thinking-level high
```

## Python

```python
from tryon.api.gemini import GeminiUnderstandAdapter

adapter = GeminiUnderstandAdapter(model="gemini-4-argon")
out = adapter.understand(
    video="lookbook.mp4",
    prompt="Summarise the collection.",
    video_processing="agentic",
    thinking_level="medium",
    max_tokens=131072,
)
print(out["text"])
```

## MCP

Tool: `understand_gemini_4_argon`. Restart MCP after upgrading OpenTryOn.

## See also

- [Gemini 4 Argon model card](https://ai.google.dev/gemini-api/docs/models/gemini-4-argon)
- [Migration / generateContent changes](https://ai.google.dev/gemini-api/docs/generate-content/latest-model)
- [Long decode (Interactions)](https://ai.google.dev/gemini-api/docs/long-decode)
- [Agentic video](https://ai.google.dev/gemini-api/docs/generate-content/video-understanding)
- [Integration plan](../advanced/gemini-4-argon-integration-plan.md)
