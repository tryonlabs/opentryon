"""
Tests for the `opentryon` CLI.

Fast/offline checks (registry integrity, argument parsing for every
registered model, dry-run resolution) always run. A real end-to-end API call
for `vton --model flux-vto` also runs if BFL_API_KEY is set in the
environment.

Run:
    python3.10 tests/test_cli.py
"""
import contextlib
import io
import os
import sys
import tempfile

from dotenv import load_dotenv

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)
load_dotenv(os.path.join(REPO_ROOT, ".env"))

from tryon.cli.registry import SERVICES, validate_registry  # noqa: E402
from tryon.cli.runner import build_model_parser  # noqa: E402
from tryon.cli.main import main as cli_main  # noqa: E402


def check_registry_has_no_flag_collisions():
    validate_registry()
    print("\u2713 registry: no reserved/duplicate flag collisions")


def check_wan3_model_aliases():
    from tryon.api.wan.adapter import WanVideoAdapter

    assert WanVideoAdapter._resolve_model("wan3.0") == "wan3.0-video"
    assert WanVideoAdapter._resolve_model("wan-3.0") == "wan3.0-video"
    assert WanVideoAdapter._is_wan3_model("wan3.0-video")
    assert WanVideoAdapter._is_wan3_model("wan3")
    assert not WanVideoAdapter._is_wan3_model("wan2.6-t2v")
    print("\u2713 Wan 3.0 aliases resolve to wan3.0-video")


def check_every_model_parser_builds():
    count = 0
    for service, models in SERVICES.items():
        for model_id, spec in models.items():
            build_model_parser(service, model_id, spec)
            count += 1
    print(f"\u2713 built argument parsers for all {count} service/model combinations")


def check_flux_vto_dry_run():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = cli_main([
            "vton", "--model", "flux-vto",
            "--person-image", "data/model-1.jpg",
            "--garment-image", "data/garment.png",
            "--dry-run",
        ])
    printed = buf.getvalue()
    print(printed, end="")
    assert code == 0 and "FluxVTONAdapter" in printed
    print("\u2713 vton flux-vto --dry-run resolves the expected call")


def check_flux_vto_real_call():
    if not os.getenv("BFL_API_KEY"):
        print("\u26a0 skipping real API test: BFL_API_KEY not set")
        return

    with tempfile.TemporaryDirectory() as tmp:
        output_dir = os.path.join(tmp, "cli_out")
        code = cli_main([
            "vton", "--model", "flux-vto",
            "--person-image", os.path.join(REPO_ROOT, "data", "model-1.jpg"),
            "--garment-image", os.path.join(REPO_ROOT, "data", "garment.png"),
            "--garment-description", "black leather biker jacket",
            "-o", output_dir,
        ])
        assert code == 0
        saved = [f for f in os.listdir(output_dir) if f.endswith(".png")]
        assert saved, "expected at least one saved image"
        print(f"\u2713 real BFL API call via CLI succeeded, saved {saved[0]}")


def check_p_image_tryon_dry_run():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = cli_main([
            "vton", "--model", "p-image-tryon",
            "--person-image", "data/model-1.jpg",
            "--garment-image", "data/garment.png", "data/garment2.png",
            "--turbo",
            "--dry-run",
        ])
    printed = buf.getvalue()
    print(printed, end="")
    assert code == 0
    assert "PImageTryOnAdapter" in printed and "generate_and_decode" in printed, printed
    assert "'turbo': True" in printed, printed
    print("\u2713 vton p-image-tryon --dry-run resolves the expected call")


