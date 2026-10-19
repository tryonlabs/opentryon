# OpenTryOn v0.0.8 Release Notes

## Body measurement, FLUX 3 Klein and Video, lip-sync, 3D, and a larger understand / decide / embed set

**Release Date**: 19 October 2026

OpenTryOn v0.0.8 adds **13 model ids** (15 registry slots, because FLUX 3 Image Klein is on both `generate` and `edit`) and **three service categories**: `measure`, `audio-to-video`, and `generate-3d`. **163 models**, **168 MCP tools** (163 models + 5 discovery / key / planner), up from 148 models / 153 tools. Thirteen services: `vton`, `generate`, `edit`, `understand`, `video-generate`, `audio-to-video`, `generate-3d`, `bg-remove`, `tts`, `decide`, `embed`, `classify`, `measure`.

## What's New

### New `measure` service — Clad body sizing

| CLI model | Path | What it does |
|---|---|---|
| `clad-body-photo` | Clad API (`CLAD_API_KEY`) | One photo + height → async job → ISO 8559-1 measurements |
| `clad-body-questionnaire` | Clad API | Eight-question sizing flow, no photo |
| `clad-body-local` | `clad-body` library | Measure existing Anny or MHR param JSON. Not photo reconstruction |

### Image and video

| CLI model | Service | What it does |
|---|---|---|
| `flux3-image-klein` | `generate` + `edit` | Distilled FLUX 3 Image, first-party BFL (`BFL_API_KEY`) |
| `flux3-image-klein-local` | `generate` + `edit` | Same family via Diffusers `ModularPipeline` |
| `flux3-video` | `video-generate` | FLUX 3 Video: text, keyframes, video-to-video, draft |
| `sana-sprint` | `generate` | Local NVLabs SANA-Sprint, 1–4 steps |

### New `audio-to-video` and `generate-3d` services

| CLI model | Service | What it does |
|---|---|---|
| `nvidia-lipsync` | `audio-to-video` | NVIDIA Maxine LipSync NIM (self-hosted gRPC; no hosted REST) |
| `trellis` | `generate-3d` | Microsoft TRELLIS image/text → mesh (GLB/STL) |

### Understand, decide, embed

| CLI model | Service | What it does |
|---|---|---|
| `nemotron-3.5-super-vl` | `understand` | NVIDIA NIM VLM (image, video, text; no audio). Same `NVIDIA_API_KEY` |
| `videojev-4b`, `videojev-35b-a3b` | `decide` | Local video grounding and multiple-choice QA. No hosted API |
| `gemini-embedding-2` | `embed` | Hosted multimodal embeddings (text, image, audio, video, PDF). `GEMINI_API_KEY` |

The docs site was also restyled to the TryOn brand system.

## Breaking changes

- No removed model ids and no new required dependency in `install_requires`.
- New services are opt-in: `measure` needs `CLAD_API_KEY` for the hosted models; `nvidia-lipsync` needs a local NIM gRPC target; `clad-body-local` needs `pip install 'clad-body[anny]'` or `'clad-body[mhr]'`.

## Install / Upgrade

```bash
pip install -U opentryon
pip install -U "opentryon[local]"
```

From source:

```bash
git checkout v0.0.8
pip install -e .
```

## Quick examples

```bash
opentryon measure --model clad-body-photo --photo full_body.jpg --height-cm 172
opentryon measure --model clad-body-questionnaire --age 30 --gender female --height-cm 168
opentryon generate --model flux3-image-klein --prompt "linen shirt, studio light"
opentryon video-generate --model flux3-video --prompt "model turning, soft daylight"
opentryon understand --model nemotron-3.5-super-vl --image look.jpg --prompt "Describe the outfit"
opentryon embed --model gemini-embedding-2 --text "black leather ankle boots"
opentryon generate-3d --model trellis --image product.jpg
```

## Docs

- Site: https://tryonlabs.github.io/opentryon/
- Changelog: [CHANGELOG.md](../CHANGELOG.md)
- Clad: [API](https://tryonlabs.github.io/opentryon/api-reference/clad-body) · [local](https://tryonlabs.github.io/opentryon/local-models/clad-body-local)
- Still queued (not in this release): `segment` and `detect` — [new services backlog](https://tryonlabs.github.io/opentryon/advanced/new-services-backlog)

## Notes

- Restart MCP after upgrade so clients see the new tools.
- TryOn Studio capability screens still cover Image, VTON, Understand, Video, BG Remove, and TTS. `measure`, `decide`, `embed`, `classify`, `audio-to-video`, and `generate-3d` are available from the CLI and any MCP client, including Agent chat when you name the model.
- **163 models** across 13 services → **168 MCP tools**.

## Links

- PyPI: https://pypi.org/project/opentryon/0.0.8/
- Tag: https://github.com/tryonlabs/opentryon/releases/tag/v0.0.8
- Previous: [v0.0.7](RELEASE_NOTES_v0.0.7.md)
