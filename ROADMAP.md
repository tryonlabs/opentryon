# OpenTryOn Roadmap

> **Last Updated**: 17 August 2026 · **Current release**: [v0.0.4](https://pypi.org/project/opentryon/0.0.4/) · **Next milestone**: **v0.1.0 — Fashion ML Toolkit Core**  
> **Horizon**: Aug 2026 – early 2027 · Fashion-first; other domains later

This roadmap tracks what shipped and what comes next. Product strategy: [`VISION.md`](VISION.md).

**Who we build for (priority):** fashion AI/ML engineers · fashion agent builders · fashion app builders · fashion companies (train + MCP) · CLI-first developers.

**North star (v0.1.0):** an ML engineer can load a fashion train pack, fine-tune a small adapter, run garment/identity evals + a baseline bench, invoke the result via CLI/MCP, and run one agentic fashion workflow on top — without assembling five research repos by hand.

---

## At a glance

```
┌─────────────────────────────────────────────────────────────────────────┐
│ SHIPPED — v0.0.3 / v0.0.4 (August 2026)  ·  Phase 0: invoke layer       │
├─────────────────────────────────────────────────────────────────────────┤
│ ✓ Unified `opentryon` CLI + FastMCP (same registry / invoke_model)      │
│ ✓ Broad cloud adapters: VTON / generate / edit / video / understand     │
│ ✓ v0.0.4: LTX-2.5, Hailuo 2.3, Wan dual-path, Runway Gen-4.5, Qwen3.8   │
│ ✓ OpenAPI + Postman snapshots · docs · Gradio · tryon-studio via MCP    │
│ ✓ Local extras: FLUX.2 Turbo, Kimi-VL, LLaVA, BEN2, LTX, Wan, Qwen3.8   │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ NEXT — v0.1.0 Fashion ML Toolkit Core (near term)                       │
├─────────────────────────────────────────────────────────────────────────┤
│ • Fashion prompt packs + train-pack schema / datasets                   │
│ • Train / LoRA recipes (`opentryon train`) + notebooks                  │
│ • Eval + Fashion Bench v0 (`opentryon eval`)                            │
│ • One productized local OSS VTON path (CatVTON / IDM / OOT — pick one)  │
│ • Fashion agentic workflows via MCP (Try-On QA or Fine-Tune Coach)      │
│ • Efficiency card for that local path (VRAM / latency table)            │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ LATER — efficiency platform, agents suite, adjacent domains             │
├─────────────────────────────────────────────────────────────────────────┤
│ • Broader quantization / distillation / serving recipes                  │
│ • Full fashion agents v1 (PDP, lookbook, router, return-risk, …)        │
│ • Async / batch / caching DX · video VTON / 3D VTON                     │
│ • Multi-domain packs only after fashion train/eval patterns prove out   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Completed (through v0.0.4) — Phase 0

### Developer surfaces
- [x] **`opentryon` CLI** — `vton`, `generate`, `edit`, `understand`, `video-generate`, `bg-remove`
- [x] **MCP server** (`mcp-server/`) on FastMCP 3.x — one tool per registry model
- [x] **Shared runner** — `tryon.cli.runner.invoke_model()` for CLI + MCP
- [x] **Registry** — `tryon/cli/registry.py` as source of truth
- [x] **OpenAPI / Swagger** — `openapi/opentryon-media.openapi.yaml`
- [x] **Postman** — `postman/opentryon-media.postman_collection.json`
- [x] **Docs** — Docusaurus site; PyPI `opentryon==0.0.4`
- [x] **tryon-studio** — separate UI repo over MCP
- [x] **Model integration guidelines** — Path A API vs Path B local

### Fashion cloud / local (invoke)
- [x] VTON: FLUX VTO, Nova Canvas, Kling AI, Segmind, Pruna P-Image-Try-On, FASHN, Nano Banana 2 Lite, **Qwen-Image** (API + local)
- [x] Image: Nano Banana family, FLUX.2 (+ local Turbo), GPT Image, Luma Photon, Seedream, Ideogram, Grok Imagine Image, Pruna P-Image / Edit / Upscale, **Qwen-Image 3.0** (API) + **Qwen-Image-2512 / Edit-2511** (local)
- [x] Video: Veo, Sora, Luma Ray 2/3.2, Seedance, Kling 3 / Omni / Turbo, Grok Imagine Video, Gemini Omni, Pruna P-Video / Replace / Avatar / Animate, **LTX-2.5** (API + local), **Hailuo 2.3**, **Wan** (API + local 2.2), **Runway Gen-4.5**
- [x] Understand: Kimi K2.6 / K2.7 Code / K3; Kimi-VL & LLaVA-NeXT (local); **Qwen3.8-Max** (API) + **Qwen3.8-27B** (local)
- [x] BEN2, datasets (Fashion-MNIST, VITON-HD, Subjects200K), preprocessing, TryOnDiffusion research code
- [x] Early LangChain agents + Gradio demos

Skipped by design (for now): Ideogram-via-Pruna (use direct Ideogram adapter).

---

## Next — Fashion ML Toolkit Core → v0.1.0

**Theme:** From “call any model” → “train, judge, and run fashion models like an engineer.”  
CLI/MCP remain the distribution spine; new capabilities register the same way.

### Slice A — Fashion data & prompt packs
- [ ] Versioned **prompt packs** (try-on, PDP/catalog, lookbook, video, model-swap, QA rubrics)
- [ ] **Train-pack schema** (`images/`, captions, splits, `license.md`, `cards.yaml`)
- [ ] Fashion train packs on top of existing loaders (+ DressCode / brand-folder recipes)
- [ ] CLI: `opentryon data validate|split|stats` (names TBD)

### Slice B — Train / finetune
- [ ] `tryon/train/` (or equivalent) + config-driven YAML recipes
- [ ] **Brand-style image LoRA** (FLUX / SD family) end-to-end
- [ ] **One VTON/local LoRA path** (prefer CatVTON-FLUX or FLUX-fill) 
- [ ] Notebook + CLI: `opentryon train --config …`
- [ ] Artifact layout: `runs/<id>/adapter`, metrics, sample grids

### Slice C — Eval & Fashion Bench v0
- [ ] Garment fidelity / identity / pose / artifact checklist (+ automated proxies where possible)
- [ ] Side-by-side runner: cloud baseline vs local vs finetuned
- [ ] Public **Fashion Bench v0** (fixed prompts + image pairs)
- [ ] CLI: `opentryon eval run|report`

### Slice D — Local OSS VTON (productize one)
- [ ] Ship **one** of CatVTON / IDM-VTON / OOTDiffusion under `tryon.models` + `opentryon[local]`
- [ ] Same invoke path as cloud adapters (agents don’t care where it runs)
- [ ] Docs: install, VRAM, dry-run, known limits

### Slice E — Fashion agentic workflows (MCP-native)
- [ ] Task workflows (not chatbots) that call registry tools
- [ ] First agent: **Try-On QA** *or* **Fine-Tune Coach** (lock one for v0.1.0)
- [ ] Thin Python API + MCP exposure; Studio consumes later

### Slice F — Efficiency card (thin slice)
- [ ] For the shipped local VTON + LoRA path: VRAM / latency table
- [ ] 8-bit / `torch.compile` notes only where real
- [ ] Export adapter → reload in CLI/MCP guide

### Suggested internal order
| Order | Slice | Notes |
|---|---|---|
| 1 | A — Data + prompts | Unblocks train/eval |
| 2 | B + C | Finetune and bench in parallel |
| 3 | D | One ownable local VTON |
| 4 | E | Agent on top of tools + evals |
| 5 | F | Numbers for the path we actually ship |

Intermediate tags: `0.0.4` / `0.0.5` as slices land; **v0.1.0** when A–E are usable end-to-end.

### Conceptual package layout (target)
```
tryon/
  cli/ api/ models/     # existing
  train/                # NEW recipes / runners
  eval/                 # NEW metrics / bench / reports
  workflows/            # NEW agentic fashion graphs
  prompts/              # NEW versioned prompt packs
  datasets/             # expand train packs + cards
```

---

## Later (after v0.1.0)

### Efficiency & deploy platform
- [ ] Broader quantization / distillation / pruning recipes
- [ ] Serving guidance (batching, warm models, caching)
- [ ] Published scorecards per supported local model family

### Fashion agents suite
- [ ] Catalog / PDP Optimizer, Lookbook Director, Provider Router, Return-Risk Advisor
- [ ] Graph/loop patterns kept **fashion-workflow-specific** until the pattern is proven

### DX & infra
- [ ] Broader async / batch helpers
- [ ] Test coverage toward >85% on core train/eval/invoke paths
- [ ] Commercial license clarity (adapters vs weights vs Studio)

### Exploring
- [ ] Video VTON / 3D VTON
- [ ] Additional providers (more HF weights)
- [ ] VLM/LLM finetune recipes beyond the first fashion path
- [ ] **Multi-domain** packs (beauty, home, …) only after fashion train/eval/agent patterns work

---

## Success metrics

| Signal | Target |
|---|---|
| Invoke (already) | CLI ↔ MCP parity; dry-runs offline |
| Train | One documented LoRA path runs on a stated GPU class |
| Eval | Fashion Bench v0 report reproducible from a fresh clone |
| Agents | ≥1 MCP workflow used by design partners / community examples |
| Docs | “Fashion ML engineer quickstart” ([outline](docs/docs/getting-started/fashion-ml.md)) alongside “API caller quickstart” |
| Community | Monthly toolkit drops; Discord + LinkedIn |

---

## Contributor focus

**Good first issues:** prompt-pack PRs, bench image pairs, dry-run tests, docs/examples, type hints.

**High-value next:** LoRA recipe hardening, Fashion Bench metrics, first local VTON adapter, Try-On QA or Fine-Tune Coach workflow.

See [Contributing](CONTRIBUTING.md), [new-model checklist](docs/docs/advanced/new-model-checklist.md), and [VISION.md](VISION.md).

---

**Links:** [PyPI](https://pypi.org/project/opentryon/) · [Release v0.0.4](https://github.com/tryonlabs/opentryon/releases/tag/v0.0.4) · [Docs](https://tryonlabs.github.io/opentryon/) · [Discord](https://discord.gg/T5mPpZHxkY)
