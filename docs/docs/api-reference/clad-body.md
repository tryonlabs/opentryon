---
sidebar_position: 43
title: Clad body measurements (API)
description: ISO 8559-1 body measurements from a photo or questionnaire via api.clad.you
---

# Clad body measurements (API)

[Clad](https://clad.you/) turns a **photo** or **eight-question sizing flow** into a 3D body model and **ISO 8559-1-style measurements** (bust, waist, hip, inseam, and more). OpenTryOn exposes the hosted REST API on the **`measure`** service.

| Registry id | Input | Flow |
|---|---|---|
| `clad-body-photo` | `--photo` + `--height-cm` | Async job → poll → measurements |
| `clad-body-questionnaire` | Height, mass, shape, build, … | Sync JSON response |

Local re-measurement of existing Anny/MHR params (no photo): **`clad-body-local`** — see [Clad body (local)](../local-models/clad-body-local.md).

## Auth

```bash
CLAD_API_KEY=ck_live_...
# optional override
# CLAD_API_BASE_URL=https://api.clad.you
```

Create a key at [clad.you/developers](https://clad.you/developers). OpenAPI: [api.clad.you](https://api.clad.you/).

## CLI

```bash
# Photo → body (requires known height)
opentryon measure --model clad-body-photo \
  --photo data/person-full.jpg \
  --height-cm 172

# Questionnaire (no photo)
opentryon measure --model clad-body-questionnaire \
  --height-cm 168 --mass-kg 62 --gender female \
  --body-shape hourglass --belly 2 --build 2

# Dry-run
opentryon measure --model clad-body-photo --photo person.jpg --height-cm 170 --dry-run
```

Results are saved as JSON (`output_kind=text`). By default the GLB mesh is **omitted**; pass `--include-mesh` to embed base64 GLB (large).

## MCP

- `measure_clad_body_photo`
- `measure_clad_body_questionnaire`

## Python

```python
from tryon.api.clad import CladBodyApiAdapter

adapter = CladBodyApiAdapter()
result = adapter.measure_from_photo("person.jpg", height_cm=172)
print(result["measurements"])
```

## Notes

- Photo jobs are **async**; the adapter polls until `completed` or `--max-wait-time`.
- Measurements are intended for **size-aware try-on and tailoring**, not medical diagnosis.
- Apache-2.0 **clad-body** library: [github.com/datar-psa/clad-body](https://github.com/datar-psa/clad-body).