def check_nano_banana_2_lite_dry_runs():
    cases = [
        (
            ["vton", "--model", "nano-banana-2-lite",
             "--model-image", "data/model-1.jpg",
             "--garment-image", "data/garment.png",
             "--garment-description", "olive green bomber jacket"],
            "generate_virtual_tryon",
        ),
        (
            ["generate", "--model", "nano-banana-2-lite",
             "--prompt", "A fashion model wearing a summer collection",
             "--aspect-ratio", "16:9"],
            "generate_text_to_image",
        ),
        (
            ["edit", "--model", "nano-banana-2-lite",
             "--image", "data/model-1.jpg",
             "--prompt", "Change the outfit to a formal business suit"],
            "generate_image_edit",
        ),
    ]
    for argv, expect_method in cases:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = cli_main([*argv, "--dry-run"])
        printed = buf.getvalue()
        assert code == 0, printed
        assert "NanoBanana2LiteAdapter" in printed and f".{expect_method}(" in printed, printed
    print("\u2713 vton/generate/edit nano-banana-2-lite --dry-run resolve the expected calls")


def check_fashn_dry_runs():
    for model_id, expect_model_name in [
        ("fashn-tryon-max", "tryon-max"),
        ("fashn-tryon-v1.6", "tryon-v1.6"),
    ]:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = cli_main([
                "vton", "--model", model_id,
                "--person-image", "data/model-1.jpg",
                "--garment-image", "data/garment.png",
                "--dry-run",
            ])
        printed = buf.getvalue()
        print(printed, end="")
        assert code == 0, printed
        assert "FashnVTONAdapter" in printed and "generate_and_decode" in printed, printed
        assert f"'model_name': '{expect_model_name}'" in printed, printed
    print("\u2713 vton fashn-tryon-max / fashn-tryon-v1.6 --dry-run resolve the expected calls")


def check_gemini_omni_dry_runs():
    cases = [
        (
            ["video-generate", "--model", "gemini-omni",
             "--prompt", "A fashion model walking a runway",
             "--aspect-ratio", "9:16"],
            "generate_text_to_video",
        ),
        (
            ["video-generate", "--model", "gemini-omni",
             "--prompt", "Animate a slow walk",
             "--image", "data/model-1.jpg"],
            "generate_image_to_video",
        ),
        (
            ["video-generate", "--model", "gemini-omni",
             "--prompt", "Dim the lights",
             "--previous-interaction-id", "v1_fake_interaction"],
            "generate_text_to_video",
        ),
    ]
    for argv, expect_method in cases:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = cli_main([*argv, "--dry-run"])
        printed = buf.getvalue()
        assert code == 0, printed
        assert "GeminiOmniAdapter" in printed and f".{expect_method}(" in printed, printed
    print("\u2713 video-generate gemini-omni --dry-run resolves text / image / edit paths")


def check_kimi_dry_runs():
    for model_id, expect_kwarg in [
        ("kimi-k2.6", "'thinking': True"),
        ("kimi-k2.7-code", "'model': 'kimi-k2.7-code'"),
        ("kimi-k3", "'reasoning_effort': 'max'"),
        ("kimi-vl", "'num_frames': 8"),
    ]:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = cli_main([
                "understand", "--model", model_id,
                "--image", "data/model-1.jpg",
                "--prompt", "Describe the outfit",
                "--dry-run",
            ])
        printed = buf.getvalue()
        assert code == 0 and expect_kwarg in printed, printed
    print("\u2713 understand kimi-k2.6 / kimi-k2.7-code / kimi-k3 / kimi-vl --dry-run resolve the expected calls")


def check_qwen_dry_runs():
    for model_id, expect_kwarg in [
        ("qwen3.8-max", "'reasoning_effort': 'xhigh'"),
        ("qwen3.8", "'enable_thinking': True"),
    ]:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = cli_main([
                "understand", "--model", model_id,
                "--image", "data/model-1.jpg",
                "--prompt", "Describe the outfit",
                "--dry-run",
            ])
        printed = buf.getvalue()
        assert code == 0 and expect_kwarg in printed, printed
    print("\u2713 understand qwen3.8-max / qwen3.8 --dry-run resolve the expected calls")


