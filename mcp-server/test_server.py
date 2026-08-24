#!/usr/bin/env python3
"""Lightweight, offline sanity checks for the OpenTryOn MCP server.

Mirrors the structure of ``../tests/test_cli.py``: plain functions (no
pytest dependency), run top to bottom, each asserting one thing and
printing a checkmark. Everything here is a dry-run / in-process check --
no network calls, no API keys required.

Run with the same interpreter that has ``fastmcp`` and ``opentryon``
installed:

    python test_server.py
"""

from __future__ import annotations

import asyncio
import importlib.util
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import server
from tryon.cli.registry import SERVICES

_HAS_TORCH = importlib.util.find_spec("torch") is not None


def _count_registry_models() -> int:
    return sum(len(models) for models in SERVICES.values())


async def check_tool_count_matches_registry() -> None:
    tools = await server.mcp._list_tools()
    expected = _count_registry_models() + 3  # + list_opentryon_tools, opentryon_status, planner_agent
    assert len(tools) == expected, f"expected {expected} tools, got {len(tools)}"
    print(f"\u2713 {len(tools)} MCP tools registered ({_count_registry_models()} models + 2 discovery + planner_agent)")


async def check_every_model_has_a_tool() -> None:
    tools = await server.mcp._list_tools()
    names = {t.name for t in tools}
    missing = []
    for service, models in SERVICES.items():
        for model_id in models:
            name = server._tool_name(service, model_id)
            if name not in names:
                missing.append(name)
    assert not missing, f"missing MCP tools for: {missing}"
    print("\u2713 every registry (service, model) has a matching MCP tool")


async def check_required_args_are_required() -> None:
    tool = await server.mcp.get_tool("vton_flux_vto")
    schema = tool.parameters
    assert schema["required"] == ["person", "garment"], schema["required"]
    assert "output_dir" in schema["properties"] and "dry_run" in schema["properties"]
    print("\u2713 vton_flux_vto schema has the right required/optional fields")


async def check_choices_become_enum() -> None:
    tool = await server.mcp.get_tool("vton_flux_vto")
    prop = tool.parameters["properties"]["output_format"]
    # optional field with choices -> {"anyOf": [{"enum": [...]}, {"type": "null"}]}
    enums = [b["enum"] for b in prop.get("anyOf", [prop]) if "enum" in b]
    assert enums and set(enums[0]) == {"jpeg", "png", "webp"}, prop
    print("\u2713 Arg.choices are exposed as a JSON schema enum")


async def check_dry_run_calls() -> None:
    # (tool_name, args, needs_local_extra)
    cases = [
        ("vton_flux_vto", {"person": "p.jpg", "garment": "g.jpg", "dry_run": True}, False),
        ("vton_p_image_tryon", {"person_image": "p.jpg", "garment_images": ["g1.jpg", "g2.jpg"], "dry_run": True}, False),
        ("vton_nano_banana_2_lite", {"person": "p.jpg", "garment": "g.jpg", "dry_run": True}, False),
        ("vton_fashn_tryon_max", {"model_image": "p.jpg", "product_image": "g.jpg", "dry_run": True}, False),
        ("vton_fashn_tryon_v1_6", {"model_image": "p.jpg", "product_image": "g.jpg", "dry_run": True}, False),
        ("generate_nano_banana", {"prompt": "a red dress", "dry_run": True}, False),
        ("generate_nano_banana_2_lite", {"prompt": "a red dress", "dry_run": True}, False),
        ("edit_nano_banana_2_lite", {"image": "p.jpg", "prompt": "make it blue", "dry_run": True}, False),
        ("edit_gpt_image", {"images": ["a.jpg", "b.jpg"], "prompt": "make it blue", "dry_run": True}, False),
        ("understand_kimi_k2_6", {"image": "i.jpg", "dry_run": True}, False),
        ("understand_kimi_k2_7_code", {"image": "i.jpg", "dry_run": True}, False),
        ("understand_kimi_k3", {"image": "i.jpg", "dry_run": True}, False),
        ("understand_qwen3_8_max", {"image": "i.jpg", "dry_run": True}, False),
        ("generate_qwen_image", {"prompt": "editorial still", "dry_run": True}, False),
        ("edit_qwen_image", {"image": ["p.jpg"], "prompt": "make it blue", "dry_run": True}, False),
        ("vton_qwen_image", {"person": "p.jpg", "garment": "g.jpg", "dry_run": True}, False),
        ("generate_qwen_image_local", {"prompt": "editorial still", "dry_run": True}, True),
        ("edit_qwen_image_local", {"image": ["p.jpg"], "prompt": "make it blue", "dry_run": True}, True),
        ("vton_qwen_image_local", {"person": "p.jpg", "garment": "g.jpg", "dry_run": True}, True),
        ("video_generate_veo", {"prompt": "a cat", "image": "cat.jpg", "dry_run": True}, False),
        ("video_generate_gemini_omni", {"prompt": "a cat walking", "dry_run": True}, False),
        ("video_generate_seedance", {"prompt": "runway walk", "dry_run": True}, False),
        ("video_generate_luma_ray_3_2", {"prompt": "dolly shot", "dry_run": True}, False),
        ("video_generate_kling_v3", {"prompt": "fashion pan", "dry_run": True}, False),
        ("video_generate_kling_v3_omni", {"prompt": "lookbook", "dry_run": True}, False),
        ("video_generate_kling_v2_5_turbo", {"prompt": "quick clip", "dry_run": True}, False),
        ("video_generate_grok_imagine_video", {"prompt": "cinematic", "dry_run": True}, False),
        ("generate_seedream", {"prompt": "editorial still", "dry_run": True}, False),
        ("generate_ideogram", {"prompt": "poster type", "dry_run": True}, False),
        ("generate_grok_imagine_image", {"prompt": "product shot", "dry_run": True}, False),
        ("bg_remove_ben2", {"image": "i.jpg", "dry_run": True}, True),
    ]
    checked = 0
    for name, args, needs_local in cases:
        if needs_local and not _HAS_TORCH:
            # `_extra_missing` intentionally runs before the dry-run check
            # (matches the CLI's `--dry-run` behavior) so a local-only model
            # dry-runs as a clean failure, not a crash, when torch isn't
            # installed. Confirm that instead of the success path.
            tool = await server.mcp.get_tool(name)
            result = await tool.run(args)
            data = result.structured_content
            assert data["success"] is False and "opentryon[local]" in data["error"], f"{name}: {data}"
            checked += 1
            continue
        tool = await server.mcp.get_tool(name)
        result = await tool.run(args)
        data = result.structured_content
        assert data["success"] is True, f"{name}: {data}"
        assert data["dry_run"] is True, f"{name}: {data}"
        checked += 1
    print(f"\u2713 {checked} representative tools resolve dry-run calls correctly")


