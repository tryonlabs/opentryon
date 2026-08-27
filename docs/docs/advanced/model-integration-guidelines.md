---
sidebar_position: 4
title: Model Integration Guidelines
description: Agent-facing spec for integrating first-party cloud APIs and local/open-weight models into OpenTryOn (CLI + MCP).
keywords:
  - contributing
  - new model
  - API integration
  - local models
  - Hugging Face
  - Ollama
  - LM Studio
  - Unsloth
  - agent guidelines
---

# Model Integration Guidelines

**Audience:** humans and coding agents adding a model to OpenTryOn.

**Canonical mechanical checklist:** [Adding a New Model Integration](./new-model-checklist.md)  
**Runtime defaults:** repo root `AGENTS.md` (local clone; that file is not published on GitHub)

This document is the **decision + architecture** layer. The checklist is the **file-by-file** layer. Do both.

---

## 1. Scope and defaults

OpenTryOn is the **canonical model registry** for TryOn Labs tooling:

- CLI (`opentryon`) and MCP tools are generated from `tryon/cli/registry.py`
- Adapters live under `tryon/api/` (hosted) or `tryon/models/` (local / self-hosted)
- Commercial product surfaces (`tryon-server`, agents) should call these adapters or a thin worker wrapping them — they should not invent a second client stack

### Default provider policy

| Preference | Rule |
|---|---|
| **First-party API** | Prefer the **model company’s own API** (BFL, Kling, Luma, Moonshot, Google, OpenAI, LTX, Ideogram, …). |
| **Third-party hosters** | Fal, Replicate, Segmind, Together, etc. are **opt-in only** when the user explicitly asks, or when no first-party API exists and self-host is impractical. |
| **Self-host / local** | Prefer when the user asks for open weights, GPU deployment, privacy, or COGS control. |

### Dual-path models

When a model exists both as open weights **and** as a hosted API:

1. Integrate **one path per request** (usually the one the user named).
2. Use **two registry ids** if both ship later, e.g. `ltx-2.5` (`extra="local"`) and `ltx-2.5-api` (`extra="core"`).
3. Never fold provider selection into a single adapter that mixes HTTP and GPU loading.

---

## 2. Decision tree (run this first)

```text
Is the request for a hosted HTTP API?
  YES → Path A: API integration (§3)
  NO  → Is it open-weight / local / self-deploy?
          YES → Path B: Local deployment (§4)
          BOTH requested → ship Path B and Path A as separate ModelSpecs
```

Before writing code, collect:

| Item | Why |
|---|---|
| Official docs URL + auth scheme | First-party source of truth |
| Exact model / version ids | Registry + CLI `--model-version` |
| Sync vs async (job + poll) | Adapter shape |
| Input/output modalities | Service bucket + `output_kind` |
| Env var names | `env.template` |
| License / gated HF / ARR clauses | Docs + legal gate |
| Min VRAM / disk (local) | Adapter heuristics + docs |
| Reference adapters in-repo | Copy patterns, don’t invent |

**Stop and ask the user** if docs conflict, the API is third-party-only, or VRAM requirements are unclear for the target machine.

---

## 3. Path A — API integration (first-party)

### 3.1 Where code lives

| Situation | Location |
|---|---|
| Existing vendor package | `tryon/api/<provider>/` (add class or file) |
| New vendor, multiple endpoints/models | New `tryon/api/<provider>/` package |
| New vendor, single service only | `tryon/api/<service>/` use-case dir (`vton`, `generate`, …) until it grows |
| Tiny single-file adapter | `tryon/api/<name>.py` (e.g. `veo.py`) |

Full placement rules: [new-model checklist §1](./new-model-checklist.md).

### 3.2 Adapter contract

- Constructor: `__init__(self, api_key: Optional[str] = None, ...)`, env fallback, `ValueError` if missing.
- Optional SDK missing → `ImportError` with install hint.
- Flexible media inputs: path, URL, `PIL.Image`, `bytes`, `BytesIO`.
- Method names (shared vocabulary):

  | Service | Methods |
  |---|---|
  | `generate` / `edit` | `generate_text_to_image`, `generate_image_edit`, `generate_multi_image` |
  | `vton` | `generate_and_decode` (or thin wrapper) |
  | `understand` | `understand` / `understand_image` / `understand_video` |
  | `video-generate` | `generate_text_to_video`, `generate_image_to_video` |
  | `bg-remove` | `remove_background` |

- Returns: images → `List[Image.Image]` (or bytes if needed); video → raw `bytes`; understand → `dict`.
- Module docstring: summary, official docs link, model ids, 1–2 examples.