def check_kimi_understand_requires_image_or_video():
    from tryon.api.kimi import KimiUnderstandAdapter

    try:
        KimiUnderstandAdapter(api_key="fake-key-for-validation-test").understand(prompt="hi")
    except ValueError as e:
        assert "image" in str(e) and "video" in str(e)
        print("\u2713 KimiUnderstandAdapter.understand() rejects missing image/video")
    else:
        raise AssertionError("expected ValueError when neither image nor video is given")


def check_qwen_understand_requires_image_or_video():
    from tryon.api.qwen import QwenUnderstandAdapter

    try:
        QwenUnderstandAdapter(api_key="fake-key-for-validation-test").understand(prompt="hi")
    except ValueError as e:
        assert "image" in str(e) and "video" in str(e)
        print("\u2713 QwenUnderstandAdapter.understand() rejects missing image/video")
    else:
        raise AssertionError("expected ValueError when neither image nor video is given")


def check_qwen_image_dry_runs():
    cases = [
        (
            ["generate", "--model", "qwen-image",
             "--prompt", "editorial lookbook, linen trench"],
            "generate_text_to_image",
            "'enable_thinking': True",
        ),
        (
            ["edit", "--model", "qwen-image",
             "--images", "data/model-1.jpg",
             "--prompt", "Change the outfit to a formal business suit"],
            "generate_image_edit",
            "'prompt_extend': True",
        ),
        (
            ["vton", "--model", "qwen-image",
             "--person-image", "data/model-1.jpg",
             "--garment-image", "data/garment.png",
             "--garment-description", "olive green bomber jacket"],
            "generate_virtual_tryon",
            "'enable_thinking': True",
        ),
    ]
    for argv, expect_method, expect_kwarg in cases:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = cli_main([*argv, "--dry-run"])
        printed = buf.getvalue()
        assert code == 0, printed
        assert "QwenImageAdapter" in printed and f".{expect_method}(" in printed, printed
        assert expect_kwarg in printed, printed
    print("\u2713 generate/edit/vton qwen-image --dry-run resolve the expected calls")


def check_qwen_image_local_helpers():
    from tryon.models.qwen_image.adapter import (
        QwenImageLocalAdapter,
        _uses_edit_plus,
    )

    assert _uses_edit_plus("Qwen/Qwen-Image-Edit-2511")
    assert _uses_edit_plus("Qwen/Qwen-Image-Edit-2509")
    assert not _uses_edit_plus("Qwen/Qwen-Image-Edit")
    assert not _uses_edit_plus("Qwen/Qwen-Image-2512")
    assert QwenImageLocalAdapter._resolve_hw(None, None, "16:9") == (1664, 928)
    assert QwenImageLocalAdapter._resolve_hw(1024, 768, "1:1") == (1024, 768)
    prompt = QwenImageLocalAdapter.build_tryon_prompt(
        garment_description="olive green bomber jacket"
    )
    assert "olive green bomber jacket" in prompt
    assert "first image" in prompt
    print("\u2713 Qwen-Image local helpers resolve Edit-Plus, aspect map, and VTON prompt")


def check_qwen_image_local_dry_runs():
    cases = [
        (
            ["generate", "--model", "qwen-image-local",
             "--prompt", "editorial lookbook, linen trench"],
            "generate_text_to_image",
            "'true_cfg_scale': 4.0",
        ),
        (
            ["edit", "--model", "qwen-image-local",
             "--images", "data/model-1.jpg",
             "--prompt", "Change the outfit to a formal business suit"],
            "generate_image_edit",
            "'num_inference_steps': 40",
        ),
        (
            ["vton", "--model", "qwen-image-local",
             "--person-image", "data/model-1.jpg",
             "--garment-image", "data/garment.png",
             "--garment-description", "olive green bomber jacket"],
            "generate_virtual_tryon",
            "'true_cfg_scale': 4.0",
        ),
    ]
    for argv, expect_method, expect_kwarg in cases:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = cli_main([*argv, "--dry-run"])
        printed = buf.getvalue()
        assert code == 0, printed
        assert "QwenImageLocalAdapter" in printed and f".{expect_method}(" in printed, printed
        assert expect_kwarg in printed, printed
    print("\u2713 generate/edit/vton qwen-image-local --dry-run resolve the expected calls")


