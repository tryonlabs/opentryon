"""Offline tests for the planner agent (no live LLM / image APIs).

Run:
    conda run -n opentryon python tests/test_planner_agent.py
"""
from __future__ import annotations

import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from tryon.agents.planner.plan import (
    Plan,
    clarify_message,
    is_capability_question,
    is_unsupported_request,
    parse_plan_json,
    required_inputs,
)
from tryon.agents.planner.agent import PlannerAgent
from tryon.agents.planner.media import encode_images, encode_one_image


def check_parse_plan_json_raw_and_fenced():
    plan = parse_plan_json('{"intent":"vton","reason":"try on","task":"try the shirt"}')
    assert plan.intent == "vton" and plan.task == "try the shirt"

    plan = parse_plan_json(
        'Sure.\n```json\n{"intent":"model_swap","reason":"swap","task":"asian model 30s"}\n```'
    )
    assert plan.intent == "model_swap"

    plan = parse_plan_json('{"intent":"try_on","task":"x"}')
    assert plan.intent == "vton"
    plan = parse_plan_json('{"intent":"capabilities","task":"what can you do"}')
    assert plan.intent == "help"
    print("\u2713 parse_plan_json handles raw, fenced, and alias intents")


def check_parse_rejects_unknown_intent():
    try:
        parse_plan_json('{"intent":"weather"}')
    except ValueError as exc:
        assert "Unknown intent" in str(exc)
    else:
        raise AssertionError("expected ValueError")
    print("\u2713 unknown intent is rejected")


def check_vton_without_images_clarifies():
    agent = PlannerAgent(
        classifier=lambda **kwargs: Plan(intent="vton", task=kwargs["prompt"], reason="try-on")
    )
    result = agent.run("Try this shirt on the model", dry_run=True)
    assert result["intent"] == "clarify"
    assert "person_image" in result["missing_inputs"]
    assert "garment_image" in result["missing_inputs"]
    assert result["success"] is True
    print("\u2713 vton without images asks to clarify")


def check_vton_dry_run_routes():
    agent = PlannerAgent(
        classifier=lambda **kwargs: Plan(intent="vton", task=kwargs["prompt"], reason="try-on")
    )
    result = agent.run(
        "Try the garment on the person",
        person_image="person.jpg",
        garment_image="shirt.jpg",
        dry_run=True,
    )
    assert result["intent"] == "vton"
    assert result["agent"] == "vton"
    assert result["dry_run"] is True
    assert result["service"] == "vton"
    assert result["model"] == "kling-ai"
    assert "invoke_model" in result["message"]
    assert "KlingAIVTONAdapter" in (result.get("call") or "")
    print("\u2713 vton with both images dry-runs kling-ai via invoke_model")


def check_model_swap_and_fashion_dry_run():
    swap = PlannerAgent(
        classifier=lambda **kwargs: Plan(intent="model_swap", task=kwargs["prompt"])
    ).run("Replace with a 30s athletic model", image="outfit.jpg", dry_run=True)
    assert swap["intent"] == "model_swap" and swap["agent"] == "model_swap"
    assert swap["service"] == "edit" and swap["model"] == "nano-banana-pro"
    assert "exact same outfit" in (swap.get("call") or "").lower() or swap.get("recipe") == "swap"

    fashion = PlannerAgent(
        classifier=lambda **kwargs: Plan(intent="fashion", task=kwargs["prompt"])
    ).run("Generate a red evening gown on a runway", dry_run=True)
    assert fashion["intent"] == "fashion" and fashion["agent"] == "fashion"
    assert fashion["service"] == "generate" and fashion["model"] == "nano-banana-pro"
    print("\u2713 model_swap and fashion dry-run via invoke_model recipes")


def check_named_model_wan_30_dry_run():
    agent = PlannerAgent(
        classifier=lambda **kwargs: Plan(intent="fashion", task=kwargs["prompt"])
    )
    result = agent.run("Generate a clip using wan-3.0", dry_run=True)
    assert result["success"] is True
    assert result["dry_run"] is True
    assert result["service"] == "video-generate"
    assert result["model"] == "wan-3.0"
    assert "WanVideoAdapter" in (result.get("call") or "")
    print("\u2713 named-model chat dry-runs wan-3.0 via invoke_model")


