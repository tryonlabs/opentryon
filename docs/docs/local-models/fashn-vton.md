---
sidebar_position: 9
title: FASHN VTON v1.5 (local)
description: Open-weight, Apache-2.0 maskless virtual try-on from FASHN AI, run on your own GPU.
keywords:
  - FASHN VTON 1.5
  - virtual try-on
  - maskless try-on
  - Apache-2.0
  - local
---

# FASHN VTON v1.5 (local)

[FASHN VTON v1.5](https://github.com/fashn-AI/fashn-vton-1.5) is a 972M-parameter try-on model that generates photorealistic results **directly in pixel space, with no segmentation mask**. Give it a person photo and a garment image — worn on a model *or* a flat-lay product shot — and it renders the person wearing the garment. OpenTryOn runs it locally through `FashnVTONLocalAdapter` (Path B, `extra="local"`).

| | |
|---|---|
| **Registry id** | `fashn-vton-1.5` (service `vton`) |
| **Weights** | [`fashn-ai/fashn-vton-1.5`](https://huggingface.co/fashn-ai/fashn-vton-1.5) + [`fashn-ai/DWPose`](https://huggingface.co/fashn-ai/DWPose), about 2 GB total |
| **Code** | [github.com/fashn-AI/fashn-vton-1.5](https://github.com/fashn-AI/fashn-vton-1.5) |
| **License** | **Apache-2.0** code and weights. Third parties: DWPose and YOLOX (Apache-2.0); [`fashn-human-parser`](https://github.com/fashn-AI/fashn-human-parser) has its own terms — review before commercial use |
| **Precision** | bfloat16 on Ampere+ GPUs (RTX 30xx/40xx, A100, H100); float32 on older GPUs and CPU |

Compared with the other local try-on models: [Leffa](leffa.md) has MIT code (check the weight card), [CatVTON](catvton.md) is CC BY-NC-SA. FASHN VTON 1.5 is the commercial-friendly option. Hosted twin: `fashn-tryon-max` / `fashn-tryon-v1.6` ([FASHN API](../api-reference/fashn.md), `FASHN_API_KEY`).

:::note Verify on your hardware
FASHN's page says it "runs on consumer GPUs" but publishes no VRAM figure, and a technical paper is still forthcoming. No GPU was available when this was integrated, so the weight load and a real try-on were not exercised end to end.
:::

## Requirements

```bash
pip install opentryon[local]
pip install "git+https://github.com/fashn-AI/fashn-vton-1.5.git"   # provides the fashn_vton package
```

The package pulls `onnxruntime-gpu` for DWPose pose detection and needs a working CUDA setup. On CPU-only hosts: `pip uninstall onnxruntime-gpu && pip install onnxruntime`.

Weights download automatically on first use to `~/.cache/opentryon/fashn-vton-1.5`. To use a pre-downloaded folder (`model.safetensors` plus `dwpose/`) set:

```bash
export FASHN_VTON_WEIGHTS_DIR=/path/to/weights
```

## CLI

```bash
# Model-worn garment, upper body
opentryon vton --model fashn-vton-1.5 \
  --person-image person.jpg --garment-image shirt.jpg --category tops

# Flat-lay product shot, dress, quality settings, 2 variations
opentryon vton --model fashn-vton-1.5 \
  --person-image person.jpg --garment-image dress_flatlay.png \
  --category one-pieces --garment-photo-type flat-lay \
  --steps 50 --num-samples 2 --seed 7
```

| Flag | Notes |
|---|---|
| `--person-image` / `--garment-image` | Path or URL — required |
| `--category` | `tops` (default), `bottoms`, `one-pieces` |
| `--garment-photo-type` | `model` (default) or `flat-lay` |
| `--num-samples` | 1–4 images per call |
| `--steps` | Diffusion steps: 20 fast, 30 balanced (default), 50 quality |
| `--guidance-scale` | Classifier-free guidance (default 1.5) |
| `--seed` | Default 42 |
| `--no-segmentation-free` | Turn off the default segmentation-free mode, which preserves body features and allows unconstrained garment volume |
| `--weights-dir`, `--device` | Overrides |

## Python

```python
from tryon.models.fashn_vton import FashnVTONLocalAdapter

adapter = FashnVTONLocalAdapter()  # weights auto-download on first use
images = adapter.generate_and_decode("person.jpg", "garment.jpg", category="tops", num_samples=2)
images[0].save("tryon.png")
```

## Notes

- MCP tool: `vton_fashn_vton_1_5`.
- Planner pins: `fashn vton 1.5`, `fashn-vton-1.5`, `fashn vton local`. The `vton` capability default stays `kling-ai`.
- Each call loads the pipeline once per adapter instance; reuse the instance for batches.
