---
sidebar_position: 4
title: Wan 2.2 (local)
description: Open-weight Wan 2.2 text/image-to-video via Hugging Face Diffusers.
---

# Wan 2.2 (local Diffusers)

Open-weight [Wan 2.2](https://github.com/Wan-Video/Wan2.2) via Diffusers. Default checkpoint: [`Wan-AI/Wan2.2-TI2V-5B-Diffusers`](https://huggingface.co/Wan-AI/Wan2.2-TI2V-5B-Diffusers) (unified T2V + I2V, lower VRAM than A14B).

Hosted twin: [Wan API](../api-reference/wan.md) (`--model wan-api`).

## Requirements

```bash
pip install opentryon[local]
pip install -U "diffusers>=0.35" transformers accelerate ftfy
# CUDA GPU required
```

## CLI

```bash
opentryon video-generate --model wan-2.2 \
  --prompt "A fashion model walking a runway at dusk" \
  --num-frames 81 --seed 42

opentryon video-generate --model wan-2.2 \
  --image look.jpg --prompt "Gentle fabric motion" --num-frames 81
```

## Python

```python
from tryon.models import Wan22Adapter

adapter = Wan22Adapter()  # Wan-AI/Wan2.2-TI2V-5B-Diffusers
video = adapter.generate_text_to_video(
    prompt="A cinematic shot of fabric flowing in wind",
    num_frames=81,
    seed=42,
)
open("wan22.mp4", "wb").write(video)
```
