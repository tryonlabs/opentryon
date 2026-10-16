---
sidebar_position: 22
title: Clad body (local)
description: ISO 8559-1 measurements from Anny or MHR parametric body JSON via clad-body
---

# Clad body (local)

When you already have **Anny** or **MHR** body parameters (for example from a Clad API `params` field or your own fitting pipeline), measure them locally with the Apache-2.0 [`clad-body`](https://github.com/datar-psa/clad-body) library.

Registry id: **`clad-body-local`** on `measure` (`extra="local"`).

## Install

```bash
pip install opentryon[local]
pip install 'clad-body[anny]'   # PyTorch + Anny
# or
pip install 'clad-body[mhr]'    # MHR / SAM 3D Body params file
```

## CLI

```bash
opentryon measure --model clad-body-local \
  --params path/to/anny_params.json \
  --preset core

opentryon measure --model clad-body-local \
  --params sam3d_params.json \
  --body-backend mhr \
  --only bust_cm waist_cm hip_cm
```

Presets: `core`, `standard`, `enhanced`, `fitted`, plus garment tags (`tops`, `bottoms`, …). See upstream [clad-body README](https://github.com/datar-psa/clad-body).

## Hosted twin

Photo or questionnaire sizing without running mesh code: **`clad-body-photo`** / **`clad-body-questionnaire`** ([API docs](../api-reference/clad-body.md), `CLAD_API_KEY`).

## MCP

`measure_clad_body_local`
