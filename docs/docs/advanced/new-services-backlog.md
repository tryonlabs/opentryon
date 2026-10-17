---
sidebar_position: 8
title: New services backlog (segment, detect, measure)
description: Integration queue for parsing, e-commerce detection, and body measurement — design before adapters.
---

# New services backlog

These capabilities need a **new CLI service** (and usually a new `output_kind`) before model adapters land. Integrate **one category at a time**; start with platform plumbing (`segmentation` output), then the first model in that category.

Status key: **next** = ready to implement after design sign-off · **watch** = licence, API maturity, or scope blocker · **skip** = defer.

---

## 1. `segment` — human / garment parsing (masks)

**Service contract (target v1)**

| Field | Choice |
|---|---|
| CLI | `opentryon segment --model <id> --image …` |
| Method | `segment` |
| `output_kind` | **`segmentation`** (new) — indexed label PNG + `labels` JSON; optional per-class binary masks |
| MCP | Base64 PNG(s) + JSON metadata |

**Integration queue**

| Priority | Registry id (draft) | Path | Vendor / weights | Licence / notes | Status |
|---:|---|---|---|---|---|
| 1 | `fashn-human-parser` | B | [fashn-ai/fashn-human-parser](https://github.com/fashn-AI/fashn-human-parser) (SegFormer-B4, 18 classes) | SegFormer / FASHN terms — **confirm commercial use** before default | **next** (after licence pick) |
| 2 | `aitryon-parsing-v1` | A | Alibaba DashScope **OutfitAnyone parsing** companion | Same `DASHSCOPE_API_KEY` as `outfitanyone-plus`; Beijing region | **next** (API) |
| 3 | `segformer-b2-clothes` | B | HF `mattmdjaga/segformer_b2_clothes` | Research / “other” licence | **watch** |
| 4 | `alibaba-aitryon-parsing` | A | Documented with `aitryon-plus` flows | Already referenced in [OutfitAnyone-Plus](../api-reference/outfitanyone-plus.md) | **watch** (alias of #2) |
| — | Leffa ONNX parsing | — | Internal to `leffa` adapter only | Not a registry id unless unified | **skip** (for now) |

**Downstream:** `klein-4b-tryon` (`--mask-image`), inpainting edits, catalogue QA.

**Blocker:** Product/legal must pick a **commercial-clean default parser** (survey note in [integrate-next](../community/integrate-next.md)).

---

## 2. `detect` — e-commerce object detection

**Service contract (target v1)**

| Field | Choice |
|---|---|
| CLI | `opentryon detect --model <id> --image …` |
| Method | `detect` |
| `output_kind` | **`text`** (JSON file) in v1: `{detections: [{label, score, bbox_xyxy}]}` |

**Integration queue**

| Priority | Registry id (draft) | Path | Vendor / weights | Licence / notes | Status |
|---:|---|---|---|---|---|
| 1 | `trendyol-yolov9` | B | Trendyol YOLOv9 (84 product classes, survey Oct 2026) | **CC BY-SA 4.0** — share-alike for derivatives | **watch** (paper/weights GA) |
| 2 | `trendyol-dinov2-embed` | B | DINOv2 256-d embedder (same survey) | CC BY-SA — consider **`embed`** service instead if boxes not needed | **watch** |
| 3 | — | A | No first-party “fashion detect” API in Wave 2 table | Use `understand` VLMs for prose only | **skip** |

**Blocker:** Stable HF repo + class list; NMS/threshold CLI flags frozen in docs.

---

## 3. `measure` — body measurements / sizing

**Service contract (target v1)**

| Field | Choice |
|---|---|
| CLI | `opentryon measure --model <id> …` |
| Method | `measure` |
| `output_kind` | **`text`** (JSON): ISO 8559-1-style measurements + garment-type tags |

**Integration queue**

| Priority | Registry id (draft) | Path | Input | Vendor | Status |
|---:|---|---|---|---|---|
| 1 | `clad-body-api` | A | Photo(s) per Clad hosted API | [Clad](https://github.com/datar-psa/clad-body) hosted (“free for now”) | **watch** (API schema + auth) |
| 2 | `clad-body-local` | B | `--mesh` (Anny / MHR) | `datar-psa/clad-body` library (Apache-2.0) | **watch** (mesh pipeline UX) |
| 3 | — | — | Photo → mesh → measure | Multi-step planner flow, not one adapter | **next** (design only) |

**Blocker:** Clad API stability; whether OpenTryOn v1 is **photo-only** (API) or **mesh-only** (local).

---

## Suggested category order

1. **`segment`** — highest leverage for VTON preprocess (after licence + `segmentation` output_kind).
2. **`detect`** — catalogue / agent automation.
3. **`measure`** — sizing niche; depends on Clad API clarity.

---

## Related (not in this doc)

- **`music-generate`** + Lyria 3.5 — separate from `tts`; see [integrate-next](../community/integrate-next.md) survey line.
- **3D garments / sewing** — `pygarment` / GarmentCode — large scope; own design pass.
