---
title: Model Swap Agent
description: Outfit-preserving edit recipe over invoke_model. Prefer PlannerAgent for chat.
keywords:
  - model swap agent
  - nano banana
  - invoke_model
  - outfit preservation
---

# Model Swap Agent

`ModelSwapAgent` keeps the **outfit-preserving prompt rewrite**, then calls the live registry. It is not a LangChain tool loop. For Studio chat, call [`PlannerAgent`](./planner-agent.md) / MCP `planner_agent`.

Default model: **`edit` / `nano-banana-pro`**. Pass `model="flux2-pro"` (or name a model in the prompt via the planner) to pin another generate/edit id.

```python
from tryon.agents.model_swap import ModelSwapAgent

agent = ModelSwapAgent()
result = agent.generate(
    image="outfit.jpg",
    prompt="Replace with a 30s athletic model",
    dry_run=True,
)
print(result["recipe"], result["model"])
# swap  nano-banana-pro
```

The rewritten prompt insists on keeping clothing, lighting, and composition. Execution is `invoke_model("edit", "nano-banana-pro", image=…, prompt=…)`.

See [Planner Agent](./planner-agent.md) for chat and MCP.