### 3.3 Async job pattern (video / long gen)

Most first-party video APIs are submit → poll → download. Mirror existing adapters (`KlingVideoAdapter`, `SoraVideoAdapter`, Luma):

1. `POST` create job  
2. Poll status with timeout + interval kwargs  
3. Download result URL → `bytes`  
4. Surface clear errors (auth, moderation, quota, timeout)

Do **not** block forever; default timeouts should match peer adapters (often several minutes for video).

### 3.4 Auth patterns we already use

| Pattern | Examples | Notes |
|---|---|---|
| Bearer API key | BFL, many REST APIs | `Authorization: Bearer …` or provider-specific header |
| Dual key / JWT | Kling | Access + secret → signed token |
| Cloud IAM | AWS Nova | Access key / secret / region |
| OpenAI-compatible | Moonshot/Kimi, some local servers | Base URL + key; reuse OpenAI SDK carefully |

Prefer the vendor’s official SDK when it is maintained and lightweight; otherwise `requests` is fine.

### 3.5 Registry + MCP

Add `ModelSpec` under the correct service in `tryon/cli/registry.py`:

- `extra="core"` (default)
- `env_hint="PROVIDER_API_KEY"`
- `output_kind` set correctly
- Use `call_name="model"` when CLI `--model-version` must map to adapter `model=` (avoid `dest="model"` collision)

MCP tools appear automatically from the registry — **do not** hand-write per-model MCP wrappers.

### 3.6 Docs and config

- `env.template` + adapter page under `docs/docs/api-reference/`
- One-line CLI mention in `docs/docs/getting-started/cli.md`
- `docs/sidebars.ts`
- README only if a **new service category** appears
- `CHANGELOG.md` under Added

### 3.7 Reference implementations

| Kind | Look at |
|---|---|
| Sync image API | `tryon/api/nano_banana/`, `tryon/api/ideogram/` |
| VTON | `tryon/api/vton/flux_vto.py`, `tryon/api/kling_ai.py` |
| Video poll | `tryon/api/kling_video.py`, `tryon/api/openAI/video_adapter.py` |
| OpenAI-compatible chat/vision | `tryon/api/kimi/adapter.py` |

---

## 4. Path B — Local / self-hosted deployment

Local adapters run **on the user’s (or our) GPU**. They use `extra="local"` and `pip install opentryon[local]`.

### 4.1 Choose a local backend

Pick the **thinnest** backend that matches the model’s official recommendation:

| Backend | Use when | Typical stack | Adapter home |
|---|---|---|---|
| **Hugging Face Diffusers / Transformers** | Official HF weights, diffusion / VLM / video pipelines | `diffusers`, `transformers`, `accelerate`, `torch` | `tryon/models/<model>/` |
| **Ollama** | LLM / VLM already published as an Ollama model; want simple local HTTP | Ollama HTTP API (`localhost:11434`) | Prefer thin client under `tryon/models/` or `tryon/api/` if treated as local OpenAI-compat — document `OLLAMA_HOST` |
| **LM Studio** | User runs OpenAI-compatible local server | OpenAI SDK → `base_url` (e.g. `http://localhost:1234/v1`) | Same as OpenAI-compat local client; env for base URL + optional key |
| **Unsloth** | Fine-tune / optimized inference path the user explicitly wants | Unsloth + Transformers | Training or specialized local adapter; keep heavy deps in `LOCAL_INFERENCE_DEPS` / training extra |
| **ComfyUI / external process** | Only if vendor’s primary path is Comfy graphs and Diffusers is incomplete | Subprocess or HTTP to Comfy — **last resort**; prefer Diffusers/`ltx-pipelines` when available | Document clearly; avoid baking Comfy into core CLI |

**Default for open video/image weights:** Hugging Face Diffusers (or the vendor’s official PyTorch package), not ComfyUI.

### 4.2 Local adapter contract

Same method vocabulary and return types as Path A.

Additional rules:

- Constructor may take `model_id`, `model_path`, `device`, dtype, offload flags — **no API key required** unless HF gated (`HF_TOKEN`).
- Raise `ImportError` if `torch` / `diffusers` missing, pointing to `pip install opentryon[local]`.
- Implement **VRAM-aware defaults** when models are large (see `Flux2TurboAdapter`).
- Prefer `enable_model_cpu_offload()` / quantization over OOMing.
- Never import heavy local stacks from `tryon/api/__init__.py` (cloud stays lazy).
- Export from `tryon/models/__init__.py`.
- Add heavy deps only to `LOCAL_INFERENCE_DEPS` in `setup.py`.

### 4.3 Hugging Face specifics

