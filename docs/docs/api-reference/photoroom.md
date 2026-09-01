---
sidebar_position: 10
title: Photoroom Virtual Try-On
description: Photoroom Image Editing API — shopper Virtual Try-On and catalog Virtual Model
---

# Photoroom Virtual Try-On / Virtual Model

First-party [Photoroom Image Editing API](https://docs.photoroom.com/image-editing-api-plus-plan/virtual-try-on) (`POST /v2/edit`). One adapter, two registry ids:

| Job | CLI `--model` | MCP tool | Person photo |
|---|---|---|---|
| Shopper fitting room | `photoroom-vton` | `vton_photoroom_vton` | Required (custom model) |
| Catalog on-model | `photoroom-virtual-model` | `vton_photoroom_virtual_model` | Optional; otherwise a preset (`avery` default) |

Product pages: [Virtual Try-On](https://www.photoroom.com/tools/virtual-try-on), [Virtual Model](https://www.photoroom.com/tools/virtual-model). API: [Virtual Try-On](https://docs.photoroom.com/image-editing-api-plus-plan/virtual-try-on), [Virtual Model](https://docs.photoroom.com/image-editing-api-plus-plan/virtual-model).

Both set `virtualModel.mode=ai.auto`. Try-on sends the shopper as `virtualModel.model.custom`; Virtual Model uses `virtualModel.model.preset.name` unless you pass a custom model photo.

## Auth

```bash
export PHOTOROOM_API_KEY=your_key
# Watermarked tests:
# export PHOTOROOM_API_KEY=sandbox_your_key
# or: export PHOTOROOM_SANDBOX=1
```

Get a key at [app.photoroom.com/api](https://app.photoroom.com/api). Plus / Enterprise plan — Virtual Model and Virtual Try-On are Image Editing API features.

## CLI

```bash
# Shopper try-on
opentryon vton --model photoroom-vton \
  --person-image selfie.jpg \
  --garment-image dress.jpg \
  --pose standing \
  --scene studio

# Catalog: flat-lay → on-model (no shopper photo)
opentryon vton --model photoroom-virtual-model \
  --garment-image flatlay.jpg \
  --preset-model avery \
  --scene street \
  --pose standing \
  --dry-run
```

`--remove-background` is off by default so the generated scene is kept (`referenceBox=originalImage`). Optional `--prompt` (e.g. `street style`), `--scene-image`, and `--additional-product-images`.

Preset models include `avery`, `sam`, `taylor`, `kendall`, `jordan`, `jackson`, `ava`, and others listed in the [Virtual Model docs](https://docs.photoroom.com/image-editing-api-plus-plan/virtual-model). Output size default `PORTRAIT_HD_3_2`. 2K / 4K output is an Enterprise add-on on Photoroom’s side.

## Python

```python
from tryon.api import PhotoroomVTONAdapter

adapter = PhotoroomVTONAdapter()  # PHOTOROOM_API_KEY

worn = adapter.generate_and_decode(
    person="selfie.jpg",
    garment="dress.jpg",
    mode="try-on",
    pose="standing",
)
catalog = adapter.generate_virtual_model(
    garment="flatlay.jpg",
    preset_model="avery",
    scene="street",
)
```

## Planner / Studio

Name **`photoroom-vton`** or **Photoroom** to pin shopper try-on. Name **`photoroom-virtual-model`** for catalog on-model. After MCP restart, Connect lists **Photoroom** (`PHOTOROOM_API_KEY`). The VTON default stays `kling-ai`.
