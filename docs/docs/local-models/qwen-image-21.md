---
title: Qwen-Image-2.1 (local)
description: Open-weight Qwen-Image-2.1 and 2.1-Turbo via Diffusers QwenImage21Pipeline.
---

# Qwen-Image-2.1 (local)

Open weights for the [Qwen-Image-2.1](https://huggingface.co/Qwen/Qwen-Image-2.1) family ship on Hugging Face and ModelScope. **Qwen-Image-2.1 Pro** is hosted-only on DashScope (`qwen-image-2.1-pro`); open checkpoints are:

| Checkpoint | Registry id | Notes |
| --- | --- | --- |
| [Qwen/Qwen-Image-2.1](https://huggingface.co/Qwen/Qwen-Image-2.1) | `qwen-image-2.1-local` | Full model |
| [Qwen/Qwen-Image-2.1-Turbo](https://huggingface.co/Qwen/Qwen-Image-2.1-Turbo) | `qwen-image-2.1-turbo-local` | 8-step Turbo schedule |
| ModelScope mirror | same ids | https://modelscope.cn/models/Qwen/Qwen-Image-2.1-Turbo |

Hosted twins: `qwen-image-2.1-pro` and `qwen-image-2.1-turbo` (`DASHSCOPE_API_KEY`). See [Qwen-Image API](../api-reference/qwen-image.md).

## Requirements

```bash
pip install opentryon[local]
pip install -U diffusers transformers accelerate torch
```

Diffusers must include `QwenImage21Pipeline` (recent main or release with [PR #14804](https://github.com/huggingface/diffusers/pull/14804)).

## CLI

```bash
opentryon generate --model qwen-image-2.1-turbo-local \
  --prompt "Editorial fashion still" --width 1328 --height 1328

opentryon edit --model qwen-image-2.1-local \
  --images data/model-1.jpg --prompt "Change the jacket to navy wool"
```

Env overrides: `QWEN_IMAGE_21_MODEL_ID` or `QWEN_IMAGE_21_MODEL_PATH`.

## Python

```python
from tryon.models import QwenImage21LocalAdapter

adapter = QwenImage21LocalAdapter(model_id="Qwen/Qwen-Image-2.1-Turbo")
images = adapter.generate_text_to_image("Minimal product photo", width=1328, height=1328)
```

Unified T2I and edit use the same pipeline; pass references on edit/VTON (`generate_virtual_tryon`).
