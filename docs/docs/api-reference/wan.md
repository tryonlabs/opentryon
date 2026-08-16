---
sidebar_position: 23
title: Wan (Alibaba API)
description: First-party Alibaba Wan video generation via DashScope / Model Studio.
---

# Wan (Alibaba DashScope API)

First-party [Alibaba Cloud Model Studio](https://www.alibabacloud.com/help/en/model-studio/text-to-video-guide) Wan video API (async video-synthesis).

Local twin: [Wan 2.2 local](../local-models/wan-2.2.md) (`--model wan-2.2`).

| CLI model | Default API model |
|---|---|
| `wan-api` | `wan2.6-t2v` (also `wan2.7-t2v`, `wan2.2-t2v-plus`, `wan2.6-i2v`, …) |

## Environment

```bash
export DASHSCOPE_API_KEY=...
# export WAN_API_BASE_URL=https://dashscope-intl.aliyuncs.com/api/v1
# China: https://dashscope.aliyuncs.com/api/v1
# Workspace: https://{WorkspaceId}.ap-southeast-1.maas.aliyuncs.com/api/v1
```

## CLI

```bash
opentryon video-generate --model wan-api \
  --prompt "A fashion model walking a runway, soft light" \
  --model-version wan2.6-t2v --duration 5 --resolution 720P

opentryon video-generate --model wan-api \
  --image look.jpg --prompt "Subject turns" --model-version wan2.6-i2v
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
```
