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

- Agents in **Cursor**, **Claude Desktop**, or **[tryon-studio](https://github.com/tryonlabs/tryon-studio)** can call try-on, generate, edit, video, understand, and bg-remove tools directly
- New registry models appear as tools with **zero hand-written MCP wrappers**
- CLI and MCP cannot drift — one runner, one registry

## Understand tools (including Qwen3.8)

Multimodal image/video understanding tools include Kimi, LLaVA-NeXT, and the
**Qwen3.8** dual path:

| MCP tool | Backend | Needs |
|---|---|---|
| `understand_qwen3_8_max` | DashScope Qwen3.8-Max (text/image/video, thinking + `reasoning_effort`) | `DASHSCOPE_API_KEY` |
| `understand_qwen3_8` | Local `Qwen/Qwen3.8-27B` | `pip install opentryon[local]` + GPU |

Qwen3.8 is a native multimodal / coding / agent family; OpenTryOn’s MCP tools
expose the **understand** entry point (image and/or video + prompt). Full
capability notes: [Qwen3.8-Max](../api-reference/qwen3.8.md) and
[Qwen3.8 local](../local-models/qwen3.8.md).

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

Every generated tool accepts `dry_run` and `output_dir`, matching the CLI.

## Client config

See example configs in the repo:

- [`mcp-server/examples/cursor_mcp_config.json`](https://github.com/tryonlabs/opentryon/blob/main/mcp-server/examples/cursor_mcp_config.json)
- [`mcp-server/examples/claude_desktop_config.json`](https://github.com/tryonlabs/opentryon/blob/main/mcp-server/examples/claude_desktop_config.json)

Full tool tables and architecture notes: [`mcp-server/README.md`](https://github.com/tryonlabs/opentryon/blob/main/mcp-server/README.md).

## Related

- [Unified CLI](cli)
- [Qwen3.8-Max understanding](../api-reference/qwen3.8)
- [Qwen3.8 local model](../local-models/qwen3.8)
- [Adding a new model](../advanced/new-model-checklist)
- [Configuration](configuration)
