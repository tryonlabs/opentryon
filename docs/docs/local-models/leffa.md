---
sidebar_position: 8
title: Leffa (Open-Weight VTON)
description: CVPR 2025 local virtual try-on — person + garment on your GPU (franciszzj/Leffa).
---

# Leffa (open-weight VTON)

[Leffa](https://github.com/franciszzj/Leffa) (CVPR 2025) is a dedicated
person-image try-on model: it learns **flow fields in attention** so garment
logos and fine texture stay aligned. OpenTryOn runs the official inference
stack locally (`extra="local"`).

| | |
|---|---|
| **Registry id** | `leffa` |
| **Weights** | [`franciszzj/Leffa`](https://huggingface.co/franciszzj/Leffa) |
| **Code** | [github.com/franciszzj/Leffa](https://github.com/franciszzj/Leffa) (MIT) |
| **Paper** | [arXiv:2412.08486](https://arxiv.org/abs/2412.08486) |
| **VRAM** | A100 ~6s/image at fp16; 12GB+ recommended |
| **License** | Code MIT; **confirm the HF weight card** before commercial D2C |

This is **not** Qwen-Image / Muse composition try-on. It is a garment-fit
specialist (VITON-HD + DressCode checkpoints, plus pose transfer).

## Install

```bash
pip install opentryon[local]
```

CUDA GPU required. First run:

1. Downloads the Leffa GitHub source (or uses `LEFFA_HOME` if you already cloned it).
2. `snapshot_download`s `franciszzj/Leffa` (try-on pth + demo preprocess ckpts).

## Environment

```bash
# Optional
# LEFFA_HOME=/path/to/clone/of/franciszzj/Leffa
# LEFFA_CKPT=/path/to/hf/snapshot
# HF_TOKEN=hf_...   # only if the Hub repo is gated for your account
```

## CLI

```bash
opentryon vton --model leffa \
  --person-image person.jpg --garment-image top.jpeg \
  --garment-type upper_body --vt-model-type viton_hd --dry-run

opentryon vton --model leffa \
  --person-image person.jpg --garment-image top.jpeg \
  --mask-image agnostic.png --steps 30 --seed 42
```

`--mask-image` (white = clothing region to replace) is strongly recommended.
Without it, OpenTryOn tries Leffa's AutoMasker/DensePose extras; if those
deps are missing, it falls back to a geometric mask and a blank DensePose
map (lower quality).

`--control-type pose_transfer` uses the DeepFashion pose-transfer checkpoint
(`src` = target pose person, `garment` / ref = appearance person).

## Python

```python
from tryon.models import LeffaAdapter

adapter = LeffaAdapter()  # lazy-loads weights on first call
images = adapter.generate_and_decode("person.jpg", "garment.jpg")
images[0].save("tryon.png")
```

## MCP

Tool: `vton_leffa`. Needs `pip install opentryon[local]` + GPU. Restart MCP
after upgrading OpenTryOn so TryOn Studio lists it.

## See also

- [CatVTON](./catvton.md) — lighter &lt;8GB concatenation try-on (CC BY-NC-SA)
- [Qwen-Image local](./qwen-image.md) — composition I2I, not a VTON specialist
- Hosted dedicated VTON: OutfitAnyone-Plus, Photoroom, Google Vertex, FLUX VTO
