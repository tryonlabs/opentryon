# OpenTryOn v0.0.9 Release Notes

## Decision models, three new services, Gemini 4 Argon and Omni 1.2, Kimi K3.1 Pro

**Release Date**: 11 November 2026

OpenTryOn v0.0.9 adds **47 model ids** and **three service categories**: `robot-act`, `detect` and `parse`. **210 models**, **215 MCP tools** (210 models + 5 discovery / key / planner), up from 163 models / 168 tools. Sixteen services: `vton`, `generate`, `edit`, `understand`, `video-generate`, `audio-to-video`, `generate-3d`, `bg-remove`, `tts`, `decide`, `embed`, `classify`, `measure`, `robot-act`, `detect`, `parse`.

## What's New

### Decision models (`decide`)

`decide` grows from 7 to 27 models. They all share one question schema (`noul` / `choice` / `score`) and return calibrated probabilities instead of text, so you can swap models without changing your questions.

| CLI model | Path | What it is |
|---|---|---|
| `pplx-decider` | Perplexity Decisions API (`PERPLEXITY_API_KEY`) | Decider v1.2 (27B) / Flash v1.2 (4B); images; optional web grounding |
| `pplx-decider-local` | your SGLang server | Open `perplexity-ai/pplx-decider-v1.1-27b` |
| `clef` | Cloudflare Workers AI (`CLOUDFLARE_API_TOKEN` + `CLOUDFLARE_ACCOUNT_ID`) | Clef (27B) / Clef-flash (9B); images |
| `clef-local` | your SGLang server | Open `Cloudflare/clef` |
| `kev-openrouter` | OpenRouter (`OPENROUTER_API_KEY`) | Jared Palmer's Kev 4B (no first-party API exists) |
| `kev-local` | the Kev repo's `kev.serve` | Kev 0.8B to 27B; MLX on Apple Silicon |
| `autotrust-jev-local` | your vLLM `serve.sh` | AutoTrust JEV-35B / 27B-VL (no hosted API exists) |
| `d3-turbo` … `d3-edge` (+ `-local`) | vLLM Semantic Router (`DECISION_API_KEY`) | Decision 3.0, 0.6B to 27B; adds `box` and `track` questions |
| `mercury-decide` | Inception (`INCEPTION_API_KEY`) | Text + images |

### Understand

| CLI model | What it is |
|---|---|
| `gemini-4-argon` | Google's flagship reasoning model: agentic video processing, long decode, background jobs (`GEMINI_API_KEY`) |
| `gemini-4-argon-cyber-permissive` | Allowlisted variant for defensive cyber work |
| `kimi-k3.1-pro` | Moonshot's K3 successor, 1M context, image + video; `--kimi-model kimi-k3.1-pro-highspeed` for the faster variant |
| `moondream-3.1`, `moondream-3-preview`, `moondream-3.1-local` | Query and caption (`MOONDREAM_API_KEY`, or local Photon) |
| `mercury-3` | Inception's diffusion LLM, text-only, 1M context |
| `beam`, `flint-local` / `flint-openrouter`, `sage-a1.5-local`, `ripple-65b-openrouter` / `ripple-65b-local` | Text-only agent and coding models, named-model-only |

### Image and video

| CLI model | Service | What it does |
|---|---|---|
| `flux3-max` | `video-generate` | FLUX 3 Max (BFL); `flux3-video` gains `--version latest\|max` |
| `kling-v4` | `video-generate` | Kling 4.0 |
| `gemini-omni` | `video-generate` | **Now defaults to Gemini Omni 1.2 Flash**: up to 15s with native audio, new `--duration` |
| `seedream --model-version seedream-5-0-flash` | `generate` + `edit` | Seedream 5.0 Flash, the faster, cheaper 5.0 tier |
| `nano-banana-2` / `-2.1` / `-2-lite` with `--video` | `generate` | Poster or thumbnail from a video clip |
| `cosmos3-nano-t2i`, `cosmos3-nano-v2v` | `generate`, `video-generate` | Cosmos 3 Nano certified NIM (self-hosted) |