def check_qwen_image_requires_prompt_and_tryon_inputs():
    from tryon.api.qwen import QwenImageAdapter

    adapter = QwenImageAdapter(api_key="fake-key-for-validation-test")
    try:
        adapter.generate_text_to_image(prompt="")
    except ValueError as e:
        assert "prompt" in str(e)
    else:
        raise AssertionError("expected ValueError when prompt is empty")

    try:
        adapter.generate_virtual_tryon(person="data/model-1.jpg")
    except ValueError as e:
        assert "Garment" in str(e) or "garment" in str(e)
    else:
        raise AssertionError("expected ValueError when garment is missing")
    print("\u2713 QwenImageAdapter rejects empty prompt and missing try-on garment")


def check_minimax_h3_requires_prompt():
    from tryon.api.minimax import MiniMaxH3Adapter
    from tryon.models.minimax_h3.adapter import snap_num_frames

    adapter = MiniMaxH3Adapter(api_key="fake-key-for-validation-test")
    try:
        adapter.generate_text_to_video(prompt="")
    except ValueError as e:
        assert "prompt" in str(e)
    else:
        raise AssertionError("expected ValueError when MiniMax H3 prompt is empty")

    assert snap_num_frames(120) == 124
    assert snap_num_frames(124) == 124
    assert snap_num_frames(400) == 362
    print("\u2713 MiniMaxH3Adapter rejects empty prompt; local frame snap stays on 17*n+5")


def check_muse_image_requires_prompt():
    from tryon.api.muse import MuseImageAdapter

    adapter = MuseImageAdapter(api_key="fake-key-for-validation-test")
    try:
        adapter.generate_text_to_image(prompt="")
    except ValueError as e:
        assert "prompt" in str(e)
    else:
        raise AssertionError("expected ValueError when Muse Image prompt is empty")

    try:
        adapter.generate_virtual_tryon(person="data/model-1.jpg", garment=None)
    except (ValueError, TypeError) as e:
        assert "Garment" in str(e) or "garment" in str(e) or "required" in str(e).lower()
    else:
        raise AssertionError("expected error when Muse Image try-on garment is missing")
    print("\u2713 MuseImageAdapter rejects empty prompt and missing try-on garment")


def check_kimi_k26_real_call():
    if not os.getenv("MOONSHOT_API_KEY"):
        print("\u26a0 skipping real API test: MOONSHOT_API_KEY not set")
        return

    with tempfile.TemporaryDirectory() as tmp:
        output_dir = os.path.join(tmp, "cli_out")
        code = cli_main([
            "understand", "--model", "kimi-k2.6",
            "--image", os.path.join(REPO_ROOT, "data", "model-1.jpg"),
            "--prompt", "Describe the outfit worn in this image in one sentence.",
            "-o", output_dir,
        ])
        assert code == 0
        saved = [f for f in os.listdir(output_dir) if f.endswith(".json")]
        assert saved, "expected a saved understand result"
        print(f"\u2713 real Kimi K2.6 API call via CLI succeeded, saved {saved[0]}")


