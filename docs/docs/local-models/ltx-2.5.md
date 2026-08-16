---
sidebar_position: 3
title: LTX-2.5 (local)
description: Open-weight LTX-2.5 text/image-to-video via Hugging Face Diffusers on a local GPU.
keywords:
  - LTX-2.5
  - Lightricks
  - Diffusers
  - local video
  - open weights
---

# LTX-2.5 (local Diffusers)

Open-weight [LTX-2.5](https://ltx.io/model/ltx-2-5) via [`Lightricks/LTX-2.5-Diffusers`](https://huggingface.co/Lightricks/LTX-2.5-Diffusers). Runs on your CUDA GPU with the distilled recipe (explicit sigma schedule, CPU offload by default). Outputs MP4 with synchronized audio.

Hosted API twin: [LTX-2.5 (official API)](../api-reference/ltx-2.5.md) (`--model ltx-2.5-api`).

## Requirements

| Item | Notes |
|------|--------|
| GPU | CUDA required; ~16GB VRAM minimum with offload; 24GB+ preferred |
| Disk | ~72GB for distilled snapshot (exclude `transformer_full/` if downloading manually) |
| License | LTX-2.x Community License — free commercial use under $10M ARR; accept HF gated terms |
| Diffusers | **Must install from main** — LTX-2.5 is not in a stable Diffusers release yet |

```bash
pip install opentryon[local]
pip install "git+https://github.com/huggingface/diffusers"
export HF_TOKEN=hf_...   # after accepting the model card terms
```

Optional overrides:

```bash
# export LTX_MODEL_ID=Lightricks/LTX-2.5-Diffusers
# export LTX_MODEL_PATH=/path/to/local/snapshot
```

## CLI

```bash
opentryon video-generate --model ltx-2.5 \
  --prompt "A fashion model walking a runway at dusk, camera tracking, soft ambient sound" \
  --width 960 --height 544 --num-frames 121 --frame-rate 24 --seed 42

opentryon video-generate --model ltx-2.5 \
  --image look.jpg \
  --prompt "Gentle fabric motion as the model turns, atelier ambience" \
  --width 960 --height 544 --num-frames 121
```

`width`/`height` must be divisible by 32. `num_frames` must satisfy `num_frames % 8 == 1` (e.g. 97, 121).

## Python

```python
from tryon.models import LTX25Adapter

adapter = LTX25Adapter()  # loads Lightricks/LTX-2.5-Diffusers
video = adapter.generate_text_to_video(
    prompt="A cinematic shot of a red fox walking through snow, camera tracking",
    width=960,
    height=544,
    num_frames=121,
    seed=42,
)
open("ltx25.mp4", "wb").write(video)
```

## Notes

- Default path uses the **distilled** transformer + convolutional VAE decode (same as the HF quick start).
- Prompts work best as long single-paragraph audiovisual captions.
- For production Playground metering, wrap this adapter in a GPU job worker — do not load weights inside Django.
