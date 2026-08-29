---
sidebar_position: 5
title: MCP Server
description: Expose every OpenTryOn registry model as Model Context Protocol tools for Cursor, Claude, and tryon-studio
keywords:
  - MCP
  - Model Context Protocol
  - FastMCP
  - Cursor
  - Claude
  - opentryon
---

# MCP Server

OpenTryOn ships a [Model Context Protocol](https://modelcontextprotocol.io) server under `mcp-server/`. Every model in `tryon.cli.registry` becomes an MCP tool automatically — the same surface as the `opentryon` CLI, via `tryon.cli.runner.invoke_model()`.

**Current release:** works with OpenTryOn **v0.0.4+** (`pip install -U opentryon`).

## Why it matters

- Agents in **Cursor**, **Claude Desktop**, or **tryon-studio** can call try-on, generate, edit, video, understand, and bg-remove tools directly. Studio **chat** goes through `planner_agent`: it classifies intent, then runs a **filtered slice** of those same registry tools via `invoke_model`. Capability screens skip the planner and call the model tools themselves.
- New registry models appear as tools with **zero hand-written MCP wrappers**
- CLI and MCP cannot drift — one runner, one registry

## Understand tools (including Qwen3.8)

Multimodal image/video understanding tools include Kimi, LLaVA-NeXT, and the
**Qwen3.8** dual path:

| MCP tool | Backend | Needs |
|---|---|---|
| `understand_qwen3_8_max` | DashScope Qwen3.8-Max (text/image/video, thinking + `reasoning_effort`) | `DASHSCOPE_API_KEY` |
| `understand_qwen3_8` | Local `Qwen/Qwen3.8-27B` | `pip install opentryon[local]` + GPU |

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

Qwen3.8 is a native multimodal / coding / agent family; OpenTryOn’s MCP tools
expose the **understand** entry point (image and/or video + prompt). Full
capability notes: [Qwen3.8-Max](../api-reference/qwen3.8.md),
[Qwen-Image](../api-reference/qwen-image.md), and
[Qwen3.8 local](../local-models/qwen3.8.md).

## MiniMax H3 tools (video)

Same `MINIMAX_API_KEY` as Hailuo 2.3. H3 is a **dual path** (hosted V2 vs local Diffusers); Hailuo 2.3 stays API-only.

| MCP tool | Backend | Needs |
|---|---|---|
| `video_generate_minimax_h3` | MiniMax H3 official V2 API (T2V / I2V, 4–15s, 768P/2K) | `MINIMAX_API_KEY` |
| `video_generate_minimax_h3_local` | Open-weight `MiniMaxAI/MiniMax-H3` (768p H3-Base) | `pip install opentryon[local]` + CUDA + Diffusers from main |
| `video_generate_hailuo_2_3` | MiniMax Hailuo 2.3 (V1) | `MINIMAX_API_KEY` |

See [MiniMax H3 API](../api-reference/minimax-h3.md) and [MiniMax H3 local](../local-models/minimax-h3.md).

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

## Quick start

```bash
cd mcp-server
pip install -r requirements.txt   # includes fastmcp
cp ../env.template ../.env        # fill API keys you need
python server.py                  # stdio (default for most MCP clients)
# or:
python server.py --transport http --host 127.0.0.1 --port 8000
```

Discovery tools:

- `list_opentryon_tools` — list services / models / tool names / env readiness
- `opentryon_status` — configuration status report
- `list_api_keys` / `set_api_keys` — inspect or upsert host `.env` keys (never returns secret values). TryOn Studio Connect uses these.

Every generated tool accepts `dry_run` and `output_dir`, matching the CLI.

## Client config

See example configs in the repo:

- [`mcp-server/examples/cursor_mcp_config.json`](https://github.com/tryonlabs/opentryon/blob/main/mcp-server/examples/cursor_mcp_config.json)
- [`mcp-server/examples/claude_desktop_config.json`](https://github.com/tryonlabs/opentryon/blob/main/mcp-server/examples/claude_desktop_config.json)

Full tool tables and architecture notes: [`mcp-server/README.md`](https://github.com/tryonlabs/opentryon/blob/main/mcp-server/README.md).

## Related

- [Planner Agent](../agents/planner-agent)
- [Unified CLI](cli)
- [Qwen3.8-Max understanding](../api-reference/qwen3.8)
- [Qwen-Image generate / edit / VTON](../api-reference/qwen-image)
- [Qwen-Image local model](../local-models/qwen-image)
- [Qwen3.8 local model](../local-models/qwen3.8)
- [MiniMax H3 API](../api-reference/minimax-h3)
- [MiniMax H3 local](../local-models/minimax-h3)
- [Muse Image](../api-reference/muse-image)
- [P-Image-Ideogram](../api-reference/p-image-ideogram)
- [Adding a new model](../advanced/new-model-checklist)
- [Configuration](configuration)
