# OpenTryOn v0.0.6 Release Notes

## Two new services (`decide`, `embed`), a second TTS vendor, and the Oct 2026 model wave

**Release Date**: 12 October 2026

OpenTryOn v0.0.6 adds **42 registry models** on top of v0.0.5 and two new service categories. Same CLI / MCP / registry surface — **132 models**, **137 MCP tools** (132 models + 5 discovery / key / planner), up from 90 models / 95 tools. Nine services: `vton`, `generate`, `edit`, `understand`, `video-generate`, `bg-remove`, `tts`, `decide`, `embed`.

## What's New

### New services

| Service | What it does | Models |
|---|---|---|
| **`decide`** | Typed, calibrated answers (yes/no, choice, score) about text / images / speech — no text output | `jev` (Typesafe API), `d1-3b`, `d1-omni-600m` (Liquid AI, local), `thx-01` (hosted), `thx-01-local` |
| **`embed`** | Multimodal embeddings saved to `.npz` (`--query` adds similarity scores) | `embeddinggemma-2`, `pplx-embed-v2-late-0.6b`, `pplx-embed-v2-late-9b` (all local) |
| **`tts`** *(introduced after v0.0.5)* | Text-to-speech | `eleven-v4`, `eleven-v4-turbo`, `gemini-3.8-flash-tts`, `gemini-3.8-flash-lite-tts` |

`decide` and `embed` are named-model-only in the planner (no chat intent, no default changes).

### Virtual try-on

| Model | Path | CLI |
|---|---|---|
| **FASHN VTON v1.5** | Local, **Apache-2.0**, maskless pixel-space | `fashn-vton-1.5` |
| **Qwen-Image-2.1** | DashScope + local Diffusers (also on generate / edit) | `qwen-image-2.1-pro` / `-turbo` / `-local` / `-turbo-local` |

### Image generate / edit

| Model | Path | CLI |
|---|---|---|
| **Nano Banana 2.1** | Gemini API (`gemini-nano-banana-2.1`); adds 1:4 / 4:1 / 1:8 / 8:1 | `nano-banana-2.1` |
| **FLUX 3 Image** | BFL API, up to 4K, up to 10 reference images on edit | `flux3-image` |
| **Qwen-Image-2.1** | See above | `qwen-image-2.1-*` |

### Video

| Change | CLI |
|---|---|
| **Cosmos 3 Nano local** (Diffusers, BF16/CUDA) | `cosmos3-local` |
| **H3 Max Relight** (Fal; video + lighting sphere) | `fal-h3-max-relight` |
| **H3 Max Lip Sync** (Fal) | `fal-h3-max-lipsync` |
| **P-Video-2-Pro** (Pruna) | `p-video-2-pro` |
| **Veo 3.1** Generate / Fast / **Lite**, 4K, `--last-image`, `--reference-image` | `veo` |
| **Gemini Omni 1.1 Flash** with `--resolution` and `--video` (extend) | `gemini-omni` |
| **Seedance 2.5** reference-to-video (`--reference-image/-video/-audio`) | `seedance` |

### Understanding

| Model | Path | CLI |
|---|---|---|
| **Gemini 3.8 Flash** | Image, video, audio, PDF in; `--thinking-level` | `gemini-3.8-flash` |
| **Claude Haiku 5.5** | Anthropic Messages API (text + image) | `claude-haiku-5-5` |
| **DeepSeek-V4.1-Flash** | DeepSeek Platform (image only) | `deepseek-flash` |
| **DeepSeek-VL2 / DeepSeek-OCR** | Local only | `deepseek-vl2` / `deepseek-ocr` |
| **GLM-5.3-FlashX** | Z.ai | `glm-5.3-flashx` |
| **Qwen3.8-Omni-Flash** | DashScope (adds audio) | `qwen3.8-omni-flash` |
| **Ternary Bonsai 2 27B** | Local llama.cpp / MLX server | `ternary-bonsai-2-27b` |
| **Limite 1B - Violetto** | Local; deliberately out of fashion/media scope | `limite-1b-violetto` |

