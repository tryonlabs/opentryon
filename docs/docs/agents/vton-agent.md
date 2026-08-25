---
title: Virtual Try-On Agent
description: Thin VTON recipe over invoke_model. Prefer PlannerAgent for chat.
keywords:
  - virtual try-on agent
  - vton
  - kling ai
  - invoke_model
---

# Virtual Try-On Agent

`VTOnAgent` is a **thin Python facade** over the live registry. It is not a LangChain tool loop. For Studio chat, call [`PlannerAgent`](./planner-agent.md) / MCP `planner_agent`.

Default model: **`kling-ai`**. A named model in the prompt (FASHN, FLUX VTO, Segmind, Qwen-Image, …) pins that VTON registry id.

```python
from tryon.agents.vton import VTOnAgent

agent = VTOnAgent()
result = agent.generate(
    person_image="person.jpg",
    garment_image="shirt.jpg",
    prompt="Use FASHN",
    dry_run=True,
)
print(result["service"], result["model"], result.get("call"))
# vton  fashn-tryon-max  ...
```

Live path: `run_recipe("vton", …)` → `invoke_model("vton", model, …)` — the same runner as MCP `vton_kling_ai`.

See [Planner Agent](./planner-agent.md) for chat, filtering, and MCP.
