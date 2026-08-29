# File-by-file checklist

Canonical long form: `docs/docs/advanced/new-model-checklist.md`. Use this as the agent’s working list.

## OpenTryOn code

- [ ] Adapter (`tryon/api/<provider>/` or `tryon/models/<model>/`)
- [ ] Subpackage `__init__.py` export
- [ ] `_LAZY_ATTRS` (cloud) or `tryon/models/__init__.py` (local)
- [ ] `setup.py` — light SDK in `install_requires`; torch/diffusers in `LOCAL_INFERENCE_DEPS`
- [ ] `tryon/cli/registry.py` `ModelSpec` + `Arg`s (`call_name` if adapter wants `model=`)
- [ ] `tryon/agents/planner/bind.py` aliases (longest needle first)
- [ ] `mcp-server/config.py` `_PROVIDER_CATALOG` only if a **new** env var / provider
- [ ] `env.template` — key, where to get it, which CLI models need it

## Tests

- [ ] `tests/test_cli.py` dry-run (and aliases / validation if non-obvious)
- [ ] `mcp-server/test_server.py` — tool exists, dry-run, unlocks if new key
- [ ] `tests/test_planner_agent.py` — named-model pin if the id could collide (e.g. `ideogram` vs `p-image-ideogram`)

## Documentation (OpenTryOn)

Root `README.md` is a short front door (~150–250 lines). No full API tutorials or long `.env` dumps there.

- [ ] `docs/docs/getting-started/cli.md` — service table + one example
- [ ] New page: `docs/docs/api-reference/<name>.md` **or** `docs/docs/local-models/<name>.md`
- [ ] `docs/sidebars.ts`
- [ ] `docs/docs/api-reference/overview.md` or `docs/docs/local-models/overview.md`
- [ ] `docs/docs/intro.md` if the model adds a capability/category
- [ ] `docs/docs/getting-started/mcp.md` + `mcp-server/README.md` if the visible tool list changes
- [ ] `docs/docs/getting-started/configuration.md` if a new env var appears
- [ ] `docs/docs/agents/planner-agent.md` if naming/defaults change
- [ ] Related provider page (e.g. distinguish Ideogram 4.0 vs P-Image-Ideogram)
- [ ] `CHANGELOG.md` under Unreleased / Added
- [ ] `AGENTS.md` verified model/tool counts after tests pass
- [ ] `openapi/` / `postman/` only if we snapshot that upstream HTTP API
- [ ] README service table: **one line** only if a new **service category** or notable highlight

Publish GitHub Pages only when asked: `cd docs && npm run deploy`.

## Sibling repos

- [ ] TryOn Studio — [studio.md](studio.md)
- [ ] Other product READMEs only if the user asks (do not invent adapters there)
