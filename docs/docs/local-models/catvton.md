---
sidebar_position: 9
title: CatVTON (Open-Weight VTON)
description: ICLR 2025 concatenation virtual try-on — under 8GB VRAM at 1024×768 (zhengchong/CatVTON).
---

# CatVTON (open-weight VTON)

[CatVTON](https://github.com/Zheng-Chong/CatVTON) (ICLR 2025) concatenates
the person and garment in latent space on **SD 1.5 inpainting**, skipping
text cross-attention. The trainable attention adapters are small (~50M);
full inference is about **899M params** and typically **under 8GB VRAM** at
1024×768.

| | |
|---|---|
| **Registry id** | `catvton` |
| **Weights** | [`zhengchong/CatVTON`](https://huggingface.co/zhengchong/CatVTON) |
| **Code** | [github.com/Zheng-Chong/CatVTON](https://github.com/Zheng-Chong/CatVTON) |
| **Paper** | [arXiv:2407.15886](https://arxiv.org/abs/2407.15886) |
| **VRAM** | &lt;8GB @ 1024×768 (fp16/bf16) |
| **License** | **CC BY-NC-SA 4.0** (code + checkpoints) — **not for commercial D2C** |

The same HF repo also contains a **FLUX.1-Fill LoRA** (`flux-lora/`, 37.4M).
Official FLUX inference code was not released with the LoRA; OpenTryOn
implements the documented **SD 1.5** pipeline (`mix` / `vitonhd` / `dresscode`
attention folders).

## Install

```bash
pip install opentryon[local]
```

The SD 1.5 inpainting base (`runwayml/stable-diffusion-inpainting`) may be
gated. Override with a community mirror:

```bash
export CATVTON_BASE_MODEL=botp/stable-diffusion-v1-5-inpainting
```

## Environment

```bash
# CATVTON_ATTN_CKPT=zhengchong/CatVTON
# CATVTON_BASE_MODEL=runwayml/stable-diffusion-inpainting
# HF_TOKEN=hf_...
```

## CLI

```bash
opentryon vton --model catvton \
  --person-image person.jpg --garment-image dress.jpg \
  --garment-type dresses --attn-version mix --dry-run

opentryon vton --model catvton \
  --person-image person.jpg --garment-image top.jpeg \
  --mask-image agnostic.png --steps 50 --width 768 --height 1024
```

`--attn-version mix` is the 1024 mix checkpoint (default). `vitonhd` and
`dresscode` are the 512 dataset-specific adapters.

Pass `--mask-image` (white = replace) when you have an agnostic mask. Without
it, OpenTryOn uses a geometric upper/lower/dress rectangle.

## Python

```python
from tryon.models import CatVTONAdapter

adapter = CatVTONAdapter(attn_version="mix")
images = adapter.generate_and_decode("person.jpg", "garment.jpg")
images[0].save("tryon.png")
```

## MCP

Tool: `vton_catvton`. Needs `pip install opentryon[local]` + GPU. Restart MCP
so TryOn Studio lists it.

## See also

- [Leffa](./leffa.md) — MIT-licensed code, stronger detail/logo story, heavier stack
- Hosted dedicated VTON if you cannot use CC BY-NC-SA weights in production
