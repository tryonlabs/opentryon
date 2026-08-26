"""Planner Agent — Studio chat entrypoint.

Classifies the user query with a cheap LLM, then either answers a help
question from the live registry catalog or runs a **filtered slice** of the
same tools the MCP server exposes (via ``invoke_model``).

The planner is allowed to use every registry tool, but binds one model per
turn: a user-named id (exclusive) or the capability default. Recipes
(VTON / model-swap) rewrite kwargs; other intents call ``invoke_model``
directly. Named models in the prompt (e.g. ``wan-3.0``) pin the registry
id from the full catalog. VTON / model-swap are recipes (defaults +
prompt rewrite), not LangChain agents.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage

from tryon.agents.llm import agent_llm_model, agent_llm_provider, chat_model
from tryon.agents.planner.catalog import (
    FALLBACK_HELP,
    FALLBACK_UNSUPPORTED,
    capabilities_brief,
    models_brief,
    normalize_help_markdown,
    out_of_scope_message,
    strip_emojis,
)
from tryon.agents.planner.media import (
    cleanup_materialized,
    materialize_image,
    media_from_invoke,
    specialist_error_message,
)
from tryon.agents.planner.plan import (
    ACTION_INTENTS,
    Plan,
    clarify_message,
    current_utterance,
    is_capability_question,
    is_unsupported_request,
    parse_plan_json,
    present_inputs,
    required_inputs,
)
from tryon.agents.planner.recipes import execute_call, prepare_call
from tryon.agents.planner.bind import NamedModelUnknown, unknown_model_message

ClassifyFn = Callable[..., Plan]


def _clean_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    for key in ("message", "reason", "error"):
        value = payload.get(key)
        if isinstance(value, str):
            payload[key] = strip_emojis(value)
    return payload


SYSTEM_PROMPT = """You route TryOn Studio chat to exactly one intent.
Reply with JSON only — no markdown, no extra keys.

Intents:
- "vton": virtual try-on. User wants a garment put on a person. Needs person_image + garment_image.
- "model_swap": replace the person in a photo, keep the clothes. Needs an outfit photo plus a description of the new model.
- "generate": text-to-image, no required file.
- "edit": edit or restyle an existing photo. Needs an image.
- "video": text-to-video or image-to-video.
- "understand": caption or ask about an image / video URL.
- "bg_remove": remove background. Needs an image.
- "fashion": catch-all generate/edit/video when the modality is unclear.
- "multi_step": user clearly wants two or more tools in sequence (e.g. remove BG then try-on). The planner may use any registry tool or recipe (vton / model_swap / generate / edit / video / understand / bg_remove) for the primary step.
- "help": greetings, small talk, questions about what this product can do, or a request we cannot perform (3D worlds, games, CAD, audio, code, websites). Not a request to produce an in-scope image or video yet.
- "clarify": the task is a generation/try-on/swap job but a required input is missing. List missing_inputs.
- "out_of_scope": clearly unrelated (weather, math homework, general coding, news). Do not use this for greetings or product questions. Use "help" (not this) when they asked for a creative job we simply do not support.

JSON shape:
{"intent":"vton|model_swap|generate|edit|video|understand|bg_remove|fashion|multi_step|help|clarify|out_of_scope","reason":"short","task":"rewritten specialist prompt","model":"","missing_inputs":[]}

Rules:
- "reason" and "task" are plain text — no emoji.
- "Hi", "hello", "what can you do?", "what tasks?", "which models?" → "help".
- "Can you edit an image?", "Can you perform image understanding?", "do you support try-on?" with no files → "help" (explain), not the action.
- We only do 2D fashion/product images, short video, virtual try-on, model-swap, image/video understanding, and background remove. We do not create 3D worlds, 3D models, games, CAD, audio, music, code, or websites.
- If they ask for something we cannot do — even if they say "generate", "create", or "can you" — use "help". Do NOT run generate/edit/video. The help reply will apologize and list the closest supported tasks.
- "Can you generate a 3d world?", "make a 3D scene", "generate a game" → "help". "Generate a red evening gown" → "generate".
- Prefer "vton" when a person photo AND a garment photo are present (or clearly implied) and the user wants to try the garment on.
- Prefer "model_swap" when there is one outfit photo and the user wants a different person/model in that same outfit.
- "Generate a model wearing X" from text only is "generate" or "fashion", not vton.
- Leave "model" as "" unless the user explicitly named a registry id or alias (wan-3.0, hailuo, kling-ai, nano-banana-pro, sora, flux2-pro, kimi-k2.6, …). Copy that id exactly. Do NOT fill in a default.
- If they named a model, that is the only model to run. If they did not, the planner uses the capability default.
- "How do I try a shirt on?" with no images is "help" (explain), not vton, unless they are clearly asking you to run try-on now.
- Classify the Current request. Previous turns are context only.
- "understand" / "edit" / "bg_remove" / "vton" only when they want you to run that job now. If a required file is missing, use "clarify" and list missing_inputs with a short ask — never set reason to just "missing inputs".
- Copy the user's request into "task" (cleaned), do not invent new creative direction.
"""

HELP_SYSTEM_PROMPT = """You are the OpenTryOn planner in TryOn Studio.
Answer the user using ONLY the capability catalog in the next message.
Be concise, professional, and specific. Plain language only.

