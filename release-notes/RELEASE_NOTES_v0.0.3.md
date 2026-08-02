# OpenTryOn v0.0.3 Release Notes

## CLI, MCP, and a much wider media model surface

**Release Date**: 2 August 2026

OpenTryOn v0.0.3 is a large feature release: a unified `opentryon` CLI, a registry-driven FastMCP server, many new image/video providers (Seedance, Seedream, Kling 3, Luma Ray 3.2, Grok Imagine, Ideogram, Pruna), Kimi understanding models, FASHN / Pruna try-on, and a cleaner separation from the tryon-studio web UI.

## What's New

### Unified CLI (`opentryon`)

Installable console script for every registry model:

```bash
opentryon <service> --model <model> [params...]
# services: vton | generate | edit | understand | video-generate | bg-remove
```

Supports `--dry-run` and `-o/--output-dir`. Local GPU models need `pip install opentryon[local]`.

### MCP Server

`mcp-server/` is rebuilt on FastMCP 3.x. Tools are generated from `tryon.cli.registry` (same path as the CLI via `invoke_model()`). Discovery tools: `list_opentryon_tools`, `opentryon_status`.

### New media providers

| Area | Models |
|---|---|
| Image generate / edit | Seedream 5.0 Pro, Ideogram 4.0, Grok Imagine Image, Pruna P-Image / Edit / Upscale |
| Video | Seedance 2.5, Luma Ray 3.2, Kling 3.0 / Omni / Turbo, Grok Imagine Video 1.5, Gemini Omni Flash, Pruna P-Video / Replace / Avatar / Animate |
| Try-on | Pruna P-Image-Try-On, FASHN tryon-max / v1.6, Nano Banana 2 Lite (cheap composition path) |
| Understand | Kimi K2.6 / K2.7 Code / K3 (API), Kimi-VL + LLaVA-NeXT (local) |

### Demos / product split

The Next.js dashboard prototypes moved to [`tryon-studio`](https://github.com/tryonlabs/tryon-studio). This package keeps Gradio demos and notebooks only.

## Install / Upgrade

```bash
pip install -U opentryon
# optional local/GPU models:
pip install -U "opentryon[local]"
```

From source:

```bash
git checkout v0.0.3
pip install -e .
```

## Docs

- Site: https://tryonlabs.github.io/opentryon/
- Changelog: [CHANGELOG.md](../CHANGELOG.md)
- CLI: [Unified CLI](https://tryonlabs.github.io/opentryon/docs/getting-started/cli)
- Pruna: [API reference](https://tryonlabs.github.io/opentryon/docs/api-reference/pruna)

## Breaking / migration notes

- Prefer `opentryon` / MCP over ad-hoc root scripts (legacy examples live under `examples/legacy/` and `tests/legacy/`).
- Web UI consumers should point at tryon-studio + MCP, not removed `demo/virtual-tryon` paths.
- Core `pip install opentryon` stays cloud-light; torch/transformers are only in the `[local]` extra.

## Links

- PyPI: https://pypi.org/project/opentryon/0.0.3/
- Tag: https://github.com/tryonlabs/opentryon/releases/tag/v0.0.3
- Previous: [v0.0.2](RELEASE_NOTES_v0.0.2.md)
