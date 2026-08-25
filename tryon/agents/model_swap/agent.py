"""Model Swap Agent — outfit-preserving edit recipe over the live registry.

Keeps the prompt rewrite from the old LangChain agent, then calls
``invoke_model`` on ``nano-banana-pro`` (or a named edit/generate model).
"""

from typing import Any, Dict, Optional

from tryon.agents.planner.recipes import run_recipe


class ModelSwapAgent:
    """Registry-backed model swap (new person, same outfit)."""

    def __init__(
        self,
        llm_provider: str = "openai",
        llm_model: Optional[str] = None,
        temperature: float = 0.0,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        **llm_kwargs: Any,
    ):
        self.llm_provider = (llm_provider or "openai").lower()
        self.llm_model = llm_model
        self.temperature = temperature
        self.api_key = api_key
        self.model = (model or "nano-banana-pro").lower().replace(" ", "-").replace("_", "-")
        self._llm_kwargs = llm_kwargs

    def generate(
        self,
        image: str,
        prompt: str,
        resolution: Optional[str] = None,
        use_search_grounding: bool = False,
        verbose: bool = False,
        dry_run: bool = False,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        del resolution, use_search_grounding, verbose, kwargs
        return run_recipe(
            "model_swap",
            prompt,
            image=image,
            hinted_model=self.model,
            dry_run=dry_run,
        )
