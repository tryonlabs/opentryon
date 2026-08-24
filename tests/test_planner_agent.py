"""Offline tests for the planner agent (no live LLM / image APIs).

Run:
    conda run -n opentryon python tests/test_planner_agent.py
"""
from __future__ import annotations

import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from tryon.agents.planner.plan import Plan, parse_plan_json, required_inputs
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
    assert "vton agent" in result["message"]
    print("\u2713 vton with both images dry-runs to the vton agent")


def check_model_swap_and_fashion_dry_run():
    swap = PlannerAgent(
        classifier=lambda **kwargs: Plan(intent="model_swap", task=kwargs["prompt"])
    ).run("Replace with a 30s athletic model", image="outfit.jpg", dry_run=True)
    assert swap["intent"] == "model_swap" and swap["agent"] == "model_swap"

    fashion = PlannerAgent(
        classifier=lambda **kwargs: Plan(intent="fashion", task=kwargs["prompt"])
    ).run("Generate a red evening gown on a runway", dry_run=True)
    assert fashion["intent"] == "fashion" and fashion["agent"] == "fashion"
    print("\u2713 model_swap and fashion dry-run to the matching agents")


def check_out_of_scope_does_not_delegate():
    agent = PlannerAgent(
        classifier=lambda **kwargs: Plan(intent="out_of_scope", reason="not fashion")
    )
    called = {"n": 0}

    def boom(*_a, **_k):
        called["n"] += 1
        raise AssertionError("specialist should not run")

    agent._delegate = boom  # type: ignore[method-assign]
    result = agent.run("What's the weather in Paris?")
    assert result["intent"] == "out_of_scope"
    assert called["n"] == 0
    print("\u2713 out_of_scope never calls a specialist")


def check_required_inputs():
    assert required_inputs("vton") == ("person_image", "garment_image")
    assert required_inputs("model_swap") == ("image",)
    assert required_inputs("fashion") == ()
    print("\u2713 required_inputs per intent")


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


def main():
    check_parse_plan_json_raw_and_fenced()
    check_parse_rejects_unknown_intent()
    check_vton_without_images_clarifies()
    check_vton_dry_run_routes()
    check_model_swap_and_fashion_dry_run()
    check_out_of_scope_does_not_delegate()
    check_required_inputs()
    check_encode_images_png_bytes()
    print("\nAll planner agent checks passed.")


if __name__ == "__main__":
    main()
