# OpenTryOn

[![Documentation](https://img.shields.io/badge/Documentation-Read%20Docs-teal?style=flat-square)](https://tryonlabs.github.io/opentryon/)
[![PyPI](https://img.shields.io/pypi/v/opentryon?style=flat-square)](https://pypi.org/project/opentryon/)
[![Discord](https://img.shields.io/badge/Discord-Join%20Chat-blue?style=flat-square&logo=discord)](https://discord.gg/T5mPpZHxkY)
[![License](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg?style=flat-square)](https://creativecommons.org/licenses/by-nc/4.0/)

Open-source AI toolkit for fashion technology: virtual try-on, image/video generation & editing, multimodal understanding, background removal, preprocessing, datasets, and TryOnDiffusion research code.

**Current release: [v0.0.4](https://github.com/tryonlabs/opentryon/releases/tag/v0.0.4)** — LTX-2.5, Hailuo 2.3, Wan dual-path, Runway Gen-4.5, Qwen3.8 understand (API + local), plus the v0.0.3 CLI/MCP media surface.

📚 **Full documentation:** [https://tryonlabs.github.io/opentryon/](https://tryonlabs.github.io/opentryon/)  
API tutorials, configuration, examples, and agent guides live there — not in this README.

## What you get

| Category | Highlights |
|---|---|
| **Virtual try-on** | FLUX VTO, Nova Canvas, Kling AI, Segmind, Pruna P-Image-Try-On, FASHN, Nano Banana 2 Lite |
| **Generate / edit** | Nano Banana family, FLUX.2, GPT Image, Luma Photon, Seedream 5.0 Pro, Ideogram 4.0, Grok Imagine Image, Pruna P-Image / Edit / Upscale; local FLUX.2-dev Turbo |
| **Understand** | Kimi K2.6 / K2.7 Code / K3 (API), Kimi-VL & LLaVA-NeXT (local), **Qwen3.8-Max** (API) + **Qwen3.8-27B** (local) |
| **Video** | Veo, Sora, Luma Ray 2 + Ray 3.2, Seedance 2.5, Kling 3.0 / Omni / Turbo, Grok Imagine Video 1.5, Gemini Omni Flash, Pruna P-Video / Replace / Avatar / Animate, **LTX-2.5** (API + local), **Hailuo 2.3**, **Wan** (API + local 2.2), **Runway Gen-4.5** |
| **Other** | BEN2 background removal, garment/human preprocessing, fashion datasets, LangChain agents |

## Three ways to use it

1. **CLI** — `opentryon <service> --model <model> [params...]`
2. **MCP server** — expose every registry model as tools for Claude, Cursor, or [tryon-studio](https://github.com/tryonlabs/tryon-studio)
3. **Python** — `from tryon.api import ...` (and `tryon.cli.runner.invoke_model`)

The unified Next.js + Tailwind web UI is **not** in this repo — it lives in [`tryon-studio`](https://github.com/tryonlabs/tryon-studio) and talks to OpenTryOn over MCP.

## Install

```bash
git clone https://github.com/tryonlabs/opentryon.git
cd opentryon
conda env create -f environment.yml
conda activate opentryon
pip install -e .
# Optional local/GPU models: pip install -e ".[local]"
```

Or with pip: `pip install -r requirements.txt && pip install -e .`

```bash
cp env.template .env   # add the API keys you need
```

Details: [Installation](https://tryonlabs.github.io/opentryon/docs/getting-started/installation) · [Configuration](https://tryonlabs.github.io/opentryon/docs/getting-started/configuration)

## Quick start

```bash
# Dry-run (no API call) — verifies CLI + registry wiring
opentryon vton --model flux-vto \
  --person-image data/model-1.jpg --garment-image data/garment.png --dry-run

# Real call (needs BFL_API_KEY in .env)
opentryon vton --model flux-vto \
  --person-image data/model-1.jpg --garment-image data/garment.png \
  --garment-description "olive green bomber jacket"

# Multimodal understanding (needs MOONSHOT_API_KEY)
opentryon understand --model kimi-k3 --image data/model-1.jpg \
  --prompt "Describe this outfit for a product listing." --reasoning-effort high
```

```python
from tryon.api import KimiUnderstandAdapter

adapter = KimiUnderstandAdapter(model="kimi-k3")
result = adapter.understand_image(
    "data/model-1.jpg",
    prompt="Describe this outfit.",
    reasoning_effort="high",
)
print(result["text"])
```

More examples: [Quickstart](https://tryonlabs.github.io/opentryon/docs/getting-started/quickstart) · [CLI](https://tryonlabs.github.io/opentryon/docs/getting-started/cli) · [API Reference](https://tryonlabs.github.io/opentryon/docs/api-reference/overview)

## CLI services

```bash
opentryon <service> --model <model> [params...]
opentryon understand --help                    # list models
opentryon understand --model kimi-k3 --help    # list that model's flags
```

| Service | Purpose | Example models |
|---|---|---|
| `vton` | Virtual try-on | `flux-vto`, `p-image-tryon`, `fashn-tryon-max`, … |
| `generate` | Text-to-image | `nano-banana-pro`, `flux2-pro`, `gpt-image`, … |
| `edit` | Image editing | `nano-banana-2`, `flux2-flex`, `gpt-image`, … |
| `understand` | Image/video understanding | `kimi-k2.6`, `kimi-k3`, `kimi-vl`, … |
| `video-generate` | Text/image-to-video | `veo`, `sora`, `gemini-omni`, … |
| `bg-remove` | Background removal | `ben2` |

Models marked local need `pip install opentryon[local]`. Full table and flags: [Unified CLI](https://tryonlabs.github.io/opentryon/docs/getting-started/cli).

## MCP server

```bash
cd mcp-server
pip install -r requirements.txt
python server.py                                    # stdio (Claude Desktop / Cursor)
python server.py --transport http --host 127.0.0.1 --port 8000
```

Tools are generated from `tryon/cli/registry.py` — the same registry as the CLI. See [`mcp-server/README.md`](mcp-server/README.md).

## Demos & notebooks

This package ships **Gradio** demos and **Jupyter** notebooks only:

```bash
python run_demo.py --name extract_garment   # also: model_swap, outfit_generator
```

Notebooks: [`notebooks/`](notebooks/). Web UI: [tryon-studio](https://github.com/tryonlabs/tryon-studio).

## Layout

```
opentryon/
├── tryon/           # Package: api/, cli/, models/, agents/, datasets/, preprocessing/
├── tryondiffusion/  # Research diffusion training / inference
├── mcp-server/      # FastMCP server (registry → tools)
├── openapi/         # OpenAPI / Swagger snapshot (upstream media APIs)
├── postman/         # Postman collection for media providers
├── demo/            # Gradio demos
├── notebooks/       # Jupyter examples
├── docs/            # Docusaurus documentation site
├── tests/           # CLI / adapter smoke checks
└── env.template     # API key template
```

## Documentation map

| Topic | Where |
|---|---|
| Install & config | [Getting Started](https://tryonlabs.github.io/opentryon/docs/getting-started/installation) |
| CLI | [CLI guide](https://tryonlabs.github.io/opentryon/docs/getting-started/cli) |
| MCP | [MCP server](https://tryonlabs.github.io/opentryon/docs/getting-started/mcp) · [`mcp-server/README.md`](mcp-server/README.md) |
| OpenAPI / Postman | [Swagger guide](https://tryonlabs.github.io/opentryon/docs/getting-started/openapi-swagger) · [`openapi/`](openapi/) · [`postman/`](postman/) |
| Per-provider APIs | [API Reference](https://tryonlabs.github.io/opentryon/docs/api-reference/overview) |
| Local / GPU models | [Local Models](https://tryonlabs.github.io/opentryon/docs/local-models/overview) |
| Agents | [Agents](https://tryonlabs.github.io/opentryon/docs/agents/vton-agent) |
| Roadmap | [Roadmap](https://tryonlabs.github.io/opentryon/docs/community/roadmap) · [`ROADMAP.md`](ROADMAP.md) |
| Add a new model | [New model checklist](https://tryonlabs.github.io/opentryon/docs/advanced/new-model-checklist) |
| TryOnDiffusion | [Overview](https://tryonlabs.github.io/opentryon/docs/tryondiffusion/overview) · [paper](https://arxiv.org/abs/2306.08276) |

When contributing docs or APIs: put long tutorials in `docs/`, not this README. Keep README as the project front door only.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Open an issue before large changes; prefer PRs that update the registry, tests, and docs together.

## License

[Creative Commons BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/). Non-commercial use with attribution to [this repository](https://github.com/tryonlabs/opentryon); indicate any changes you make.

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=tryonlabs/opentryon&type=date&legend=top-left)](https://www.star-history.com/#tryonlabs/opentryon&type=date&legend=top-left)

---

Made with ❤️ by [TryOn Labs](https://www.tryonlabs.ai) · [Discord](https://discord.gg/T5mPpZHxkY)