def check_named_model_nvidia_nim_dry_run():
    agent = PlannerAgent(
        classifier=lambda **kwargs: Plan(intent="video", task=kwargs["prompt"])
    )
    result = agent.run("Generate a clip using cosmos3", dry_run=True)
    assert result["success"] is True
    assert result["service"] == "video-generate"
    assert result["model"] == "cosmos3"
    assert "Cosmos3VideoAdapter" in (result.get("call") or "")

    from tryon.agents.planner.bind import match_named_model, slice_for_intent

    fashion = slice_for_intent("fashion")
    pinned = match_named_model("describe this with cosmos3-reasoner", fashion)
    assert pinned is not None and pinned.model == "cosmos3-reasoner"
    omni = match_named_model("use nemotron-omni on this photo", fashion)
    assert omni is not None and omni.model == "nemotron-omni"
    print("\u2713 named-model chat dry-runs cosmos3 and pins cosmos3-reasoner / nemotron-omni")


def check_out_of_scope_does_not_delegate():
    agent = PlannerAgent(
        classifier=lambda **kwargs: Plan(intent="out_of_scope", reason="not fashion")
    )
    called = {"n": 0}

    def boom(*_a, **_k):
        called["n"] += 1
        raise AssertionError("registry tool should not run")

    agent._execute = boom  # type: ignore[method-assign]
    result = agent.run("What's the weather in Paris?")
    assert result["intent"] == "out_of_scope"
    assert called["n"] == 0
    assert "virtual try-on" in result["message"].lower() or "fashion" in result["message"].lower()
    assert "no fashion-related inputs" not in result["message"].lower()
    print("\u2713 out_of_scope never calls invoke_model")


def check_help_answers_without_specialist():
    from tryon.agents.planner.catalog import FALLBACK_HELP, capabilities_brief

    brief = capabilities_brief()
    assert "vton" in brief and "generate" in brief and "video-generate" in brief

    agent = PlannerAgent(
        classifier=lambda **kwargs: Plan(intent="help", reason="capability question", task=kwargs["prompt"])
    )
    called = {"n": 0}

    def boom(*_a, **_k):
        called["n"] += 1
        raise AssertionError("registry tool should not run")

    agent._execute = boom  # type: ignore[method-assign]
    result = agent.run("What all tasks can you complete?")
    assert result["success"] is True
    assert result["intent"] == "help"
    assert result["agent"] == "planner"
    assert called["n"] == 0
    assert "virtual try-on" in result["message"].lower() or "try-on" in result["message"].lower()
    dry = agent.run("Hi", dry_run=True)
    assert dry["intent"] == "help" and dry["dry_run"] is True
    assert FALLBACK_HELP.startswith("Hi")
    print("\u2713 help answers from the catalog and never calls invoke_model")


def check_normalize_help_markdown():
    from tryon.agents.planner.catalog import normalize_help_markdown

    messy = (
        "Hello! Here are a few things I can help you with:\n"
        "\n"
        "-\n"
        "**Virtual Try-On**\n"
        ": Compose a garment onto a person image.\n"
        "-\n"
        "**Image Generation**\n"
        ": Create images from text prompts.\n"
        "-\n"
        "Let me know what you'd like to do!\n"
    )
    out = normalize_help_markdown(messy)
    assert "- **Virtual Try-On**: Compose a garment onto a person image." in out
    assert "- **Image Generation**: Create images from text prompts." in out
    assert "\n-\n" not in f"\n{out}\n"
    assert not any(line.strip() == "-" for line in out.splitlines())
    assert "- Let me know" not in out
    print("\u2713 help markdown collapses hyphen / label / description onto one line")


def check_strip_emojis():
    from tryon.agents.planner.catalog import normalize_help_markdown, strip_emojis

    assert strip_emojis("Yes, I can generate an image! 🎨 To get started:") == (
        "Yes, I can generate an image! To get started:"
    )
    cleaned = normalize_help_markdown(
        "Absolutely! Here's what I can do: 😊\n- **Virtual Try-On** — compose a garment."
    )
    assert "😊" not in cleaned and "🎨" not in cleaned
    assert "Here's what I can do:" in cleaned
    print("\u2713 emoji are stripped from planner replies")


def check_required_inputs():
    assert required_inputs("vton") == ("person_image", "garment_image")
    assert required_inputs("model_swap") == ("image",)
    assert required_inputs("edit") == ("image",)
    assert required_inputs("bg_remove") == ("image",)
    assert required_inputs("understand") == ("image",)
    assert required_inputs("fashion") == ()
    assert required_inputs("video") == ()
    assert required_inputs("help") == ()
    print("\u2713 required_inputs per intent")