1. Confirm repo id, gated access, and license (community / ARR / non-commercial).
2. Prefer official `from_pretrained` snippets from the model card.
3. If support is only on `diffusers` **main**, pin that in docs and optionally in local deps notes.
4. Env: `HF_TOKEN`, `MODEL_PATH` / vendor-specific path overrides in `env.template`.
5. Disk: document download size; exclude unused subfolders when documenting `hf download`.

### 4.4 Ollama specifics

1. Confirm model name (`ollama pull …`) and modality (text vs vision).
2. Call the local HTTP API; do not shell out to the `ollama` CLI for generation.
3. Env: `OLLAMA_HOST` (default `http://127.0.0.1:11434`).
4. Fail with a clear message if the daemon is down.
5. Register under `understand` (or chat) unless the model is image/video generative.

### 4.5 LM Studio specifics

1. Treat as **OpenAI-compatible** local server.
2. Env: `LM_STUDIO_BASE_URL` (or generic `OPENAI_BASE_URL`) + optional key.
3. Reuse patterns from OpenAI / Kimi adapters; do not assume cloud OpenAI URLs.
4. Document that the user must load the model in LM Studio before calling the CLI.

### 4.6 Unsloth specifics

1. Use for **training / accelerated local inference** when requested — not the default for every HF model.
2. Keep Unsloth behind the `local` or `training` extra.
3. If the runtime path is still Transformers after training, prefer a normal HF local adapter for inference and document Unsloth only in training docs.

### 4.7 Self-deployed GPU worker (product later)

In-process CLI adapters are enough for OpenTryOn. For Playground / tryon-server:

1. Wrap the **same** `tryon.models` adapter in a small job HTTP service (submit / status / download).
2. Do not load 10B+ models inside the Django web process.
3. Meter credits only at the product layer — OpenTryOn itself stays unmetered.

### 4.8 Reference implementations

| Kind | Look at |
|---|---|
| Local diffusion image | `tryon/models/flux2_turbo/` |
| Local VLM | `tryon/models/kimi_vl/` |
| Local VTON weights | `tryon/models/ootdiffusion/` (if present) |

---

## 5. Service and `output_kind` mapping

| Capability | Registry service | Typical `output_kind` |
|---|---|---|
| Virtual try-on | `vton` | `images` |
| Text/image → image | `generate` | `images` |
| Image edit | `edit` | `images` |
| Caption / VLM / LLM | `understand` | `text` |
| Text/image → video | `video-generate` | `video_bytes` |
| Background remove | `bg-remove` | `images` |

New category only if none of the above fit — adding a service is a product decision, not a drive-by.

---

## 6. Product surfaces (out of OpenTryOn scope unless asked)

| Surface | When to touch |
|---|---|
| OpenTryOn CLI / MCP | **Always** for model integrations |
| TryOn Studio `services.ts` | Optional mirror so the local UI lists the model |
| tryon-server | Only when productizing with auth/credits |
| tryon-agent-backend | Only when an agent tool should call the model |
| Third-party marketplace publish | Separate Efficio / packaging track — not this guidelines doc |

---

## 7. Pre-merge verification

Run from the `opentryon` conda env:

```bash
conda run -n opentryon python -c "from tryon.cli.registry import validate_registry; validate_registry()"
conda run -n opentryon python -m tryon.cli.main <service> --model <id> --help
conda run -n opentryon python -m tryon.cli.main <service> --model <id> ... --dry-run
conda run -n opentryon python tests/test_cli.py
conda run -n opentryon python -m py_compile <changed files>
```

For Path A with a key present: optional live smoke (skip cleanly if env unset).  
For Path B: dry-run always; live GPU smoke only on a machine with enough VRAM.

---

## 8. Agent execution playbook

When the user says “integrate model X”:

1. **Classify** Path A / Path B / both (this doc §2).
2. **Prefer first-party API** for Path A; do not add Fal/Replicate unless asked.
3. **Read** official docs + 1–2 closest in-repo adapters.
4. **Implement** adapter → export → `setup.py` / `env.template` → `registry.py` → tests → docs (checklist).
5. **Do not** hand-add MCP tools or rewrite tryon-server unless requested.
6. **Document** license, env vars, and hardware needs honestly.
7. **Stop** and ask if the model card requires agreeing to terms, paid commercial license above an ARR threshold, or unclear auth.

---

## 9. Related docs

- [New model checklist](./new-model-checklist.md) — file touch list  
- [Local models overview](../local-models/overview.md)  
- [CLI guide](../getting-started/cli.md)  
- [Configuration / env](../getting-started/configuration.md)  
- [API reference overview](../api-reference/overview.md)  
