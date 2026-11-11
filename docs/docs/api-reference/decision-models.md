---
sidebar_position: 31
title: Open Decision Models (Decider, Clef, Kev, JEV)
description: Perplexity Decider, Cloudflare Clef, Jared Palmer's Kev and AutoTrust JEV on the decide service, hosted and self-hosted.
keywords:
  - decision model
  - System One
  - Perplexity Decider
  - Cloudflare Clef
  - Kev
  - AutoTrust JEV
  - calibrated probabilities
---

# Open Decision Models: Decider, Clef, Kev, JEV

"System One" decision models don't write text. You send a **state** (text, JSON, sometimes images) and named, typed **questions**, and get calibrated answers back in one forward pass. They all use the same question schema as [Typesafe Jev](typesafe-jev):

```json
{
  "formal":   {"type": "noul",   "instructions": "Is this formal wear?"},
  "category": {"type": "choice", "instructions": "Garment category?",
               "criteria": {"dress": "one-piece gowns", "top": "shirts and blouses"}},
  "fit":      {"type": "score",  "instructions": "How fitted is it?",
               "criteria": ["loose", "regular", "slim"]}
}
```

Answers come back as `{"model", "answers", "usage"}`: `noul` gives P(yes), `choice` gives the pick plus `probabilities` and `confidence`, and `score` gives a probability-weighted level with a `legend`.

## At a glance

| Registry id | Model | Hosting | Images | Needs |
|---|---|---|---|---|
| `pplx-decider` | Perplexity Decider v1.2 (27B) / Flash v1.2 (4B) | Perplexity Decisions API (first-party) | up to 8 | `PERPLEXITY_API_KEY` |
| `pplx-decider-local` | `perplexity-ai/pplx-decider-v1.1-27b` | your SGLang server | up to 8 | 80 GB-class GPU |
| `clef` | Cloudflare Clef (27B) / Clef-flash (9B) | Workers AI (first-party) | up to 4 | `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID` |
| `clef-local` | `Cloudflare/clef` | your SGLang server | up to 4 | 80 GB+ GPU (tested on H200) |
| `kev-openrouter` | Kev 4B | OpenRouter (third-party; Kev has no first-party API) | no | `OPENROUTER_API_KEY` |
| `kev-local` | Kev 0.8B / 4B / 9B / 27B | the Kev repo's `kev.serve` | no | 4 GB GPU (0.8B) to 80 GB (27B); MLX on Apple Silicon |
| `autotrust-jev-local` | AutoTrust JEV-35B / JEV-35B-NVFP4 / JEV-27B-VL | your vLLM `serve.sh` (no hosted API exists) | up to 8 | 32 GB (NVFP4) to 80 GB GPU |

All four model families publish Apache-2.0 weights. Vendor benchmarks are self-reported.

## Perplexity Decider

Decider replaces Qwen3.8-27B's language head with a 255-way answer-code readout, with non-causal attention in its full-attention layers.

```bash
export PERPLEXITY_API_KEY=...
opentryon decide --model pplx-decider --questions questions.json --state "Red satin evening gown, floor length"
opentryon decide --model pplx-decider --decider-model pplx-decider-flash-v1.2 --questions questions.json --image dress.jpg
opentryon decide --model pplx-decider --questions questions.json --state "Is this brand in stock at Nordstrom?" --web-grounding
```

- Endpoint: `POST https://api.perplexity.ai/v1/decisions`. Up to 255 options per `choice`, 10 levels per `score`.
- Images go inside `state` as data-URL parts (PNG, JPEG, WebP). Remote image URLs are downloaded and inlined, because the API rejects them.
- `--web-grounding` lets Decider search the web first; searches are billed separately. `--max-staleness` sets the oldest cached result it may use, in seconds.

**Self-hosted:** serve the open weights with a nightly SGLang build, then point OpenTryOn at it.

```bash
export PPLX_DECIDER_BASE_URL=http://127.0.0.1:30000   # default
opentryon decide --model pplx-decider-local --questions questions.json --state "..." --image dress.jpg
```

## Cloudflare Clef

Clef adds a joint schema head on a frozen Qwen backbone. The head routes evidence between the state, the questions and their options and scores the whole schema together.

```bash
export CLOUDFLARE_API_TOKEN=...      # a Workers AI API token
export CLOUDFLARE_ACCOUNT_ID=...
opentryon decide --model clef --questions questions.json --state "..." --image look.jpg
opentryon decide --model clef --clef-model clef-flash --questions questions.json --state "..."
```

