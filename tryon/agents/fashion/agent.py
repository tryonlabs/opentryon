"""Fashion Agent — thin recipe over the live registry.

The LangChain ``create_agent`` loop is gone. This class keeps the old
``generate()`` Python API for examples; chat should call ``PlannerAgent``.
"""

from typing import Any, Dict, List, Optional

from tryon.agents.planner.recipes import run_recipe


class FashionAgent:
    """Registry-backed fashion generate / edit / video."""

    def __init__(
        self,
        llm_provider: str = "openai",
        llm_model: Optional[str] = None,
        temperature: float = 0.0,
        api_key: Optional[str] = None,
        **llm_kwargs: Any,
    ):
        self.llm_provider = (llm_provider or "openai").lower()
        self.llm_model = llm_model
        self.temperature = temperature
        self.api_key = api_key
        self._llm_kwargs = llm_kwargs

    def generate(
        self,
        prompt: str,
        person_image: Optional[str] = None,
        garment_image: Optional[str] = None,
        image: Optional[str] = None,
        images: Optional[List[str]] = None,
        verbose: bool = False,
        dry_run: bool = False,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        del verbose, kwargs
        return run_recipe(
            "fashion",
            prompt,
            person_image=person_image,
            garment_image=garment_image,
            image=image,
            images=images,
            dry_run=dry_run,
        )
