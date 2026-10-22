---
title: Nemotron Parse
description: NVIDIA NIM document image parsing to markdown and layout boxes
---

# Nemotron Parse

**Registry ids:** `nemotron-parse` (hosted), `nemotron-parse-local` (Docker NIM).

Model id: `nvidia/nemotron-parse`. Image in → markdown (and optional bounding boxes) out. **No text-only input.**

## Hosted

```bash
export NVIDIA_API_KEY=...
opentryon parse --model nemotron-parse --image invoice.png
```

## Local NIM

```bash
docker run ... nvcr.io/nim/nvidia/nemotron-parse:1.5.0
export NEMOTRON_PARSE_BASE_URL=http://127.0.0.1:8000/v1
opentryon parse --model nemotron-parse-local --image scan.jpg --tool markdown_bbox
```

## Tools

| `--tool` | Output |
| --- | --- |
| `markdown_bbox` | Markdown + normalized boxes (default) |
| `markdown_no_bbox` | Markdown only |
| `detection_only` | Layout boxes without transcription |

Response JSON includes `markdown`, `blocks`, and `raw` tool payload.
