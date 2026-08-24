"""Planner Agent — main entrypoint for OpenTryOn agents.

Classifies the user query with a cheap LLM, then delegates to one of:

- ``FashionAgent`` — generate / edit / video / general fashion work
- ``ModelSwapAgent`` — replace the person, keep the outfit
- ``VTOnAgent`` — compose a garment onto a person photo

The planner does not call image APIs itself. It only routes.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage

from tryon.agents.llm import agent_llm_model, agent_llm_provider, chat_model
from tryon.agents.planner.media import media_from_specialist
from tryon.agents.planner.plan import (
    Plan,
    parse_plan_json,
    present_inputs,
    required_inputs,
)

ClassifyFn = Callable[..., Plan]

SYSTEM_PROMPT = """You route fashion-studio requests to exactly one specialist agent.
Reply with JSON only — no markdown, no extra keys.

Agents:
- "vton": virtual try-on. User wants a garment put on a person. Needs person_image + garment_image.
- "model_swap": replace the person in a photo, keep the clothes. Needs an image of someone wearing an outfit plus a description of the new model.
- "fashion": generate or edit fashion imagery / video from a text prompt (and optional reference images). Catch-all for catalog shots, garment generation, lookbooks, edits that are not try-on or model-swap.
- "clarify": the task is in scope but a required input is missing. List missing_inputs.
- "out_of_scope": not a fashion image/video/try-on/model-swap task.

JSON shape:
{"intent":"vton|model_swap|fashion|clarify|out_of_scope","reason":"short","task":"rewritten specialist prompt","missing_inputs":[]}

