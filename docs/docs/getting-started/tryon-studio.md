---
sidebar_position: 6
title: TryOn Studio
description: Set up TryOn Studio — the Next.js MCP client for OpenTryOn Agent chat, Connect, and capability screens
keywords:
  - TryOn Studio
  - tryon-studio
  - MCP client
  - virtual try-on UI
  - planner agent
  - Connect
---

# TryOn Studio

[TryOn Studio](https://github.com/tryonlabs/tryon-studio) is the Next.js playground for OpenTryOn. It is an **MCP client only**: it never imports OpenTryOn Python, never reads the OpenTryOn filesystem, and never stores provider API keys. Every model, adapter, and agent lives in this repo (`tryon/cli/registry.py` + `mcp-server/`). Studio talks to that stack over MCP HTTP.

This page is the setup and product tour. The protocol, tools, and server process are documented in [MCP Server](mcp).

## Architecture

```
┌────────────────────────────┐        MCP over HTTP        ┌──────────────────────────────┐
│  tryon-studio              │ ───────────────────────────▶ │  opentryon/mcp-server         │
│  Next.js (App Router)      │                              │  FastMCP, streamable-HTTP     │
│  - Connect + capabilities  │ ◀─────────────────────────── │  registry models + discovery  │
│  - Agent chat              │   JSON + images_base64 /     │  + planner_agent              │
│  - Route handlers = MCP    │   video_base64               │                                │
│    client                  │                              │                                │
└────────────────────────────┘                              └──────────────────────────────┘
```

- **OpenTryOn owns adapters and agents.** New registry models appear in Connect and the capability pickers after an MCP restart.
- **Studio’s only env var** is `OPENTRYON_MCP_URL` (default `http://127.0.0.1:8000/mcp`). Planner LLM keys, image keys, and VTON keys live in `opentryon/.env`.
- **Media on the wire** is `images_base64` / `video_base64`, not host file paths.
- Remote MCP hosts are out of scope in this phase — keep the URL on localhost.

## What is in Studio

The v1 nav is **Agent · Capabilities · Connect**. Capability screens share one shell: model + params rail, canvas, and an inspector (request / response / MCP / CLI / Python / auth). Forms default to **dry-run** so you can preview a call without spending API credits.

| Screen | Route | What it does |
|---|---|---|
| **Connect** | `/connect` | Ping MCP, list live tools, show which host keys are loaded, paste keys as a passthrough into `opentryon/.env` |
| **Agent** | `/` and `/c/[sessionId]` | Chat. Studio calls MCP `planner_agent` only — it does not run its own tool loop |
| **Image** | `/image?mode=generate` or `?mode=edit` | Text-to-image or instruction edit. `/generate` and `/edit` redirect here |
| **VTON** | `/vton` | Person + garment virtual try-on |
| **Understand** | `/understand` | Caption / Q&A on an image, a video URL, or a text LLM such as Hy4 |
| **Video** | `/video` | Text-to-video or first-frame-to-video |
| **BG Remove** | `/bg-remove` | Cut the subject out of a photo |

Use-case screens (Fashion Prompt Builder, styling, …) may still have routes for later work; they are **not** in the v1 sidebar.

### Agent chat

Chat is a super-agent over the live registry, not a launcher that only deep-links to capability pages.

- OpenTryOn classifies intent with a cheap planner LLM, then runs a **filtered slice** of the same tools the capability screens use (`invoke_model`).
- If you name a model (`wan-3.0`, `hy4-preview`, `leffa`, …) that registry id is exclusive for the turn.
- Otherwise the planner uses the capability default: VTON `kling-ai`, generate/edit `nano-banana-pro`, understand `kimi-k2.6`, video `sora`, bg-remove `ben2`.
- This turn’s first attached image is `person_image` / `image`; the second is `garment_image`. Follow-ups reuse the latest prior user photos.
- Returned `images_base64` / `video_base64` persist as chat attachments.
- Questions such as “what is Hy4 preview?” are answered from the live registry catalog (label + notes), not by guessing.

If `planner_agent` is missing, update OpenTryOn and restart MCP. Full behavior: [Planner Agent](../agents/planner-agent).

### Connect

Connect is the status desk, not a second key store.

- `list_opentryon_tools` / `opentryon_status` show what the MCP host loaded.
- `list_api_keys` / `set_api_keys` write `opentryon/.env` on the MCP machine (mode `0600`). Studio does **not** keep secrets in `studio.db`, cookies, or `localStorage`.
- Local GPU extras (`leffa`, `catvton`, `hy4-preview-local`, …) show as local/self-hosted — they do not need a Connect key. Hy4 TokenHub uses `TOKENHUB_API_KEY`; Vertex Virtual Try-On uses `GOOGLE_CLOUD_PROJECT` (ADC stays on the MCP host).

## Setup

You need **two processes**: the OpenTryOn MCP server (HTTP) and Studio.

### 1. OpenTryOn MCP (this repo)

```bash
git clone https://github.com/tryonlabs/opentryon.git
cd opentryon
pip install -e .                 # or -e ".[local]" for GPU-backed models
cp env.template .env             # image / VTON / planner LLM keys
cd mcp-server
pip install -r requirements.txt
python server.py --transport http --host 127.0.0.1 --port 8000
```

Studio requires **streamable-HTTP**, not stdio. Cursor / Claude Desktop can keep using stdio; that is a separate client. See [MCP Server](mcp) for transports, discovery tools, and Cursor/Claude config.

For Agent chat, also set in `opentryon/.env`:

```bash
OPENTRYON_AGENT_LLM_PROVIDER=openai   # openai | anthropic | google
OPENTRYON_PLANNER_LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=...                    # matching provider key
```

Restart MCP after changing planner settings or adding a registry model.

### 2. Studio

Node.js 20+ is enough. Clone [tryon-studio](https://github.com/tryonlabs/tryon-studio) next to OpenTryOn (or anywhere — they only share HTTP).

```bash
git clone https://github.com/tryonlabs/tryon-studio.git
cd tryon-studio
cp .env.local.example .env.local
npm install
npm run dev
```

`.env.local` (the only Studio config):

```bash
OPENTRYON_MCP_URL=http://127.0.0.1:8000/mcp
```

Open [http://localhost:3000/connect](http://localhost:3000/connect) first. Confirm MCP is up, scan the live tool list, then use Agent or a capability screen.

## Adding a model

Add it in OpenTryOn (`tryon/cli/registry.py`) and **restart MCP**. Connect and the capability pickers load `list_opentryon_tools` plus each tool’s JSON Schema — no Studio code change.

Do not add a parallel HTTP client in tryon-studio. Checklist: [New model checklist](../advanced/new-model-checklist).

## Related

- [MCP Server](mcp) — install, run, discovery tools, Cursor / Claude
- [`mcp-server/README.md`](https://github.com/tryonlabs/opentryon/blob/main/mcp-server/README.md) — full generated tool table
- [Planner Agent](../agents/planner-agent)
- [Unified CLI](cli)
- [Configuration](configuration)
- [tryon-studio on GitHub](https://github.com/tryonlabs/tryon-studio)
