# OpenTryOn Vision Document

> **Status:** Living document  
> **Last updated:** July 21, 2026  
> **Owner:** TryOn Labs  
> **Scope:** OpenTryOn (open-source Fashion AI toolkit) + commercial layer (TryOn Studio / Playground)

---

## 1. One-line vision

**OpenTryOn is the open-source Fashion AI toolkit** — models, training, fine-tuning, prompts, agents, efficient inference, and an open studio UI — so builders can create virtual try-on, catalog, and fashion content systems without starting from scratch.

Fashion-first now. Platform-generic later.

---

## 2. Problem

Fashion is one of the hardest domains for generative AI and one of the highest-ROI for commerce:

| Pain | Who feels it | Why it persists |
|---|---|---|
| **Fit & appearance uncertainty** drives returns | Shoppers, DTC brands | Online apparel returns often 20–40%+; try-on is still rare (~1% of stores) |
| **Catalog / PDP production is slow and expensive** | Brands, agencies, marketplaces | Photoshoots don’t scale with SKU velocity; seasonal churn multiplies cost |
| **Research ≠ product** | ML engineers, startups | Academic VTON repos (IDM-VTON, CatVTON, OOTDiffusion) are powerful but fragmented, hard to train, hard to run efficiently |
| **Vendor lock-in & API sprawl** | Product teams | Many closed APIs (FASHN, Revery, Vue.ai, Nightjar, Botika…) with different schemas, credits, and quality trade-offs |
| **No shared “fashion OS” for agents** | Builders of agentic workflows | Chat UIs and raw APIs don’t compose into catalog → try-on → lookbook → video pipelines |
| **Efficient deployment is expert-only** | Teams with limited GPU budget | Quantization, distillation, pruning, KV-cache, speculative decoding rarely packaged for fashion models |

**Market signal (directional, sources vary by definition):** virtual try-on market estimates around **~$15B in 2025 → ~$46–48B by 2030** (~26% CAGR). Reported retail outcomes include **~20–35% conversion lift**, **~25–40% return reduction**, **AOV up to ~33%** — while consumer demand far exceeds adoption. AI/ML-based try-on is among the fastest-growing segments vs classic AR overlays.

OpenTryOn exists because the gap is not “another demo” — it is **infrastructure**: training + inference + prompts + agents + studio, open enough to own, commercial enough to ship.

---

## 3. Solution

### 3.1 Product system (three layers)

```
┌─────────────────────────────────────────────────────────────────┐
│  TRYON STUDIO (open UI + commercial hosted)                     │
│  Visual workflows, brand kits, agent tasks, export to PDP/video │
├─────────────────────────────────────────────────────────────────┤
│  PLAYGROUND / API (developer closed-source surface)             │
│  Credits, orgs, logs, evals — already live for API testing      │
├─────────────────────────────────────────────────────────────────┤
│  OPENTRYON (open-source toolkit)                                │
│  CLI · MCP · adapters · local models · train/finetune · agents  │
│  prompts · efficiency recipes · datasets · docs                 │
└─────────────────────────────────────────────────────────────────┘
```

| Layer | Nature | Job |
|---|---|---|
| **OpenTryOn** | Open source (CC BY-NC today; revisit license for commercial OSS strategy) | The toolkit researchers and engineers fork, extend, and run locally or against any provider |
| **Playground** | Closed / hosted | Developers test APIs, compare models, inspect outputs — **exists today** |
| **TryOn Studio** | Open UI code path + hosted commercial product | Non-dev fashion teams: try-on, model swap, catalog, campaigns, agents — without assembling the stack |

This matches the existing TryOn Labs split: **shared core**, **developer Playground**, **outcome-focused Studio/agentic product** — OpenTryOn is the open heart of that core.

### 3.2 Capability pillars (fashion-only for now)

