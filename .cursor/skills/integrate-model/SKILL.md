---
name: integrate-model
description: Integrates a hosted API or local/open-weight model end-to-end across OpenTryOn (adapter, CLI registry, MCP, docs) and TryOn Studio (catalog, Connect keys, planner). Use when adding a new model, integrating an API, wiring a local Diffusers/Transformers/Ollama model, updating MCP after a registry change, reflecting a new model in Studio UI, or when the user asks what to integrate next / Nemotron / NVIDIA NIM / the integrate-next list.
---

# Integrate a model (OpenTryOn + Studio)

OpenTryOn is the **canonical registry**. Studio is an **MCP client only**. Do not invent a second adapter stack in Studio, tryon-server, or other repos.

Read these first, in order:

1. Decision + architecture: `docs/docs/advanced/model-integration-guidelines.md`
2. File-by-file checklist: `docs/docs/advanced/new-model-checklist.md`
3. This skill’s [checklist.md](checklist.md) and [studio.md](studio.md)
4. If the user has not named a model, pick from the living queue: [integrate-next.md](integrate-next.md) → `docs/docs/community/integrate-next.md`

Runtime defaults: repo-root `AGENTS.md` (conda env `opentryon`).

## Decision tree (do this before writing code)

```text
Hosted HTTP API?     → Path A (tryon/api/)
Open-weight / local? → Path B (tryon/models/)
Both requested?      → two registry ids, two adapters (never mix HTTP + GPU in one class)
```

| Preference | Rule |
|---|---|
| First-party API | Prefer the vendor’s own API |
| Third-party hosters | Fal, Replicate, Segmind, Together — only if the user asks, or no first-party API exists |
| Dual-path | Separate ids, e.g. `ltx-2.5` (`extra="local"`) and `ltx-2.5-api` |

Stop and ask if official docs conflict, the only API is a third-party hoster, or local VRAM is unclear.

Collect before coding: official docs URL, auth, exact model ids, sync vs poll, modalities, env var names, license, reference adapter in-repo.

## Path A vs Path B (short)

| | Path A (API) | Path B (local) |
|---|---|---|
| Code | `tryon/api/<provider>/` (or use-case dir / single file) | `tryon/models/<model>/` |
| Extra | `core` (default) | `extra="local"` |
| Env | `env_hint="PROVIDER_API_KEY"` | omit `env_hint` |
| Import | `_LAZY_ATTRS` in `tryon/api/__init__.py` | eager import in `tryon/models/__init__.py` |
| Docs page | `docs/docs/api-reference/<name>.md` | `docs/docs/local-models/<name>.md` |

Same class under multiple `ModelSpec`s (generate + edit + vton) beats duplicating adapter files.

## Integration order

Do **not** skip docs, MCP, or Studio. Work in this order:

1. **Read vendor docs** and pick Path A / B / both.
2. **Adapter** with the shared method vocabulary (`generate_text_to_image`, `generate_image_edit`, `generate_and_decode`, `understand`, `generate_text_to_video` / `generate_image_to_video`). Flexible media inputs. Env-fallback constructor.
3. **Registry first for wiring:** `tryon/cli/registry.py` `ModelSpec` (never `dest="model"`; use `call_name="model"` for version flags).
4. **MCP:** tools are generated from the registry. Do **not** hand-write per-model MCP wrappers. If a **new provider key** appears, add it to `mcp-server/config.py` `_PROVIDER_CATALOG` (label, docs URL, notes). Unlock list comes from `env_hint`.
5. **Planner needles** in `tryon/agents/planner/bind.py` — longer names **before** shorter ones (`p-image-ideogram` before `ideogram`).
6. **Tests + docs** — see [checklist.md](checklist.md).
7. **Studio** — see [studio.md](studio.md). Catalog is live MCP; restart MCP or the new model is invisible.
8. **Verify** with the commands below. Do not commit unless asked. Docs site deploy is `cd docs && npm run deploy` only when the user asks to publish.

## Verify

```bash
conda run -n opentryon python -c "from tryon.cli.registry import validate_registry; validate_registry()"
conda run -n opentryon python -m tryon.cli.main <service> --model <id> --help
conda run -n opentryon python -m tryon.cli.main <service> --model <id> ... --dry-run
conda run -n opentryon python tests/test_cli.py
conda run -n opentryon python mcp-server/test_server.py
conda run -n opentryon python -m py_compile <changed python files>
```

Skip live API calls unless a key is present; gate them on the env var.

## Do not

- Parallel client in Studio / tryon-server
- Per-model MCP tool wrappers
- Full tutorials in root `README.md` (front door only; details in `docs/`)
- Fork per-service Studio playgrounds
- Store API keys in Studio (`studio.db`, cookies, localStorage)
- Force-push or commit unless the user asks
