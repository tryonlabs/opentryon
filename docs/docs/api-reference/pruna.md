---
sidebar_position: 8
title: Pruna P-Image-Try-On
description: Multi-garment virtual try-on using Pruna AI's P-Image-Try-On API
keywords:
  - pruna
  - p-image-try-on
  - virtual try-on
  - multi-garment
  - image editing
---

# Pruna P-Image-Try-On

The `PImageTryOnAdapter` provides an interface to Pruna AI's P-Image-Try-On API for multi-garment virtual try-on, combining a person photo with one or more garment reference images.

## Overview

P-Image-Try-On fits one or more garments onto a person's photo. Unlike single-garment VTON APIs (Nova Canvas, Kling AI, Segmind), it accepts up to 11 garment reference images in one call (6 recommended), so you can compose a full outfit -- top, bottoms, shoes, accessories -- in a single request. The adapter handles image upload, prediction creation, async polling, and response decoding automatically.

**API endpoint:** `POST /v1/predictions` (`Model: p-image-try-on`)

**Reference:** [Pruna P-Image-Try-On Documentation](https://docs.api.pruna.ai/guides/models/p-image-try-on)

**Pricing:** $0.015 for the first garment image, plus $0.008 for each additional garment image (per Pruna's docs).

**Location note:** unlike most cloud adapters in this repo, `PImageTryOnAdapter` lives under `tryon.api.vton` (a use-case directory) rather than a dedicated `tryon.api.pruna/` package -- see [Adding a New Model Integration](../advanced/new-model-checklist.md#1-decide-where-the-adapter-lives) for why.

## Installation

No additional installation required. The adapter uses the `requests` and `Pillow` libraries, which are included with OpenTryOn.

## Authentication

Pruna requires an API key, sent as the `apikey` header on every request.

1. **Environment Variable** (Recommended):
   ```bash
   export PRUNA_API_KEY="your_api_key"
   ```

2. **Constructor Parameter**:
   ```python
   adapter = PImageTryOnAdapter(api_key="your_api_key")
   ```

## Quick Start

```python
from dotenv import load_dotenv
load_dotenv()

from tryon.api.vton import PImageTryOnAdapter

# Initialize adapter (uses PRUNA_API_KEY from environment)
adapter = PImageTryOnAdapter()

# Generate a multi-garment virtual try-on
images = adapter.generate_and_decode(
    person_image="data/person.jpg",
    garment_images=["data/top.jpg", "data/bottoms.jpg"],
)

# Save the result
images[0].save("outputs/tryon_result.jpg")
```

## API Reference

### Class: `PImageTryOnAdapter`

Adapter class for Pruna AI's P-Image-Try-On API.

#### Constructor

```python
PImageTryOnAdapter(
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
)
```

**Parameters:**
- `api_key` (str, optional): Pruna API key. Defaults to `PRUNA_API_KEY` environment variable. If not provided, raises `ValueError`.
- `base_url` (str, optional): Base URL for the Pruna API. Defaults to `PRUNA_BASE_URL` environment variable or `'https://api.pruna.ai'`.

#### Methods

##### `generate(person_image, garment_images, ...)`

Generate a virtual try-on result.

**Parameters:**
- `person_image` (str, PIL.Image, or file-like): Person/model photo. File paths and file-like objects are uploaded to Pruna's temporary file store automatically; URLs are passed through as-is.
- `garment_images` (str or list): One or more garment reference images (same input types as `person_image`). Up to 11 supported, 6 recommended.
- `prompt` (str, optional): Experimental guidance for non-flatlay garment images, e.g. which garment from which image to use. Default: `""`.
- `seed` (int, optional): Random seed. Omit for a random seed.
- `turbo` (bool, optional): Run faster with additional optimizations. Not recommended for more than 4 garments. Default: `False`.
- `output_format` (str, optional): `"jpg"`, `"png"`, or `"webp"`. Default: `"jpg"`.
- `output_quality` (int, optional): JPEG/WebP quality, 0-100. Default: `95`.
- `reference_pose` (optional): EXPERIMENTAL reference pose image; when provided, the person is reposed to match it before try-on.
- `preserve_input_size` (bool, optional): Return the output at the original input resolution. Default: `True`.
- `wait` (bool, optional): Use Pruna's synchronous mode and poll automatically if it takes longer than 60s. Default: `True`.
- `max_wait_time` (int, optional): Maximum polling time in seconds. Default: `120`.

**Returns:**
- `str`: URL of the generated result image.

**Raises:**
- `ValueError`: If required images are missing, the API returns an error, or the prediction fails/times out.

**Example:**
```python
url = adapter.generate(
    person_image="person.jpg",
    garment_images=["shirt.jpg", "pants.jpg"],
    turbo=True,
)
```

##### `generate_and_decode(person_image, garment_images, ...)`

Same parameters as `generate()`, but downloads and decodes the result to a PIL Image.

**Returns:**
- `List[PIL.Image.Image]`: A single-element list containing the decoded result image.

**Example:**
```python
images = adapter.generate_and_decode(
    person_image="data/person.jpg",
    garment_images=["data/top.jpg", "data/bottoms.jpg"],
    output_format="png",
)
images[0].save("outputs/tryon_result.png")
```

## Image Input Formats

Both `person_image` and each entry in `garment_images` accept:

- **File paths**: `"data/person.jpg"` -- uploaded to Pruna's temporary file store automatically
- **URLs**: `"https://example.com/person.jpg"` -- passed straight through
- **PIL Images**: `Image.open("person.jpg")` -- uploaded as PNG
- **Base64 strings**: decoded and uploaded

Uploaded files live on Pruna's servers for a limited time (per Pruna's docs) and are used only for the duration of the prediction.

## Multi-Garment Try-On

Unlike Nova Canvas, Kling AI, or Segmind (one garment per call), P-Image-Try-On composes multiple garments in a single request:

```python
images = adapter.generate_and_decode(
    person_image="model.jpg",
    garment_images=["jacket.jpg", "shirt.jpg", "trousers.jpg", "shoes.jpg"],
)
```

For more than 4 garments, avoid `turbo=True` (Pruna's docs note it's not recommended beyond that).

## Asynchronous Processing

By default (`wait=True`), the adapter uses Pruna's synchronous mode (`Try-Sync: true`) and transparently falls back to polling `GET /v1/predictions/status/{id}` if the request doesn't finish within Pruna's ~60 second synchronous window. Pass `wait=False` to always submit asynchronously and poll up to `max_wait_time` seconds.

```python
url = adapter.generate(
    person_image="person.jpg",
    garment_images=["shirt.jpg"],
    wait=False,
    max_wait_time=180,
)
```

## Error Handling

```python
from tryon.api.vton import PImageTryOnAdapter

try:
    adapter = PImageTryOnAdapter()
    images = adapter.generate_and_decode(
        person_image="person.jpg",
        garment_images=["shirt.jpg"],
    )
except ValueError as e:
    print(f"Error: {e}")
```

Common errors:
- Missing API key
- Missing person or garment image(s)
- API request failure
- Prediction failed or timed out

## opentryon CLI / MCP Server

P-Image-Try-On is also wired into the `opentryon` CLI and MCP server as `vton --model p-image-tryon`:

```bash
opentryon vton --model p-image-tryon \
  --person-image person.jpg \
  --garment-image top.jpg --garment-image bottoms.jpg \
  --turbo
```

## See Also

- [Virtual Try-On Examples](../examples/virtual-tryon) - Usage examples
- [API Reference Overview](overview) - Complete API reference
- [Nano Banana 2 Lite](nano-banana#nanobanana2liteadapter-gemini-31-flash-lite-image--nano-banana-2-lite) - A faster/cheaper (lower-fidelity) alternative for virtual try-on
- [Pruna P-Image-Try-On Documentation](https://docs.api.pruna.ai/guides/models/p-image-try-on) - Official API docs
