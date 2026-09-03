---
sidebar_position: 5
title: MiniMax H3 (local)
description: Open-weight MiniMax H3 text/image-to-video via Hugging Face Diffusers ModularPipeline on a local GPU.
keywords:
  - MiniMax H3
  - Hailuo 3
  - Diffusers
  - local video
  - open weights
---

# MiniMax H3 (local Diffusers)

Open-weight [MiniMax H3](https://huggingface.co/MiniMaxAI/MiniMax-H3) via Hugging Face Diffusers `ModularPipeline` (`t2va` / `fl2va`). Runs on your CUDA GPU with ComponentsManager CPU offload by default. Outputs MP4 with native stereo audio.

Hosted API twin: [MiniMax H3 (official API)](../api-reference/minimax-h3.md) (`--model minimax-h3`). Fast hosted variant: `--model minimax-h3-max` (no local twin).

Local weights are **H3-Base at 768p** (short edge). The hosted **H3-Regenerate-2K** pass is not open-sourced — use the API for 2K.

## License (read this)

The MiniMax H3 **Community License for local weights excludes the United States, the European Union, the United Kingdom, and South Korea** unless you have a separate authorization. The **hosted API** (`--model minimax-h3`) is globally available. Confirm the current terms on the [model card](https://huggingface.co/MiniMaxAI/MiniMax-H3) before downloading.

## Requirements

| Item | Notes |
|------|--------|
| GPU | CUDA required. Transformer ~61.7GB bf16 + Qwen3-VL conditioner ~62GB. Offload is on by default. |
| Host RAM | ~75GB+ if you int8-quantize for a 24–32GB consumer card (see Diffusers memory recipes) |
| Disk | Large snapshot (`MiniMaxAI/MiniMax-H3`); `fl2va` loads `transformer/`, not `transformer_ref/` |
| Diffusers | **Must install from main** — MiniMax-H3 ModularPipeline is not in a stable Diffusers release yet |

```bash
pip install opentryon[local]
pip install "git+https://github.com/huggingface/diffusers"
export HF_TOKEN=hf_...   # if the repo is gated or rate-limited
```

Optional overrides:

```bash
# export MINIMAX_H3_MODEL_ID=MiniMaxAI/MiniMax-H3
# export MINIMAX_H3_MODEL_PATH=/path/to/local/snapshot
```

## CLI

```bash
opentryon video-generate --model minimax-h3-local \
  --prompt "A fashion model walking a runway at dusk, camera tracking, soft ambient sound" \
  --width 960 --height 544 --num-frames 124 --seed 42

opentryon video-generate --model minimax-h3-local \
  --image look.jpg \
  --prompt "Gentle fabric motion as the model turns" \
  --width 960 --height 544 --num-frames 124
```

`width` / `height` must be divisible by 32. Default **960×544** is a practical smaller canvas (~2.3× faster than 1344×768). `num_frames` snaps to `17*n+5` in the ~5–15s window at 24 fps (124 ≈ 5s).

There is no `guidance_scale` or negative prompt — the open transformer is CFG-distilled.

## Python

```python
from tryon.models import MiniMaxH3LocalAdapter

adapter = MiniMaxH3LocalAdapter()  # MiniMaxAI/MiniMax-H3, CPU offload on
video = adapter.generate_text_to_video(
    prompt="A cinematic shot of fabric flowing in wind, atelier ambience",
    width=960,
    height=544,
    num_frames=124,
    seed=42,
)
open("h3-local.mp4", "wb").write(video)
```

## Notes

- Omni-reference (`ref2va` / `transformer_ref/`) is not wired into the CLI; use the [hosted API](../api-reference/minimax-h3.md) for reference-to-video, or Diffusers directly.
- Consumer-GPU int8 + group offload recipes live in the [Diffusers MiniMax-H3 docs](https://huggingface.co/docs/diffusers/main/en/api/pipelines/minimax_h3).
- MCP tool: `video_generate_minimax_h3_local`.
