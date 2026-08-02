---
sidebar_position: 4
title: Unified CLI (opentryon)
description: Run every OpenTryOn adapter -- virtual try-on, image/video generation, editing, understanding, and background removal -- from a single opentryon command.
keywords:
  - opentryon CLI
  - command line interface
  - virtual try-on CLI
  - image generation CLI
---

# Unified CLI (`opentryon`)

Once OpenTryOn is installed (`pip install -U opentryon` or `pip install -e .`;
**v0.0.3+** recommended), every adapter in the repo is available through a
single `opentryon` command with three levels of control: **service** &rarr;
**model** &rarr; **parameters**.

```bash
opentryon <service> --model <model> [params...]
```

- **service**: what kind of task -- `vton`, `generate`, `edit`, `understand`, `video-generate`, `bg-remove`
- **model**: which adapter/provider to use for that service, e.g. `--model flux-vto`
- **parameters**: model-specific flags (image inputs, prompts, sampling knobs, etc.)

## Services and Models

| Service | What it does | Models |
|---|---|---|
| `vton` | Virtual try-on: compose a garment onto a person image | `flux-vto`, `nova-canvas`, `kling-ai`, `segmind`, `p-image-tryon`, `fashn-tryon-max`, `fashn-tryon-v1.6`, `nano-banana-2-lite` |
| `generate` | Text-to-image generation | `nano-banana`, `nano-banana-pro`, `nano-banana-2`, `flux2-pro`, `flux2-flex`, `flux2-turbo` (local), `gpt-image`, `luma-image`, `seedream`, `ideogram`, `grok-imagine-image`, `p-image` |
| `edit` | Image editing (image + instruction &rarr; image) | `nano-banana`, `nano-banana-pro`, `nano-banana-2`, `flux2-pro`, `flux2-flex`, `flux2-turbo` (local), `gpt-image`, `seedream`, `p-image-edit`, `p-image-upscale` |
| `understand` | Image/video understanding | `kimi-k2.6`, `kimi-k2.7-code`, `kimi-k3`, `kimi-vl` (local), `llava-next` (local) |
| `video-generate` | Text/image-to-video generation | `veo`, `sora`, `luma-video`, `luma-ray-3.2`, `seedance`, `kling-v3`, `kling-v3-omni`, `kling-v2-5-turbo`, `grok-imagine-video`, `gemini-omni`, `p-video`, `p-video-replace`, `p-video-avatar`, `p-video-animate` |
| `bg-remove` | Background removal | `ben2` (local) |

Models marked "local" run on your own GPU and require
`pip install opentryon[local]`; everything else calls a cloud API and needs
the corresponding API key set in your environment (see
[Configuration](configuration.md)).

## Discovering Flags

Every level of the CLI is self-documenting:

```bash
opentryon --help                              # list services
opentryon understand --help                   # list models for a service
opentryon understand --model kimi-k2.6 --help # list that model's parameters
```

## Examples

```bash
# Virtual try-on
opentryon vton --model flux-vto \
  --person-image model.png --garment-image garment.png

# Text-to-image
opentryon generate --model nano-banana-pro \
  --prompt "A fashion model wearing elegant evening wear" --resolution 4K

# Image editing
opentryon edit --model gpt-image \
  --images person.jpg --prompt "Change the jacket to black leather"

# Image/video understanding (Kimi K2.6, general-purpose -- not fashion-only)
opentryon understand --model kimi-k2.6 \
  --image garment.jpg --prompt "Describe this outfit."
opentryon understand --model kimi-k2.6 \
  --video runway_clip.mp4 --prompt "Summarize the styling shown."

# Coding-focused multimodal understanding
opentryon understand --model kimi-k2.7-code \
  --image ui_mockup.png --prompt "Write the HTML/CSS for this design."

# Kimi K3 (flagship multimodal reasoning)
opentryon understand --model kimi-k3 \
  --image garment.jpg \
  --prompt "Write a marketplace-ready title and bullet points." \
  --reasoning-effort high

# Open-weight local understanding (no API key, needs a GPU)
opentryon understand --model kimi-vl --image garment.jpg

# Text-to-video
opentryon video-generate --model veo \
  --prompt "A model walking a runway in slow motion" --duration 6

# Seedance 2.5 / Kling 3.0 / Ray 3.2 / Grok Imagine Video / Pruna P-Video
opentryon video-generate --model seedance --prompt "10s lookbook walk" --duration 10
opentryon video-generate --model kling-v3 --prompt "atelier pan" --mode pro --sound on
opentryon video-generate --model luma-ray-3.2 --prompt "dolly through mist" --resolution 720p
opentryon video-generate --model grok-imagine-video --prompt "cinematic push-in" --duration 6
opentryon video-generate --model p-video --prompt "runway walk, soft light" --duration 5
opentryon video-generate --model p-video-replace --video clip.mp4 --images identity.jpg
opentryon video-generate --model p-video-avatar --image portrait.jpg --voice-script "Hello from the showroom."
opentryon video-generate --model p-video-animate --video driver.mp4 --image subject.jpg

# Seedream / Ideogram / Grok Imagine Image / Pruna P-Image
opentryon generate --model seedream --prompt "editorial sneaker still" --size 2K
opentryon generate --model ideogram --prompt 'Poster "SUMMER 2026"' --rendering-speed QUALITY
opentryon generate --model grok-imagine-image --prompt "street-art collage" --aspect-ratio 16:9
opentryon generate --model p-image --prompt "luxury knitwear flatlay" --aspect-ratio 1:1
opentryon edit --model p-image-edit --images photo.jpg --prompt "clean studio background"
opentryon edit --model p-image-upscale --image photo.jpg --target 8

# Background removal
opentryon bg-remove --model ben2 --image product.jpg --refine
```

Every command accepts `-o/--output-dir` (default: `outputs/`) and
`--dry-run` (print the resolved adapter call without invoking the API/GPU):

```bash
opentryon vton --model flux-vto \
  --person-image model.png --garment-image garment.png --dry-run
```

## Local (GPU-only) Models

Local models (`flux2-turbo`, `kimi-vl`, `llava-next`, `ben2`) need the
`local` extra:

```bash
pip install opentryon[local]
```

Running a local model without it prints an install hint instead of a raw
stack trace:

```
✗ 'Kimi-VL (open-weight, local)' requires local ML dependencies that aren't installed.
  Install them with: pip install opentryon[local]
```

## See Also

- [MCP Server](mcp)
- [OpenAPI & Postman](openapi-swagger)
- [Kimi K2.6 / K2.7 Code / K3 understanding](../api-reference/kimi.md)
- [Kimi-VL open-weight local model](../local-models/kimi-vl.md)
- [Adding a new model to the CLI](../advanced/new-model-checklist.md)
- [Roadmap](../community/roadmap)