async def check_alt_method_on_image_switches_method() -> None:
    tool = await server.mcp.get_tool("video_generate_veo")
    text_to_video = await tool.run({"prompt": "a cat", "dry_run": True})
    image_to_video = await tool.run({"prompt": "a cat", "image": "cat.jpg", "dry_run": True})
    assert "generate_text_to_video" in text_to_video.structured_content["call"]
    assert "generate_image_to_video" in image_to_video.structured_content["call"]
    print("\u2713 veo switches to generate_image_to_video only when --image is set")


async def check_unknown_service_and_model_errors() -> None:
    from tryon.cli.runner import invoke_model

    r1 = invoke_model("not-a-service", "x", dry_run=True)
    assert r1["success"] is False and "Unknown service" in r1["error"], r1

    r2 = invoke_model("vton", "not-a-model", dry_run=True)
    assert r2["success"] is False and "Unknown model" in r2["error"], r2
    print("\u2713 invoke_model returns structured errors for unknown service/model")


async def check_list_opentryon_tools() -> None:
    tool = await server.mcp.get_tool("list_opentryon_tools")
    result = await tool.run({"service": "understand"})
    data = result.structured_content
    assert "kimi-k2.6" in data["services"]["understand"]["models"]
    assert "kimi-k3" in data["services"]["understand"]["models"]
    assert "kimi-vl" in data["services"]["understand"]["models"]
    assert "qwen3.8-max" in data["services"]["understand"]["models"]

    bad = await tool.run({"service": "not-a-service"})
    assert bad.structured_content["success"] is False
    print("\u2713 list_opentryon_tools lists models and rejects unknown services")


async def check_planner_agent_schema() -> None:
    tools = await server.mcp._list_tools()
    names = {t.name for t in tools}
    assert "planner_agent" in names
    tool = await server.mcp.get_tool("planner_agent")
    schema = tool.parameters
    assert "prompt" in schema["required"]
    for field in ("person_image", "garment_image", "image", "images", "dry_run"):
        assert field in schema["properties"], field
    print("\u2713 planner_agent is registered with prompt + optional image args")


async def check_status_message_mentions_every_service() -> None:
    msg = server.config.status_message()
    for service in SERVICES:
        assert f"[{service}]" in msg, f"missing section for {service}"
    print("\u2713 opentryon_status covers every service")


async def main() -> None:
    checks = [
        check_tool_count_matches_registry,
        check_every_model_has_a_tool,
        check_required_args_are_required,
        check_choices_become_enum,
        check_dry_run_calls,
        check_alt_method_on_image_switches_method,
        check_unknown_service_and_model_errors,
        check_list_opentryon_tools,
        check_planner_agent_schema,
        check_status_message_mentions_every_service,
    ]
    for check in checks:
        await check()
    print("\nAll MCP server checks passed.")


if __name__ == "__main__":
    asyncio.run(main())