| | `clef` | `clef-flash` |
|---|---|---|
| Size | 27B (Qwen3.8-27B) | 9B (Qwen3.5-9B) |
| Context | 65,536 tokens | 24,576 tokens |
| Input price | $0.24 per M tokens | $0.038 per M tokens |

Up to 64 questions and 4 images (PNG, JPEG, WebP; 4 MiB each) per request. Output tokens are free and Cloudflare lists zero data retention. Prices are Cloudflare's published rates at the time of writing.

**Self-hosted:** run Cloudflare's SGLang image (`lmsysorg/sglang:dev-clef`, `sglang serve --model-path Cloudflare/clef --port 30000`), then use `--model clef-local` (`CLEF_BASE_URL`, default `http://127.0.0.1:30000`).

## Kev (Jared Palmer)

Kev is a LoRA plus a small pointer head on Qwen base models. The pointer head scores each option against the question while the state's computation is shared across questions. Kev has no first-party API.

```bash
# Hosted, through OpenRouter's System One endpoint (Kev 4B, 8K context)
export OPENROUTER_API_KEY=...
opentryon decide --model kev-openrouter --questions questions.json --state "Customer was charged twice for order 1182"

# Self-hosted, any size, with the Kev repo's server
git clone https://github.com/jaredpalmer/kev.git && cd kev && uv sync --extra serve
uv run --extra serve python -m kev.serve --run jaredpalmer/kev-4b --port 8008
opentryon decide --model kev-local --questions questions.json --state "..."
```

Kev is text-only: pass image descriptions or product data as the state. `KEV_API_KEY` is only needed if you set one on your server.

## AutoTrust JEV

AutoTrust's JEV builds open System One models around a learned decision block (a LoRA plus decision head) on a frozen Qwen backbone, and it reads images. It is a separate company and model from Typesafe's Jev (`--model jev`).

AutoTrust runs no hosted API and no third-party host serves JEV, so `autotrust-jev-local` talks to the server you start yourself:

```bash
hf download autotrust/JEV-35B --local-dir JEV-35B     # or autotrust/JEV-35B-NVFP4 for a 32 GB GPU
bash JEV-35B/serve.sh                                 # vLLM + POST /v1/decide on :8000
opentryon decide --model autotrust-jev-local --questions questions.json --state "..." --image look.jpg
```

JEV's `/v1/decide` answers one question per request, so OpenTryOn sends one request per question and maps the replies onto the shared answer shape:

- `noul`: the server scores `false` and `true`; the answer is P(true).
- `choice`: criteria keys become the options, and their descriptions are added to the question.
- `score`: JEV's native score is a fixed 0–5 scale, so your ordered levels are asked as a choice over the levels, and `score` is the probability-weighted level index.

## Python

```python
from tryon.api.perplexity import PerplexityDeciderAdapter
from tryon.api.cloudflare import ClefAdapter
from tryon.api.systemone import SystemOneAdapter
from tryon.api.autotrust import AutoTrustJevAdapter

questions = {"formal": {"type": "noul", "instructions": "Is this formal wear?"}}

PerplexityDeciderAdapter().decide(questions, state="Red satin gown", image=["gown.jpg"])
ClefAdapter(model="clef-flash").decide(questions, state="Red satin gown")
SystemOneAdapter(preset="kev-local").decide(questions, state="Red satin gown")
AutoTrustJevAdapter().decide(questions, state="Red satin gown")
```

`SystemOneAdapter` works with any server that speaks the `/v1/systemone` contract. Presets: `kev-openrouter`, `kev-local`, `clef-local` and `pplx-decider-local`.

## Already integrated

Three other decision models from the same wave were already in the `decide` service: [Typesafe Jev](typesafe-jev) (`jev`), [Liquid AI d1](../local-models/liquid-d1.md) (`d1-3b`, `d1-omni-600m`) and the vLLM Semantic Router D3 family (`d3-turbo` to `d3-edge`, hosted and local).

## Sources

- [Perplexity Decisions API](https://docs.perplexity.ai/docs/decisions/quickstart) · [pplx-decider-v1.1-27b](https://huggingface.co/perplexity-ai/pplx-decider-v1.1-27b)
- [Workers AI: Clef](https://developers.cloudflare.com/workers-ai/models/clef/) · [Cloudflare/clef](https://huggingface.co/Cloudflare/clef)
- [jaredpalmer/kev-4b](https://huggingface.co/jaredpalmer/kev-4b) · [OpenRouter System One](https://openrouter.ai/docs/guides/community/typesafe-sdk)
- [autotrust/JEV-35B](https://huggingface.co/autotrust/JEV-35B) · [autotrust/JEV-27B-VL](https://huggingface.co/autotrust/JEV-27B-VL)
