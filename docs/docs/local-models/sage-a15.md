---
title: Sage-A1.5 (local)
description: InternScience Sage-A1.5 agentic MoE via SGLang or vLLM
---

# Sage-A1.5 (local)

**Registry id:** `sage-a1.5-local` on `understand`.

Weights: [InternScience/Sage-A1.5](https://huggingface.co/InternScience/Sage-A1.5) (35B MoE). **No first-party hosted API** in OpenTryOn; serve locally with SGLang or vLLM (see model README).

```bash
python -m sglang.launch_server --model-path InternScience/Sage-A1.5 --port 8000 \
  --context-length 262144 --reasoning-parser qwen3 --tool-call-parser qwen3_coder

export SAGE_A15_BASE_URL=http://127.0.0.1:8000/v1
opentryon understand --model sage-a1.5-local \
  --system "You are a helpful assistant." \
  --prompt "Outline steps to validate a garment segmentation mask."
```

Verification mode (opt-in):

```bash
opentryon understand --model sage-a1.5-local \
  --system "You are a careful analyst." \
  --verification \
  --prompt "Cross-check population figures for two cities."
```

Requires a **non-empty** `--system` when `--verification` is set.