## Breaking / behaviour changes

- **Sora is deprecated.** OpenAI removed the Sora video API on 24 Sep 2026. `--model sora` is kept for backwards compatibility but emits a `DeprecationWarning` and live calls fail.
- **Planner default video model is now `veo`** (was `sora`).
- **`gemini-omni` now targets `gemini-omni-1.1-flash`**; the old `gemini-omni-flash-preview` id (deprecated 30 Sep 2026) is rejected.
- **`veo` is Veo 3.1 only**; the Veo 3.0 ids (shut down 30 Jun 2026) are rejected.
- `nano-banana-2` is kept, but Google deprecated its model id (`gemini-3.1-flash-image`, no shutdown date yet) — prefer `nano-banana-2.1`.
- New core dependency: **`anthropic>=0.75.0`**. New `[local]` dependency: **`thx01>=0.1.0`** (for `thx-01-local`).

## Install / Upgrade

```bash
pip install -U opentryon
# optional local/GPU models (Leffa, CatVTON, Qwen-Image, Cosmos 3, H3, LTX, Wan 2.2, …):
pip install -U "opentryon[local]"
```

Several local models need libraries newer than the shared `[local]` pins, so install them in a separate environment: Liquid d1 (`transformers>=5.15`), pplx-embed-v2-late (`sentence-transformers>=6.0.0`), EmbeddingGemma 2 (`sentence-transformers`), and FASHN VTON 1.5 (`pip install "git+https://github.com/fashn-AI/fashn-vton-1.5.git"`, git-only).

From source:

```bash
git checkout v0.0.6
pip install -e .
```

## Quick examples

```bash
opentryon generate --model nano-banana-2.1 --prompt "Panoramic lookbook banner" --aspect-ratio 4:1
opentryon vton --model fashn-vton-1.5 --person-image person.jpg --garment-image shirt.jpg   # local GPU
opentryon understand --model gemini-3.8-flash --video runway.mp4 --prompt "Summarise the looks"
opentryon understand --model claude-haiku-5-5 --image garment.jpg --prompt "Fabric, colour, fit?"
opentryon video-generate --model veo --prompt "Transition" --image a.jpg --last-image b.jpg --duration 8
opentryon video-generate --model fal-h3-max-relight --video runway.mp4 --reference-image sphere.png
opentryon tts --model gemini-3.8-flash-tts --text "Welcome to the spring collection." --voice Kore
opentryon decide --model d1-3b --questions questions.json --image dress.jpg                   # local GPU
opentryon embed --model embeddinggemma-2 --text "red gown" --image dress.jpg --query "formal dress"
```

## Docs

- Site: https://tryonlabs.github.io/opentryon/
- Changelog: [CHANGELOG.md](../CHANGELOG.md)
- CLI: [Unified CLI](https://tryonlabs.github.io/opentryon/getting-started/cli)
- Backlog: [Integrate next](https://tryonlabs.github.io/opentryon/community/integrate-next)

## Notes

- Restart MCP after upgrade so Studio and other clients see the new tools. TryOn Studio has no capability screens yet for `decide` or `embed`; the tools work from any MCP client and the Agent chat (named model).
- Typesafe Jev is early access (sign-ups were reported paused on 2026-09-22). Several local models (Liquid d1, EmbeddingGemma 2, pplx-embed-v2-late, FASHN VTON 1.5, Cosmos 3 local) were integrated without a GPU, so their weight loading was not exercised end to end.
- Not integrated: NVIDIA PivotOPD (a training method with no released checkpoints).
- **132 models** across services → **137 MCP tools**.

## Links

- PyPI: https://pypi.org/project/opentryon/0.0.6/
- Tag: https://github.com/tryonlabs/opentryon/releases/tag/v0.0.6
- Previous: [v0.0.5](RELEASE_NOTES_v0.0.5.md)
