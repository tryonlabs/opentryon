---
sidebar_position: 5
title: MCP Server
description: Install and run the OpenTryOn Model Context Protocol server — registry tools for Cursor, Claude, and TryOn Studio
keywords:
  - MCP
  - Model Context Protocol
  - FastMCP
  - Cursor
  - Claude
  - TryOn Studio
  - opentryon
---

# MCP Server

OpenTryOn ships a [Model Context Protocol](https://modelcontextprotocol.io) server under `mcp-server/`. Every model in `tryon.cli.registry` becomes an MCP tool automatically — the same surface as the `opentryon` CLI, via `tryon.cli.runner.invoke_model()`.

**Current release:** OpenTryOn **v0.0.4+** (`pip install -U opentryon`).

This page is the Docusaurus guide for the server. Keep it next to:

- **In-repo README (full tool table):** [`mcp-server/README.md`](https://github.com/tryonlabs/opentryon/blob/main/mcp-server/README.md)
- **TryOn Studio (the web MCP client):** [TryOn Studio](tryon-studio)

## Why it matters

- Agents in **Cursor**, **Claude Desktop**, or **TryOn Studio** call try-on, generate, edit, video, understand, and bg-remove tools directly.
- Studio **chat** goes through `planner_agent`: it classifies intent, then runs a **filtered slice** of those same registry tools via `invoke_model`. Capability screens skip the planner and call the model tools themselves.
- New registry models appear as tools with **zero hand-written MCP wrappers**.
- CLI and MCP cannot drift — one runner, one registry.

## Install

```bash
cd opentryon
pip install -e .              # core (API-backed) models
# optional GPU extras (leffa, catvton, kimi-vl, qwen3.8, ben2, …):
pip install -e ".[local]"

cd mcp-server
pip install -r requirements.txt
```

Copy repo-root `env.template` to `.env` and fill the keys you plan to use. The server and every adapter read that same file.

## Run

```bash
# stdio — what Claude Desktop / Cursor expect
python server.py

# streamable-HTTP — required by TryOn Studio
python server.py --transport http --host 127.0.0.1 --port 8000
```

On startup the server prints a configuration report to stderr (which keys are set, which models are ready) — the same text `opentryon_status` returns at runtime.

| Transport | Typical client | Endpoint |
|---|---|---|
| stdio (default) | Cursor, Claude Desktop | process stdin/stdout |
| HTTP | [TryOn Studio](tryon-studio), FastMCP `Client` over the network | `http://127.0.0.1:8000/mcp` |

Studio’s only URL is `OPENTRYON_MCP_URL=http://127.0.0.1:8000/mcp`. Remote MCP hosts are out of scope for Studio.

## Clients

### TryOn Studio

HTTP MCP plus a Next.js UI (Agent, Connect, Image, VTON, Understand, Video, BG Remove). Full setup: [TryOn Studio](tryon-studio).

### Cursor

Add to `.cursor/mcp.json` (project) or `~/.cursor/mcp.json` (global). Example: [`mcp-server/examples/cursor_mcp_config.json`](https://github.com/tryonlabs/opentryon/blob/main/mcp-server/examples/cursor_mcp_config.json).

```json
{
  "mcpServers": {
    "opentryon": {
      "command": "python",
      "args": ["/absolute/path/to/opentryon/mcp-server/server.py"]
    }
  }
}
```

### Claude Desktop

Add to `claude_desktop_config.json`. Example: [`mcp-server/examples/claude_desktop_config.json`](https://github.com/tryonlabs/opentryon/blob/main/mcp-server/examples/claude_desktop_config.json).

```json
{
  "mcpServers": {
    "opentryon": {
      "command": "python",
      "args": ["/absolute/path/to/opentryon/mcp-server/server.py"]
    }
  }
}
```

### Python (FastMCP client)

See [`mcp-server/examples/example_usage.py`](https://github.com/tryonlabs/opentryon/blob/main/mcp-server/examples/example_usage.py).

```python
import asyncio
from fastmcp import Client

async def main():
    async with Client("server.py") as client:
        result = await client.call_tool("vton_flux_vto", {
            "person": "model.jpg",
            "garment": "garment.jpg",
            "dry_run": True,
        })
        print(result.data)

asyncio.run(main())
```

## Discovery, keys, and the planner

Always available, independent of which models you configured:

| Tool | Role |
|---|---|
| `list_opentryon_tools` | Services, models, MCP tool names, env readiness |
| `opentryon_status` | Same human-readable report printed on startup |
| `list_api_keys` / `set_api_keys` | Inspect or upsert host `.env` keys (never returns secret values). Studio Connect uses these |
| `planner_agent` | Studio Agent chat entrypoint. Cheap LLM classifies intent, then `invoke_model` on a filtered slice. [Planner Agent](../agents/planner-agent) |

Every generated model tool also accepts `dry_run` and `output_dir`, matching the CLI.

## Selected tools

The tables below highlight newer families. The complete generated list lives in [`mcp-server/README.md`](https://github.com/tryonlabs/opentryon/blob/main/mcp-server/README.md) and grows with `tryon/cli/registry.py`.

## Understand tools (including Qwen3.8 and Hy4)

Multimodal image/video understanding tools include Kimi, LLaVA-NeXT, the
**Qwen3.8** dual path, and **Hy4 preview** (TokenHub LLM + local vLLM/SGLang):

| MCP tool | Backend | Needs |
|---|---|---|
| `understand_qwen3_8_max` | DashScope Qwen3.8-Max (text/image/video, thinking + `reasoning_effort`) | `DASHSCOPE_API_KEY` |
| `understand_qwen3_8` | Local `Qwen/Qwen3.8-27B` | `pip install opentryon[local]` + GPU |
| `understand_hy4_preview` | Tencent Hy4 preview (TokenHub LLM) | `TOKENHUB_API_KEY` |
| `understand_hy4_preview_local` | Hy4 via local vLLM/SGLang OpenAI server | `HY4_BASE_URL` (default localhost:8000) |

## Qwen-Image tools (generate / edit / VTON)

Same DashScope key as Qwen3.8-Max. Image generation is **Qwen-Image**, not
the Qwen3.8 VLM:

| MCP tool | Backend | Needs |
|---|---|---|
| `generate_qwen_image` | Qwen-Image 3.0 T2I (default `qwen-image-3.0-pro`) | `DASHSCOPE_API_KEY` |
| `edit_qwen_image` | Qwen-Image I2I (1–3 refs) | `DASHSCOPE_API_KEY` |
| `vton_qwen_image` | Person + garment composition | `DASHSCOPE_API_KEY` |

Typical loop: `understand_qwen3_8_max` captions a garment, then
`generate_qwen_image` or `vton_qwen_image` uses that description.

Local Diffusers twin (`pip install opentryon[local]` + CUDA):

| MCP tool | Backend | Needs |
|---|---|---|
| `generate_qwen_image_local` | `Qwen/Qwen-Image-2512` T2I | GPU + recent Diffusers |
| `edit_qwen_image_local` | `Qwen/Qwen-Image-Edit-2511` I2I | GPU + recent Diffusers |
| `vton_qwen_image_local` | Edit-Plus person + garment | GPU + recent Diffusers |

See [Qwen-Image local](../local-models/qwen-image.md).

## Local dedicated VTON (Leffa + CatVTON)

| MCP tool | Backend | Needs |
|---|---|---|
| `vton_leffa` | franciszzj/Leffa (CVPR 2025) | GPU + `opentryon[local]` |
| `vton_catvton` | zhengchong/CatVTON (ICLR 2025, CC BY-NC-SA) | GPU + `opentryon[local]` |

See [Leffa](../local-models/leffa.md) and [CatVTON](../local-models/catvton.md).

Qwen3.8 is a native multimodal / coding / agent family; OpenTryOn’s MCP tools
expose the **understand** entry point (image and/or video + prompt). Full
capability notes: [Qwen3.8-Max](../api-reference/qwen3.8.md),
[Qwen-Image](../api-reference/qwen-image.md), and
[Qwen3.8 local](../local-models/qwen3.8.md).

## MiniMax H3 tools (video)

Same `MINIMAX_API_KEY` as Hailuo 2.3. H3 is a **dual path** (hosted V2 vs local Diffusers); Hailuo 2.3 stays API-only. H3 Max is the hosted fast variant (no local twin).

| MCP tool | Backend | Needs |
|---|---|---|
| `video_generate_minimax_h3` | MiniMax H3 official V2 API (T2V / I2V / R2V, 4–15s, 768P/2K) | `MINIMAX_API_KEY` |
| `video_generate_minimax_h3_max` | MiniMax H3 Max (fast V2; T2V / I2V, 5–15s, 480P/768P) | `MINIMAX_API_KEY` |
| `video_generate_fal_h3_max` | Fal-hosted H3 Max (T2V / I2V / R2V, 5–15s, 480P/768P) | `FAL_KEY` |
| `video_generate_minimax_h3_local` | Open-weight `MiniMaxAI/MiniMax-H3` (768p H3-Base) | `pip install opentryon[local]` + CUDA + Diffusers from main |
| `video_generate_hailuo_2_3` | MiniMax Hailuo 2.3 (V1) | `MINIMAX_API_KEY` |

See [MiniMax H3 API](../api-reference/minimax-h3.md), [MiniMax H3 Max (Fal)](../api-reference/fal-h3-max.md), and [MiniMax H3 local](../local-models/minimax-h3.md).

## NVIDIA NIM tools (understand + video)

Same `NVIDIA_API_KEY` for Nemotron Omni, Cosmos 3 Reasoner, and Cosmos 3 Generator.

| MCP tool | Backend | Needs |
|---|---|---|
| `understand_nemotron_omni` | Nemotron 3 Nano Omni (image / video / audio) | `NVIDIA_API_KEY` |
| `understand_cosmos3_reasoner` | Cosmos 3 Reasoner (physical-world VLM) | `NVIDIA_API_KEY` |
| `video_generate_cosmos3` | Cosmos 3 Generator nano (T2V / I2V) | `NVIDIA_API_KEY` |

See [NVIDIA NIM](../api-reference/nvidia-nim.md).

## Google Virtual Try-On (Vertex)

Dedicated person + product try-on. **Not** `GEMINI_API_KEY` / Nano Banana.

| MCP tool | Backend | Needs |
|---|---|---|
| `vton_google_vton` | Vertex `virtual-try-on-001` | `GOOGLE_CLOUD_PROJECT` + ADC |

See [Google Virtual Try-On](../api-reference/google-vton.md).

## OutfitAnyone-Plus (DashScope, Beijing)

Dedicated Alibaba try-on. **Not** Qwen-Image composition. Needs a China Beijing-region `DASHSCOPE_API_KEY`.

| MCP tool | Backend | Needs |
|---|---|---|
| `vton_outfitanyone_plus` | `aitryon-plus` | Beijing `DASHSCOPE_API_KEY` |

See [OutfitAnyone-Plus](../api-reference/outfitanyone-plus.md).

## Photoroom (Virtual Try-On / Virtual Model)

Image Editing API Plus. Same `PHOTOROOM_API_KEY`. Prefix with `sandbox_` for watermarked tests.

| MCP tool | Backend | Needs |
|---|---|---|
| `vton_photoroom_vton` | Shopper try-on (`virtualModel.model.custom`) | `PHOTOROOM_API_KEY` |
| `vton_photoroom_virtual_model` | Catalog on-model (preset or custom) | `PHOTOROOM_API_KEY` |

See [Photoroom](../api-reference/photoroom.md).

## Muse Image tools (generate / edit / VTON)

First-party Meta Model API (`MODEL_API_KEY`). **No local twin.** Muse Video is not on the API yet.

| MCP tool | Backend | Needs |
|---|---|---|
| `generate_muse_image` | Muse Image T2I (`muse-image-1.0`) | `MODEL_API_KEY` |
| `edit_muse_image` | Muse Image I2I / multi-ref | `MODEL_API_KEY` |
| `vton_muse_image` | Person + garment composition | `MODEL_API_KEY` |

See [Muse Image](../api-reference/muse-image.md) and [Muse Video (not available)](../api-reference/muse-video.md).

## P-Image-Ideogram (generate)

Same `PRUNA_API_KEY` as the rest of the Pruna family. **Not** Ideogram 4.0 (`generate_ideogram` / `IDEOGRAM_API_KEY`).

| MCP tool | Backend | Needs |
|---|---|---|
| `generate_p_image_ideogram` | Pruna `Model: p-image-ideogram` (thinking very-low–very-high, 1K/2K) | `PRUNA_API_KEY` |

See [P-Image-Ideogram](../api-reference/p-image-ideogram.md).

## Related

- [TryOn Studio](tryon-studio) — Next.js MCP client (Agent, Connect, capability screens)
- [`mcp-server/README.md`](https://github.com/tryonlabs/opentryon/blob/main/mcp-server/README.md) — architecture notes and full generated tool table
- [Planner Agent](../agents/planner-agent)
- [Unified CLI](cli)
- [Configuration](configuration)
- [Adding a new model](../advanced/new-model-checklist)
- [Qwen3.8-Max understanding](../api-reference/qwen3.8)
- [Hy4 preview TokenHub](../api-reference/hy4)
- [Hy4 local vLLM/SGLang](../local-models/hy4)
- [Qwen-Image generate / edit / VTON](../api-reference/qwen-image)
- [Qwen-Image local model](../local-models/qwen-image)
- [Qwen3.8 local model](../local-models/qwen3.8)
- [MiniMax H3 API](../api-reference/minimax-h3)
- [MiniMax H3 Max (Fal)](../api-reference/fal-h3-max)
- [MiniMax H3 local](../local-models/minimax-h3)
- [Muse Image](../api-reference/muse-image)
- [P-Image-Ideogram](../api-reference/p-image-ideogram)
