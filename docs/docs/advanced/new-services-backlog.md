---
sidebar_position: 8
title: New services backlog
description: segment, detect, and follow-ups after measure (Clad)
---

# New services backlog

## `measure` — shipped

| Id | Path | Notes |
|---|---|---|
| `clad-body-photo` | A | Clad API photo + height |
| `clad-body-questionnaire` | A | Clad eight-question flow |
| `clad-body-local` | B | `clad-body` on Anny/MHR params |

Docs: [Clad API](../api-reference/clad-body.md), [local](../local-models/clad-body-local.md).

---

## `segment` — next category

| Priority | Id (draft) | Path | API / model | Status |
|---:|---|---|---|---|
| 1 | `fashn-human-parser` | B | fashn-ai/fashn-human-parser | **watch** (licence) |
| 2 | `aitryon-parsing-v1` | A | DashScope parsing | **next** after `segmentation` output_kind |
| 3 | `segformer-b2-clothes` | B | HF clothes SegFormer | **watch** |

---

## `detect` — after segment

| Priority | Id (draft) | Path | API / model | Status |
|---:|---|---|---|---|
| 1 | `trendyol-yolov9` | B | 84-class product detector (CC BY-SA) | **watch** |
