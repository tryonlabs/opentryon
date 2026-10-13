---
sidebar_position: 23
title: Extract-Outfit (local)
description: Garment extraction ("try-off") — QIE-2511 Extract-Outfit LoRA on Qwen-Image-Edit-2511 turns a worn outfit photo into a flat studio mockup.
keywords:
  - Extract-Outfit
  - garment extraction
  - try-off
  - flat mockup
  - Qwen-Image-Edit-2511
  - LoRA
  - local
---

# Extract-Outfit (local)

[`prithivMLmods/QIE-2511-Extract-Outfit`](https://huggingface.co/prithivMLmods/QIE-2511-Extract-Outfit) is an Apache-2.0 LoRA for `Qwen/Qwen-Image-Edit-2511` (also compatible with 2509) that does the reverse of try-on: it removes the person, pose and background and renders the **clothing as a clean, flat studio mockup**, keeping fabric texture, colour, stitching and patterns. Use it to turn on-model or street photos into catalogue-style garment images, or to produce garment input for [try-on](../getting-started/cli.md). OpenTryOn exposes it in the `edit` service as `qie-2511-extract-outfit` (Path B, `extra="local"`).

| | |
|---|---|
| Base model | `Qwen/Qwen-Image-Edit-2511` (Apache-2.0), Diffusers `QwenImageEditPlusPipeline` |
| LoRA | `prithivMLmods/QIE-2511-Extract-Outfit` (Apache-2.0), loaded onto the pipeline before offload |
| Trigger prompt | `Extract the clothing and create a flat mockup.` (the default) |
| Hardware | Same as [`qwen-image-local`](qwen-image.md): CUDA GPU, ~40GB+ VRAM in bf16; CPU offload is on by default for smaller cards |

The whole stack is Apache-2.0, so it is the commercially clean choice among the garment-extraction LoRAs. It is a community adapter: the card shows example images but publishes **no metrics**, so judge quality on your own photos.

**Input must show the full outfit.** A half-cropped photo only extracts the visible region.

## Requirements

```bash
pip install opentryon[local]
pip install -U diffusers transformers accelerate peft
```

`peft` is needed to load LoRA weights; the adapter raises a clear error if it is missing. Overrides: `EXTRACT_OUTFIT_LORA_ID` (LoRA repo or path) and `QWEN_IMAGE_EDIT_MODEL_ID` / `QWEN_IMAGE_EDIT_PATH` (base model, shared with `qwen-image-local`).

## CLI

```bash
opentryon edit --model qie-2511-extract-outfit --image model_wearing_look.jpg

# More control
opentryon edit --model qie-2511-extract-outfit --image look.jpg \
  --steps 40 --true-cfg-scale 4.0 --seed 7 --num-images 2 --no-cpu-offload
```

Flags: `--image` (exactly one), `--prompt` (defaults to the trigger prompt; other prompts may not activate the LoRA), `--steps`, `--true-cfg-scale`, `--guidance-scale`, `--seed`, `--num-images`, `--lora-id`, `--edit-model-id`, `--dtype`, `--no-cpu-offload`. Output is saved under `outputs/` like any `edit` model.

## Python

```python
from tryon.models.extract_outfit import ExtractOutfitAdapter

adapter = ExtractOutfitAdapter()
images = adapter.extract_outfit("model_wearing_look.jpg")
images[0].save("flat_mockup.png")
```

## Notes

- MCP tool: `edit_qie_2511_extract_outfit`. Planner pins: `extract outfit`, `extract the outfit`, `qie-2511-extract-outfit`.
- The adapter subclasses the repo's Qwen-Image local runner, so loading, dtype and offload behave exactly like `qwen-image-local`.
- Similar models exist on the FLUX.2 klein 9B base (`fal/virtual-tryoff-lora`), but that base is non-commercial; see [Integrate next](../community/integrate-next.md).
- No GPU was available when this was integrated; the adapter is tested against a stubbed pipeline (LoRA attached once and before offload, trigger prompt, validation), not real weights.
