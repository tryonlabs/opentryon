---
sidebar_position: 23
title: Wan (Alibaba API)
description: First-party Alibaba Wan video generation via DashScope / Model Studio, including Wan 3.0.
---

# Wan (Alibaba DashScope API)

First-party [Alibaba Cloud Model Studio](https://www.alibabacloud.com/help/en/model-studio/text-to-video-guide) Wan video API (async video-synthesis).

Wan 3.0 is a closed, hosted model (`wan3.0-video`). Alibaba has not published 3.0 open weights; the local twin remains [Wan 2.2](../local-models/wan-2.2.md) (`--model wan-2.2`).

| CLI model | Default API model |
|---|---|
| `wan-api` | `wan2.6-t2v` (also `wan2.7-t2v`, `wan2.2-t2v-plus`, `wan2.6-i2v`, …) |
| `wan-3.0` | `wan3.0-video` (preview; T2V, first/last frame, document or webpage) |

Wan 3.0 uses `input.media[]` (`first_frame`, `last_frame`, `file`, `link`) rather than Wan 2.x `img_url`. Official API: [Wan 3.0 video generation](https://help.aliyun.com/en/model-studio/wan3-video-generation-api-reference). Access may be invitation / preview.

## Environment

```bash
export DASHSCOPE_API_KEY=...
# export WAN_API_BASE_URL=https://dashscope-intl.aliyuncs.com/api/v1
# China: https://dashscope.aliyuncs.com/api/v1
# Workspace: https://{WorkspaceId}.ap-southeast-1.maas.aliyuncs.com/api/v1
```

Same key as Qwen3.8 / Qwen-Image. Match region between the key, `WAN_API_BASE_URL`, and the model.

## CLI

```bash
opentryon video-generate --model wan-api \
  --prompt "A fashion model walking a runway, soft light" \
  --model-version wan2.6-t2v --duration 5 --resolution 720P

opentryon video-generate --model wan-api \
  --image look.jpg --prompt "Subject turns" --model-version wan2.6-i2v

opentryon video-generate --model wan-3.0 \
  --prompt "A kitten running on a rooftop under moonlight" \
  --duration 5 --resolution 720P

opentryon video-generate --model wan-3.0 \
  --image look.jpg --last-frame look-end.jpg \
  --prompt "Subject turns toward camera" --duration 8

opentryon video-generate --model wan-3.0 \
  --prompt "Turn this deck into a product film" \
  --file https://example.com/lookbook.pptx --duration 10
```

## Python

```python
from tryon.api.wan import WanVideoAdapter

adapter = WanVideoAdapter()
video = adapter.generate_text_to_video(
    prompt="A kitten runs on the grass",
    model="wan2.6-t2v",
    duration=5,
    resolution="720P",
)
open("out.mp4", "wb").write(video)

wan3 = adapter.generate_text_to_video(
    prompt="A kitten running on a rooftop under moonlight",
    model="wan3.0-video",
    duration=5,
    resolution="720P",
)
open("wan3.mp4", "wb").write(wan3)
```
