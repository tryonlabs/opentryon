# Fashion Agent

`FashionAgent` is a **thin facade** over the live registry (`invoke_model`). It is not a LangChain tool-calling loop.

For TryOn Studio chat and new code, use **`PlannerAgent`** — it classifies intent, binds a filtered registry slice, and runs the same tools the MCP server exposes.

```python
from tryon.agents.fashion import FashionAgent

agent = FashionAgent()
result = agent.generate(
    prompt="Generate a red evening gown on a runway",
    dry_run=True,
)
print(result["service"], result["model"])
# generate  nano-banana-pro
```

Named models in the prompt (for example `wan-3.0`) pin that registry id, including video models.

See `docs/docs/agents/planner-agent.md`.