def check_understand_without_image_clarifies():
    agent = PlannerAgent(
        classifier=lambda **kwargs: Plan(intent="understand", task=kwargs["prompt"])
    )
    result = agent.run("What do you see in this photo?", dry_run=True)
    assert result["intent"] == "clarify"
    assert result["success"] is True
    assert "image" in result["missing_inputs"]
    assert "attach" in result["message"].lower()
    assert "missing inputs" not in result["message"].lower()
    print("\u2713 understand without an image asks to attach one")


def check_capability_questions_are_help():
    assert is_capability_question("Can you perform image understanding?")
    assert is_capability_question("Can you edit an image?")
    assert is_capability_question("Current request: Can you edit an image?\nQuick action: edit")
    assert not is_capability_question("Edit this photo to make the sky blue")

    agent = PlannerAgent(
        classifier=lambda **kwargs: Plan(intent="understand", task=kwargs["prompt"], reason="run understand")
    )
    called = {"n": 0}

    def boom(*_a, **_k):
        called["n"] += 1
        raise AssertionError("registry tool should not run")

    agent._execute = boom  # type: ignore[method-assign]
    result = agent.run("Can you perform image understanding?")
    assert result["intent"] == "help"
    assert result["success"] is True
    assert called["n"] == 0

    edit = PlannerAgent(
        classifier=lambda **kwargs: Plan(intent="edit", task=kwargs["prompt"], reason="missing inputs")
    )
    edit._execute = boom  # type: ignore[method-assign]
    asked = edit.run("Can you edit an image?")
    assert asked["intent"] == "help"
    assert called["n"] == 0
    print("\u2713 capability questions become help, not invoke or 'missing inputs'")


def check_unsupported_generate_is_help():
    from tryon.agents.planner.catalog import FALLBACK_UNSUPPORTED

    assert is_unsupported_request("Can you generate a 3d World?")
    assert is_unsupported_request("Current request: generate a 3D scene\nPrevious turns: hi")
    assert not is_unsupported_request("Generate a red evening gown on a runway")

    agent = PlannerAgent(
        classifier=lambda **kwargs: Plan(intent="generate", task=kwargs["prompt"])
    )
    called = {"n": 0}

    def boom(*_a, **_k):
        called["n"] += 1
        raise AssertionError("registry tool should not run")

    agent._execute = boom  # type: ignore[method-assign]
    result = agent.run("Can you generate a 3d World?")
    assert result["intent"] == "help"
    assert result["success"] is True
    assert called["n"] == 0
    lowered = result["message"].lower()
    assert "sorry" in lowered
    assert "image generate" in lowered or "generate" in lowered
    assert FALLBACK_UNSUPPORTED.startswith("Sorry")
    print("\u2713 unsupported generate asks apologize and list related tasks")


def check_clarify_message_is_human():
    assert "garment" in clarify_message("vton", ["person_image", "garment_image"]).lower()
    assert "attach" in clarify_message("edit", ["image"]).lower()
    assert clarify_message("edit", ["image"]).lower() != "missing inputs"
    print("\u2713 clarify copy asks for the file instead of 'missing inputs'")


def check_llm_clarify_junk_reason_is_rewritten():
    agent = PlannerAgent(
        classifier=lambda **kwargs: Plan(intent="clarify", reason="missing inputs", missing_inputs=[])
    )
    result = agent.run("Can you edit an image?")
    assert result["intent"] == "help"
    result2 = PlannerAgent(
        classifier=lambda **kwargs: Plan(intent="clarify", reason="missing inputs", missing_inputs=["image"])
    ).run("Edit this photo")
    assert result2["intent"] == "clarify"
    assert "attach" in result2["message"].lower()
    assert "missing inputs" not in result2["message"].lower()
    print("\u2713 classifier 'missing inputs' is rewritten")


