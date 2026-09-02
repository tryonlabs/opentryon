---
sidebar_position: 10
title: Hy4 preview (local vLLM / SGLang)
description: Serve Tencent Hy4 preview open weights with official vLLM or SGLang, then call OpenTryOn hy4-preview-local.
---

# Hy4 preview (local weights)

Open weights: [`tencent/Hy4-preview`](https://huggingface.co/tencent/Hy4-preview)
and [`tencent/Hy4-preview-FP8`](https://huggingface.co/tencent/Hy4-preview-FP8)
(Apache-2.0). Official serving is **vLLM or SGLang**, then an OpenAI-compatible
client — the same `Hy4Adapter` as TokenHub, with `--endpoint local`.

OpenTryOn does **not** load 770B parameters in-process. Do not expect
`pip install opentryon[local]` + a single GPU to run this model.

| | |
|---|---|
| **Registry id** | `hy4-preview-local` |
| **Served model name** | `hy4-preview` |
| **Default URL** | `HY4_BASE_URL` or `http://127.0.0.1:8000/v1` |
| **VRAM** | FP8 checkpoint ~770GB+ weights; official recipe `--tensor-parallel-size 8` (tested class: 8×B300 / 16×B200). BF16 is ~1.5TB. |

Hosted twin: [Hy4 TokenHub](../api-reference/hy4.md).

## Serve (official)

vLLM (FP8, 8-way TP):

```bash
docker run --gpus all \
  -p 8000:8000 \
  --ipc=host \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  vllm/vllm-openai:hy4-preview tencent/Hy4-preview-FP8 \
    --tensor-parallel-size 8 \
    --speculative-config '{"num_speculative_tokens":3,"method":"mtp"}' \
    --attention-backend FLASHMLA_SPARSE \
    --tool-call-parser hy_v4 \
    --reasoning-parser hy_v4 \
    --enable-auto-tool-choice \
    --port 8000 \
    --served-model-name hy4-preview
```

See the [Hugging Face card](https://huggingface.co/tencent/Hy4-preview) for
SGLang (`lmsysorg/sglang:hy4-preview`).

## CLI

```bash
# HY4_BASE_URL=http://127.0.0.1:8000/v1
opentryon understand --model hy4-preview-local \
  --prompt "Hello! Briefly introduce yourself." --dry-run
```

Local thinking off uses the vendor chat-template flag `reasoning_effort=no_think`
(`--no-thinking`).

## Python

```python
from tryon.api import Hy4Adapter

adapter = Hy4Adapter(endpoint="local")
result = adapter.understand(prompt="Hello")
print(result["text"])
```

## MCP

Tool: `understand_hy4_preview_local`. No TokenHub key. Point `HY4_BASE_URL` at
the vLLM/SGLang server, then restart MCP so Studio lists the model.

## See also

- [Hy4 TokenHub](../api-reference/hy4.md)
- [Hugging Face `tencent/Hy4-preview`](https://huggingface.co/tencent/Hy4-preview)
