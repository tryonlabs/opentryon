---
sidebar_position: 14
title: Tencent Hy4 preview (TokenHub)
description: Tencent Hy4 preview LLM via TokenHub OpenAI Chat Completions — 770B MoE, 1M context.
keywords:
  - Hy4
  - Hy4 preview
  - Tencent Hy
  - Hunyuan
  - TokenHub
  - LLM
  - understand
---

# Tencent Hy4 preview (TokenHub)

[Hy4 preview](https://hy.tencent.ai/research/hy4-preview) is Tencent Hy Team's
next-generation **language model** (770B MoE, 49B active, 1M context). OpenTryOn
exposes it on **`understand`** — text in, text out. It is **not** a virtual
try-on or video-generation model.

Hosted path: Tencent Cloud [TokenHub](https://www.tencentcloud.com/document/product/1300/80695)
OpenAI Chat Completions (`hy4-preview`). Local / open-weight serving:
[Hy4 local (vLLM / SGLang)](../local-models/hy4.md).

| | |
|---|---|
| **Registry id** | `hy4-preview` |
| **Adapter** | `Hy4Adapter` |
| **Auth** | `TOKENHUB_API_KEY` (alias `TENCENT_TOKENHUB_API_KEY`) |
| **Default base URL** | `https://tokenhub-intl.tencentcloudmaas.com/v1` |
| **License (weights)** | Apache-2.0 on Hugging Face |

Do not use OpenRouter or other third-party hosters for this adapter — first-party
TokenHub only.

## CLI

```bash
opentryon understand --model hy4-preview \
  --prompt "Write a 3-sentence lookbook caption for a linen trench." --dry-run

opentryon understand --model hy4-preview \
  --prompt "Describe this outfit." --image garment.jpg --reasoning-effort high
```

`--image` is optional (OpenAI vision part). Hy4's public API is a **text LLM**;
if TokenHub rejects the image part, omit `--image`. There is **no** `--video`.

`--no-thinking` sets TokenHub `thinking.type=disabled`. Default reasoning depth
is `high` (`temperature=0.9`, `top_p=1.0`).

## Python

```python
from tryon.api import Hy4Adapter

adapter = Hy4Adapter()  # TOKENHUB_API_KEY
result = adapter.understand(prompt="Summarize this merchandising brief.")
print(result["text"])
print(result.get("reasoning"))
```

## MCP

Tool: `understand_hy4_preview`. Restart MCP so TryOn Studio lists it. Connect
saves `TOKENHUB_API_KEY`.

## See also

- [Hy4 local (vLLM / SGLang)](../local-models/hy4.md)
- [Hy API Guide](https://www.tencentcloud.com/document/product/1300/80695)
