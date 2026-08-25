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

The **planner** is the main entrypoint for OpenTryOn agents (including TryOn Studio chat). It uses a **small LLM** to classify the user request, then either **answers a help question from the live model catalog** or **runs a filtered slice of the same tools the MCP server exposes** (`invoke_model`).

Capability screens (Image, VTON, Video, …) still call MCP model tools directly. Chat only calls `planner_agent`. Studio does not grow a second tool-calling loop.

```
user query  →  PlannerAgent (cheap LLM classify)
                 ├─ help / clarify / out_of_scope
                 ├─ bind filtered registry slice (never all ~66 tools at once)
                 └─ invoke_model(service, model, **kwargs)
                      same runner as MCP `vton_kling_ai`, `video_generate_wan_3_0`, …
```

There is **no vector RAG index**. Help is grounded in `tryon.cli.registry`. Named models in the prompt (for example `wan-3.0`) pin that registry id, so chat can run tools the capability UI already has.

VTON and model-swap are **recipes** (defaults + outfit-preserving prompt rewrite), not LangChain agents.

| Intent | Typical inputs | Default tool |
|---|---|---|
| `vton` | person image + garment image | `vton` / `kling-ai` |
| `model_swap` | outfit photo + new-person description | `edit` / `nano-banana-pro` |
| `generate` / `fashion` | text prompt | `generate` / `nano-banana-pro` |
| `edit` | image + instruction | `edit` / `nano-banana-pro` |
| `video` | text, optional first frame | `video-generate` / `sora` |
| `understand` | image or video URL | `understand` / `kimi-k2.6` |
| `bg_remove` | image | `bg-remove` / `ben2` |
| `multi_step` | two or more tools (e.g. BG then try-on) | classified; **currently one** `invoke_model` (default generate) |
| `clarify` | missing files | planner asks |
| `out_of_scope` | unrelated | planner declines |

`FashionAgent`, `VTOnAgent`, and `ModelSwapAgent` remain as thin Python facades over the same recipes for example scripts. Prefer `PlannerAgent` for new code. A `multi_step` intent is recognized but does **not** yet chain tools — it binds a wide slice and runs a single `invoke_model`.

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