### New `robot-act`, `detect` and `parse` services

| CLI model | Service | What it does |
|---|---|---|
| `dream-1`, `dream-1-flash` | `robot-act` | Dream Labs World Action Model (`DREAM_API_KEY`) |
| `cosmos3-nano-droid` | `robot-act` | Cosmos 3 Nano-DROID policy (certified NIM) |
| `moondream-3.1`, `moondream-3-preview`, `moondream-3.1-local` | `detect` | Boxes, points and SVG segmentation masks |
| `nemotron-parse`, `nemotron-parse-local` | `parse` | NVIDIA document OCR (NIM hosted or local) |

### Embed

| CLI model | What it is |
|---|---|
| `nemotron-3.5-embed-1b`, `nemotron-3.5-embed-1b-local` | NVIDIA text + document-image embeddings |

## Breaking changes

- **`google-genai>=2.30.1`** is now required (was `>=1.52.0`). Gemini Omni, Gemini 4 Argon background jobs and Nano Banana video-to-image use the Interactions API, which the 1.x SDK lacks. `pip install -U opentryon` upgrades it.
- **`gemini-omni` defaults to `gemini-omni-1.2-flash`.** Pass `--omni-model gemini-omni-1.1-flash` to keep 1.1 until Google routes it to 1.2 on 3 December 2026.
- No model ids were removed. New services and providers are opt-in and need their own keys or a self-hosted server.

## Fixes

- **Seedream**: `seedream` sent `seedream-5-0-pro-260628`, which BytePlus ModelArk does not list. It now sends the published `dola-seedream-5-0-pro-260628`, and 5.0 Lite and 4.5 use their dated ids. The `--model-version` names you pass are unchanged.

## Install / Upgrade

```bash
pip install -U opentryon
pip install -U "opentryon[local]"
```

From source:

```bash
git checkout v0.0.9
pip install -e .
```

## Quick examples

```bash
opentryon decide --model pplx-decider --questions questions.json --image dress.jpg
opentryon decide --model clef --clef-model clef-flash --questions questions.json --state "Red satin gown"
opentryon understand --model gemini-4-argon --video runway.mp4 --prompt "List every look and its fabric"
opentryon understand --model kimi-k3.1-pro --image look.jpg --prompt "Describe the outfit"
opentryon video-generate --model gemini-omni --prompt "Slow tracking shot down a runway" --duration 15
opentryon detect --model moondream-3.1 --image look.jpg --object "handbag" --skill segment
opentryon parse --model nemotron-parse --image size_chart.png
```

## Docs

- Site: https://tryonlabs.github.io/opentryon/
- Changelog: [CHANGELOG.md](../CHANGELOG.md)
- Decision models: [Decider, Clef, Kev, JEV](https://tryonlabs.github.io/opentryon/api-reference/decision-models)
- Pending, not in this release: Seedream 5.5 (no ModelArk API id yet), Inkling 2 Small (weights pending), Hima ASR (needs a speech-to-text service), VFlash (no public artifacts) — see [Integrate next](https://tryonlabs.github.io/opentryon/community/integrate-next)

## Notes

- Restart MCP after upgrade so clients see the new tools.
- TryOn Studio capability screens cover Image, VTON, Understand, Video, BG Remove, TTS and Detect. `decide`, `embed`, `classify`, `measure`, `robot-act`, `parse`, `audio-to-video` and `generate-3d` are available from the CLI and any MCP client, including Agent chat when you name the model.
- Text-only models such as `beam`, `flint-*`, `sage-a1.5-local` and `ripple-65b-*` are outside the fashion/media scope and are named-model-only.
- **210 models** across 16 services → **215 MCP tools**.

## Links

- PyPI: https://pypi.org/project/opentryon/0.0.9/
- Tag: https://github.com/tryonlabs/opentryon/releases/tag/v0.0.9
- Previous: [v0.0.8](RELEASE_NOTES_v0.0.8.md)