def check_bind_filters_registry_slice():
    from tryon.agents.planner.bind import (
        NamedModelUnknown,
        match_named_model,
        pick_model,
        slice_for_intent,
    )

    vton = slice_for_intent("vton")
    assert all(item.service == "vton" for item in vton)
    assert any(item.model == "kling-ai" for item in vton)
    assert not any(item.model == "wan-3.0" for item in vton)

    fashion = slice_for_intent("fashion")
    services = {item.service for item in fashion}
    assert services == {"generate", "edit", "video-generate"}
    named = match_named_model("use wan-3.0 please", fashion)
    assert named is not None and named.model == "wan-3.0" and named.service == "video-generate"

    pii = pick_model("generate", "poster with p-image-ideogram")
    assert pii is not None and pii.model == "p-image-ideogram" and pii.service == "generate"
    ideo = pick_model("generate", "poster with ideogram")
    assert ideo is not None and ideo.model == "ideogram"

    picked = pick_model("video", "runway gen 4.5 clip")
    assert picked is not None and picked.model == "runway-gen4.5"
    default_vton = pick_model("vton", "try this on")
    assert default_vton is not None and default_vton.model == "kling-ai"
    print("\u2713 bind filters slices and pins named models")

    assert pick_model("generate", "a red evening gown").model == "nano-banana-pro"
    assert pick_model("edit", "make the sky blue").model == "nano-banana-pro"
    assert pick_model("understand", "what is in this photo").model == "kimi-k2.6"
    assert pick_model("video", "runway walk clip").model == "sora"
    assert pick_model("bg_remove", "remove the background").model == "ben2"
    named_gen = pick_model("generate", "Generate a clip using wan-3.0")
    assert named_gen is not None and named_gen.model == "wan-3.0"
    leaked = pick_model("generate", "a red evening gown", hinted="wan-3.0")
    assert leaked is not None and leaked.model == "nano-banana-pro"
    try:
        pick_model("generate", "use foobar-9000 please", hinted="foobar-9000")
    except NamedModelUnknown as exc:
        assert exc.name == "foobar-9000"
    else:
        raise AssertionError("expected NamedModelUnknown")
    gpt = pick_model(
        "edit",
        "edit this image using gpt-image. Change male to female in this image.",
        hinted="nano-banana-pro",
    )
    assert gpt is not None and gpt.model == "gpt-image" and gpt.service == "edit"

    polluted = pick_model(
        "edit",
        "Current request: edit this image using gpt-image. Change male to female.\n"
        "Previous turns (context only; classify the Current request):\n"
        "Assistant: Completed via generate/nano-banana-pro.",
        hinted="nano-banana-pro",
    )
    assert polluted is not None and polluted.model == "gpt-image"

    from tryon.agents.planner.recipes import prepare_call

    prepared = prepare_call(
        "edit",
        "Change male to female",
        image="photo.jpg",
        mention_text="edit this image using gpt-image.",
        hinted_model="nano-banana-pro",
    )
    assert prepared.model == "gpt-image" and prepared.service == "edit"
    assert prepared.kwargs.get("images") == ["photo.jpg"]

    flux = prepare_call(
        "edit",
        "Change the garment to a saree",
        image="photo.jpg",
        mention_text="Edit this image using flux 2 pro model.",
    )
    assert flux.model == "flux2-pro" and flux.service == "edit"
    assert flux.kwargs.get("input_image") == "photo.jpg"
    print("\u2713 unnamed tasks use capability defaults; named model is exclusive")


def check_capability_defaults_via_planner():
    generate = PlannerAgent(
        classifier=lambda **kwargs: Plan(intent="generate", task=kwargs["prompt"], model="wan-3.0")
    ).run("Generate a red evening gown", dry_run=True)
    assert generate["model"] == "nano-banana-pro"
    assert generate["service"] == "generate"

    video = PlannerAgent(
        classifier=lambda **kwargs: Plan(intent="video", task=kwargs["prompt"])
    ).run("Make a short runway clip", dry_run=True)
    assert video["model"] == "sora" and video["service"] == "video-generate"

    understand = PlannerAgent(
        classifier=lambda **kwargs: Plan(intent="understand", task=kwargs["prompt"])
    ).run("What is in this photo?", image="photo.jpg", dry_run=True)
    assert understand["model"] == "kimi-k2.6" and understand["service"] == "understand"

    edit = PlannerAgent(
        classifier=lambda **kwargs: Plan(intent="edit", task=kwargs["prompt"])
    ).run("Make the sky blue", image="photo.jpg", dry_run=True)
    assert edit["model"] == "nano-banana-pro" and edit["service"] == "edit"

    named = PlannerAgent(
        classifier=lambda **kwargs: Plan(intent="generate", task=kwargs["prompt"], model="wan-3.0")
    ).run("Generate a clip using wan-3.0", dry_run=True)
    assert named["model"] == "wan-3.0" and named["service"] == "video-generate"

    gpt_edit = PlannerAgent(
        classifier=lambda **kwargs: Plan(
            intent="edit", task="Change male to female", model="nano-banana-pro"
        )
    ).run(
        "edit this image using gpt-image. Change male to female in this image.",
        image="photo.jpg",
        dry_run=True,
    )
    assert gpt_edit["model"] == "gpt-image" and gpt_edit["service"] == "edit"

    unknown = PlannerAgent(
        classifier=lambda **kwargs: Plan(intent="generate", task=kwargs["prompt"], model="foobar-9000")
    ).run("Generate a look using foobar-9000", dry_run=True)
    assert unknown["intent"] == "clarify"
    assert unknown["success"] is True
    assert "foobar-9000" in unknown["message"]
    assert unknown.get("model") in (None, "")
    print("\u2713 planner defaults vs named vs unknown model")


