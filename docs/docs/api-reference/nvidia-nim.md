---
sidebar_position: 42
title: NVIDIA NIM (Nemotron / Cosmos)
description: Path A NVIDIA NIM adapters — Nemotron 3 Nano Omni, Cosmos 3 Reasoner, and Cosmos 3 Generator
---

# NVIDIA NIM (Nemotron / Cosmos)

One key, `NVIDIA_API_KEY` from [build.nvidia.com](https://build.nvidia.com), unlocks Nemotron / Cosmos / TRELLIS / LipSync registry ids.

| CLI `--model` | Service | Adapter | Upstream id |
|---|---|---|---|
| `nemotron-omni` | `understand` | `NemotronOmniUnderstandAdapter` | `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning` |
| `nemotron-3.5-super-vl` | `understand` | `Nemotron35SuperVLUnderstandAdapter` | `nvidia/nemotron-3.5-super-vl-120b-a12b` |
| `nemotron-3.5-embed-1b` | `embed` | `Nemotron35EmbedAdapter` | `nvidia/nemotron-3.5-embed-1b` |
| `nemotron-parse` | `parse` | `NemotronParseAdapter` | `nvidia/nemotron-parse` |
| `cosmos3-reasoner` | `understand` | `Cosmos3ReasonerAdapter` | `nvidia/cosmos3-nano-reasoner` |
| `cosmos3` | `video-generate` | `Cosmos3VideoAdapter` | Cosmos 3 Generator nano (`POST` infer, `b64_video`) |
| `trellis` | `generate-3d` | `TrellisMeshAdapter` | Microsoft TRELLIS (`POST` genai infer → GLB/STL) |
| `nvidia-lipsync` | `audio-to-video` | `LipSyncAdapter` | Maxine LipSync NIM (self-hosted gRPC; no hosted REST) |

Nemotron is **understanding / agents**, not T2I or VTON. Cosmos 3 Generator is **physics-aware T2V / I2V**. There is no NVIDIA VTON NIM — dedicated try-on APIs and local weights stay on the [integrate-next](../community/integrate-next.md) Wave 2 list.

Official docs:

- [Nemotron 3 Nano Omni](https://docs.api.nvidia.com/nim/reference/nvidia-nemotron-3-nano-omni-30b-a3b-reasoning)
- [Nemotron 3.5 Super VL](https://build.nvidia.com/nvidia/nemotron-3.5-super-vl-120b-a12b/modelcard)
- [Cosmos 3 Reasoner](https://build.nvidia.com/nvidia/cosmos3-nano-reasoner)
- [Cosmos 3 Generator API](https://docs.nvidia.com/nim/cosmos/latest/api-reference.html)
- [Cosmos 3 nano model card](https://build.nvidia.com/nvidia/cosmos3-nano/modelcard)

## Auth

```bash
export NVIDIA_API_KEY=nvapi-...
# optional chat override
# export NVIDIA_API_BASE_URL=https://integrate.api.nvidia.com/v1
# optional Generator infer URL (self-hosted NIM)
# export COSMOS3_INFER_URL=http://127.0.0.1:8000/v1/infer
```

Studio Connect lists **NVIDIA NIM (Nemotron / Cosmos)** after an MCP restart.

## Understand — Nemotron Omni

OpenAI-compatible `POST /v1/chat/completions`. Inputs: image, video, **audio**, text. Thinking is on by default (`chat_template_kwargs.enable_thinking`).

```bash
opentryon understand --model nemotron-omni \
  --image garment.jpg \
  --prompt "Describe this outfit."

opentryon understand --model nemotron-omni \
  --video lookbook.mp4 \
  --prompt "What garments appear, in order?"

opentryon understand --model nemotron-omni \
  --audio clip.wav \
  --prompt "Transcribe and summarize."
```

MCP tool: `understand_nemotron_omni`.

## Understand — Nemotron 3.5 Super VL

Same OpenAI-compatible chat surface. **Image + video + text** (no audio — use Nemotron Omni for audio). Reasoning via `enable_thinking` (on by default). 120B total / 12B active MoE; up to 1M context on NIM.

```bash
opentryon understand --model nemotron-3.5-super-vl \
  --image lookbook.jpg \
  --prompt "List each garment type and dominant colors."

opentryon understand --model nemotron-3.5-super-vl \
  --video runway.mp4 \
  --prompt "Describe outfit changes shot by shot." \
  --no-thinking
```

MCP tool: `understand_nemotron_3_5_super_vl`.

## Understand — Cosmos 3 Reasoner

Same chat surface, different model. Physical-world image/video QA. `--thinking` prefixes NVIDIA’s documented reasoning hint.

```bash
opentryon understand --model cosmos3-reasoner \
  --video clip.mp4 \
  --prompt "What physical interactions occur?" \
  --thinking
```

MCP tool: `understand_cosmos3_reasoner`.

## Video — Cosmos 3 Generator

JSON infer body: T2V when `prompt` has no `image`; I2V when `--image` is set. Response field `b64_video` (MP4). Default hosted URL is `https://ai.api.nvidia.com/v1/genai/nvidia/cosmos3-nano`. If that catalog path 404s (the hosted snippet has been incomplete at times), point `COSMOS3_INFER_URL` at a [self-hosted Generator NIM](https://docs.nvidia.com/nim/cosmos/latest/introduction.html).

Resolution is a tier (`256` / `480` / `720`) plus optional aspect (`720_16_9`, `480_9_16`, …). Bare `720` means `720_16_9` (1280×720). Default 121 frames at 24 fps.

```bash
opentryon video-generate --model cosmos3 \
  --prompt "A fashion model walks a concrete runway at dusk." \
  --resolution 720 --num-output-frames 121

opentryon video-generate --model cosmos3 \
  --prompt "gentle turn" \
  --image look.jpg
```

MCP tool: `video_generate_cosmos3`.

Text-to-image, video-to-video, and Nano-DROID actions are on the certified NIM, not this hosted catalog. See [Cosmos 3 Nano NIM](cosmos3-nano).

## Python

```python
from tryon.api.nvidia import (
    NemotronOmniUnderstandAdapter,
    Nemotron35SuperVLUnderstandAdapter,
    Cosmos3ReasonerAdapter,
    Cosmos3VideoAdapter,
)

caption = NemotronOmniUnderstandAdapter().understand(
    image="garment.jpg",
    prompt="Describe this outfit.",
)
clip = Cosmos3VideoAdapter().generate_text_to_video(
    "A robot walks through a clean atelier.",
)
```

## Local weights

The open `nvidia/Cosmos3-Nano` weights run through Diffusers as `--model cosmos3-local` — see [Cosmos 3 (local)](../local-models/cosmos3.md).

## Planner

Named-model pins: `nemotron-3.5-super-vl`, `nemotron-omni`, `cosmos3-reasoner`, `cosmos3`, `cosmos3-local` (and longer phrases such as `nemotron 3.5 super vl`). Defaults: `kimi-k2.6` / `veo`.

## Generate 3D — TRELLIS

```bash
opentryon generate-3d --model trellis \
  --prompt "Red leather handbag on a studio pedestal" \
  --output-format glb

opentryon generate-3d --model trellis --image product.jpg --output-format glb
```

MCP tool: `generate_3d_trellis`. Optional `TRELLIS_INFER_URL` for a local NIM container.

## Audio-to-video — LipSync (self-hosted)

```bash
export LIPSYNC_CLIENT_SCRIPT=/path/to/nim-clients/lipsync/python/scripts/lipsync.py
export LIPSYNC_GRPC_TARGET=127.0.0.1:8001

opentryon audio-to-video --model nvidia-lipsync \
  --video portrait.mp4 --audio line.wav
```

MCP tool: `audio_to_video_nvidia_lipsync`. For hosted dubbing without a GPU NIM, use `video-generate --model fal-h3-max-lipsync`.

## Not in this release

- Nemotron Omni **local** weights (`nemotron-omni-local`) — 30B-A3B Path B later
- Cosmos 3 Generator **super** (32B)
- Cosmos Transfer / Predict 2.5
