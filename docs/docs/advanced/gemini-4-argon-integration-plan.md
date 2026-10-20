---
sidebar_position: 2
title: Gemini 4 Argon — integration plan
description: Integration plan and phase notes for Google Gemini 4 Argon in OpenTryOn (shipped on understand).
keywords:
  - Gemini 4 Argon
  - gemini-4-argon
  - integration plan
  - Google Gemini API
  - understand
---

# Gemini 4 Argon — integration plan

**Status:** Shipped — registry id `gemini-4-argon` on `understand` (P1–P3: multimodal, agentic video, long decode + background Interactions).  
**Last reviewed against Google docs:** 2026-10-20 (UTC).  
**Owner workflow:** [Model integration guidelines](./model-integration-guidelines.md) → [New model checklist](./new-model-checklist.md) → `/integrate-model`.

---

## 1. What “Gemini 4 Argon” is (public catalog, Oct 2026)

Google’s [Models](https://ai.google.dev/gemini-api/docs/models) page lists **one** stable id under **“All Gemini 4 models”**:

| Model id | Role | API surface (primary) |
|---|---|---|
| `gemini-4-argon` | Flagship **reasoning** multimodal model | `generateContent` (Gemini API / `google-genai`) |

There is **no** separate public `gemini-4-flash` (or other Gemini 4 chat sku) in that catalog today. When we say “Gemini 4 family” for OpenTryOn, we mean **one model id** with **many optional API capabilities**, not a matrix of sibling endpoints like Nano Banana / Omni / TTS.

**Official references (read before coding):**

- [Gemini 4 Argon model card](https://ai.google.dev/gemini-api/docs/models/gemini-4-argon)
- [What’s new / migration (generateContent)](https://ai.google.dev/gemini-api/docs/generate-content/latest-model)
- [Long decode (Interactions API)](https://ai.google.dev/gemini-api/docs/long-decode)
- [Background execution](https://ai.google.dev/gemini-api/docs/background-execution)
- [Agentic video understanding](https://ai.google.dev/gemini-api/docs/generate-content/video-understanding)
- Gemini API OpenAPI — see Google’s published spec under [ai.google.dev](https://ai.google.dev) (host `generativelanguage.googleapis.com`)

**Auth:** Path A only — same **`GEMINI_API_KEY`** as existing Gemini integrations (`gemini-3.8-flash`, Nano Banana, Veo, Omni, embeddings). No open weights.

**Billing note:** Argon is **not on the free tier**; introductory pricing through 2026-11-30 is documented on the migration page.

---

## 2. Capability map → OpenTryOn services

Argon is **text-out** for generation; it does **not** replace image/video **generate** models in our registry.

| Upstream capability | Inputs | OpenTryOn fit | Proposed phase |
|---|---|---|---|
| Multimodal **understanding** (text, image, video, audio, PDF) | Same as `gemini-3.8-flash` | **`understand`** | **P1 — MVP** |
| **Thinking** (`low` / `medium` / `high`, default `medium`) | Prompt + media | **`understand`** (`--thinking-level`) | P1 |
| **Agentic video** (`media_processing=agentic`) | Video + prompt | **`understand`** (new flag) | **P2** |
| **Long decode** (>64K thinking+output, up to ~1M − input) | Text/media + high `max_output_tokens` | **`understand`** (extended `--max-tokens` + SDK continuation) | **P2** |
| **Interactions API** + `background: true` + `store: true` | Long jobs, poll/stream | Optional **`understand`** long-running mode or separate **`generate`**-like job CLI | **P3** |
| Function calling, structured outputs, URL context, search/maps grounding | Agent payloads | Planner / future agent tools — **not** core CLI vocabulary today | P4+ |
| Code execution, computer use (preview), file search | Sandboxed tools | **Out of scope** unless product asks for a new `agent-run` service | — |
| Batch / Flex / Priority inference | Billing modes | Optional registry flags later | P4+ |
| Live API, image generation, TTS | Other model ids | **Not Argon** — keep `gemini-3.8-flash-tts`, Nano Banana, Omni, etc. | — |
| Managed agents (Antigravity, Deep Research) | Separate product | **Out of scope** for OpenTryOn registry | — |

**Fashion / TryOn relevance (understand path):**

- Garment and look **attribute extraction** from photos (same as 3.8 Flash).
- **Runway / lookbook video** QA and summarization — Argon targets harder, longer reasoning; agentic video helps long clips.
- **PDF** size charts, care labels, vendor spec sheets.
- **Audio** briefs (voice notes) → structured merchandising copy.
- **Not** a replacement for `decide` models (Jev, Mercury Decide, d3) unless we add a separate “use LLM to classify” workflow — Argon is generative understanding, not System One.

---

## 3. Relationship to existing `gemini-3.8-flash`

OpenTryOn already ships:

- Adapter: `GeminiUnderstandAdapter` (`tryon/api/gemini/understand.py`)
- Registry: `understand --model gemini-3.8-flash`
- Docs: [Gemini 3.8 Flash](../api-reference/gemini-3-8.md)

**Recommendation:** Add a **second registry id** `gemini-4-argon` on the **same adapter class**, mirroring how other vendors expose multiple model ids on one client (e.g. Inception `mercury-3` vs chat variants).

| | `gemini-3.8-flash` | `gemini-4-argon` |
|---|---|---|
| Positioning | Fast, capable Flash; default multimodal workhorse | Flagship reasoning; hard agentic / coding / science |
| Context | 1M input; 65,536 max output (today’s adapter cap) | **Unified 1M** shared by input + thinking + output |
| Default thinking | API default if omitted | **`medium`** (document in CLI help) |
| Max output (simple call) | ≤ 65,536 (current validation) | Default 64K stream / 32K non-stream REST hop; **long decode** beyond |
| Explicit context cache | Supported upstream for 3.x | **Not supported** — implicit cache only |
| Sampling (`temperature`, etc.) | N/A in our adapter | **Ignored upstream** — do not add CLI flags |
| Cost | Flash pricing | Higher; paid tier only |

Keep **both** ids indefinitely: planner and docs should steer “fast/cheap multimodal” → 3.8 Flash, “hard reasoning / long output” → Argon.

---

## 4. API / SDK design (implementation notes)

### 4.1 Path A stack

- **SDK:** `google-genai` — bump repo pin from `>=1.52.0` to **`>=2.30.1`** (Python) per [migration guide](https://ai.google.dev/gemini-api/docs/generate-content/latest-model).
- **Client:** Reuse `genai.Client(api_key=GEMINI_API_KEY)`.
- **Method:** Extend `understand()` → `client.models.generate_content(model="gemini-4-argon", ...)`.

### 4.2 Config differences vs 3.8 (must implement in adapter branches)

| Topic | 3.8 Flash (current) | 4 Argon (planned) |
|---|---|---|
| `max_output_tokens` | Hard cap **65,536** in adapter | Allow **≥ 32,768** defaults; support **> 65,536** via SDK `automatic_continuation=True` (default in 2.30.1+) |
| Non-stream REST hop | 65,536 | **32,768** per hop — document for anyone using raw REST |
| `thinking_config` | `ThinkingConfig(thinking_level=...)` | Same enum `low` / `medium` / `high` |
| `thinking_budget` | Not exposed | **Do not add**; deprecated with warning upstream |
| Timeouts | Implicit / short | **≥ 20 minutes** HTTP timeout for long decode |
| Thought signatures | N/A today | Required for future multi-turn tool flows — preserve in agent work, not P1 CLI |
| Agentic video | Not exposed | Optional `media_processing` on video `Part` (`static` default, `agentic` opt-in) |

### 4.3 Long decode — two integration options

| Approach | When | OpenTryOn behavior |
|---|---|---|
| **A. generateContent + SDK continuation** (preferred P2) | `max_output_tokens` > 65,536, standard CLI | Single `understand()` call; SDK stitches hops; increase timeout |
| **B. Interactions API** (`POST /v1beta/interactions`, `background: true`, `store: true`) | Very long jobs, streaming progress, 24h wall clock | New code path: create → poll → join `model_output` steps; heavier CLI/MCP surface |

Start with **A**; add **B** only if users need background jobs without holding a client open.

### 4.4 Media handling

Reuse existing `_part()` / Files API / YouTube URL behavior from `understand.py`.

**P2 add-ons:**

- `--video-processing static|agentic` (default `static`) on video parts only.
- Optional `--media-resolution` if we expose [media resolution](https://ai.google.dev/gemini-api/docs/generate-content/media-resolution) (low token use on long video).

---

## 5. Registry & product wiring (checklist preview)

When implementation starts, touch (in order):

1. **`tryon/api/gemini/understand.py`** — `VALID_MODELS`, model-specific limits, agentic video, long decode.
2. **`tryon/cli/registry.py`** — new `ModelSpec` `gemini-4-argon` on `understand` (`env_hint=GEMINI_API_KEY`).
3. **`tryon/api/__init__.py`** — no change if class name unchanged.
4. **`tryon/agents/planner/bind.py`** — needles: `gemini 4 argon`, `gemini-4-argon`, `gemini 4` (careful ordering vs `gemini 3`).
5. **`mcp-server/config.py`** — extend `gemini` provider blurb (understand argon + long decode note).
6. **`docs/docs/api-reference/gemini-4-argon.md`** — user-facing reference (split from 3.8 page).
7. **`docs/docs/api-reference/gemini-3-8.md`** — cross-link “when to use Argon”.
8. **`tests/test_cli.py`** — dry-run + validation tests (max_tokens bounds, agentic flag).
9. **`requirements.txt`** — `google-genai>=2.30.1`.
10. **`env.template`** — no new env var.

**Registry id:** `gemini-4-argon` (stable id string matches Google).

**CLI flags (MVP = parity with 3.8):**

- `--image`, `--video`, `--audio`, `--pdf`, `--prompt`, `--system`
- `--thinking-level low|medium|high` (document default `medium` for Argon)
- `--max-tokens` — raise validation ceiling for Argon (see phase table below)

**Do not** add per-model MCP tools — registry-generated `understand_gemini_4_argon` only.

---

## 6. Phased delivery

| Phase | Scope | Exit criteria |
|---|---|---|
| **P0** | This document + queue entry | Reviewed; SDK pin decision accepted |
| **P1 — MVP** | `understand --model gemini-4-argon` with same media matrix as 3.8; thinking levels; `max_tokens` up to **65,536**; docs + tests + planner | `validate_registry()`, dry-run, mocked genai test optional |
| **P2 — Argon differentiators** | `--max-tokens` > 65536 with SDK continuation; `--video-processing agentic`; 20m timeout; default max_output 65536 in config | Long video fixture test (dry-run flags only if no key) |
| **P3 — Interactions / background** | Optional `--background` long job mode via Interactions API | Poll + cancel documented; gated on key |
| **P4 — Agent extras** | Structured output / tools for internal agents | Only if planner or Studio needs them |

Implement **one phase per PR** to keep review size manageable.

---

## 7. Testing strategy

- **Registry:** `validate_registry()` after `ModelSpec` addition.
- **CLI dry-run:** Assert `GeminiUnderstandAdapter` + `model='gemini-4-argon'` + media kwargs (copy `check_gemini_38_understand_and_tts` pattern).
- **Validation unit tests:** Argon rejects `max_tokens` &lt; 32768 only if we enforce migration minimum; agentic without video; thinking_level enum.
- **Live tests:** Gate on `GEMINI_API_KEY`; smoke: short image prompt; optional long `--max-tokens 131072` on text-only prompt.
- **No live test** for Interactions until P3.

---

## 8. Risks, open questions, out of scope

### Risks

| Risk | Mitigation |
|---|---|
| SDK pin forces downstream conda/env churn | Document in PR; run `mcp-server/test_server.py` + understand tests |
| Long decode cost / run time | Default `--max-tokens` 65536; document pricing; warn in registry `notes` |
| Empty text mid-decode (`continuation_token` only thinking) | Document in user-facing doc; rely on SDK continuation |
| `total_input_tokens` billing confusion on multi-hop | Link Google “count tokens” section in doc |
| User expects “Gemini 4” image/video **generation** | Clarify in doc: use Nano Banana / Omni / Veo ids |

### Open questions (resolve before P2)

1. Will Google add more Gemini 4 model ids (e.g. Flash)? If yes, extend `VALID_MODELS` + registry choices — watch [Models page](https://ai.google.dev/gemini-api/docs/models).
2. **Vertex AI** / enterprise endpoints — out of scope unless we add `GOOGLE_CLOUD_PROJECT` style dual path (not requested).
3. Should planner map generic **“gemini 4”** → `gemini-4-argon` while **“gemini flash”** stays on 3.8?
4. Expose **streaming** to CLI stdout for long video agentic runs, or keep buffered `response.text` only in P1?

### Explicitly out of scope (v1)

- Computer use, code execution, file search, Deep Research, Antigravity
- Replacing `gemini-3.8-flash` as default multimodal model
- Local / open-weight Path B (none published)
- Third-party hosters (Fal/Replicate) for Argon

---

## 9. Suggested queue entry (integrate-next)

When P1 starts, add to [Integrate next](../community/integrate-next.md):

- **Gemini 4 Argon** — `understand` / Path A / `GEMINI_API_KEY` / P1 MVP then P2 agentic + long decode.

---

## 10. Summary recommendation

**Integrate Gemini 4 Argon as a new `understand` registry id** on the existing **`GeminiUnderstandAdapter`**, Path A only, with a **phased rollout**: multimodal parity first (P1), then Argon-specific video agentic mode and long decode (P2), then Interactions background jobs only if needed (P3). Treat “multiple capabilities” as **feature flags and API modes**, not separate OpenTryOn adapters, until Google ships additional Gemini 4 model ids.