def check_encode_images_png_bytes():
    png = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00"
        b"\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00"
        b"\x00\x00\x00IEND\xaeB`\x82"
    )
    encoded = encode_images([png])
    assert len(encoded) == 1 and encode_one_image(encoded[0]) == encoded[0]
    print("\u2713 encode_images round-trips PNG bytes to base64")


def check_materialize_image_downscales_base64():
    import base64
    import io
    from PIL import Image
    from tryon.agents.planner.media import (
        cleanup_materialized,
        materialize_image,
        specialist_error_message,
    )

    assert materialize_image(None) is None
    assert materialize_image("person.jpg") == "person.jpg"
    assert materialize_image("https://cdn.example/a.jpg") == "https://cdn.example/a.jpg"

    tiny = io.BytesIO()
    Image.new("RGB", (8, 8), (255, 0, 0)).save(tiny, format="PNG")
    temps: list[str] = []
    encoded = base64.b64encode(tiny.getvalue()).decode()
    path = materialize_image(encoded, temps)
    assert path and os.path.isfile(path) and path != encoded
    cleanup_materialized(temps)
    assert not os.path.isfile(path)

    buf = io.BytesIO()
    Image.new("RGB", (3000, 1200), (10, 20, 30)).save(buf, format="JPEG")
    temps = []
    path = materialize_image(base64.b64encode(buf.getvalue()).decode(), temps)
    with Image.open(path) as img:
        assert max(img.size) <= 2048
        assert img.size[0] == 2048
    cleanup_materialized(temps)

    err = (
        "Error code: 429 - {'error': {'message': 'Request too large for gpt-4o "
        "on tokens per min (TPM): Limit 30000, Requested 139669.', "
        "'code': 'rate_limit_exceeded'}}"
    )
    assert "2048" in specialist_error_message(err)
    moon = specialist_error_message(
        "ValueError: Moonshot API key must be provided either as a parameter "
        "or through the MOONSHOT_API_KEY environment variable."
    )
    assert "MOONSHOT_API_KEY" in moon
    assert "opentryon/.env" in moon
    assert "ValueError" not in moon
    quota = specialist_error_message(
        "ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, "
        "'message': 'You exceeded your current quota.\\n* Quota exceeded', "
        "'status': 'RESOURCE_EXHAUSTED'}}"
    )
    assert "\n" in quota
    assert '"code": 429' in quota
    print("\u2713 chat base64 uploads become downscaled temp files, not LLM tokens")


def main():
    check_parse_plan_json_raw_and_fenced()
    check_parse_rejects_unknown_intent()
    check_vton_without_images_clarifies()
    check_vton_dry_run_routes()
    check_model_swap_and_fashion_dry_run()
    check_named_model_wan_30_dry_run()
    check_named_model_nvidia_nim_dry_run()
    check_out_of_scope_does_not_delegate()
    check_help_answers_without_specialist()
    check_normalize_help_markdown()
    check_strip_emojis()
    check_required_inputs()
    check_understand_without_image_clarifies()
    check_capability_questions_are_help()
    check_unsupported_generate_is_help()
    check_clarify_message_is_human()
    check_llm_clarify_junk_reason_is_rewritten()
    check_bind_filters_registry_slice()
    check_capability_defaults_via_planner()
    check_encode_images_png_bytes()
    check_materialize_image_downscales_base64()
    print("\nAll planner agent checks passed.")


if __name__ == "__main__":
    main()
