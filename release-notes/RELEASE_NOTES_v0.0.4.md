# OpenTryOn v0.0.4 Release Notes

## More video APIs, dual-path local models, and Qwen3.8 understanding

**Release Date**: 17 August 2026

OpenTryOn v0.0.4 expands the invoke layer shipped in v0.0.3 with new first-party video providers, dual-path (API + local) models, Qwen3.8 multimodal understanding, and clearer agent-facing integration docs. Same CLI / MCP / registry surface — more models show up automatically.

## What's New

### Video providers

| Model | Path | CLI |
|---|---|---|
| **LTX-2.5** | Official API + local Diffusers | `ltx-2.5-api` / `ltx-2.5` |
| **MiniMax Hailuo 2.3** | Official API only | `hailuo-2.3` |
| **Alibaba Wan** | DashScope API + local Wan 2.2 Diffusers | `wan-api` / `wan-2.2` |
| **Runway Gen-4.5** | Official API only | `runway-gen4.5` |

### Understanding — Qwen3.8

| Model | Path | CLI |
|---|---|---|
| **Qwen3.8-Max** | DashScope OpenAI-compatible | `qwen3.8-max` |
| **Qwen3.8-27B** | Local Transformers (`Qwen/Qwen3.8-27B`) | `qwen3.8` |

Native text + image + video → text. Thinking on by default; `--reasoning-effort xhigh|medium|low` on Max; `--no-thinking` on both paths. MCP: `understand_qwen3_8_max`, `understand_qwen3_8`.

### Docs / DX

- Agent guidelines: Path A (first-party API) vs Path B (local / HF / Ollama / LM Studio / Unsloth) — `docs/docs/advanced/model-integration-guidelines.md`
- New API & local docs pages for LTX, Hailuo, Wan, Runway, Qwen3.8
- `env.template` updated (`LTX_*`, `MINIMAX_*`, `DASHSCOPE_*` / `QWEN_*`, `RUNWAYML_*`, `QWEN38_MODEL_ID`, …)

## Install / Upgrade

```bash
pip install -U opentryon
# optional local/GPU models (LTX-2.5, Wan 2.2, Qwen3.8, …):
pip install -U "opentryon[local]"
```

From source:

```bash
git checkout v0.0.4
pip install -e .
```

## Quick examples

```bash
opentryon video-generate --model ltx-2.5-api --prompt "runway walk" --duration 8
opentryon video-generate --model hailuo-2.3 --prompt "runway walk" --duration 6
opentryon video-generate --model wan-api --prompt "runway walk" --duration 5
opentryon video-generate --model runway-gen4.5 --prompt "runway walk" --duration 5
opentryon understand --model qwen3.8-max --image garment.jpg --prompt "Describe this outfit."
opentryon understand --model qwen3.8 --image garment.jpg   # needs GPU + [local]
```

## Docs

- Site: https://tryonlabs.github.io/opentryon/
- Changelog: [CHANGELOG.md](../CHANGELOG.md)
- CLI: [Unified CLI](https://tryonlabs.github.io/opentryon/docs/getting-started/cli)
- Qwen3.8 API: [docs](https://tryonlabs.github.io/opentryon/docs/api-reference/qwen3.8)
- Model integration guidelines: [docs](https://tryonlabs.github.io/opentryon/docs/advanced/model-integration-guidelines)

## Notes

- No breaking CLI/MCP changes vs v0.0.3 — new registry entries only.
- Local LTX / Wan / Qwen need `opentryon[local]` (and often a recent Diffusers/Transformers); see each model’s docs page.
- Full agent/tool surfaces for Qwen Max remain on DashScope; OpenTryOn exposes the **understand** path (+ `chat()` escape hatch).

## Links

- PyPI: https://pypi.org/project/opentryon/0.0.4/
- Tag: https://github.com/tryonlabs/opentryon/releases/tag/v0.0.4
- Previous: [v0.0.3](RELEASE_NOTES_v0.0.3.md)
