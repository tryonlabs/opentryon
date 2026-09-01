# OpenTryOn MCP Server

An [MCP](https://modelcontextprotocol.io) (Model Context Protocol) server that exposes every model in the [`opentryon`](../README.md) toolkit -- virtual try-on, image/video generation & editing, multimodal image & video understanding, and background removal -- as tools an LLM agent (Claude, Cursor, ChatGPT, or any MCP client) can call directly.

Requires **OpenTryOn v0.0.4+** (`pip install -U opentryon`). Docs: [MCP Server guide](https://tryonlabs.github.io/opentryon/docs/getting-started/mcp).

Built on [FastMCP](https://gofastmcp.com) 3.x, the actively-maintained, high-level Python framework for MCP servers (FastMCP 1.0 was folded into the official MCP Python SDK in 2024; this server uses the standalone FastMCP 2/3 project, which adds streamable-HTTP transport, better auth, and much less boilerplate).

## Why this is registry-driven

Every tool below is generated **dynamically** at import time from `tryon.cli.registry.SERVICES` -- the exact same data-driven registry that powers the `opentryon` CLI (see [`getting-started/cli.md`](../docs/docs/getting-started/cli.md)). There is no hand-written per-model wrapper function and no JSON schema to maintain by hand.

This means:

- **New models require zero MCP-server changes.** Add a model to `tryon/cli/registry.py` (see [`advanced/new-model-checklist.md`](../docs/docs/advanced/new-model-checklist.md)) and it instantly appears here as a new tool, with an accurate schema, the next time the server starts.
- **The CLI and the MCP server can never drift apart.** Both call the same `tryon.cli.runner.invoke_model()` execution path.
- Tool schemas (required/optional fields, enums for `choices`, per-field descriptions) are generated straight from each model's `Arg` definitions via Python's `inspect` + Pydantic, not duplicated JSON.

## Installation

```bash
cd opentryon
pip install -e .              # core (API-backed) models
# or, to also enable local/GPU models (llava-next, kimi-vl, qwen3.8, qwen-image-local, leffa, catvton, flux2-turbo, ben2, ltx-2.5, wan-2.2):
pip install -e ".[local]"

cd mcp-server
pip install -r requirements.txt
```

Copy `env.template` (repo root) to `.env` and fill in whichever API keys you plan to use -- the server (and every adapter) reads that same `.env` file, so no separate MCP-specific secret handling is needed.

## Running

```bash
# stdio transport (what Claude Desktop / Cursor / most MCP clients expect)
python server.py

# streamable-HTTP transport, for remote/network clients
python server.py --transport http --host 0.0.0.0 --port 8000
```

On startup the server prints a configuration status report to stderr (which API keys are set, which models are ready) -- the same information the `opentryon_status` tool returns at runtime.

### Claude Desktop

Add to `claude_desktop_config.json` (see [`examples/claude_desktop_config.json`](examples/claude_desktop_config.json)):

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

### Cursor

Add to `.cursor/mcp.json` (project) or `~/.cursor/mcp.json` (global) -- see [`examples/cursor_mcp_config.json`](examples/cursor_mcp_config.json):

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

### Programmatically (FastMCP client)

See [`examples/example_usage.py`](examples/example_usage.py) for a full walkthrough. Quick version:

```python
import asyncio
from fastmcp import Client

async def main():
    async with Client("server.py") as client:
        result = await client.call_tool("vton_flux_vto", {
            "person": "model.jpg",
            "garment": "garment.jpg",
            "dry_run": True,   # preview the call, spend no API credits
        })
        print(result.data)

asyncio.run(main())
```

## Discovery tools

Two meta tools are always available regardless of what's configured:

- **`list_opentryon_tools(service=None)`** -- lists every service/model combination, its MCP tool name, which env var(s) it needs, and whether it's currently configured. Call this first.
- **`opentryon_status()`** -- the same human-readable status report printed on startup.

## API keys (host `.env`)

Studio Connect and other MCP clients can inspect and upsert keys **on this machine**. Secrets are written to `opentryon/.env` (mode `0600`) and applied to the running process. Tools never return secret values.

- **`list_api_keys()`** -- unique env vars from the registry, grouped by provider, with `configured` true/false and which models they unlock.
- **`set_api_keys(keys)`** -- `{ "GEMINI_API_KEY": "..." }` (Kling/AWS send both vars in one call). Unknown names are rejected. Most adapters pick up the new value without a restart.

## Agent entrypoint

- **`planner_agent(prompt, person_image=None, garment_image=None, image=None, images=None, dry_run=false)`** -- TryOn Studio chat entrypoint. A cheap LLM (`OPENTRYON_PLANNER_LLM_MODEL`) classifies intent (**help**, VTON, model-swap, generate/edit/video, …) then runs a **filtered slice** of the same registry tools listed below via `invoke_model`. Named models in the prompt (e.g. `wan-3.0`) pin the registry id. `dry_run=true` resolves the call without hitting an image API. Capability screens still call the model tools directly. See [Planner Agent](../docs/docs/agents/planner-agent.md).

## Every generated tool accepts

- All of the model's own parameters (mirrors `opentryon <service> --model <model> --help` exactly), with the same required/optional-ness, defaults, and choice/enum constraints as the CLI.
- **`dry_run`** (bool, default `false`) -- preview the resolved adapter call (`ClassName(**init_kwargs).method(**call_kwargs)`) without hitting any API, GPU, or network.
- **`output_dir`** (str, default `"outputs"`) -- where to save any resulting images/video/JSON.

Every tool returns a structured dict: `{"success": true/false, ...}` -- never raises, so an LLM caller always gets a clean result to reason about instead of a stack trace.

## Available tools (registry-driven; count grows with `tryon/cli/registry.py`)

### vton -- Virtual try-on: compose a garment onto a person image

| Tool | Model | Requires |
|---|---|---|
| `vton_flux_vto` | Black Forest Labs FLUX VTO | `BFL_API_KEY` |
| `vton_google_vton` | Google Vertex Virtual Try-On (`virtual-try-on-001`) | `GOOGLE_CLOUD_PROJECT` + ADC |
| `vton_outfitanyone_plus` | Alibaba OutfitAnyone-Plus (`aitryon-plus`) | Beijing `DASHSCOPE_API_KEY` |
| `vton_photoroom_vton` | Photoroom Virtual Try-On | `PHOTOROOM_API_KEY` |
| `vton_photoroom_virtual_model` | Photoroom Virtual Model (flat-lay → on-model) | `PHOTOROOM_API_KEY` |
| `vton_nova_canvas` | Amazon Nova Canvas | `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` |
| `vton_kling_ai` | Kling AI (Kolors Virtual Try-On) | `KLING_AI_API_KEY` / `KLING_AI_SECRET_KEY` |
| `vton_segmind` | Segmind Try-On Diffusion | `SEGMIND_API_KEY` |
| `vton_p_image_tryon` | Pruna P-Image-Try-On | `PRUNA_API_KEY` |
| `vton_nano_banana_2_lite` | Nano Banana 2 Lite (composition try-on) | `GEMINI_API_KEY` |
| `vton_qwen_image` | Qwen-Image 3.0 (person + garment I2I) | `DASHSCOPE_API_KEY` |
| `vton_qwen_image_local` | Qwen-Image-Edit-2511 (open-weight, local) | local/GPU |
| `vton_leffa` | Leffa (CVPR 2025 local VTON) | local/GPU |
| `vton_catvton` | CatVTON (ICLR 2025 local VTON, CC BY-NC-SA) | local/GPU |
| `vton_muse_image` | Muse Image (composition try-on) | `MODEL_API_KEY` |

### generate -- Text-to-image generation

| Tool | Model | Requires |
|---|---|---|
| `generate_nano_banana` | Nano Banana (Gemini 2.5 Flash Image) | `GEMINI_API_KEY` |
| `generate_nano_banana_pro` | Nano Banana Pro (Gemini 3 Pro Image Preview) | `GEMINI_API_KEY` |
| `generate_nano_banana_2` | Nano Banana 2 (Gemini 3.1 Flash Image) | `GEMINI_API_KEY` |
| `generate_flux2_pro` | FLUX.2 [pro] | `BFL_API_KEY` |
| `generate_flux2_flex` | FLUX.2 [flex] | `BFL_API_KEY` |
| `generate_flux2_turbo` | FLUX.2-dev Turbo (local, 8-step) | local/GPU |
| `generate_gpt_image` | OpenAI GPT Image | `OPENAI_API_KEY` |
| `generate_luma_image` | Luma Photon | `LUMA_AI_API_KEY` |
| `generate_seedream` | ByteDance Seedream 5.0 Pro | `ARK_API_KEY` |
| `generate_ideogram` | Ideogram 4.0 | `IDEOGRAM_API_KEY` |
| `generate_grok_imagine_image` | xAI Grok Imagine Image Quality | `XAI_API_KEY` |
| `generate_p_image` | Pruna P-Image | `PRUNA_API_KEY` |
| `generate_p_image_ideogram` | P-Image-Ideogram (Pruna × Ideogram) | `PRUNA_API_KEY` |
| `generate_qwen_image` | Qwen-Image 3.0 | `DASHSCOPE_API_KEY` |
| `generate_qwen_image_local` | Qwen-Image-2512 (open-weight, local) | local/GPU |
| `generate_muse_image` | Muse Image (Meta Model API) | `MODEL_API_KEY` |

### edit -- Image editing (image + instruction -> image)

| Tool | Model | Requires |
|---|---|---|
| `edit_nano_banana` | Nano Banana (Gemini 2.5 Flash Image) | `GEMINI_API_KEY` |
| `edit_nano_banana_pro` | Nano Banana Pro | `GEMINI_API_KEY` |
| `edit_nano_banana_2` | Nano Banana 2 | `GEMINI_API_KEY` |
| `edit_flux2_pro` | FLUX.2 [pro] | `BFL_API_KEY` |
| `edit_flux2_flex` | FLUX.2 [flex] | `BFL_API_KEY` |
| `edit_flux2_turbo` | FLUX.2-dev Turbo (local, image-to-image) | local/GPU |
| `edit_gpt_image` | OpenAI GPT Image | `OPENAI_API_KEY` |
| `edit_seedream` | ByteDance Seedream 5.0 Pro (edit / multi-ref) | `ARK_API_KEY` |
| `edit_p_image_edit` | Pruna P-Image-Edit | `PRUNA_API_KEY` |
| `edit_p_image_upscale` | Pruna P-Image-Upscale | `PRUNA_API_KEY` |
| `edit_qwen_image` | Qwen-Image 3.0 (I2I, 1–3 refs) | `DASHSCOPE_API_KEY` |
| `edit_qwen_image_local` | Qwen-Image-Edit-2511 (open-weight, local) | local/GPU |
| `edit_muse_image` | Muse Image (Meta Model API, edit / multi-ref) | `MODEL_API_KEY` |

### understand -- Image & video understanding / captioning

General-purpose multimodal understanding (not fashion-only). Useful for garments
and lookbooks as well as documents, UI screenshots, product photos, and video clips.

| Tool | Model | Requires | Notes |
|---|---|---|---|
| `understand_llava_next` | LLaVA-NeXT (local VLM captioning) | local/GPU | Fashion-oriented captioning helper |
| `understand_kimi_k2_6` | Kimi K2.6 (Moonshot AI) | `MOONSHOT_API_KEY` | Image + video; optional thinking |
| `understand_kimi_k2_7_code` | Kimi K2.7 Code | `MOONSHOT_API_KEY` | Coding-focused multimodal; thinking always on |
| `understand_kimi_k3` | Kimi K3 | `MOONSHOT_API_KEY` | Flagship reasoning; `reasoning_effort` |
| `understand_kimi_vl` | Kimi-VL (open-weight, local) | local/GPU | Open counterpart to Kimi APIs |
| `understand_qwen3_8_max` | Qwen3.8-Max (DashScope) | `DASHSCOPE_API_KEY` | Native text/image/video; thinking + `reasoning_effort` (`xhigh`/`medium`/`low`); hosted Max ~1M context, long video |
| `understand_qwen3_8` | Qwen3.8-27B (open-weight, local) | local/GPU | Dense open multimodal (`Qwen/Qwen3.8-27B`); thinking toggle; frame-sampled video |
| `understand_nemotron_omni` | Nemotron 3 Nano Omni (NVIDIA NIM) | `NVIDIA_API_KEY` | Image + video + audio; thinking on by default |
| `understand_cosmos3_reasoner` | Cosmos 3 Reasoner (NVIDIA NIM) | `NVIDIA_API_KEY` | Physical-world image/video QA |

**Qwen3.8 via MCP:** both tools call the shared `understand` entry point (`image`
and/or `video` + `prompt`). Hosted Max also accepts `enable_thinking` /
`reasoning_effort` / `max_tokens`; local accepts `num_frames`, `max_new_tokens`,
`temperature`, and `enable_thinking`. Vendor coding/agent/tool surfaces beyond
understand remain on DashScope / self-hosted stacks — OpenTryOn exposes the
vision-understanding path here. See
[`docs/docs/api-reference/qwen3.8.md`](../docs/docs/api-reference/qwen3.8.md) and
[`docs/docs/local-models/qwen3.8.md`](../docs/docs/local-models/qwen3.8.md).
Image generate / edit / VTON use the sibling Qwen-Image tools
(`generate_qwen_image`, `edit_qwen_image`, `vton_qwen_image`) — see
[`docs/docs/api-reference/qwen-image.md`](../docs/docs/api-reference/qwen-image.md).
Local Diffusers twin: `generate_qwen_image_local`, `edit_qwen_image_local`,
`vton_qwen_image_local` — see
[`docs/docs/local-models/qwen-image.md`](../docs/docs/local-models/qwen-image.md).

### video-generate -- Text/image-to-video generation

| Tool | Model | Requires |
|---|---|---|
| `video_generate_veo` | Google Veo | `GEMINI_API_KEY` |
| `video_generate_sora` | OpenAI Sora | `OPENAI_API_KEY` |
| `video_generate_luma_video` | Luma Dream Machine (Ray 2) | `LUMA_AI_API_KEY` |
| `video_generate_luma_ray_3_2` | Luma Ray 3.2 (Agents API) | `LUMA_AGENTS_API_KEY` / `LUMA_AI_API_KEY` |
| `video_generate_seedance` | ByteDance Seedance 2.5 | `ARK_API_KEY` |
| `video_generate_kling_v3` | Kling 3.0 | `KLING_AI_API_KEY` / `KLING_AI_SECRET_KEY` |
| `video_generate_kling_v3_omni` | Kling 3.0 Omni | `KLING_AI_API_KEY` / `KLING_AI_SECRET_KEY` |
| `video_generate_kling_v2_5_turbo` | Kling 2.5 Turbo | `KLING_AI_API_KEY` / `KLING_AI_SECRET_KEY` |
| `video_generate_grok_imagine_video` | xAI Grok Imagine Video 1.5 | `XAI_API_KEY` |
| `video_generate_gemini_omni` | Gemini Omni Flash | `GEMINI_API_KEY` |
| `video_generate_p_video` | Pruna P-Video | `PRUNA_API_KEY` |
| `video_generate_p_video_replace` | Pruna P-Video-Replace | `PRUNA_API_KEY` |
| `video_generate_p_video_avatar` | Pruna P-Video-Avatar | `PRUNA_API_KEY` |
| `video_generate_p_video_animate` | Pruna P-Video-Animate | `PRUNA_API_KEY` |
| `video_generate_ltx_2_5_api` | LTX-2.5 (official API) | `LTX_API_KEY` |
| `video_generate_ltx_2_5` | LTX-2.5 (local Diffusers) | local/GPU |
| `video_generate_hailuo_2_3` | MiniMax Hailuo 2.3 | `MINIMAX_API_KEY` |
| `video_generate_minimax_h3` | MiniMax H3 (official API) | `MINIMAX_API_KEY` |
| `video_generate_minimax_h3_local` | MiniMax H3 (local Diffusers) | local/GPU |
| `video_generate_wan_api` | Alibaba Wan 2.x (DashScope) | `DASHSCOPE_API_KEY` |
| `video_generate_wan_3_0` | Alibaba Wan 3.0 (DashScope) | `DASHSCOPE_API_KEY` |
| `video_generate_wan_2_2` | Wan 2.2 (local Diffusers) | local/GPU |
| `video_generate_runway_gen4_5` | Runway Gen-4.5 | `RUNWAYML_API_SECRET` |
| `video_generate_cosmos3` | NVIDIA Cosmos 3 Generator nano | `NVIDIA_API_KEY` |

### bg-remove -- Background removal

| Tool | Model | Requires |
|---|---|---|
| `bg_remove_ben2` | BEN2 background remover (local) | local/GPU |

Run `list_opentryon_tools()` at any time for the live, authoritative version of this table (including per-model parameter docs) plus real-time configuration status.

## Architecture

```
mcp-server/
├── server.py       # FastMCP app; builds one tool per (service, model) from the registry
├── config.py       # .env loading + registry-driven readiness/status report
├── pyproject.toml
├── requirements.txt
├── test_server.py  # offline dry-run tests (no pytest, no network/API keys needed)
└── examples/
    ├── claude_desktop_config.json
    ├── cursor_mcp_config.json
    └── example_usage.py
```

`server.py`'s core trick (`_build_tool_fn`): for each `ModelSpec` in the registry, it builds a real Python function whose `inspect.signature()` has one keyword-only parameter per `Arg` (correct type -- `str`/`int`/`float`/`List[str]`/`Literal[...]` for `choices`/`bool` for flags -- and correct required-ness/default), then registers it with `@mcp.tool`. FastMCP inspects that signature to generate the tool's JSON schema, so the schema is always in sync with the registry with no manual duplication. The function body itself is a one-liner that forwards everything to `tryon.cli.runner.invoke_model(service, model, **kwargs)` -- the same execution path `opentryon <service> --model <model>` uses on the CLI.

## Testing

```bash
python test_server.py
```

Checks (all offline, no API keys or GPU required):
- every registry (service, model) has a corresponding MCP tool, and vice versa
- generated schemas have the right required/optional fields and turn `choices` into JSON schema enums
- representative `dry_run` calls resolve to the expected adapter call across services (vton, generate, edit, understand, video-generate, bg-remove)
- `alt_method_on_image` models (veo/sora/luma-video) switch from text-to-video to image-to-video only when an image is supplied
- unknown service/model and missing-local-extra cases return structured errors instead of raising
- the two discovery tools (`list_opentryon_tools`, `opentryon_status`) work and reject invalid input
- `list_api_keys` / `set_api_keys` report provider status and upsert a temp `.env` without echoing secrets

## Troubleshooting

- **"requires local ML dependencies that aren't installed"** -- run `pip install opentryon[local]` in the same environment the server runs in, and make sure you have a CUDA GPU for the local models that need one.
- **A tool call returns `{"success": false, "error": "..."}`** -- this is by design: adapter/API errors are caught and returned as structured data rather than crashing the MCP connection. Check `error` (and `traceback` for real failures) for details, or call `opentryon_status` to check whether the required API key is set.
- **Tool not appearing** -- restart the server after editing the registry; tools are built once at import time. API keys set via `set_api_keys` (or Connect) update this process immediately.
