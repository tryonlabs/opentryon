---
sidebar_position: 4
title: Integrate next
description: Living backlog of models to add to OpenTryOn — NVIDIA NIM, virtual try-on APIs and local weights, then new modalities
---

# Integrate next

Living **candidate queue** for new adapters. This is not a commitment and it is not the v0.1.0 product roadmap.

| File | Role |
|---|---|
| This page | Canonical list (git + docs site) |
| [`ROADMAP.md`](https://github.com/tryonlabs/opentryon/blob/main/ROADMAP.md) | Product slices (train / eval / one local VTON / agents) |
| [`.cursor/skills/integrate-model/`](https://github.com/tryonlabs/opentryon/tree/main/.cursor/skills/integrate-model) | How to integrate once you pick a row |

**Surveyed:** 29 August 2026 · Sources: [build.nvidia.com/models](https://build.nvidia.com/models), [Google `virtual-try-on-001`](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/imagen/virtual-try-on-001), [Alibaba OutfitAnyone-Plus](https://www.alibabacloud.com/help/en/model-studio/aitryon-plus-api), [Photoroom Virtual Try-On](https://docs.photoroom.com/image-editing-api-plus-plan/virtual-try-on), [CatVTON](https://github.com/Zheng-Chong/CatVTON/), [Leffa](https://github.com/franciszzj/Leffa), [Nemotron](https://www.nvidia.com/en-us/ai-data-science/foundation-models/nemotron/), [Cosmos 3](https://docs.nvidia.com/cosmos/latest/cosmos3/index.html).

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

## Wave 2 — Virtual try-on (fashion / D2C / marketplace)

Compile-only as of 29 Aug 2026 — **do not integrate until asked.** Developers building fitting rooms, PDP/catalog on-model shots, and marketplace listing tools need **dedicated** person+garment try-on, not another general I2I compose.

**Trust order for Path A:** hyperscalers and durable public platforms first (Google, Amazon, Alibaba, BFL, Kuaishou, Meta). Fashion specialists we already ship (FASHN, Pruna) stay. Smaller photo-API vendors are `watch` unless a customer names them. Do **not** add Fal / Replicate / PiAPI wrappers of models we already call first-party.

NVIDIA has **no** dedicated VTON NIM. Product roadmap Slice D is still: pick **one** local OSS path for v0.1.0.

### Already in OpenTryOn (do not re-add)

| Registry id | Vendor | Kind | Notes |
|---|---|---|---|
| `flux-vto` | Black Forest Labs | Dedicated VTON API | First-party FLUX VTO |
| `google-vton` | Google Cloud Vertex | Dedicated VTON API | `virtual-try-on-001`; ADC + `GOOGLE_CLOUD_PROJECT`, not `GEMINI_API_KEY` |
| `outfitanyone-plus` | Alibaba Cloud Model Studio | Dedicated VTON API | `aitryon-plus`; Beijing-region `DASHSCOPE_API_KEY`, not Qwen-Image compose |
| `photoroom-vton` / `photoroom-virtual-model` | Photoroom | Dedicated VTON + catalog API | Image Editing `/v2/edit`; shopper try-on **or** flat-lay → on-model |
| `nova-canvas` | Amazon Bedrock | Dedicated VTON API | Garment classes incl. footwear |
| `kling-ai` | Kuaishou (Kling / Kolors) | Dedicated VTON API | First-party Kolors v1 / v1.5 |
| `fashn-tryon-max` / `fashn-tryon-v1.6` | FASHN | Dedicated VTON API | Fashion suite; v1.6 is the fast e-comm path |
| `p-image-tryon` | Pruna | Dedicated VTON API | Multi-garment (up to 11 refs) |
| `segmind` | Segmind | Hosted try-on diffusion | Third-party hoster; keep, do not add more hosters |
| `nano-banana-2-lite` | Google Gemini | Composition I2I | **Not** Vertex `virtual-try-on-001` |
| `qwen-image` / `qwen-image-local` | Alibaba Qwen | Composition I2I | **Not** OutfitAnyone `aitryon-plus` |
| `muse-image` | Meta | Composition I2I | Multi-ref edit, not a garment-fit model |

### Path A — dedicated VTON APIs to add

Prefer first-party APIs. Related catalog jobs (product→model, model-swap, parsing) are listed only when they are that vendor’s try-on product.

| Candidate | Vendor durability | Task | Suggested id | Why | Status |
|---|---|---|---|---|---|
| **Google `virtual-try-on-001`** | Google Cloud (GA 20 Jan 2026; listed discontinue 20 Jan 2027) | Shopper / catalog image VTON | `google-vton` | Dedicated Vertex / Gemini Enterprise predict API. Person + product image, 1–4 samples, C2PA watermark. Auth is **ADC / GCP project**, not `GEMINI_API_KEY`. Distinct from Nano Banana compose. [Docs](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/imagen/virtual-try-on-001) | shipped |
| **Alibaba OutfitAnyone-Plus (`aitryon-plus`)** | Alibaba Cloud Model Studio | Image VTON + combo top/bottom | `outfitanyone-plus` | Dedicated DashScope try-on (async). Top, bottoms, dress, face restore, parsing companion `aitryon-parsing-v1`. Same company as Qwen; **Beijing-region key**, not the Qwen-Image compose path. [Docs](https://www.alibabacloud.com/help/en/model-studio/aitryon-plus-api) | shipped |
| **Photoroom Virtual Try-On / Virtual Model** | Photoroom (widely used e-comm photo API) | Fitting room **or** garment→lifestyle model | `photoroom-vton` / `photoroom-virtual-model` | API-first catalog/shopper flows. Virtual Model is “flat-lay in, on-model out” (no person photo). Complements dedicated person+SKU VTON. [API](https://docs.photoroom.com/image-editing-api-plus-plan/virtual-try-on) · [Product](https://www.photoroom.com/tools/virtual-model) | shipped |
| Pixelcut Try-On | Pixelcut (e-comm photo; Shopify-heavy) | Image VTON + garment transfer | `pixelcut-vton` | REST `/v1/try-on`; upper/lower/full. Smaller than Google/Alibaba. [API](https://www.pixelcut.ai/api/try-on) | `watch` |
| Fitroom | Specialist startup | Combo top+bottom in one request | `fitroom` | Strong e-comm DX; weaker long-term vendor signal. | `watch` |
| Claid | Specialist | Catalog try-on | — | Photo-API vendor; overlap with Photoroom. | `watch` |
| BytePlus Effects / live AR try-on | ByteDance | Real-time AR, not still VTON | — | SDK/effects stack. Seedream image/edit is already in the registry (`seedream`). | `watch` |
| Tencent Cloud FitDiT (hosted) | Tencent | Commercial FitDiT | — | Open weights are NC; Tencent Cloud is the commercial door. Confirm a public REST API before Path A. | `watch` |
| Adobe Firefly Services | Adobe | General gen/edit | — | Commercially durable Creative Cloud; **no** dedicated person+garment VTON API found. | `skip` |
| Shopify / Google Shopping / Walmart Zeekit | Platform lock-in | In-app try-on | — | Not a developer API we can register. | `skip` |
| Kling via Fal / PiAPI / Replicate | Aggregators | Same Kolors VTON | — | We already have first-party `kling-ai`. | `skip` |
| Snap Camera Kit / glasses AR | Snap | Accessory AR | — | Different modality (mesh/AR), not image VTON. | `watch` |

**Related try-on jobs (same developers, not a second `vton` clone):**

| Job | What they call | Prefer |
|---|---|---|
| Shopper fitting room | Person selfie + SKU photo | Google VTO, FASHN, Kling, BFL, Amazon, OutfitAnyone |
| Catalog on-model | Flat-lay → generated model | Photoroom Virtual Model; FASHN product-to-model (vendor suite — do not invent a parallel adapter until asked) |
| Multi-SKU outfit | Top + bottoms one call | OutfitAnyone combo, Fitroom combo, Pruna multi-ref (shipped) |
| Model swap / consistent model | Face/body swap, keep garment | FASHN model-swap (vendor suite) |
| Video try-on | Temporal garment on a clip | CatV2TON local; no durable first-party video-VTON API picked yet |
| Parsing / hotspots | Garment masks, bboxes | Alibaba `aitryon-parsing-v1`; OpenTryOn already has preprocess helpers |

### Path B — local / open-weight VTON

Pick **one** for v0.1.0 Slice D (`tryon.models` + `opentryon[local]`). Many research checkpoints are **CC BY-NC-SA** — fine for OSS demos, a problem for D2C/marketplace production. Confirm license before making one the default.

| Candidate | Origin | Suggested id | VRAM / notes | License (typical) | Status |
|---|---|---|---|---|---|
| **Leffa** | CVPR 2025; HF `franciszzj/Leffa` | `leffa` | Diffusers; VITON-HD + DressCode try-on + pose transfer; strong **detail/logo** story | Code **MIT**; confirm weight card for commercial D2C | shipped |
| **CatVTON** + **CatVTON-FLUX** LoRA | ICLR 2025; FLUX.1-Fill LoRA ~37M | `catvton` | &lt;8GB @ 1024×768; SD 1.5 concatenation pipeline (FLUX LoRA weights exist; official FLUX infer code not released) | **CC BY-NC-SA 4.0** (code + checkpoints); FLUX-Fill base has its own terms | shipped |
| IDM-VTON | ECCV 2024; `yisol/IDM-VTON` | `idm-vton` | Higher fidelity; ~18–24GB typical | **CC BY-NC-SA** | `watch` |
| OOTDiffusion | `levihsu/OOTDiffusion` | `ootdiffusion` | Community baseline; setup scripts already under `tryon/` | Check repo | `watch` |
| FitDiT | Tencent-affiliated DiT; `BoyuanJiang/FitDiT` | `fitdit` | High garment-detail DiT; ComfyUI exists | **CC BY-NC-SA**; commercial via Tencent Cloud | `watch` |
| CatV2TON | Same lab as CatVTON | `catv2ton` | **Video** try-on; needs a video-VTON design pass | Check repo (likely NC like CatVTON) | `watch` |
| FLUX-fill LoRA (train slice) | BFL Fill + brand LoRA | — | Not a third cloud VTON; `opentryon train` path | FLUX terms | `watch` |
| OutfitAnyone **weights** | HumanAIGC / Alibaba paper | — | Demos lock person upload; use **`aitryon-plus` API** instead | Restricted demos | `skip` |
| VITON-HD / StableVITON | 2022–2023 warping/diffusion | — | Superseded for new work | Mixed | `skip` |
| Qwen-Image-Edit-2511 local | Already `qwen-image-local` | — | Composition I2I, not a VTON specialist | — | shipped |

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

NVIDIA / Nemotron has no VTON NIM. Cloud dedicated VTON is already broad (FLUX VTO, **Google Vertex**, **OutfitAnyone-Plus**, **Photoroom**, Amazon Nova, Kling, FASHN, Pruna). Local weights shipped: **Leffa** (`leffa`, MIT code) and **CatVTON** (`catvton`, CC BY-NC-SA). Full tables: Wave 2 above.

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
2. ~~`google-vton`~~ **shipped** (Path A Vertex `virtual-try-on-001`, 29 Aug 2026).
3. ~~`outfitanyone-plus` / `photoroom-vton` / `photoroom-virtual-model`~~ **shipped** (Path A, 29 Aug 2026).
4. ~~`leffa` / `catvton`~~ **shipped** (Path B local VTON, 1 Sep 2026).
5. **New services** only after one local VTON: LipSync (A2V), TRELLIS (3D).
6. **SANA-Sprint** if we want a fast local T2I that is not another FLUX/Qwen clone.
7. Optional: `nemotron-omni-local` if someone will run 30B-A3B.

---

## Shipped (do not re-add)

Invoke-layer highlights already in the registry: FLUX.2 (+ Turbo local), Nano Banana family, GPT Image, Muse Image, Ideogram 4.0, P-Image-Ideogram, Qwen-Image API+local, Veo, Sora, LTX-2.5, Hailuo 2.3, MiniMax H3 / H3 Max, **Fal H3 Max**, Wan, Runway Gen-4.5, **Nemotron Omni**, **Cosmos 3 Reasoner**, **Cosmos 3 Generator**, Kimi K2.6/K2.7/K3, Qwen3.8, **Hy4 preview** (`hy4-preview` TokenHub + `hy4-preview-local` vLLM/SGLang), BEN2, dedicated cloud VTON (`flux-vto`, `google-vton`, `outfitanyone-plus`, `photoroom-vton`, `photoroom-virtual-model`, `nova-canvas`, `kling-ai`, FASHN, `p-image-tryon`, Segmind) plus composition try-on (`nano-banana-2-lite`, `qwen-image`, `muse-image`) and **local dedicated VTON** (`leffa`, `catvton`). Full table: CLI `--help` / registry.

---

## Maintenance

When adding a row: vendor, modality, Path A/B, proposed registry id, license/API URL, status.  
When shipping: move to **Shipped**, delete the `next` row, note the registry id.  
Re-survey NVIDIA: [build.nvidia.com/models](https://build.nvidia.com/models) + Cosmos / Nemotron blogs. Do not paste the entire NIM catalog.  
Re-survey VTON: Vertex Imagen try-on, DashScope OutfitAnyone, Photoroom/Pixelcut, Hugging Face CatVTON / Leffa / IDM-VTON. Prefer first-party APIs over aggregators.