def check_new_media_models_dry_runs():
    cases = [
        (["generate", "--model", "seedream", "--prompt", "editorial fashion still"],
         "SeedreamAdapter", "generate_text_to_image"),
        (["generate", "--model", "ideogram", "--prompt", "poster with crisp type"],
         "IdeogramAdapter", "generate_text_to_image"),
        (["generate", "--model", "grok-imagine-image", "--prompt", "studio product shot"],
         "GrokImagineImageAdapter", "generate_text_to_image"),
        (["generate", "--model", "muse-image", "--prompt", "editorial fashion still"],
         "MuseImageAdapter", "generate_text_to_image"),
        (["edit", "--model", "muse-image", "--prompt", "swap outfit",
          "--images", "data/model-1.jpg"],
         "MuseImageAdapter", "generate_image_edit"),
        (["vton", "--model", "muse-image",
          "--person-image", "data/model-1.jpg", "--garment-image", "data/garment.png"],
         "MuseImageAdapter", "generate_virtual_tryon"),
        (["edit", "--model", "seedream", "--prompt", "swap outfit",
          "--images", "data/model-1.jpg"],
         "SeedreamAdapter", "generate_image_edit"),
        (["video-generate", "--model", "seedance", "--prompt", "runway walk"],
         "SeedanceAdapter", "generate_text_to_video"),
        (["video-generate", "--model", "seedance", "--prompt", "animate",
          "--image", "data/model-1.jpg"],
         "SeedanceAdapter", "generate_image_to_video"),
        (["video-generate", "--model", "luma-ray-3.2", "--prompt", "dolly through atelier"],
         "LumaRay32Adapter", "generate_text_to_video"),
        (["video-generate", "--model", "kling-v3", "--prompt", "slow pan fashion"],
         "KlingVideoAdapter", "generate_text_to_video"),
        (["video-generate", "--model", "kling-v3-omni", "--prompt", "multi-shot lookbook"],
         "KlingVideoAdapter", "generate_text_to_video"),
        (["video-generate", "--model", "kling-v2-5-turbo", "--prompt", "quick preview"],
         "KlingVideoAdapter", "generate_text_to_video"),
        (["video-generate", "--model", "grok-imagine-video", "--prompt", "cinematic push-in"],
         "GrokImagineVideoAdapter", "generate_text_to_video"),
        (["video-generate", "--model", "grok-imagine-video", "--prompt", "animate",
          "--image", "data/model-1.jpg"],
         "GrokImagineVideoAdapter", "generate_image_to_video"),
        (["generate", "--model", "p-image", "--prompt", "knitwear flatlay"],
         "PImageAdapter", "generate_text_to_image"),
        (["edit", "--model", "p-image-edit", "--prompt", "studio background",
          "--images", "data/model-1.jpg"],
         "PImageEditAdapter", "generate_image_edit"),
        (["edit", "--model", "p-image-upscale", "--image", "data/model-1.jpg", "--target", "4"],
         "PImageUpscaleAdapter", "upscale"),
        (["video-generate", "--model", "p-video", "--prompt", "runway walk"],
         "PVideoAdapter", "generate_text_to_video"),
        (["video-generate", "--model", "p-video", "--prompt", "gentle turn",
          "--image", "data/model-1.jpg"],
         "PVideoAdapter", "generate_image_to_video"),
        (["video-generate", "--model", "p-video-replace",
          "--video", "data/model-1.jpg", "--images", "data/model-1.jpg"],
         "PVideoReplaceAdapter", "generate_video_replace"),
        (["video-generate", "--model", "p-video-avatar",
          "--image", "data/model-1.jpg",
          "--voice-script", "Welcome to the collection."],
         "PVideoAvatarAdapter", "generate_video_avatar"),
        (["video-generate", "--model", "p-video-animate",
          "--video", "data/model-1.jpg", "--image", "data/model-1.jpg"],
         "PVideoAnimateAdapter", "generate_video_animate"),
        (["video-generate", "--model", "ltx-2.5-api", "--prompt", "runway walk"],
         "LTXVideoAdapter", "generate_text_to_video"),
        (["video-generate", "--model", "ltx-2.5-api", "--prompt", "animate",
          "--image", "data/model-1.jpg"],
         "LTXVideoAdapter", "generate_image_to_video"),
        (["video-generate", "--model", "ltx-2.5", "--prompt", "runway walk"],
         "LTX25Adapter", "generate_text_to_video"),
        (["video-generate", "--model", "ltx-2.5", "--prompt", "animate",
          "--image", "data/model-1.jpg"],
         "LTX25Adapter", "generate_image_to_video"),
        (["video-generate", "--model", "hailuo-2.3", "--prompt", "runway walk"],
         "HailuoVideoAdapter", "generate_text_to_video"),
        (["video-generate", "--model", "hailuo-2.3", "--prompt", "animate",
          "--image", "data/model-1.jpg"],
         "HailuoVideoAdapter", "generate_image_to_video"),
        (["video-generate", "--model", "minimax-h3", "--prompt", "runway walk"],
         "MiniMaxH3Adapter", "generate_text_to_video"),
        (["video-generate", "--model", "minimax-h3", "--prompt", "animate",
          "--image", "data/model-1.jpg"],
         "MiniMaxH3Adapter", "generate_image_to_video"),
        (["video-generate", "--model", "minimax-h3-local", "--prompt", "runway walk"],
         "MiniMaxH3LocalAdapter", "generate_text_to_video"),
        (["video-generate", "--model", "minimax-h3-local", "--prompt", "animate",
          "--image", "data/model-1.jpg"],
         "MiniMaxH3LocalAdapter", "generate_image_to_video"),
        (["video-generate", "--model", "wan-api", "--prompt", "runway walk"],
         "WanVideoAdapter", "generate_text_to_video"),
        (["video-generate", "--model", "wan-api", "--prompt", "animate",
          "--image", "data/model-1.jpg"],
         "WanVideoAdapter", "generate_image_to_video"),
        (["video-generate", "--model", "wan-3.0", "--prompt", "runway walk"],
         "WanVideoAdapter", "generate_text_to_video"),
        (["video-generate", "--model", "wan-3.0", "--prompt", "animate",
          "--image", "data/model-1.jpg"],
         "WanVideoAdapter", "generate_image_to_video"),
        (["video-generate", "--model", "wan-2.2", "--prompt", "runway walk"],
         "Wan22Adapter", "generate_text_to_video"),
        (["video-generate", "--model", "wan-2.2", "--prompt", "animate",
          "--image", "data/model-1.jpg"],
         "Wan22Adapter", "generate_image_to_video"),
        (["video-generate", "--model", "runway-gen4.5", "--prompt", "runway walk"],
         "RunwayVideoAdapter", "generate_text_to_video"),
        (["video-generate", "--model", "runway-gen4.5", "--prompt", "animate",
          "--image", "data/model-1.jpg"],
         "RunwayVideoAdapter", "generate_image_to_video"),
    ]
    for argv, expect_cls, expect_method in cases:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = cli_main([*argv, "--dry-run"])
        printed = buf.getvalue()
        assert code == 0, printed
        assert expect_cls in printed and f".{expect_method}(" in printed, printed
    print("\u2713 new Seedance/Seedream/Ideogram/Grok/Kling/Ray3.2/Pruna/LTX/Hailuo/MiniMax-H3/Muse/Wan/Runway --dry-run calls resolve")


if __name__ == "__main__":
    check_registry_has_no_flag_collisions()
    check_wan3_model_aliases()
    check_every_model_parser_builds()
    check_flux_vto_dry_run()
    check_flux_vto_real_call()
    check_p_image_tryon_dry_run()
    check_nano_banana_2_lite_dry_runs()
    check_fashn_dry_runs()
    check_gemini_omni_dry_runs()
    check_new_media_models_dry_runs()
    check_kimi_dry_runs()
    check_qwen_dry_runs()
    check_qwen_image_dry_runs()
    check_qwen_image_local_helpers()
    check_qwen_image_local_dry_runs()
    check_kimi_understand_requires_image_or_video()
    check_qwen_understand_requires_image_or_video()
    check_qwen_image_requires_prompt_and_tryon_inputs()
    check_minimax_h3_requires_prompt()
    check_muse_image_requires_prompt()
    check_kimi_k26_real_call()
    print("\nAll CLI checks passed.")
