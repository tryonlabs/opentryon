---
title: Planner Agent
description: Cheap-LLM intent router that delegates to fashion, model-swap, or virtual try-on specialists.
keywords:
  - planner agent
  - intent classification
  - fashion agent
  - model swap
  - vton
  - tryon studio
---

# Planner Agent

The **planner** is the main entrypoint for OpenTryOn agents (including TryOn Studio chat). It uses a **small LLM** to classify the user request, then hands the job to one specialist and returns that specialist's output to the caller.

```
user query  →  PlannerAgent (cheap LLM)  →  fashion | model_swap | vton
                                          ↘ frontend / MCP (`planner_agent`)
```

Specialists are unchanged:

| Intent | Agent | Typical inputs |
|---|---|---|
| `vton` | [`VTOnAgent`](./vton-agent.md) | person image + garment image |
| `model_swap` | [`ModelSwapAgent`](./model-swap-agent.md) | outfit photo + description of the new model |
| `fashion` | `FashionAgent` | text prompt, optional reference images (generate / edit / video) |
| `clarify` | (none) | planner asks for missing files |
| `out_of_scope` | (none) | planner declines |

The planner does **not** call image/video provider APIs itself. That keeps the routing call cheap.

## Environment

Set these in `opentryon/.env` (see `env.template`). Keys are never collected in TryOn Studio.

```bash
# openai | anthropic | google
OPENTRYON_AGENT_LLM_PROVIDER=openai

# Cheap model for intent only (default: gpt-4o-mini / haiku / gemini-flash)
OPENTRYON_PLANNER_LLM_MODEL=gpt-4o-mini

# Stronger model for the specialist agents
OPENTRYON_AGENT_LLM_MODEL=gpt-4o

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
print(result["intent"], result["message"])
# result["images_base64"] — frontend-ready
```

`dry_run=True` classifies only (no specialist, no image API):

```python
preview = agent.run("Generate a red evening gown", dry_run=True)
# {"intent": "fashion", "agent": "fashion", "dry_run": True, ...}
```

## CLI

```bash
cd examples/agents
python planner_agent.py --prompt "Generate a red evening gown on a runway" --dry-run
python planner_agent.py --prompt "Try this shirt on the model" --person person.jpg --garment shirt.jpg
python planner_agent.py --prompt "Replace with a 30s athletic model" --image outfit.jpg
```

## MCP

TryOn Studio chat calls this tool (restart the MCP server after upgrading):

```
planner_agent(prompt, person_image?, garment_image?, image?, images?, dry_run=false)
```

Returns `success`, `intent`, `agent`, `message`, `images_base64` / `video_base64`. Image arguments accept a path, URL, or base64 string — the same contract as the other OpenTryOn MCP tools.

## Tests

```bash
conda run -n opentryon python tests/test_planner_agent.py
```
