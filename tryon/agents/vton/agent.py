"""Virtual Try-On Agent — VTON recipe over the live registry.

No LangChain tool loop. Defaults to ``kling-ai`` unless the prompt names
another VTON model (FASHN, FLUX VTO, Segmind, …).
"""

from typing import Any, Dict, List, Optional

from tryon.agents.planner.recipes import run_recipe


class VTOnAgent:
    """Registry-backed virtual try-on."""

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
        person_image: str,
        garment_image: str,
        prompt: str,
        verbose: bool = False,
        dry_run: bool = False,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        del verbose, kwargs
        return run_recipe(
            "vton",
            prompt,
            person_image=person_image,
            garment_image=garment_image,
            dry_run=dry_run,
        )

    def generate_and_decode(
        self,
        person_image: str,
        garment_image: str,
        prompt: str,
        **kwargs: Any,
    ) -> List:
        return self.generate(
            person_image=person_image,
            garment_image=garment_image,
            prompt=prompt,
            **kwargs,
        )
