---
sidebar_position: 4
title: NVIDIA Cosmos 3 (local)
description: Open-weight NVIDIA Cosmos 3 Nano text/image-to-video via Hugging Face Diffusers on a local GPU.
keywords:
  - Cosmos 3
  - NVIDIA
  - Cosmos3-Nano
  - Diffusers
  - local video
  - open weights
---

# NVIDIA Cosmos 3 (local Diffusers)

Open-weight [Cosmos 3 Nano](https://huggingface.co/nvidia/Cosmos3-Nano) (16B parameters) via the Diffusers `Cosmos3OmniPipeline`. Runs text-to-video and image-to-video on your own CUDA GPU.

Hosted twin: [NVIDIA NIM Cosmos 3 Generator](../api-reference/nvidia-nim.md) (`--model cosmos3`).

## Requirements

| Item | Notes |
|------|--------|
| GPU | CUDA required; large VRAM (16B parameters). VRAM is not published upstream: start with `--cpu-offload` on smaller cards |
| Precision | **BF16 only** — FP16 / FP8 / FP4 are not supported upstream |
| License | OpenMDW 1.1 (commercial and non-commercial use) |
| Diffusers | Needs a build that ships `Cosmos3OmniPipeline` (install from main if your release lacks it) |

```bash
pip install opentryon[local]
pip install "git+https://github.com/huggingface/diffusers"
```

Optional overrides:

```bash
# export COSMOS3_MODEL_ID=nvidia/Cosmos3-Nano
# export COSMOS3_MODEL_PATH=/path/to/local/snapshot
```

## CLI

```bash
opentryon video-generate --model cosmos3-local \
  --prompt "A fashion model walking a runway at dusk, tracking camera" \
  --width 1280 --height 720 --num-frames 189 --seed 42

opentryon video-generate --model cosmos3-local \
  --image look.jpg --prompt "Slow turn, soft fabric motion" --cpu-offload
```

Defaults match the upstream recipe: 1280×720, 189 frames @ 24 fps, 35 steps, guidance 6.0, UniPC scheduler with `flow_shift=10`. The Diffusers safety checker is on by default.

## Python

```python
from tryon.models import Cosmos3LocalAdapter

adapter = Cosmos3LocalAdapter()  # loads nvidia/Cosmos3-Nano
video = adapter.generate_text_to_video(
    prompt="A fashion model walking a runway at dusk, tracking camera",
    num_frames=189, height=720, width=1280, seed=42,
)
open("cosmos3.mp4", "wb").write(video)
```

MCP tool: `video_generate_cosmos3_local`.

## Notes

- Upstream examples use **structured JSON captions** (`json.dumps({...})`); plain text works and a `dict` prompt is serialised to JSON automatically.
- Cosmos 3 sound / T2I via vLLM-Omni and the local Cosmos 3 Reasoner are not wired yet — see [integrate-next](../community/integrate-next.md).
- For production metering, run this adapter in a GPU worker rather than the web process.
