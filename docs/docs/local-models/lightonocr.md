---
title: LightOnOCR-3 (Document OCR)
description: LightOn's Apache-2.0 LightOnOCR-3 turns page images and PDFs into markdown, with optional labelled layout blocks, on the parse service.
keywords:
  - LightOnOCR-3
  - OCR
  - document parsing
  - size chart
  - PDF to markdown
---

# LightOnOCR-3 (Document OCR)

[LightOnOCR-3](https://huggingface.co/lightonai/LightOnOCR-3-0.8B) is LightOn's open-weight OCR model (Apache-2.0, released October 2026). It reads a page image and returns markdown. With grounding turned on, it also returns a label and a bounding box for every block, and renders tables and charts as HTML tables. OpenTryOn exposes it on the **`parse`** service, next to [Nemotron Parse](../api-reference/nemotron-parse).

Fashion uses include size charts, spec and tech sheets, line sheets, invoices and care-label scans.

| Registry id | How it runs | Needs |
|---|---|---|
| `lightonocr-3-local` | In-process Hugging Face Transformers | GPU or Apple Silicon; `transformers>=5.2`, `torch` |
| `lightonocr-3-vllm` | Client for a vLLM / SGLang server you run | Your server; nothing heavy on the client |

LightOn has no hosted API for LightOnOCR-3, and no third-party host serves it.

## Variants

| `--variant` | Model | Notes |
|---|---|---|
| `0.8b` (default) | `lightonai/LightOnOCR-3-0.8B` | About 0.9B parameters, roughly 2 GB in BF16 |
| `4b` | `lightonai/LightOnOCR-3-4B` | LightOn's recommended quality tier |

Both use the Qwen3.5 vision-language architecture. The 1B sibling keeps the older LightOnOCR-2 architecture and isn't wired here. LightOn reports 85.5 (0.8B) and 86.3 (4B) on olmOCR-Bench; these are vendor figures.

## CLI

```bash
# Markdown from one page image
opentryon parse --model lightonocr-3-local --image size_chart.png

# Labelled blocks with bounding boxes, pages 1-2 of a PDF, larger model
opentryon parse --model lightonocr-3-local --image tech_pack.pdf --pages 1-2 --grounding --variant 4b

# Against your own vLLM server
vllm serve lightonai/LightOnOCR-3-0.8B --trust-remote-code \
  --default-chat-template-kwargs '{"enable_thinking": false}'
opentryon parse --model lightonocr-3-vllm --image size_chart.pdf --grounding
```

| Flag | Meaning |
|---|---|
| `--image`, `-i` | Page image or PDF (path or URL) |
| `--grounding` | Also return labelled blocks with bounding boxes |
| `--pages` | PDF pages to read, e.g. `1-3,5` (default: all) |
| `--max-tokens` | Max tokens per page (default 4096) |
| `--variant`, `--model-id`, `--device` | `lightonocr-3-local` only |
| `--base-url`, `--served-model` | `lightonocr-3-vllm` only (defaults from `LIGHTONOCR_BASE_URL`, `LIGHTONOCR_MODEL`) |

PDFs are rendered with `pypdfium2` (`pip install pypdfium2`) so the longest side is 2048 px, LightOn's recommended setting.

## Output

The result is saved as JSON:

```json
{
  "model": "lightonai/LightOnOCR-3-0.8B",
  "grounding": true,
  "page_count": 2,
  "markdown": "## Size guide\n\n<table>...</table>",
  "blocks": [
    {"page": 1, "label": "title", "bbox": [113, 608, 263, 623], "text": "## Size guide", "continues": false}
  ],
  "pages": [{"page": 1, "markdown": "...", "blocks": ["..."], "raw": "..."}]
}
```

- `bbox` is `[x1, y1, x2, y2]`, normalised to 0–1000 on both axes, whatever the image size.
- Labels include `text`, `title`, `list`, `table`, `chart`, `image`, `caption`, `formula`, `code`, `header`, `footer` and `page_number`.
- `continues: true` marks a block that carries on from the previous one, for example across columns; `markdown` joins them.
- Without `--grounding`, each page is plain markdown and `blocks` is empty.

## Python

```python
from tryon.models.lightonocr import LightOnOCRLocalAdapter
from tryon.api.lighton import LightOnOCRServerAdapter

result = LightOnOCRLocalAdapter(variant="0.8b").parse_document("size_chart.pdf", grounding=True)
print(result["markdown"])

served = LightOnOCRServerAdapter(base_url="http://127.0.0.1:8000/v1")
print(served.parse_document("care_label.jpg")["markdown"])
```

## Requirements

`lightonocr-3-local` loads with `Qwen3_5ForConditionalGeneration`, which needs `transformers>=5.2` (the model card was saved with 5.5.4). That's newer than the shared `opentryon[local]` pin, so use a separate environment if loading fails:

```bash
pip install "transformers>=5.5.4" torch pillow pypdfium2
```

See also: [Nemotron Parse](../api-reference/nemotron-parse) (hosted NIM OCR), [DeepSeek-OCR](deepseek-ocr).
