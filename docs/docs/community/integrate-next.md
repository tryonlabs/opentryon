---
sidebar_position: 4
title: Integrate next
description: Living backlog of models to add to OpenTryOn — NVIDIA Nemotron/NIM first, then VTON and new modalities
---

# Integrate next

Living **candidate queue** for new adapters. This is not a commitment and it is not the v0.1.0 product roadmap.

| File | Role |
|---|---|
| This page | Canonical list (git + docs site) |
| [`ROADMAP.md`](https://github.com/tryonlabs/opentryon/blob/main/ROADMAP.md) | Product slices (train / eval / one local VTON / agents) |
| [`.cursor/skills/integrate-model/`](https://github.com/tryonlabs/opentryon/tree/main/.cursor/skills/integrate-model) | How to integrate once you pick a row |

**Surveyed:** 29 August 2026 · Sources: [build.nvidia.com/models](https://build.nvidia.com/models), [Nemotron](https://www.nvidia.com/en-us/ai-data-science/foundation-models/nemotron/), [Cosmos 3](https://docs.nvidia.com/cosmos/latest/cosmos3/index.html), [NIM Cosmos WFM](https://docs.nvidia.com/nim/cosmos/latest/introduction.html).

**How to use:** pick a `next` row → follow the [integrate-model skill](https://github.com/tryonlabs/opentryon/blob/main/.cursor/skills/integrate-model/SKILL.md) (Path A first-party API, Path B local). After ship, move the row to **Shipped** and bump the date.

| Status | Meaning |
|---|---|
| `next` | Worth integrating when someone is ready |
| `watch` | Interesting; wait for a clearer API or fashion fit |
| `blocked` | No first-party API / weights / license yet |
| `skip` | Out of scope or we already cover it another way |

NVIDIA access is usually **`NVIDIA_API_KEY`** on [build.nvidia.com](https://build.nvidia.com) (hosted NIM) and/or a self-hosted NIM container. Prefer the hosted NIM for Path A; HF weights + Diffusers/vLLM for Path B. Do **not** wrap FLUX / Qwen-Image / Ideogram a second time through NIM — we already have first-party adapters.

OpenTryOn services today: `vton` · `generate` · `edit` · `understand` · `video-generate` · `bg-remove`. Rows marked **new service** need a new CLI/MCP category before an adapter.

---

## Wave 1 — NVIDIA (fits existing services)

Highest leverage: one NIM provider key unlocks understand + video. Nemotron is **not** a T2I/VTON family — it is open multimodal **understanding / agents**. Cosmos is NVIDIA’s **generation** stack.

| Candidate | Category | Path | Suggested id | Why | Status |
|---|---|---|---|---|---|
| **Nemotron 3 Nano Omni 30B-A3B Reasoning** | Understand (image + video + audio + text) | A NIM | `nemotron-omni` | Hosted NIM chat. Path B local weights later. | shipped |
| **Cosmos 3 Generator (nano, 8B)** | Text-to-video, image-to-video | A NIM (`POST` infer) | `cosmos3` | T2V if prompt only; I2V if `image` set. Optional `COSMOS3_INFER_URL`. | shipped |
| **Cosmos 3 Reasoner (nano)** | Understand (physical / video) | A NIM | `cosmos3-reasoner` | World-model VLM. | shipped |
| Nemotron Nano 12B V2 VL | Understand (image + video) | A NIM | — | Predecessor to Omni. Only if Omni is too large. | `watch` |
| Cosmos 3 Generator **super** (32B) | T2V / I2V | A NIM (`NIM_MODEL_SIZE=super`) | `cosmos3-super` | Same API as nano; heavier GPU. | `watch` |
| Cosmos Predict 2.5 2B | T2V / I2V / V2V | A NIM | `cosmos-predict-2.5` | Older WFM; prefer Cosmos 3 unless Predict-only features are needed. | `watch` |
| Nemotron 3 Nano / Super / Ultra (text) | Text-only agents | A NIM | — | Coding/planning MoE. No image/video I/O. Planner already uses other LLMs. | `skip` |
| Nemotron OCR / Parse / page-table | Document OCR | A NIM | — | Useful later for PDP/catalog agents, not invoke-layer media. | `watch` |
| Nemotron 3.5 Content Safety | Safety classifier | A NIM | — | Guardrail, not a generation/understand tool. | `watch` |

**Nemotron 3 family (context, Aug 2026)**

| Model | Role | OpenTryOn fit |
|---|---|---|
| Nemotron 3 Nano 30B-A3B | Text agents, 1M context | Low (no media) |
| Nemotron 3 Super 120B-A12B | Larger text agents | Low |
| Nemotron 3 Ultra 550B-A55B | Flagship text | Low |
| Nemotron 3.5 Lightning 30B-A3B | Fast text agents | Low |
| **Nemotron 3 Nano Omni 30B-A3B** | Image / video / speech / text | **High — Wave 1** |
| Nemotron Voicechat / ASR / Magpie TTS | Speech | Later (no speech service yet) |
| Llama-Nemotron embed/rerank VL | RAG embeddings | Out of scope |

---

## Wave 2 — Local OSS VTON (already on the product roadmap)

Pick **one** for v0.1.0. These are Path B under `tryon.models` + `opentryon[local]`. NVIDIA has **no** dedicated VTON NIM.

| Candidate | Category | Path | Suggested id | Why | Status |
|---|---|---|---|---|---|
| **CatVTON** (or CatVTON-FLUX LoRA) | Virtual try-on | B | `catvton` | Roadmap Slice D default; &lt;8GB path; LoRA story for Slice B. | `next` |
| IDM-VTON | Virtual try-on | B | `idm-vton` | Alternate if CatVTON quality/license fails. | `watch` |
| OOTDiffusion | Virtual try-on | B | `ootdiffusion` | Alternate; setup scripts already exist under `tryon/`. | `watch` |
| FLUX-fill LoRA | VTON / local LoRA | B | — | Train-slice path, not a third cloud VTON. | `watch` |

---

## By capability (NVIDIA + fashion-relevant others)

### Text-to-image

| Candidate | Path | Notes | Status |
|---|---|---|---|
| **SANA-Sprint** (NVLabs, HF Diffusers) | B | Fast local T2I (1–4 steps). Not a NIM. | `next` |
| Cosmos 3 T2I | B / vLLM-Omni | NIM Generator does **not** expose T2I (one-frame video only in TRT-LLM). | `watch` |
| FLUX.1-dev / schnell / Kontext via NIM | A | We already have BFL **FLUX.2**. Do not add a second FLUX stack. | `skip` |
| FLUX.2 Klein 4B via NIM | A | Distilled FLUX.2; only if BFL does not offer Klein. | `watch` |
| SD 3.5 Large via NIM | A | Crowded T2I table; low fashion differentiation. | `skip` |
| Qwen-Image via NIM | A | Already `qwen-image` (DashScope) + local. | `skip` |
| NVIDIA Edify (Getty/Shutterstock) | — | NIM preview **retired** 6 June 2025. | `skip` |

### Image-to-image / edit

| Candidate | Path | Notes | Status |
|---|---|---|---|
| FLUX.1 Kontext via NIM | A | In-context edit. Skip unless we want NIM as a fallback host. | `skip` |
| Cosmos Transfer 2.5 2B | A NIM | Video **control** transfer (edge/depth/seg/vis), not still I2I. See video. | — |
| SANA-Sprint ControlNet | B | Local realtime I2I if we take SANA. | `watch` |

### Virtual try-on

No NVIDIA / Nemotron VTON. Use Wave 2 (CatVTON first). Cloud VTON is already broad (FLUX VTO, FASHN, Kling, Pruna, Qwen-Image, …).

### Text-to-video

| Candidate | Path | Notes | Status |
|---|---|---|---|
| **Cosmos 3 Generator nano** | A | Wave 1 shipped (`cosmos3`). Physics-aware; fashion lookbooks are a stretch but the API is clean. | shipped |
| Cosmos Predict 2.5 | A | Legacy WFM. | `watch` |
| Muse Video | — | Consumer preview only; no Meta Model API / weights. | `blocked` |

### Audio-to-video / talking head

**New CLI service** (e.g. `audio-to-video`) — do not stuff this into `video-generate` without a design pass.

| Candidate | Path | Notes | Status |
|---|---|---|---|
| **NVIDIA LipSync** NIM | A | Audio → lip-dubbed video. Closest official A2V on the NIM catalog. | `next` |
| Cosmos 3 + sound | B / vLLM-Omni | T2V/I2V **with** synchronized audio. Not on Generator NIM. | `watch` |
| Pruna P-Video-Avatar | — | Already shipped (`p-video-avatar`). | shipped |

### Image & video understanding / multimodal

| Candidate | Path | Notes | Status |
|---|---|---|---|
| **Nemotron 3 Nano Omni** | A | Wave 1 shipped. Native audio (unlike current Kimi/Qwen understand tools). | shipped |
| Cosmos 3 Reasoner / Reason2 8B | A | Reasoner shipped (`cosmos3-reasoner`). Reason2 remains watch. | shipped / `watch` |
| Muse Glimmer 30B (on NIM) | A | Meta multimodal on NVIDIA’s catalog; we already have first-party Muse Image. Glimmer is understand, not gen. | `watch` |
| Llama 3.2 11B/90B Vision on NIM | A | Older VLMs; Omni supersedes for new work. | `skip` |

### 3D model generation

**New CLI service** (e.g. `generate-3d`). Roadmap lists 3D VTON under **Later**.

| Candidate | Path | Notes | Status |
|---|---|---|---|
| **Microsoft TRELLIS** NIM | A | Text-to-3D and image-to-3D meshes; active NVIDIA 3D NIM (Edify 3D is gone). | `next` |
| TRELLIS.2 4B | B | Local; Windows-skewed wheels as of 2026 — verify Linux before Path B. | `watch` |
| Video VTON / 3D VTON | — | Research; no product API picked. | `watch` |

### Out of scope for this list

Biology (AlphaFold, Evo2), CFD, weather, routing, chip sim, protein design — on the NIM catalog, not fashion media.

---

## Suggested integration order

1. ~~`nemotron-omni` / `cosmos3` / `cosmos3-reasoner`~~ **shipped** (Path A, 29 Aug 2026).
2. **`catvton`** (Path B) — v0.1.0 Slice D; product, not vendor chasing.
3. **New services** only after CatVTON: LipSync (A2V), TRELLIS (3D).
4. **SANA-Sprint** if we want a fast local T2I that is not another FLUX/Qwen clone.
5. Optional: `nemotron-omni-local` if someone will run 30B-A3B.

---

## Shipped (do not re-add)

Invoke-layer highlights already in the registry: FLUX.2 (+ Turbo local), Nano Banana family, GPT Image, Muse Image, Ideogram 4.0, P-Image-Ideogram, Qwen-Image API+local, Veo, Sora, LTX-2.5, Hailuo 2.3, MiniMax H3, Wan, Runway Gen-4.5, **Nemotron Omni**, **Cosmos 3 Reasoner**, **Cosmos 3 Generator**, Kimi K2.6/K2.7/K3, Qwen3.8, BEN2, cloud VTON set. Full table: CLI `--help` / registry.

---

## Maintenance

When adding a row: vendor, modality, Path A/B, proposed registry id, license/API URL, status.  
When shipping: move to **Shipped**, delete the `next` row, note the registry id.  
Re-survey NVIDIA: [build.nvidia.com/models](https://build.nvidia.com/models) + Cosmos / Nemotron blogs. Do not paste the entire NIM catalog.