Never use emoji, emoticons, kaomoji, or decorative symbols (no smileys, no palettes, no checkmarks).

Format rules (strict):
- Each list item is exactly one line: `- **Label** — short description`
- The hyphen, bold label, em dash, and description MUST stay on the same line.
- One blank line after the intro sentence, then the list, then one closing sentence.
- Do not put a hyphen or a colon on its own line.

Do not invent models, APIs, or features that are not in the catalog.
Do not ask for API keys (they stay in opentryon/.env).
If they greet you, greet back and offer 3–5 things you can do.
If they ask how to run a task, say what to type and which photos to attach.
If they asked for something we cannot do (3D worlds or models, games, CAD, audio, code, websites):
- Open with a short apology that names what we cannot do.
- Then list 3–5 supported tasks closest to what they asked (for a generate-like ask: image generate, video, edit, virtual try-on).
- Do not pretend a tool ran. Do not invent 3D or game features.
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
    """Super agent: classify, bind a registry slice, call invoke_model."""

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
                f"image: {_content_preview(image)}\n\n"
                f"{models_brief()}"
            )
            reply = self.llm.invoke(
                [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user)]
            )
            text = reply.content if isinstance(reply.content, str) else str(reply.content)
            plan = parse_plan_json(text)
        if not plan.task:
            plan.task = prompt
        return self._apply_input_gates(plan, available, prompt)

    def _apply_input_gates(self, plan: Plan, available: dict, prompt: str) -> Plan:
        if plan.intent == "clarify":
            if is_capability_question(prompt):
                plan.intent = "help"
                plan.missing_inputs = []
                plan.reason = "Capability question — explain instead of running."
                return plan
            plan.reason = clarify_message("", plan.missing_inputs)
            return plan
        if plan.intent in ACTION_INTENTS and is_unsupported_request(prompt):
            plan.intent = "help"
            plan.missing_inputs = []
            plan.reason = "Unsupported task — apologize and list related things we can do."
            return plan
        needed = required_inputs(plan.intent)
        missing = [name for name in needed if not available.get(name)]
        if not missing:
            return plan
        if is_capability_question(prompt):
            plan.intent = "help"
            plan.missing_inputs = []
            plan.reason = "Capability question with no files — explain instead of running."
            return plan
        original = plan.intent
        plan.intent = "clarify"
        plan.missing_inputs = missing
        plan.reason = clarify_message(original, missing)
        return plan

    def _answer_help(self, prompt: str) -> str:
        catalog = capabilities_brief()
        fallback = FALLBACK_UNSUPPORTED if is_unsupported_request(prompt) else FALLBACK_HELP
        if self.llm is None:
            return fallback
        try:
            reply = self.llm.invoke(
                [
                    SystemMessage(content=HELP_SYSTEM_PROMPT),
                    HumanMessage(
                        content=(
                            f"Capability catalog:\n{catalog}\n\n"
                            f"User: {current_utterance(prompt) or prompt}\n\n"
                            "Write the assistant reply now. No emoji."
                        )
                    ),
                ]
            )
            text = reply.content if isinstance(reply.content, str) else str(reply.content)
            text = normalize_help_markdown(text)
            return text or fallback
        except Exception:
            return fallback

    def _execute(
        self,
        plan: Plan,
        *,
        prompt: str,
        person_image: Optional[str],
        garment_image: Optional[str],
        image: Optional[str],
        images: Optional[List[str]],
        dry_run: bool,
    ) -> Dict[str, Any]:
        prepared = prepare_call(
            plan.intent,
            plan.task or prompt,
            person_image=person_image,
            garment_image=garment_image,
            image=image,
            images=images,
            hinted_model=plan.model or None,
            mention_text=prompt,
        )
        result = execute_call(prepared, dry_run=dry_run)
        result["service"] = prepared.service
        result["model"] = prepared.model
        result["recipe"] = prepared.recipe
        result["bound"] = prepared.bound_ids
        result["tool"] = (
            f"{prepared.service}_{prepared.model}".replace("-", "_").replace(".", "_")
        )
        result["call"] = result.get("call") or (
            f"invoke_model({prepared.service!r}, {prepared.model!r})"
        )
        return result

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
        """Classify ``prompt`` and run a filtered registry tool.

        Returns a frontend-friendly dict: ``success``, ``intent``, ``agent``,
        ``message``, ``images_base64``, ``video_base64``, ``dry_run``,
        ``service``, ``model``. MCP ``planner_agent`` args are unchanged.
        """
        del verbose  # kept for example-script compatibility
        try:
            plan = self.classify(
                prompt,
                person_image=person_image,
                garment_image=garment_image,
                image=image,
                images=images,
            )
        except Exception as exc:
            return _clean_payload({
                "success": False,
                "intent": "clarify",
                "agent": "planner",
                "error": str(exc),
                "message": f"Planner could not classify the request: {exc}",
                "images_base64": [],
                "dry_run": dry_run,
                "planner_model": getattr(self, "planner_model", None),
            })

        payload: Dict[str, Any] = {
            "success": True,
            "intent": plan.intent,
            "agent": "planner" if plan.intent in ("clarify", "help", "out_of_scope") else plan.intent,
            "reason": plan.reason,
            "task": plan.task or prompt,
            "missing_inputs": plan.missing_inputs,
            "images_base64": [],
            "dry_run": dry_run,
            "planner_model": self.planner_model,
            "specialist_model": self.specialist_model,
        }

        if plan.intent == "out_of_scope":
            payload["message"] = out_of_scope_message(plan.reason)
            return _clean_payload(payload)

        if plan.intent == "help":
            if dry_run:
                payload["call"] = "planner help (catalog-grounded answer)"
                payload["message"] = (
                    "Would answer from the live OpenTryOn catalog. "
                    "Set dry_run=false to write the reply."
                )
                return _clean_payload(payload)
            payload["message"] = normalize_help_markdown(self._answer_help(prompt))
            payload["grounding"] = "registry"
            return _clean_payload(payload)

        if plan.intent == "clarify":
            payload["message"] = plan.reason or clarify_message("", plan.missing_inputs)
            return _clean_payload(payload)

        temps: List[str] = []
        try:
            materialized_images = [
                path
                for path in (materialize_image(item, temps) for item in (images or []))
                if path
            ]
            result = self._execute(
                plan,
                prompt=prompt,
                person_image=materialize_image(person_image, temps),
                garment_image=materialize_image(garment_image, temps),
                image=materialize_image(image, temps),
                images=materialized_images or None,
                dry_run=dry_run,
            )
        except NamedModelUnknown as exc:
            payload["success"] = True
            payload["intent"] = "clarify"
            payload["agent"] = "planner"
            payload["message"] = unknown_model_message(
                exc.name, exc.intent, exc.available
            )
            return _clean_payload(payload)
        finally:
            cleanup_materialized(temps)

        payload["service"] = result.get("service")
        payload["model"] = result.get("model")
        payload["recipe"] = result.get("recipe")
        payload["tool"] = result.get("tool")
        payload["call"] = result.get("call")
        payload["bound"] = result.get("bound") or []

        if result.get("success") is False:
            payload["success"] = False
            payload["error"] = specialist_error_message(
                result.get("error") or result.get("message") or "Registry tool failed."
            )
            payload["message"] = payload["error"]
            return _clean_payload(payload)

        if dry_run:
            payload["message"] = (
                f"Would call {result.get('service')}/{result.get('model')} "
                f"via invoke_model (same runner as MCP). "
                f"Set dry_run=false to run it."
            )
            return _clean_payload(payload)

        images_b64, video_b64 = media_from_invoke(result)
        payload["images_base64"] = images_b64
        if video_b64:
            payload["video_base64"] = video_b64
        payload["provider"] = result.get("model") or result.get("tool")
        message = (
            result.get("result")
            if isinstance(result.get("result"), str)
            else None
        ) or f"Completed via {result.get('service')}/{result.get('model')}."
        if isinstance(message, str) and len(message) > 4000:
            message = message[:4000] + "…"
        payload["message"] = message
        return _clean_payload(payload)


def run_planner(prompt: str, **kwargs: Any) -> Dict[str, Any]:
    """Convenience entrypoint used by the MCP tool and the CLI example."""
    return PlannerAgent().run(prompt, **kwargs)
