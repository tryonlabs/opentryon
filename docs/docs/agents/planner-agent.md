---
title: Planner Agent
description: Super agent for TryOn Studio chat — classifies intent, then runs a filtered slice of the live MCP registry tools.
keywords:
  - planner agent
  - invoke_model
  - fashion agent
  - model swap
  - vton
  - tryon studio
---

# Planner Agent

The **planner** is the main entrypoint for OpenTryOn agents (including TryOn Studio chat). It uses a **small LLM** to classify the user request, then either **answers a help question from the live model catalog** or **runs one of the same tools the MCP server exposes** (`invoke_model`).

Capability screens (Image, VTON, Video, …) still call MCP model tools directly. Chat only calls `planner_agent`. Studio does not grow a second tool-calling loop.

```
user query  →  PlannerAgent (cheap LLM classify)
                 ├─ help / clarify / out_of_scope
                 ├─ bind: named model (full catalog) OR capability default
                 └─ invoke_model(service, model, **kwargs)
                      same runner as MCP `vton_kling_ai`, `video_generate_wan_3_0`, …
                      recipes: vton (person + garment), model_swap (outfit rewrite)
```

There is **no vector RAG index**. Help is grounded in `tryon.cli.registry`. Questions like “what is Hy4 preview?” resolve the registry id (hyphenated ids match spaced names) and reply from that model’s `label` / `notes` instead of asking the help LLM to guess.

## Model choice

Each capability has a **default model**. The planner uses that default unless the user names a model in the prompt.

| Task | Intent | Default |
|---|---|---|
| Virtual try-on | `vton` | `vton` / `kling-ai` |
| Image generation | `generate` / `fashion` | `generate` / `nano-banana-pro` |
| Image editing | `edit` | `edit` / `nano-banana-pro` |
| Model swap | `model_swap` | `edit` / `nano-banana-pro` |
| Image understanding | `understand` | `understand` / `kimi-k2.6` |
| Video generation | `video` | `video-generate` / `sora` |
| Background remove | `bg_remove` | `bg-remove` / `ben2` |

- **User named a model** (for example `wan-3.0`, `google-vton`, `outfitanyone-plus`, `photoroom-vton`, `leffa`, `catvton`, `flux2-pro`, `p-image-ideogram`, `nemotron-omni`, `cosmos3`, `seedance`, `hy4-preview`) → that registry id **only**, even if it lives in another capability. An unknown name is **not** replaced by the default; the planner asks you to pick a real id. `p-image-ideogram` pins Pruna’s model; a bare `ideogram` still pins Ideogram 4.0. `cosmos3-reasoner` pins the VLM, not the Generator. `google-vton` / `virtual-try-on-001` pin Vertex dedicated try-on, not Nano Banana. `aitryon-plus` / `outfitanyone-plus` pin OutfitAnyone-Plus, not Qwen-Image. `photoroom virtual model` pins catalog on-model; a bare `photoroom` pins shopper try-on. `leffa` / `catvton` pin local dedicated VTON (GPU extra). `seedance` / `seedance 2.5` pin BytePlus ModelArk video. `hy4-preview-local` / `hy4 local` pin the vLLM twin; a bare `hy4` / `hy4-preview` pins TokenHub.
- **No model named** → the default in the table.
- The classifier must leave `model` empty unless the user named one. A leaked default in `plan.model` is ignored unless that id also appears in the prompt.

The planner can use **any** registry tool for a turn (named models search the full catalog). Recipes (`VTOnAgent`, `FashionAgent`, `ModelSwapAgent`) are thin facades over the same `invoke_model` path. A `multi_step` intent is recognized but does **not** yet chain tools — it binds a wide slice and runs a single `invoke_model`.

| Intent | Typical inputs | Tool path |
|---|---|---|
| `vton` | person image + garment image | recipe → default or named VTON model |
| `model_swap` | outfit photo + new-person description | recipe (outfit-preserving rewrite) |
| `generate` / `fashion` | text prompt | `invoke_model` |
| `edit` | image + instruction | `invoke_model` |
| `video` | text, optional first frame | `invoke_model` |
| `understand` | image or video URL | `invoke_model` |
| `bg_remove` | image | `invoke_model` |
| `multi_step` | two or more tools (e.g. BG then try-on) | one `invoke_model` today |
| `help` | greetings, how-to, “what is \<model\>?”, or an unsupported ask (e.g. 3D world) | catalog answer (named models use registry `label` / `notes`); no `invoke_model` |
| `clarify` | missing files | planner asks for the photo(s), not “missing inputs” |
| `out_of_scope` | unrelated | planner declines |

`FashionAgent`, `VTOnAgent`, and `ModelSwapAgent` remain as thin Python facades over the same recipes for example scripts. Prefer `PlannerAgent` for new code.

## Environment

Set these in `opentryon/.env` (see `env.template`). Keys are never collected in TryOn Studio.

```bash
# openai | anthropic | google
OPENTRYON_AGENT_LLM_PROVIDER=openai

# Cheap model for intent only (default: gpt-4o-mini / haiku / gemini-flash)
OPENTRYON_PLANNER_LLM_MODEL=gpt-4o-mini
# OPENTRYON_AGENT_LLM_MODEL=gpt-4o-mini  # fallback if PLANNER model is unset

# Matching provider key (already in this file for image APIs):
OPENAI_API_KEY=...
# ANTHROPIC_API_KEY=...
# GEMINI_API_KEY=...   # or GOOGLE_API_KEY

# Optional OpenAI-compatible host (Moonshot, DashScope compatible mode, …)
# OPENTRYON_AGENT_LLM_BASE_URL=https://api.moonshot.ai/v1
# OPENTRYON_AGENT_LLM_API_KEY=...
```

## Python

```python
from tryon.agents.planner import PlannerAgent

agent = PlannerAgent()  # reads .env
result = agent.run(
    "Try this shirt on the model",
    person_image="person.jpg",
    garment_image="shirt.jpg",
)
print(result["intent"], result["model"], result["message"])
# result["images_base64"] — frontend-ready
```

`dry_run=True` classifies and resolves the registry call without spending API credits:

```python
preview = agent.run("Generate a clip using wan-3.0", dry_run=True)
# {"intent": "fashion"|"video", "service": "video-generate", "model": "wan-3.0", "dry_run": True, ...}
```

## CLI

```bash
cd examples/agents
python planner_agent.py --prompt "Generate a red evening gown on a runway" --dry-run
python planner_agent.py --prompt "Generate a clip using wan-3.0" --dry-run
python planner_agent.py --prompt "Try this shirt on the model" --person person.jpg --garment shirt.jpg
python planner_agent.py --prompt "Replace with a 30s athletic model" --image outfit.jpg
```

## MCP

TryOn Studio chat calls this tool (restart the MCP server after upgrading). **Argument schema is unchanged:**

```
planner_agent(prompt, person_image?, garment_image?, image?, images?, dry_run=false)
```

Returns `success`, `intent`, `agent`, `message`, `images_base64` / `video_base64`, plus `service` / `model` / `call` when a registry tool was bound. Image arguments accept a path, URL, or base64 string — the same contract as the other OpenTryOn MCP tools.

**Large chat uploads:** TryOn Studio sends photos as base64. The planner **does not** paste those bytes into the classifier LLM. Before `invoke_model` runs, each image is written to a temp file and downscaled to **2048px** on the long edge. Restart MCP after upgrading so this path is live.

## Tests

```bash
conda run -n opentryon python tests/test_planner_agent.py
```
