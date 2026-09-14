# OpenTryOn v0.0.5 Release Notes

## Dedicated VTON, Images 2.5, H3 family, and a registry super-agent

**Release Date**: 14 September 2026

OpenTryOn v0.0.5 grows the invoke layer shipped in v0.0.4: first-party and local virtual try-on, ChatGPT Images 2.5, MiniMax H3 / H3 Max (plus Fal as the first third-party hoster), NVIDIA NIM, Hy4, Qwen-Image, Wan 3.0, and a planner that runs a filtered slice of the live registry. Same CLI / MCP / registry surface — **90 models**, **95 MCP tools**.

## What's New

### Virtual try-on

| Model | Path | CLI |
|---|---|---|
| **Google Vertex VTON** | Vertex `recontext_image` (ADC, not `GEMINI_API_KEY`) | `google-vton` |
| **OutfitAnyone-Plus** | DashScope Beijing `aitryon-plus` | `outfitanyone-plus` |
| **Photoroom Try-On / Virtual Model** | Image Editing API | `photoroom-vton` / `photoroom-virtual-model` |
| **Leffa** | Local GPU (`opentryon[local]`) | `leffa` |
| **CatVTON** | Local GPU (CC BY-NC-SA) | `catvton` |
| **Qwen-Image VTON** | DashScope 3.0 + local Diffusers | `qwen-image` / `qwen-image-local` |
| **Muse Image** | Meta Model API composition | `muse-image` |

### Image generate / edit

| Model | Path | CLI |
|---|---|---|
| **ChatGPT Images 2.5** | OpenAI Images API Flare + Sunburst | `gpt-image-2.5` / `gpt-image-2.5-sunburst` |
| **P-Image-Ideogram** | Pruna (`PRUNA_API_KEY`, not Ideogram 4.0) | `p-image-ideogram` |
| **Qwen-Image** | DashScope + local Diffusers | `qwen-image` / `qwen-image-local` |
| **Muse Image** | Meta Model API | `muse-image` |

`--model gpt-image` remains GPT-Image-1.5. Quality on 2.5 adds `xhigh` / `max`.

### Video

| Model | Path | CLI |
|---|---|---|
| **MiniMax H3** | Official V2 API + local Diffusers | `minimax-h3` / `minimax-h3-local` |
| **MiniMax H3 Max** | First-party V2 (no R2V) | `minimax-h3-max` |
| **Fal H3 Max** | Third-party Fal queue (T2V / I2V / R2V) | `fal-h3-max` |
| **Wan 3.0** | DashScope hosted (local Wan stays `wan-2.2`) | `wan-3.0` |
| **NVIDIA Cosmos 3** | NIM Generator | `cosmos3` |

Seedance 2.5 now maps `--model-version seedance-2-5` to official ModelArk id `dreamina-seedance-2-5-260628`.

### Understanding

| Model | Path | CLI |
|---|---|---|
| **NVIDIA Nemotron Omni** | NIM chat | `nemotron-omni` |
| **NVIDIA Cosmos 3 Reasoner** | NIM VLM | `cosmos3-reasoner` |
| **Tencent Hy4 preview** | TokenHub + local vLLM/SGLang | `hy4-preview` / `hy4-preview-local` |

### Planner

- `planner_agent` classifies intent, then binds a **filtered** registry slice and calls `invoke_model` (same runner as MCP model tools). Named models in the prompt pin that id.
- `help` answers from the live catalog. Chat photos are resized to 2048px temp files before invoke (avoids GPT-4o 429 / TPM).
- VTON / model-swap are recipes, not LangChain loops. `tryon.tools` stays frozen.

## Install / Upgrade

```bash
pip install -U opentryon
# optional local/GPU models (Leffa, CatVTON, H3, Qwen-Image, LTX, Wan 2.2, …):
pip install -U "opentryon[local]"
```

From source:

```bash
git checkout v0.0.5
pip install -e .
```

## Quick examples

```bash
opentryon vton --model google-vton --person-image person.jpg --garment-image shirt.jpg
opentryon vton --model photoroom-vton --person-image person.jpg --garment-image shirt.jpg
opentryon vton --model leffa --person-image person.jpg --garment-image shirt.jpg  # needs GPU + [local]
opentryon generate --model gpt-image-2.5 --prompt "studio lookbook, navy coat"
opentryon video-generate --model minimax-h3 --prompt "runway walk" --duration 6
opentryon video-generate --model fal-h3-max --prompt "runway walk" --duration 8
opentryon understand --model hy4-preview --prompt "What can OpenTryOn do for PDP copy?"
```

## Docs

- Site: https://tryonlabs.github.io/opentryon/
- Changelog: [CHANGELOG.md](../CHANGELOG.md)
- CLI: [Unified CLI](https://tryonlabs.github.io/opentryon/docs/getting-started/cli)
- Planner: [Planner agent](https://tryonlabs.github.io/opentryon/docs/agents/planner-agent)
- Model integration guidelines: [docs](https://tryonlabs.github.io/opentryon/docs/advanced/model-integration-guidelines)

## Notes

- No breaking CLI/MCP changes vs v0.0.4 — new registry entries, planner behavior, and Seedance id mapping only.
- Restart MCP after upgrade so Studio and other clients see the new tools.
- Google VTON needs `GOOGLE_CLOUD_PROJECT` + ADC, not `GEMINI_API_KEY`. OutfitAnyone-Plus needs a Beijing-region DashScope key. Photoroom is `PHOTOROOM_API_KEY`. Fal H3 Max is `FAL_KEY` (distinct from first-party `MINIMAX_API_KEY`).
- CatVTON weights are **CC BY-NC-SA 4.0**. Muse Video is not integrable (no generation API).
- **90 models** across services → **95 MCP tools** (90 models + 5 discovery / key / planner).

## Links

- PyPI: https://pypi.org/project/opentryon/0.0.5/
- Tag: https://github.com/tryonlabs/opentryon/releases/tag/v0.0.5
- Previous: [v0.0.4](RELEASE_NOTES_v0.0.4.md)
