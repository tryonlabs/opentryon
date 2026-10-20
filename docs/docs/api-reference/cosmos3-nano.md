---
sidebar_position: 49
title: Cosmos 3 Nano variants
description: Self-hosted Cosmos 3 Nano text-to-image, video-to-video, and Nano-DROID policy.
---

# Cosmos 3 Nano variants

These three ids talk to a **self-hosted** [Cosmos 3 certified NIM](https://github.com/NVIDIA/cosmos/blob/main/cookbooks/cosmos3/README.md). They are not the hosted `build.nvidia.com` video API.

Already shipped, and unchanged:

| CLI id | What it is |
|---|---|
| `cosmos3` | Hosted Generator nano, text-to-video and image-to-video |
| `cosmos3-reasoner` | Hosted Reasoner nano |
| `cosmos3-local` | Diffusers weights `nvidia/Cosmos3-Nano` |

New, certified NIM only (`COSMOS3_NIM_URL`, default `http://127.0.0.1:8010/v1/infer`):

| CLI id | Service | `NIM_MODEL_VARIANT` | `model_mode` |
|---|---|---|---|
| `cosmos3-nano-t2i` | `generate` | `nano` | `text2image` |
| `cosmos3-nano-v2v` | `video-generate` | `nano` | `video2video` |
| `cosmos3-nano-droid` | `robot-act` | `nano-droid` | `policy` |

The hosted catalog endpoint does not serve stills, video-to-video, or the DROID policy. Start the container yourself and point `COSMOS3_NIM_URL` at it. Port 8010 is the default so it does not collide with TryOn Studio's MCP server on 8000.

```bash
opentryon generate --model cosmos3-nano-t2i --prompt "linen shirt, soft studio light"
opentryon video-generate --model cosmos3-nano-v2v --video clip.mp4 --prompt "slower turn"
opentryon robot-act --model cosmos3-nano-droid --image obs.jpg --prompt "pick up the cup" --observation obs.json
```

`obs.json` needs `observation/joint_position` (seven numbers) and `observation/gripper_position`. Nano-DROID returns an action chunk and no video. A bearer token is sent only when `NVIDIA_API_KEY` or `NGC_API_KEY` is set.

Super checkpoints (`super-t2i`, `super-i2v`, and the 4-step students) are not registered.
