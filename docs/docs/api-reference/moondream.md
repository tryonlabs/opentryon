---
sidebar_position: 48
title: Moondream
description: Moondream 3.1 and Moondream 3 Preview — query, caption, detect, point, and segment.
---

# Moondream

[Moondream](https://docs.moondream.ai/api) is a small vision model with five typed skills. OpenTryOn uses the first-party cloud API and, for 3.1, the official Photon runtime.

| CLI id | Service | Upstream id | Where it runs |
|---|---|---|---|
| `moondream-3.1` | `understand`, `detect` | `moondream3.1-9B-A2B` | Cloud, `MOONDREAM_API_KEY` |
| `moondream-3-preview` | `understand`, `detect` | `moondream3-preview` | Cloud, same key |
| `moondream-3.1-local` | `understand`, `detect` | `moondream3.1-9B-A2B` | Photon, `pip install moondream` |

Auth header on the cloud API is `X-Moondream-Auth`. Optional `MOONDREAM_BASE_URL` defaults to `https://api.moondream.ai/v1`.

## Understand

`--skill query` (default) needs `--prompt`. `--skill caption` uses `--length short|normal|long`.

```bash
opentryon understand --model moondream-3.1 --image look.jpg --prompt "What fabric is the jacket?"
opentryon understand --model moondream-3.1 --image look.jpg --skill caption --length short
```

## Detect

Coordinates are normalized from 0 to 1, origin at the top-left.

```bash
opentryon detect --model moondream-3.1 --image look.jpg --object dress
opentryon detect --model moondream-3.1 --image look.jpg --object button --skill point
opentryon detect --model moondream-3.1 --image look.jpg --object jacket --skill segment
```

`detect` writes JSON boxes `{label, score, bbox_xyxy}`. `point` writes centroids. `segment` writes an SVG path. This is open-vocabulary grounding, not the garment-parser masks tracked in the [new services backlog](../advanced/new-services-backlog).

## Local

Photon runs on NVIDIA Ampere or newer, and on Apple Silicon. Base weights do not need an API key.

```bash
pip install moondream
opentryon understand --model moondream-3.1-local --image look.jpg --prompt "Describe the outfit."
```

License: Moondream License. See the [3.1 model card](https://moondream.ai/models/moondream_3-1_9B_A2B).