Rules:
- Prefer "vton" when a person photo AND a garment photo are present (or clearly implied) and the user wants to try the garment on.
- Prefer "model_swap" when there is one outfit photo and the user wants a different person/model in that same outfit.
- "Generate a model wearing X" from text only is "fashion", not vton.
- Copy the user's request into "task" (cleaned), do not invent new creative direction.
"""


def _content_preview(value: Optional[str]) -> str:
    if not value:
        return "none"
    if value.startswith(("http://", "https://")):
        return value
    if len(value) > 80:
        return f"provided ({len(value)} chars)"
    return value


class PlannerAgent:
    """Intent router in front of FashionAgent / ModelSwapAgent / VTOnAgent."""

    def __init__(
        self,
        llm_provider: Optional[str] = None,
        llm_model: Optional[str] = None,
        specialist_llm_model: Optional[str] = None,
        api_key: Optional[str] = None,
        temperature: float = 0.0,
        classifier: Optional[ClassifyFn] = None,
        **llm_kwargs: Any,
    ):
        self._classifier = classifier
        self._specialists: Dict[str, Any] = {}
        self._api_key = api_key
        self._temperature = temperature
        self.specialist_provider = (llm_provider or agent_llm_provider()).strip().lower()
        self.specialist_model = specialist_llm_model or agent_llm_model("agent")

        if classifier is None:
            self.llm, self.llm_provider, self.planner_model = chat_model(
                role="planner",
                provider=llm_provider,
                model=llm_model,
                api_key=api_key,
                temperature=temperature,
                **llm_kwargs,
            )
        else:
            self.llm = None
            self.llm_provider = self.specialist_provider
            self.planner_model = llm_model or "stub"

    def classify(
        self,
        prompt: str,
        *,
        person_image: Optional[str] = None,
        garment_image: Optional[str] = None,
        image: Optional[str] = None,
        images: Optional[List[str]] = None,
    ) -> Plan:
        available = present_inputs(
            person_image=person_image,
            garment_image=garment_image,
            image=image,
            images=images,
        )
        if self._classifier is not None:
            plan = self._classifier(
                prompt=prompt,
                person_image=person_image,
                garment_image=garment_image,
                image=image,
                images=images,
            )
        else:
            user = (
                f"User request: {prompt}\n"
                f"Inputs present: person_image={available['person_image']}, "
                f"garment_image={available['garment_image']}, image={available['image']}, "
                f"extra_images={len(images) if images else 0}\n"
                f"person_image: {_content_preview(person_image)}\n"
                f"garment_image: {_content_preview(garment_image)}\n"
                f"image: {_content_preview(image)}"
            )
            reply = self.llm.invoke(
                [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user)]
            )
            text = reply.content if isinstance(reply.content, str) else str(reply.content)
            plan = parse_plan_json(text)
        if not plan.task:
            plan.task = prompt
        return self._apply_input_gates(plan, available)

    def _apply_input_gates(self, plan: Plan, available: dict) -> Plan:
        needed = required_inputs(plan.intent)
        missing = [name for name in needed if not available.get(name)]
        if missing:
            original = plan.intent
            plan.intent = "clarify"
            plan.missing_inputs = missing
            plan.reason = plan.reason or f"The {original} agent needs: {', '.join(missing)}."
        return plan

    def _specialist(self, name: str):
        if name in self._specialists:
            return self._specialists[name]
        kwargs = {
            "llm_provider": self.specialist_provider,
            "llm_model": self.specialist_model,
            "temperature": self._temperature,
            "api_key": self._api_key,
        }
        if name == "fashion":
            from tryon.agents.fashion.agent import FashionAgent

            agent = FashionAgent(**kwargs)
        elif name == "model_swap":
            from tryon.agents.model_swap.agent import ModelSwapAgent

            agent = ModelSwapAgent(**kwargs)
        elif name == "vton":
            from tryon.agents.vton.agent import VTOnAgent

            agent = VTOnAgent(**kwargs)
        else:
            raise ValueError(f"Unknown specialist '{name}'")
        self._specialists[name] = agent
        return agent

    def _delegate(
        self,
        plan: Plan,
        *,
        person_image: Optional[str],
        garment_image: Optional[str],
        image: Optional[str],
        images: Optional[List[str]],
        verbose: bool,
    ) -> Dict[str, Any]:
        task = plan.task or ""
        if plan.intent == "vton":
            return self._specialist("vton").generate(
                person_image=person_image or image or "",
                garment_image=garment_image or "",
                prompt=task,
                verbose=verbose,
            )
        if plan.intent == "model_swap":
            return self._specialist("model_swap").generate(
                image=image or person_image or (images[0] if images else ""),
                prompt=task,
                verbose=verbose,
            )
        return self._specialist("fashion").generate(
            prompt=task,
            person_image=person_image,
            garment_image=garment_image,
            image=image or person_image,
            images=images,
            verbose=verbose,
        )

    def run(
        self,
        prompt: str,
        *,
        person_image: Optional[str] = None,
        garment_image: Optional[str] = None,
        image: Optional[str] = None,
        images: Optional[List[str]] = None,
        dry_run: bool = False,
        verbose: bool = False,
    ) -> Dict[str, Any]:
        """Classify ``prompt`` and optionally run the matching specialist.

        Returns a frontend-friendly dict: ``success``, ``intent``, ``agent``,
        ``message``, ``images_base64``, ``video_base64``, ``dry_run``.
        """
        try:
            plan = self.classify(
                prompt,
                person_image=person_image,
                garment_image=garment_image,
                image=image,
                images=images,
            )
        except Exception as exc:
            return {
                "success": False,
                "intent": "clarify",
                "agent": "planner",
                "error": str(exc),
                "message": f"Planner could not classify the request: {exc}",
                "images_base64": [],
                "dry_run": dry_run,
                "planner_model": getattr(self, "planner_model", None),
            }

        payload: Dict[str, Any] = {
            "success": True,
            "intent": plan.intent,
            "agent": "planner" if plan.intent in ("clarify", "out_of_scope") else plan.intent,
            "reason": plan.reason,
            "task": plan.task or prompt,
            "missing_inputs": plan.missing_inputs,
            "images_base64": [],
            "dry_run": dry_run,
            "planner_model": self.planner_model,
            "specialist_model": self.specialist_model,
        }

        if plan.intent == "out_of_scope":
            payload["message"] = (
                plan.reason
                or "I can help with fashion image generation, model swap, and virtual try-on."
            )
            return payload

        if plan.intent == "clarify":
            needed = ", ".join(plan.missing_inputs) or "more detail"
            payload["message"] = plan.reason or f"I need {needed} before I can run this."
            return payload

        if dry_run:
            payload["call"] = f"{plan.intent} agent ← {plan.task or prompt}"
            payload["message"] = (
                f"Would route to the {plan.intent} agent. Set dry_run=false to run it."
            )
            return payload

        result = self._delegate(
            plan,
            person_image=person_image,
            garment_image=garment_image,
            image=image,
            images=images,
            verbose=verbose,
        )
        payload["specialist_status"] = result.get("status")
        if result.get("status") == "error":
            payload["success"] = False
            payload["error"] = result.get("error") or result.get("message") or "Specialist failed."
            payload["message"] = payload["error"]
            return payload

        images_b64, video_b64 = media_from_specialist(result)
        payload["images_base64"] = images_b64
        if video_b64:
            payload["video_base64"] = video_b64
        payload["provider"] = result.get("provider") or result.get("tool")
        message = result.get("result") or result.get("message") or f"Completed via the {plan.intent} agent."
        if isinstance(message, str) and len(message) > 4000:
            message = message[:4000] + "…"
        payload["message"] = message
        return payload


def run_planner(prompt: str, **kwargs: Any) -> Dict[str, Any]:
    """Convenience entrypoint used by the MCP tool and the CLI example."""
    return PlannerAgent().run(prompt, **kwargs)