1. **Generation & try-on** — VTON, image gen/edit, video, bg remove (cloud adapters + local weights)  
2. **Preprocessing** — garment/human segmentation, pose, captioning  
3. **Training & fine-tuning** — LoRA/QLoRA, Unsloth-style recipes, fashion datasets, brand style adapters  
4. **Prompt collections** — curated, versioned prompts for try-on, catalog, lookbook, video  
5. **Efficient inference** — quantization, distillation, pruning, KV-cache, speculative decoding, batching — *scripts that a fashion ML eng can actually run*  
6. **Agents** — task-scoped agents (PDP optimizer, catalog generator, try-on QA, lookbook director, return-risk advisor…)  
7. **Studio UI** — open-source studio for local/self-host; commercial hosted Studio for teams  

### 3.3 Design principles

- **Use-case segmented, not vendor-segmented** (CLI/MCP registry pattern already in place)  
- **One invoke path** for CLI and MCP (`invoke_model`) so tools never drift  
- **Fashion fidelity over generic demos** — garment preservation, identity, pose, lighting  
- **Efficiency is a first-class feature**, not a blog post  
- **Open to learn / closed to operate at scale** — OSS grows the ecosystem; Studio + Playground fund the company  
- **Agents are workflows**, not chatbots with fashion stickers  

---

## 4. Competitive landscape

### 4.1 Closed-source / commercial

