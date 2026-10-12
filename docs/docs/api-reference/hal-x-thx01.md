---
title: HAL-X THX-01 (decision model)
description: Hosted and local THX-01 calibrated decision model (System One compatible).
---

# HAL-X THX-01

[THX-01](https://huggingface.co/doofz/THX-01) is HAL-X’s 322M-parameter Apache-2.0 **decision** model (not a text generator). It answers typed questions about a **state** (message, ticket, document, or JSON) in one forward pass with calibrated probabilities.

## Hosted API (Path A)

- Docs: https://api.hal-x.ai/docs/thx-01/
- Registry id: `thx-01` on the `decide` service
- Env: `HALX_API_KEY` (HAL-X console; grant `/v1/systemone` for model `thx-01`)
- Endpoint: `POST https://api.hal-x.ai/v1/systemone` (TypeSafe/Jev-compatible for `choice`, `noul`, `score`; THX also supports `number`, `excerpt`, and `"cite": true`)

```bash
opentryon decide --model thx-01 \
  --state "My card was charged twice" \
  --questions '{"team":{"type":"choice","instructions":"Which team?","criteria":{"billing":"billing","tech":"technical"}}}' \
  --dry-run
```

## Local weights (Path B)

- Weights: https://huggingface.co/doofz/THX-01
- Package: `pip install thx01` (included in `opentryon[local]`)
- Registry id: `thx-01-local`

```bash
opentryon decide --model thx-01-local \
  --state "My card was charged twice" \
  --questions '{"urgent":{"type":"noul","instructions":"Needs help today?"}}'
```

## Related

- Typesafe Jev (`decide jev`, `TYPESAFE_API_KEY`) — another System One provider
- Blog: [THX-01 open source announcement](https://huggingface.co/blog/doofz/thx-01-we-open-sourced-a-322m-decision-model-that)
