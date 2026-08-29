---
sidebar_position: 8
title: Google Virtual Try-On
description: Vertex AI virtual-try-on-001 — dedicated person + product try-on (not Gemini API / Nano Banana)
---

# Google Virtual Try-On

First-party Vertex / Gemini Enterprise model **`virtual-try-on-001`**. Person photo + product photo → try-on stills (1–4 samples). Output aspect and resolution match the person image. PNG/JPEG, 10MB max. C2PA / SynthID watermark on by default.

This is **not** Nano Banana composition (`nano-banana-2-lite` / `GEMINI_API_KEY`). The Gemini Developer API does not host this model.

| CLI `--model` | MCP tool | Adapter | Upstream id |
|---|---|---|---|
| `google-vton` | `vton_google_vton` | `GoogleVTONAdapter` | `virtual-try-on-001` |

Official docs:

- [Virtual Try-On 001 (Vertex)](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/imagen/virtual-try-on-001)
- [Generate Virtual Try-On Images](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/capabilities/generate-virtual-try-on-images)

GA 20 January 2026. Google lists a discontinuation date of 20 January 2027 for this model id — check Vertex docs before relying on it past that.

## Auth

Vertex **Application Default Credentials** plus a GCP project. Studio Connect stores the project id only.

```bash
gcloud auth application-default login
export GOOGLE_CLOUD_PROJECT=your-gcp-project
# optional; default is global
# export GOOGLE_CLOUD_LOCATION=global
# or a service account:
# export GOOGLE_APPLICATION_CREDENTIALS=/path/to/sa.json
```

Enable billing and the Vertex / Agent Platform APIs on that project. If `global` 404s in your region, set `GOOGLE_CLOUD_LOCATION=us-central1`.

## CLI

No text prompt — the API rejects styling instructions. Shopper photos need `--person-generation allow_adult` (the default).

```bash
opentryon vton --model google-vton \
  --person-image person.jpg \
  --garment-image sweater.jpg

opentryon vton --model google-vton \
  --person-image person.jpg \
  --garment-image sweater.jpg \
  --num-images 2 \
  --seed 7 \
  --dry-run
```

## Python

```python
from tryon.api import GoogleVTONAdapter

adapter = GoogleVTONAdapter()  # GOOGLE_CLOUD_PROJECT
images = adapter.generate_and_decode(
    person="person.jpg",
    garment="sweater.jpg",
    number_of_images=1,
    person_generation="allow_adult",
)
images[0].save("worn.png")
```

## Planner / Studio

Name **`google-vton`** or **`virtual-try-on-001`** in chat to pin this model. The VTON default stays `kling-ai`. After MCP restart, Connect lists **Google Vertex Virtual Try-On** (`GOOGLE_CLOUD_PROJECT`). ADC still lives on the MCP host, not in Studio.