| Player | Focus | Strength | Weakness vs OpenTryOn |
|---|---|---|---|
| **[FASHN](https://fashn.ai/)** | Fashion API + studio (try-on, model create, edit, video) | Strong fashion-native API; agent skill for coding agents; credit pricing | Closed models; not a training/finetune/efficiency toolkit |
| **Vue.ai** | Enterprise retail AI suite | Full stack for large retailers | Heavy enterprise sales; not OSS toolkit |
| **Revery.ai** | Virtual dressing room APIs | E-comm developer focus | Narrower surface; closed |
| **Nightjar, Botika, SellerPic, Genlook** | Brand catalog / Shopify imagery | Shopify-native workflows, catalog consistency | Brand tools ≠ open ML platform |
| **Veesual** | High-end photo compositing | Photoreal for premium brands | B2B, not self-serve OSS |
| **Google Shopping VTO / Walmart Zeekit** | In-platform try-on | Distribution | Locked to their catalogs |
| **DressX / digital fashion** | High-fidelity / digital garments | Luxury aesthetics | Different ICP (digital fashion) |
| **Generic genAI (Gemini, GPT Image, FLUX, Veo, Sora)** | Horizontal models | Quality & speed | Not fashion-ops; no VTON training stack |

### 4.2 Open-source / research

| Project | Focus | Notes |
|---|---|---|
| **[IDM-VTON](https://github.com/yisol/idm-vton)** | Diffusion VTON (ECCV 2024) | High fidelity; popular HF demos; CC BY-NC-SA |
| **[CatVTON](https://github.com/Zheng-Chong/CatVTON)** | Efficient VTON (ICLR 2025) | &lt;8GB VRAM path; CatVTON-FLUX LoRA |
| **[OOTDiffusion](https://github.com/levihsu/OOTDiffusion)** | Outfitting fusion VTON | Foundational open model; large community |
| **OrthoTryOn** | Unified fashion gen (try-on + pose + reconstruction) | Research-efficient multi-task LoRA |
| **OpenVTO** | Studio avatar + try-on + short video loops | Early toolkit; aesthetics-first |
| **ComfyUI workflows / HF Spaces** | Ad-hoc pipelines | Powerful but not a productized toolkit |
| **OpenTryOn (us)** | Multi-provider CLI/MCP + local models + docs + agents path | Broadest *ops* surface among fashion OSS; still thin on train/efficiency/studio |

### 4.3 Positioning (where we win)

```
                    Research repos          Closed fashion APIs
                    (IDM/Cat/OOT)           (FASHN, Revery…)
                           \                     /
                            \                   /
                             \                 /
                              ▼               ▼
                     ┌─────────────────────────────┐
                     │  OPENTRYON = fashion AI OS  │
                     │  train · serve · prompt ·   │
                     │  agent · studio · any model │
                     └─────────────────────────────┘
```

**We are not “another VTON model.”**  
We are the **toolkit and studio layer** that wraps open models *and* closed APIs, adds training/efficiency/agents, and ships a path from notebook → CLI/MCP → Playground → Studio.

**Differentiation bets:**

1. **Provider-agnostic fashion registry** (already shipping)  
2. **Training + fine-tuning recipes** for brand/SKU adaptation  
3. **Efficiency pack** for running fashion models on consumer/prosumer GPUs  
4. **Prompt + eval collections** as shared assets  
5. **Agents for fashion ops outcomes** (catalog, PDP, QA)  
6. **Open Studio** + **commercial hosted Studio/Playground** dual flywheel  

---

## 5. Ideal Customer Profile (ICP)

### 5.1 OpenTryOn (OSS) ICP

| Segment | Persona | Jobs to be done |
|---|---|---|
| **Fashion-tech startups** | Founding engineer / ML lead | Ship MVP try-on or catalog AI without rebuilding adapters |
| **Agency / creative tech** | Technical producer | Script batch lookbooks; swap providers by cost/quality |
| **Academic / indie researchers** | Grad student, HF contributor | Train/finetune VTON; publish with reproducible scripts |
| **Internal ML at DTC / marketplace** | Applied ML eng | Self-host sensitive garments; evaluate closed APIs side-by-side |

**Anti-ICP (OSS):** pure marketers with no engineer; enterprises needing only a Shopify button (send to Studio later).

### 5.2 Playground ICP (exists)

- Developers integrating fashion APIs  
- Teams comparing model quality before contracting  
- Hackathon / prototype builders  

### 5.3 TryOn Studio / closed product ICP

| Tier | Who | Buying trigger |
|---|---|---|
| **Primary** | DTC apparel brands ($1M–$50M GMV) with thin photo budgets | Seasonal catalog velocity, return rates, SKU count |
| **Secondary** | Fashion e-comm / marketplaces | On-model imagery at scale; multi-brand consistency |
| **Secondary** | Creative agencies serving fashion | Faster client turnaround; reusable brand models |
| **Enterprise** | Large retailers | Security, SSO, SLA, private models, on-prem/VPC |

**Buyer:** Head of E-comm / Creative Ops / Digital Product (economic); ML/Eng as champion when self-host matters.

---

## 6. Business model (closed-source layer)

OpenTryOn remains the **community and adoption engine**. Revenue sits on hosted products and enterprise.

| Stream | Model | Notes |
|---|---|---|
| **Playground + API** | Credits / usage | Already aligned with “developers test our APIs” |
| **TryOn Studio SaaS** | Seat + usage (Starter / Pro / Studio / Enterprise) | Outcome workflows; mapped internally to credits |
| **Enterprise** | Annual contract + VPC / private weights / support | Fine-tuned brand models, SSO, audit logs |
| **Professional services** | Optional | Custom agents, training on brand data (keep productized) |
| **OSS** | Free (non-commercial today) | Consider dual-license or commercial OSS later without breaking community trust |

**Pricing principles:**

- Credits for compute-heavy gen (Playground/API)  
- Subscription for workflow/agent value (Studio)  
- Never charge for “access to docs” — docs stay open to grow OpenTryOn  

**Unit economics levers:** model routing (cheap vs quality), caching, batch, efficient local inference for self-host Enterprise, multi-provider failover.

---

## 7. Go-to-market (GTM)

### 7.1 OpenTryOn (bottom-up)

1. **GitHub + docs** as source of truth ([docs](https://tryonlabs.github.io/opentryon/))  
2. **Discord / LinkedIn / WhatsApp** — ship notes like the recent 4-API drop, not press releases  
3. **MCP + CLI** — meet developers where agents already work (Cursor, Claude, etc.)  
4. **HF Spaces / notebooks** — one-click try-on and efficiency demos  
5. **Content:** “compare FASHN vs Flux VTO vs CatVTON on the same garment” eval posts  

### 7.2 Playground (developer wedge)

1. Sign up → run try-on in minutes → export code snippet that uses OpenTryOn adapters  
2. Credits for power users; free tier for exploration  
3. Partner listings (API marketplaces) once stable  

### 7.3 Studio (top-down / sales-assist)

1. Convert Playground power users and Discord brands into Studio trials  
2. Shopify / catalog integrations as distribution (phase later)  
3. Case studies: return-rate and time-to-PDP metrics  
4. Agency channel: white-label workflows  

### 7.4 Narrative ladder

| Audience | Message |
|---|---|
| Engineers | “Fashion AI toolkit: train, serve, swap providers, agentize.” |
| Brands | “Studio that produces on-model and try-on content without a full reshoot.” |
| Investors | “OSS wedge → usage → Studio/API revenue in a $15B→$48B try-on market.” |

---

## 8. Phased plan

Horizon assumes **fashion-only** through Phase 3; generic verticalization after proof.

### Phase 0 — Foundation (done / ongoing)

- Multi-provider **CLI + MCP registry**  
- Cloud VTON / gen / edit / video / understand / bg-remove adapters (incl. Pruna, Nano Banana 2 Lite, FASHN, Gemini Omni)  
- Docs site + Discord community  
- **Playground** for API testing  
- Early agents / Gradio demos; Studio spun out as separate app talking over MCP  

**Exit criteria:** Developers can discover and dry-run every registered model; docs match registry.

### Phase 1 — Complete the toolkit core (0–4 months)

**Theme:** *From adapters to a real Fashion AI toolkit.*

| Workstream | Deliverables |
|---|---|
| **Local OSS VTON** | First-class adapters for CatVTON / IDM-VTON / OOTDiffusion (or FLUX-fill LoRA paths) under `tryon.models` |
| **Train / finetune** | Documented LoRA/QLoRA recipes; fashion dataset loaders; brand-style fine-tune notebook |
| **Prompt collections** | Versioned prompt packs (try-on, catalog, lookbook, video) in-repo |
| **Evals** | Minimal garment-fidelity / identity-preservation checklist + scripted side-by-side runner |
| **Studio OSS MVP** | Open UI that drives OpenTryOn via MCP/CLI for try-on + generate + export |
| **License clarity** | Publish commercial-use policy for adapters vs weights vs Studio |

**Exit criteria:** A new contributor can fine-tune a small fashion adapter and run local VTON with `opentryon[local]` without reading 5 research READMEs.

### Phase 2 — Efficient Fashion AI (3–8 months)

**Theme:** *Run serious models on realistic hardware.*

| Workstream | Deliverables |
|---|---|
| **Quantization** | 8-bit / 4-bit recipes for priority local models; VRAM tables in docs |
| **Distillation / pruning** | Starter scripts or wrappers where upstream supports them; clear “supported / experimental” labels |
| **Serving tricks** | KV-cache guidance, batching, speculative decoding where applicable (LLM/VLM paths first; diffusion as research track) |
| **Benchmarks** | Latency / VRAM / quality scorecards published with each efficiency release |
| **Agents v1** | 3–5 fashion agents: Catalog PDP, Try-on QA, Lookbook director, Model-swap ops, Prompt librarian |
| **Playground maturity** | Orgs, usage meters, model comparison UI |

**Exit criteria:** Published “efficient CatVTON / Flux path on 12–16GB GPU” guide with numbers; ≥2 agents used in Studio/Playground weekly by design partners.

### Phase 3 — Studio productization (6–14 months)

**Theme:** *Outcomes for brands, not knobs for engineers.*

| Workstream | Deliverables |
|---|---|
| **Hosted TryOn Studio** | Auth, projects, brand kits, batch jobs, exports |
| **Billing** | Credits + subscription tiers |
| **Integrations** | Shopify / DAM / S3 export; webhooks |
| **Private models** | Brand LoRA hosting; data retention controls |
| **Enterprise** | SSO, VPC option, SLA |

**Exit criteria:** Paying Studio or API customers; NPS/retention from design partners; clear CAC payback narrative.

### Phase 4 — Platform generalization (14+ months)

**Theme:** *Fashion-proven → adjacent verticals.*

- Beauty, eyewear, home soft-goods (same try-on/catalog patterns)  
- Shared efficiency + agent framework with vertical prompt/eval packs  
- Keep fashion as the flagship reference vertical  

---

## 9. Agents (fashion use cases)

Prioritize **task agents** with measurable outputs:

| Agent | Input | Output |
|---|---|---|
| **PDP Optimizer** | Product images + copy | Score + rewrite + image set recommendations |
| **Catalog Generator** | Flat-lay / ghost mannequin | On-model gallery + metadata |
| **Try-On QA** | Person + garment + result | Pass/fail + defect tags (bleed, pose, logo) |
| **Lookbook Director** | Brand brief + assets | Multi-shot sequence + video prompts |
| **Provider Router** | Constraints (cost, latency, quality) | Chosen model + fallback chain |
| **Return-Risk Advisor** | Garment attributes + fit notes | Risk score + try-on suggestion |
| **Fine-Tune Coach** | Brand images | Dataset checklist + train config |

Agents should call OpenTryOn tools (MCP/CLI), not reimplement providers.

---

## 10. Efficiency roadmap (detail)

Package as `opentryon efficiency` docs + scripts:

1. **Baseline** — FP16/BF16 reference latency & VRAM  
2. **Quantize** — bitsandbytes / GGUF / AWQ where model family allows  
3. **Compile / kernels** — torch.compile, FlashAttention where relevant  
4. **Distill** — student models for edge try-on previews  
5. **Prune / sparsity** — experimental; only when quality gates pass  
6. **LLM stack** — KV-cache, speculative decoding for understanding/agent planners  
7. **Ops** — batch queues, warm models, result caching  

Every recipe must answer: **GPU class, VRAM, ms/image, quality delta vs baseline.**

---

## 11. Risks & open decisions

| Risk / decision | Mitigation |
|---|---|
| CC BY-NC limits commercial OSS adoption | Dual-license or Apache for toolkit code; keep research weights under upstream licenses |
| Competing with FASHN while integrating FASHN | Stay provider-agnostic; differentiate on train/efficiency/agents/studio |
| Training data / likeness / consent | Strict dataset docs; SynthID / provenance guidance for gen video |
| Scope creep into “generic AI platform” too early | Fashion-only OKRs until Phase 3 exit |
| Studio vs Playground confusion | Playground = capabilities; Studio = tasks/outcomes (existing naming decision) |

---

## 12. Success metrics

### OpenTryOn

- GitHub stars / forks / unique contributors  
- Docs traffic; Discord active weekly users  
- Registry model count + MCP tool adoption  
- External PRs for adapters / prompts / efficiency scripts  

### Commercial

- Playground signups → first successful API call  
- Credit burn and retention  
- Studio trials → paid conversion  
- Design-partner case studies (time-to-PDP, return proxy metrics)  

---

## 13. Near-term priorities (next 90 days)

1. **Ship Phase 1 spine:** one local VTON path + one fine-tune recipe + prompt pack v0  
2. **Efficiency v0:** VRAM/latency table for that local path  
3. **Studio OSS MVP:** try-on + generate wired to MCP  
4. **GTM:** monthly “toolkit drop” posts (APIs, recipes, evals) — same tone as the 4-API LinkedIn post  
5. **Align license + commercial boundary** in README/VISION so contributors know what’s open vs hosted  

---

## 14. References (selected)

- OpenTryOn docs: https://tryonlabs.github.io/opentryon/  
- OpenTryOn repo: https://github.com/tryonlabs/opentryon  
- Market: Mordor / Grand View style VTON market reports (~$15.18B 2025 → ~$48.1B 2030, ~26% CAGR); retailer ROI writeups citing conversion/return/AOV ranges  
- Open models: IDM-VTON, CatVTON, OOTDiffusion; OrthoTryOn; OpenVTO  
- Closed: FASHN, Vue.ai, Revery, Nightjar, Botika, Genlook, Google/Walmart in-platform VTO  
- Internal: TryOn AI Strategy & Product Plan (Playground vs Studio split, tryonlabs.ai domains)

---

## Appendix A — Product naming map

| Name | Role |
|---|---|
| **OpenTryOn** | Open-source toolkit |
| **TryOn AI Playground** | Developer hosted API testing / credits |
| **TryOn Studio** (aka TryOn AI product UX) | Agentic / workflow product for fashion teams |
| **TryOn Labs** | Company / org |

## Appendix B — What “generic later” means

Do **not** rename or re-architect prematurely. Generalization = extract shared packages (`efficiency`, `agents`, `registry`) once fashion Studio has paying users and repeatable evals — then add vertical packs (beauty, eyewear) rather than diluting fashion depth.
