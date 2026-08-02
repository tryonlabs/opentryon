# OpenTryOn Roadmap

> **Last Updated**: 2 August 2026 · **Current release**: [v0.0.3](https://pypi.org/project/opentryon/0.0.3/) · **Horizon**: Aug 2026 – early 2027

This roadmap tracks what shipped in the toolkit and what remains. Product strategy detail lives in [`VISION.md`](VISION.md).

## At a glance

```
┌─────────────────────────────────────────────────────────────────────────┐
│ SHIPPED — v0.0.3 (August 2026)                                          │
├─────────────────────────────────────────────────────────────────────────┤
│ ✓ Unified `opentryon` CLI (registry-driven services + --dry-run)        │
│ ✓ FastMCP server (tools auto-generated from the same registry)          │
│ ✓ invoke_model() shared by CLI + MCP                                    │
│ ✓ Media OpenAPI/Swagger snapshot + Postman collection                   │
│ ✓ Broad cloud adapters: VTON / generate / edit / video / understand     │
│ ✓ Local extras: FLUX.2-dev Turbo, Kimi-VL, LLaVA-NeXT, BEN2             │
│ ✓ Docs site, env.template, Gradio demos, tryon-studio via MCP           │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ NEXT — toolkit depth (near term)                                        │
├─────────────────────────────────────────────────────────────────────────┤
│ • Local OSS VTON (CatVTON / IDM-VTON / OOTDiffusion or FLUX-fill paths) │
│ • Train / LoRA recipes + fashion fine-tune notebooks                    │
│ • Prompt packs + lightweight garment/identity evals                     │
│ • Deeper Studio (tryon-studio) wired to MCP                             │
│ • More datasets (DeepFashion, FashionGen, …)                            │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ LATER — efficiency, agents, platform                                    │
├─────────────────────────────────────────────────────────────────────────┤
│ • Quantization / distillation / serving recipes for local models        │
│ • Fashion agents v1 (PDP, try-on QA, lookbook, model-swap, prompts)     │
│ • Async / batch / caching DX improvements                               │
│ • Video VTON / 3D VTON exploration                                      │
│ • Additional providers (Qwen-Image, more open weights, …)               │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Completed (through v0.0.3)

### Developer surfaces
- [x] **`opentryon` CLI** — `vton`, `generate`, `edit`, `understand`, `video-generate`, `bg-remove`
- [x] **MCP server** (`mcp-server/`) on FastMCP 3.x — one tool per registry model
- [x] **Shared runner** — `tryon.cli.runner.invoke_model()` for CLI + MCP
- [x] **Registry** — `tryon/cli/registry.py` as source of truth
- [x] **OpenAPI / Swagger** — `openapi/opentryon-media.openapi.yaml` (upstream media APIs)
- [x] **Postman** — `postman/opentryon-media.postman_collection.json`
- [x] **Docs** — Docusaurus site; PyPI package `opentryon==0.0.3`
- [x] **tryon-studio** — web UI in a separate repo, talks to OpenTryOn over MCP

### Virtual try-on (cloud)
- [x] FLUX VTO, Amazon Nova Canvas, Kling AI, Segmind
- [x] Pruna P-Image-Try-On (multi-garment)
- [x] FASHN Try-On Max & v1.6
- [x] Nano Banana 2 Lite composition path

### Image generate / edit
- [x] Nano Banana family (incl. Pro / 2 / 2 Lite)
- [x] FLUX.2 Pro / Flex (+ local Turbo)
- [x] GPT Image, Luma Photon
- [x] Seedream 5.0 Pro, Ideogram 4.0, Grok Imagine Image
- [x] Pruna P-Image, P-Image-Edit, P-Image-Upscale

### Video
- [x] Veo, Sora, Luma Ray 2 + Ray 3.2
- [x] Seedance 2.5, Kling 3.0 / Omni / Turbo
- [x] Grok Imagine Video 1.5, Gemini Omni Flash
- [x] Pruna P-Video, P-Video-Replace, P-Video-Avatar, P-Video-Animate

### Understanding & other
- [x] Kimi K2.6 / K2.7 Code / K3 (API); Kimi-VL & LLaVA-NeXT (local)
- [x] BEN2 background removal
- [x] Datasets: Fashion-MNIST, VITON-HD, Subjects200K
- [x] Preprocessing (garment / human / pose) + TryOnDiffusion research code
- [x] Early LangChain agents (VTON, model-swap) + Gradio demos

---

## Remaining / in progress

### Near term (toolkit depth)
- [ ] **Local OSS VTON** — CatVTON, IDM-VTON, OOTDiffusion (or FLUX-fill LoRA) under `tryon.models`
- [ ] **Train / finetune** — documented LoRA/QLoRA recipes; brand-style fine-tune notebook
- [ ] **Prompt collections** — versioned packs (try-on, catalog, lookbook, video)
- [ ] **Evals** — garment fidelity / identity checklist + side-by-side runner
- [ ] **Studio maturity** — orgs, comparison UI, export flows in [tryon-studio](https://github.com/tryonlabs/tryon-studio)
- [ ] **Additional datasets** — DeepFashion, FashionGen, richer loaders

### Medium term (efficiency & agents)
- [ ] **Quantization / distillation** — 8-bit / 4-bit recipes; VRAM tables in docs
- [ ] **Serving guidance** — batching, latency notes for local models
- [ ] **Fashion agents v1** — Catalog PDP, Try-on QA, Lookbook director, Model-swap ops, Prompt librarian
- [ ] **DX** — broader async support, optional caching / batch helpers
- [ ] **Test coverage** — expand unit/integration coverage toward >85% on core paths

### Exploring
- [ ] Open-source **video VTON** / **3D VTON**
- [ ] Additional providers (e.g. Qwen-Image, more HF/GitHub weights)
- [ ] Stronger base-provider abstractions only where the registry pattern is insufficient
- [ ] Commercial license clarity for adapters vs weights vs Studio

Skipped by design (for now): Ideogram-via-Pruna (use direct Ideogram adapter).

---

## Success metrics (rolling)

| Signal | Target |
|---|---|
| PyPI / install | `pip install opentryon` works without GPU deps; `[local]` optional |
| Registry parity | Every CLI model has an MCP tool; dry-runs pass offline |
| Docs | New adapters documented under `docs/docs/api-reference/` + CLI table |
| Community | Monthly toolkit drops; Discord + LinkedIn engagement |

---

## Contributor focus

**Good first issues:** docs/examples, dry-run tests for new adapters, type hints, error-message polish.

**High-value next:** local OSS VTON adapters, LoRA fine-tune notebooks, eval scripts, tryon-studio ↔ MCP polish.

See [Contributing](CONTRIBUTING.md), [new-model checklist](docs/docs/advanced/new-model-checklist.md), and [VISION.md](VISION.md).

---

**Links:** [PyPI](https://pypi.org/project/opentryon/) · [Release v0.0.3](https://github.com/tryonlabs/opentryon/releases/tag/v0.0.3) · [Docs](https://tryonlabs.github.io/opentryon/) · [Discord](https://discord.gg/T5mPpZHxkY)
