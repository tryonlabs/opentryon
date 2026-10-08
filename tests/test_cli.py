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


def check_seedance_25_model_id():
    from tryon.api.byteplus.seedance import SeedanceAdapter

    assert SeedanceAdapter._resolve_model("seedance-2-5") == "dreamina-seedance-2-5-260628"
    assert SeedanceAdapter._resolve_model("seedance-2.5") == "dreamina-seedance-2-5-260628"
    assert SeedanceAdapter._resolve_model("dreamina-seedance-2-5-260628") == "dreamina-seedance-2-5-260628"
    print("\u2713 Seedance 2.5 aliases resolve to dreamina-seedance-2-5-260628")


def check_p_image_ideogram_thinking_aliases():
    from tryon.api.pruna.p_image_ideogram import _normalize_thinking

    assert _normalize_thinking("high") == "high"
    assert _normalize_thinking("very-low") == "very low"
    assert _normalize_thinking("VERY_HIGH") == "very high"
    assert _normalize_thinking("very low") == "very low"
    try:
        _normalize_thinking("ultra")
    except ValueError:
        pass
    else:
        raise AssertionError("expected invalid thinking to raise")
    print("\u2713 P-Image-Ideogram thinking aliases map to Pruna strings")


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


def check_gpt_image_25_dry_runs():
    from tryon.api.openAI.image_adapter import GPTImageAdapter

    flare = GPTImageAdapter(api_key="sk-test", model_version="gpt-image-2.5")
    assert flare.model_version == "gpt-image-2.5-flare"
    sun = GPTImageAdapter(api_key="sk-test", model_version="gpt-image-2.5-sunburst")
    assert sun.model_version == "gpt-image-2.5-sunburst"
    legacy = GPTImageAdapter(api_key="sk-test")
    assert legacy.model_version == "gpt-image-1.5"

    cases = [
        (
            ["generate", "--model", "gpt-image-2.5", "--prompt", "editorial still"],
            "generate_text_to_image",
            "gpt-image-2.5-flare",
        ),
        (
            ["generate", "--model", "gpt-image-2.5-sunburst", "--prompt", "editorial still"],
            "generate_text_to_image",
            "gpt-image-2.5-sunburst",
        ),
        (
            ["edit", "--model", "gpt-image-2.5",
             "--images", "data/model-1.jpg", "--prompt", "make it blue"],
            "generate_image_edit",
            "gpt-image-2.5-flare",
        ),
        (
            ["edit", "--model", "gpt-image-2.5-sunburst",
             "--images", "data/model-1.jpg", "--prompt", "make it blue"],
            "generate_image_edit",
            "gpt-image-2.5-sunburst",
        ),
        (
            ["generate", "--model", "gpt-image", "--prompt", "editorial still"],
            "generate_text_to_image",
            "gpt-image-1.5",
        ),
    ]
    for argv, expect_method, expect_version in cases:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = cli_main([*argv, "--dry-run"])
        printed = buf.getvalue()
        assert code == 0, printed
        assert "GPTImageAdapter" in printed and f".{expect_method}(" in printed, printed
        assert f"'model_version': '{expect_version}'" in printed, printed
    print("\u2713 generate/edit gpt-image-2.5 / sunburst --dry-run pin Flare vs 1.5")


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


def check_google_vton_dry_run():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = cli_main([
            "vton", "--model", "google-vton",
            "--person-image", "data/model-1.jpg",
            "--garment-image", "data/garment.png",
            "--num-images", "2",
            "--dry-run",
        ])
    printed = buf.getvalue()
    print(printed, end="")
    assert code == 0, printed
    assert "GoogleVTONAdapter" in printed and "generate_and_decode" in printed, printed
    assert "'number_of_images': 2" in printed, printed
    print("\u2713 vton google-vton --dry-run resolves the expected call")


def check_outfitanyone_plus_dry_run():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = cli_main([
            "vton", "--model", "outfitanyone-plus",
            "--person-image", "data/model-1.jpg",
            "--garment-image", "data/garment.png",
            "--resolution", "1024",
            "--dry-run",
        ])
    printed = buf.getvalue()
    print(printed, end="")
    assert code == 0, printed
    assert "OutfitAnyonePlusAdapter" in printed and "generate_and_decode" in printed, printed
    assert "'resolution': 1024" in printed, printed
    print("\u2713 vton outfitanyone-plus --dry-run resolves the expected call")


def check_photoroom_dry_runs():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = cli_main([
            "vton", "--model", "photoroom-vton",
            "--person-image", "data/model-1.jpg",
            "--garment-image", "data/garment.png",
            "--pose", "standing",
            "--dry-run",
        ])
    printed = buf.getvalue()
    print(printed, end="")
    assert code == 0, printed
    assert "PhotoroomVTONAdapter" in printed and "generate_and_decode" in printed, printed
    assert "'mode': 'try-on'" in printed, printed

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = cli_main([
            "vton", "--model", "photoroom-virtual-model",
            "--garment-image", "data/garment.png",
            "--preset-model", "avery",
            "--dry-run",
        ])
    printed = buf.getvalue()
    print(printed, end="")
    assert code == 0, printed
    assert "PhotoroomVTONAdapter" in printed and "generate_virtual_model" in printed, printed
    assert "'preset_model': 'avery'" in printed, printed
    print("\u2713 vton photoroom-vton / photoroom-virtual-model --dry-run resolve the expected calls")


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


def check_video_wave_dry_runs():
    """Omni 1.1 Flash resolution/extend, Veo 3.1 frames/refs/4k, Seedance refs, Cosmos 3 local."""
    cases = [
        (["video-generate", "--model", "gemini-omni", "--prompt", "continue",
          "--video", "clip.mp4", "--resolution", "1080p"],
         "GeminiOmniAdapter", "generate_text_to_video", ["'video': 'clip.mp4'", "'resolution': '1080p'"]),
        (["video-generate", "--model", "veo", "--prompt", "x", "--image", "a.png",
          "--last-image", "b.png", "--duration", "8", "--resolution", "4k",
          "--model-version", "veo-3.1-fast-generate-preview"],
         "VeoAdapter", "generate_image_to_video", ["'last_image': 'b.png'", "'resolution': '4k'"]),
        (["video-generate", "--model", "veo", "--prompt", "x",
          "--reference-image", "a.png", "b.png", "--duration", "8"],
         "VeoAdapter", "generate_text_to_video", ["'reference_images': ['a.png', 'b.png']"]),
        (["video-generate", "--model", "seedance", "--prompt", "x", "--reference-image", "a.png",
          "--reference-video", "v.mp4", "--reference-audio", "s.mp3", "--duration", "12"],
         "SeedanceAdapter", "generate_text_to_video", ["'reference_videos': ['v.mp4']", "'reference_audios': ['s.mp3']"]),
        (["video-generate", "--model", "cosmos3-local", "--prompt", "runway walk", "--cpu-offload"],
         "Cosmos3LocalAdapter", "generate_text_to_video", ["'cpu_offload': True"]),
        (["video-generate", "--model", "cosmos3-local", "--prompt", "animate", "--image", "a.png"],
         "Cosmos3LocalAdapter", "generate_image_to_video", ["'image': 'a.png'"]),
    ]
    for argv, cls, method, needles in cases:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = cli_main([*argv, "--dry-run"])
        printed = buf.getvalue()
        assert code == 0, printed
        assert cls in printed and f".{method}(" in printed, printed
        for needle in needles:
            assert needle in printed, (needle, printed)
    print("\u2713 Omni 1.1 / Veo 3.1 / Seedance refs / cosmos3-local --dry-run resolve")


def check_veo_seedance_validation():
    from tryon.api.veo import _validate_model, _validate_resolution
    _validate_resolution("veo-3.1-generate-preview", "4k", "8")
    for model, res, dur in [
        ("veo-3.1-lite-generate-preview", "4k", "8"),
        ("veo-3.1-generate-preview", "1080p", "4"),
    ]:
        try:
            _validate_resolution(model, res, dur)
        except ValueError:
            pass
        else:
            raise AssertionError((model, res, dur))
    try:
        _validate_model("veo-3.0-generate-001")
    except ValueError as exc:
        assert "shut down" in str(exc)
    else:
        raise AssertionError("Veo 3.0 should be rejected")

    from tryon.api.byteplus.seedance import SeedanceAdapter
    adapter = SeedanceAdapter(api_key="test")
    payload = adapter._build_payload(
        "p",
        reference_images=["https://e.com/a.png"],
        reference_videos=["https://e.com/v.mp4"],
        reference_audios=["https://e.com/a.mp3"],
        duration=12,
    )
    roles = [c.get("role") for c in payload["content"]]
    assert roles == [None, "reference_image", "reference_video", "reference_audio"], roles
    try:
        adapter._build_payload("p", image="https://e.com/a.png", reference_images=["https://e.com/b.png"])
    except ValueError:
        pass
    else:
        raise AssertionError("refs + first-frame must be rejected")

    from tryon.api.omni import GeminiOmniAdapter
    try:
        GeminiOmniAdapter(api_key="test", model="gemini-omni-flash-preview")
    except ValueError as exc:
        assert "deprecated" in str(exc)
    except ImportError:
        pass
    else:
        raise AssertionError("old Omni preview id must be rejected")
    print("\u2713 Veo 3.1 / Seedance reference / Omni model-id validation")


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


def check_hy4_dry_runs():
    for model_id, expect_endpoint in [
        ("hy4-preview", "'endpoint': 'tokenhub'"),
        ("hy4-preview-local", "'endpoint': 'local'"),
    ]:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = cli_main([
                "understand", "--model", model_id,
                "--prompt", "Describe a linen trench for a lookbook.",
                "--dry-run",
            ])
        printed = buf.getvalue()
        assert code == 0, printed
        assert "Hy4Adapter" in printed and ".understand(" in printed, printed
        assert expect_endpoint in printed, printed
        assert "'enable_thinking': True" in printed, printed
        assert "'reasoning_effort': 'high'" in printed, printed
    print("\u2713 understand hy4-preview / hy4-preview-local --dry-run resolve the expected calls")


def check_hy4_requires_prompt_or_image():
    from tryon.api.hy import Hy4Adapter

    try:
        Hy4Adapter(api_key="fake-key-for-validation-test").understand()
    except ValueError as e:
        assert "prompt" in str(e).lower()
    else:
        raise AssertionError("expected ValueError when Hy4 has no prompt or image")

    try:
        Hy4Adapter(api_key="fake-key-for-validation-test").understand(
            prompt="hi", video="clip.mp4"
        )
    except ValueError as e:
        assert "video" in str(e).lower()
    else:
        raise AssertionError("expected ValueError when Hy4 is given video")
    print("\u2713 Hy4Adapter.understand() requires prompt; rejects video")


def check_nvidia_nim_dry_runs():
    cases = [
        (
            ["understand", "--model", "nemotron-omni",
             "--image", "data/model-1.jpg", "--prompt", "Describe the outfit"],
            "NemotronOmniUnderstandAdapter",
            "understand",
            "'enable_thinking': True",
        ),
        (
            ["understand", "--model", "cosmos3-reasoner",
             "--image", "data/model-1.jpg", "--prompt", "What is happening?"],
            "Cosmos3ReasonerAdapter",
            "understand",
            None,
        ),
        (
            ["video-generate", "--model", "cosmos3", "--prompt", "runway walk"],
            "Cosmos3VideoAdapter",
            "generate_text_to_video",
            None,
        ),
        (
            ["video-generate", "--model", "cosmos3", "--prompt", "animate",
             "--image", "data/model-1.jpg"],
            "Cosmos3VideoAdapter",
            "generate_image_to_video",
            None,
        ),
    ]
    for argv, expect_cls, expect_method, expect_kwarg in cases:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = cli_main([*argv, "--dry-run"])
        printed = buf.getvalue()
        assert code == 0, printed
        assert expect_cls in printed and f".{expect_method}(" in printed, printed
        if expect_kwarg:
            assert expect_kwarg in printed, printed
    print("\u2713 understand nemotron-omni / cosmos3-reasoner and video-generate cosmos3 --dry-run resolve")


def check_nvidia_understand_requires_media():
    from tryon.api.nvidia import NemotronOmniUnderstandAdapter, Cosmos3ReasonerAdapter

    try:
        NemotronOmniUnderstandAdapter(api_key="fake-key-for-validation-test").understand(prompt="hi")
    except ValueError as e:
        assert "image" in str(e) and "video" in str(e) and "audio" in str(e)
    else:
        raise AssertionError("expected ValueError when Nemotron Omni has no media")

    try:
        Cosmos3ReasonerAdapter(api_key="fake-key-for-validation-test").understand(prompt="hi")
    except ValueError as e:
        assert "image" in str(e) and "video" in str(e)
        assert "audio" not in str(e)
    else:
        raise AssertionError("expected ValueError when Cosmos Reasoner has no media")
    print("\u2713 NVIDIA understand adapters reject missing media")


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

    fast = MiniMaxH3Adapter(api_key="fake-key-for-validation-test", model="MiniMax-H3-Max")
    try:
        fast.generate_text_to_video(prompt="ok", duration=4)
    except ValueError as e:
        assert "5" in str(e) and "MiniMax-H3-Max" in str(e)
    else:
        raise AssertionError("expected ValueError for H3 Max duration 4")
    try:
        fast.generate_text_to_video(prompt="ok", resolution="2K")
    except ValueError as e:
        assert "2K" in str(e) or "480P" in str(e)
    else:
        raise AssertionError("expected ValueError for H3 Max 2K")
    try:
        fast.generate_text_to_video(prompt="ok", reference_image="look.jpg")
    except ValueError as e:
        assert "reference" in str(e).lower()
    else:
        raise AssertionError("expected ValueError for H3 Max reference-to-video")
    print("\u2713 MiniMax H3 Max rejects 4s, 2K, and reference-to-video")


def check_fal_h3_max_requires_prompt():
    from tryon.api.fal import FalH3MaxAdapter

    adapter = FalH3MaxAdapter(api_key="fake-key-for-validation-test")
    try:
        adapter.generate_text_to_video(prompt="")
    except ValueError as e:
        assert "prompt" in str(e)
    else:
        raise AssertionError("expected ValueError when Fal H3 Max prompt is empty")
    try:
        adapter.generate_text_to_video(prompt="ok", duration=4)
    except ValueError as e:
        assert "5" in str(e)
    else:
        raise AssertionError("expected ValueError for Fal H3 Max duration 4")
    try:
        adapter.generate_text_to_video(prompt="ok", reference_audio="voice.mp3")
    except ValueError as e:
        assert "audio" in str(e).lower()
    else:
        raise AssertionError("expected ValueError for audio-only Fal R2V")
    try:
        adapter.generate_image_to_video(
            image="look.jpg", prompt="ok", reference_image="style.jpg"
        )
    except ValueError as e:
        assert "mutually exclusive" in str(e).lower() or "reference" in str(e).lower()
    else:
        raise AssertionError("expected ValueError when mixing I2V and R2V")
    print("\u2713 FalH3MaxAdapter rejects empty prompt, 4s, audio-only R2V, and mixed I2V+R2V")


def check_fal_h3_max_lipsync_requires_valid_resolution():
    from tryon.api.fal import FalH3MaxAdapter

    adapter = FalH3MaxAdapter(api_key="fake-key-for-validation-test")
    try:
        adapter.generate_lip_sync(image="face.jpg", audio="line.wav", resolution="4K")
    except ValueError as e:
        assert "resolution" in str(e).lower()
    else:
        raise AssertionError("expected ValueError for H3 Max Lip Sync resolution 4K")
    print("\u2713 FalH3MaxAdapter.generate_lip_sync rejects an invalid resolution")


def check_p_video_2_pro_requires_valid_duration():
    from tryon.api.pruna import PVideo2ProAdapter

    adapter = PVideo2ProAdapter(api_key="fake-key-for-validation-test")
    try:
        adapter.generate_text_to_video(prompt="ok", duration=20)
    except ValueError as e:
        assert "duration" in str(e).lower()
    else:
        raise AssertionError("expected ValueError for P-Video-2-Pro duration 20")
    try:
        adapter.generate_text_to_video(prompt="")
    except ValueError as e:
        assert "prompt" in str(e)
    else:
        raise AssertionError("expected ValueError for P-Video-2-Pro empty prompt")
    print("\u2713 PVideo2ProAdapter rejects empty prompt and out-of-range duration")


def check_qwen_omni_flash_audio_requires_omni_model():
    from tryon.api.qwen import QwenUnderstandAdapter

    adapter = QwenUnderstandAdapter(api_key="fake-key-for-validation-test", model="qwen3.8-max")
    try:
        adapter.understand(audio="voice.wav", prompt="What is said?")
    except ValueError as e:
        assert "omni" in str(e).lower()
    else:
        raise AssertionError("expected ValueError when qwen3.8-max is given audio")
    print("\u2713 QwenUnderstandAdapter rejects audio input on a non-omni model")


def check_glm_rejects_invalid_reasoning_effort():
    from tryon.api.zai import GLMUnderstandAdapter

    adapter = GLMUnderstandAdapter(api_key="fake-key-for-validation-test")
    try:
        adapter.understand(image="data/model-1.jpg", prompt="hi", reasoning_effort="ultra")
    except ValueError as e:
        assert "reasoning_effort" in str(e)
    else:
        raise AssertionError("expected ValueError for an invalid GLM reasoning_effort")
    print("\u2713 GLMUnderstandAdapter rejects an invalid reasoning_effort")


def check_deepseek_flash_requires_image():
    from tryon.api.deepseek import DeepSeekUnderstandAdapter

    adapter = DeepSeekUnderstandAdapter(api_key="fake-key-for-validation-test")
    try:
        adapter.understand(prompt="hi")
    except ValueError as e:
        assert "image" in str(e).lower()
    else:
        raise AssertionError("expected ValueError when deepseek-flash gets no image")
    try:
        adapter.understand_image("data/model-1.jpg", prompt="hi", reasoning_effort="ultra")
    except ValueError as e:
        assert "reasoning_effort" in str(e)
    else:
        raise AssertionError("expected ValueError for an invalid DeepSeek reasoning_effort")
    print("\u2713 DeepSeekUnderstandAdapter requires an image and rejects an invalid reasoning_effort")


def check_ternary_bonsai_reports_connection_errors_clearly():
    from tryon.models.ternary_bonsai import TernaryBonsaiAdapter

    adapter = TernaryBonsaiAdapter(base_url="http://127.0.0.1:1")
    try:
        adapter.understand(prompt="hi")
    except RuntimeError as e:
        assert "prismml.com" in str(e).lower() or "bonsai" in str(e).lower()
    else:
        raise AssertionError("expected RuntimeError when no local Bonsai server is running")
    print("\u2713 TernaryBonsaiAdapter raises a clear error when the local server is unreachable")


def check_new_model_integrations_dry_runs():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = cli_main([
            "video-generate", "--model", "p-video-2-pro",
            "--prompt", "A model walking a runway", "--duration", "10", "--dry-run",
        ])
    printed = buf.getvalue()
    assert code == 0 and "PVideo2ProAdapter" in printed and "'duration': 10" in printed, printed

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = cli_main([
            "video-generate", "--model", "fal-h3-max-lipsync",
            "--image", "data/model-1.jpg", "--audio", "data/voice.wav",
            "--resolution", "1080P", "--dry-run",
        ])
    printed = buf.getvalue()
    assert code == 0 and "generate_lip_sync" in printed and "'resolution': '1080P'" in printed, printed

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = cli_main([
            "understand", "--model", "qwen3.8-omni-flash",
            "--audio", "data/voice.wav", "--prompt", "What is said?", "--dry-run",
        ])
    printed = buf.getvalue()
    assert code == 0 and "'model': 'qwen3.8-omni-flash'" in printed, printed

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = cli_main([
            "understand", "--model", "glm-5.3-flashx",
            "--image", "data/model-1.jpg", "--prompt", "Describe the outfit", "--dry-run",
        ])
    printed = buf.getvalue()
    assert code == 0 and "GLMUnderstandAdapter" in printed and "'reasoning_effort': 'max'" in printed, printed

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = cli_main([
            "understand", "--model", "deepseek-flash",
            "--image", "data/model-1.jpg", "--prompt", "Describe the outfit",
            "--reasoning-effort", "none", "--dry-run",
        ])
    printed = buf.getvalue()
    assert code == 0 and "DeepSeekUnderstandAdapter" in printed and "'reasoning_effort': 'none'" in printed, printed

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = cli_main([
            "understand", "--model", "ternary-bonsai-2-27b",
            "--prompt", "hi", "--thinking-budget-tokens", "512", "--dry-run",
        ])
    printed = buf.getvalue()
    assert code == 0 and "'thinking_budget_tokens': 512" in printed, printed

    print(
        "\u2713 video-generate p-video-2-pro / fal-h3-max-lipsync and "
        "understand qwen3.8-omni-flash / glm-5.3-flashx / deepseek-flash / ternary-bonsai-2-27b "
        "--dry-run resolve the expected calls"
    )


def check_deepseek_local_dry_runs():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = cli_main([
            "understand", "--model", "deepseek-vl2",
            "--image", "data/model-1.jpg", "--prompt", "Describe the outfit", "--dry-run",
        ])
    printed = buf.getvalue()
    assert code == 0 and "DeepSeekVL2Adapter" in printed and "'do_sample': False" in printed, printed

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = cli_main([
            "understand", "--model", "deepseek-vl2",
            "--video", "data/clip.mp4", "--prompt", "Summarize", "--num-frames", "4", "--dry-run",
        ])
    printed = buf.getvalue()
    assert code == 0 and "'video': 'data/clip.mp4'" in printed and "'num_frames': 4" in printed, printed

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = cli_main([
            "understand", "--model", "deepseek-ocr",
            "--image", "data/model-1.jpg", "--dry-run",
        ])
    printed = buf.getvalue()
    assert code == 0 and "DeepSeekOCRAdapter" in printed and "'mode': 'markdown'" in printed, printed

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = cli_main([
            "understand", "--model", "deepseek-ocr",
            "--image", "data/model-1.jpg", "--ocr-mode", "free", "--no-crop-mode", "--dry-run",
        ])
    printed = buf.getvalue()
    assert code == 0 and "'mode': 'free'" in printed and "'crop_mode': False" in printed, printed

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = cli_main(["understand", "--model", "deepseek-ocr", "--dry-run"])
    assert code != 0, "expected deepseek-ocr to require --image"

    print(
        "\u2713 understand deepseek-vl2 (image/video) / deepseek-ocr (--ocr-mode, "
        "not --mode) --dry-run resolve the expected calls"
    )


def check_limite_dry_run_and_requires_prompt():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = cli_main([
            "understand", "--model", "limite-1b-violetto",
            "--prompt", "If x + 3 = 8, what is x?", "--dry-run",
        ])
    printed = buf.getvalue()
    assert code == 0 and "LimiteAdapter" in printed and "'max_new_tokens': 512" in printed, printed

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = cli_main(["understand", "--model", "limite-1b-violetto", "--dry-run"])
    assert code != 0, "expected limite-1b-violetto to require --prompt"

    print("\u2713 understand limite-1b-violetto --dry-run resolves the expected call and requires --prompt")


def check_elevenlabs_requires_text_and_valid_choices():
    from tryon.api.elevenlabs import ElevenLabsAdapter

    adapter = ElevenLabsAdapter(api_key="fake-key-for-validation-test")
    try:
        adapter.generate_speech("")
    except ValueError as e:
        assert "text" in str(e).lower()
    else:
        raise AssertionError("expected ValueError for empty text")
    try:
        adapter.generate_speech("hi", voice_id="")
    except ValueError as e:
        assert "voice_id" in str(e).lower()
    else:
        raise AssertionError("expected ValueError for empty voice_id")
    try:
        adapter.generate_speech("hi", model="eleven_v5")
    except ValueError as e:
        assert "model" in str(e).lower()
    else:
        raise AssertionError("expected ValueError for an unsupported model")
    try:
        adapter.generate_speech("hi", output_format="mp3_9999")
    except ValueError as e:
        assert "output_format" in str(e).lower()
    else:
        raise AssertionError("expected ValueError for an invalid output_format")
    print("\u2713 ElevenLabsAdapter rejects empty text/voice_id and invalid model/output_format")


def check_audio_extension_sniffing():
    from tryon.cli.runner import _sniff_audio_extension

    assert _sniff_audio_extension(b"ID3" + b"\x00" * 10) == ".mp3"
    assert _sniff_audio_extension(b"\xff\xfb" + b"\x00" * 10) == ".mp3"
    assert _sniff_audio_extension(b"RIFF\x00\x00\x00\x00WAVEfmt ") == ".wav"
    assert _sniff_audio_extension(b"OggS" + b"\x00" * 10) == ".opus"
    assert _sniff_audio_extension(b"\x00" * 20) == ".raw"
    print("\u2713 _sniff_audio_extension detects mp3/wav/opus, falls back to .raw for headerless PCM")


def check_tts_dry_runs():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = cli_main([
            "tts", "--model", "eleven-v4",
            "--text", "Welcome to the spring collection.", "--dry-run",
        ])
    printed = buf.getvalue()
    assert code == 0 and "ElevenLabsAdapter" in printed and "'model': 'eleven_v4'" in printed, printed
    assert "'voice_id': '21m00Tcm4TlvDq8ikWAM'" in printed, printed

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = cli_main([
            "tts", "--model", "eleven-v4-turbo",
            "--text", "[whispers] Hello.", "--output-format", "wav_44100",
            "--voice-id", "custom-voice-id", "--dry-run",
        ])
    printed = buf.getvalue()
    assert code == 0 and "'model': 'eleven_v4_turbo'" in printed and "'output_format': 'wav_44100'" in printed, printed
    assert "'voice_id': 'custom-voice-id'" in printed, printed

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = cli_main(["tts", "--model", "eleven-v4", "--dry-run"])
    assert code != 0, "expected eleven-v4 to require --text"

    print("\u2713 tts eleven-v4 / eleven-v4-turbo --dry-run resolve the expected calls")


def check_decide_embed_haiku_relight_dry_runs():
    """claude-haiku-5-5, fal-h3-max-relight and the new decide / embed services."""
    cases = [
        (["understand", "--model", "claude-haiku-5-5", "--image", "a.jpg", "--prompt", "fabric?",
          "--effort", "low", "--no-thinking"],
         "ClaudeUnderstandAdapter", "understand", ["'effort': 'low'", "'thinking': False", "'model': 'claude-haiku-5-5'"]),
        (["video-generate", "--model", "fal-h3-max-relight", "--video", "clip.mp4",
          "--reference-image", "sphere.png", "--resolution", "1080P"],
         "FalH3MaxAdapter", "generate_relight", ["'video': 'clip.mp4'", "'reference_image': 'sphere.png'", "'resolution': '1080P'"]),
        (["decide", "--model", "d1-3b", "--questions", "q.json", "--image", "a.jpg", "b.jpg"],
         "LiquidD1Adapter", "decide", ["'variant': 'd1-3B'", "'image': ['a.jpg', 'b.jpg']"]),
        (["decide", "--model", "d1-omni-600m", "--questions", "q.json", "--audio", "clip.wav"],
         "LiquidD1Adapter", "decide", ["'variant': 'd1-omni-600M'", "'audio': 'clip.wav'"]),
        (["decide", "--model", "jev", "--questions", "q.json", "--state", "red satin gown"],
         "JevAdapter", "decide", ["'model': 'jev-latest'", "'state': 'red satin gown'"]),
        (["embed", "--model", "embeddinggemma-2", "--text", "red gown", "--image", "a.jpg",
          "--query", "formal dress", "--dim", "256", "--modalities", "text+image"],
         "EmbeddingGemma2Adapter", "embed", ["'modalities': 'text+image'", "'dim': 256", "'query': 'formal dress'"]),
        (["embed", "--model", "pplx-embed-v2-late-9b", "--image", "p1.png", "p2.png", "--query", "wool coat"],
         "PplxEmbedLateAdapter", "embed", ["'variant': '9b'", "'image': ['p1.png', 'p2.png']"]),
        (["embed", "--model", "pplx-embed-v2-late-0.6b", "--text", "a b"],
         "PplxEmbedLateAdapter", "embed", ["'variant': '0.6b'"]),
    ]
    for argv, cls, method, needles in cases:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = cli_main([*argv, "--dry-run"])
        printed = buf.getvalue()
        assert code == 0, printed
        assert cls in printed and f".{method}(" in printed, printed
        for needle in needles:
            assert needle in printed, (needle, printed)
    for argv in (
        ["decide", "--model", "jev", "--questions", "q.json", "--dry-run"],   # --state required
        ["decide", "--model", "d1-3b", "--dry-run"],                          # --questions required
    ):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
            try:
                code = cli_main(argv)
            except SystemExit as exc:
                code = exc.code
        assert code != 0, argv
    print("\u2713 claude-haiku-5-5 / fal-h3-max-relight / decide (d1, jev) / embed --dry-run resolve")


def check_decision_helpers_and_adapters():
    import json
    import tempfile
    from unittest import mock

    from tryon.decision import load_questions, load_state

    good = {
        "refund": {"type": "noul", "instructions": "Refund?"},
        "team": {"type": "choice", "instructions": "Team?", "criteria": {"a": "x", "b": "y"}},
        "urgency": {"type": "score", "instructions": "Urgency?", "criteria": ["low", "high"]},
    }
    assert load_questions(good) == good
    assert load_questions(json.dumps(good)) == good
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(good, f)
    assert load_questions(f.name) == good
    for bad in (
        {}, "not json", {"q": {"type": "maybe", "instructions": "x"}}, {"q": {"type": "noul"}},
        {"q": {"type": "choice", "instructions": "x", "criteria": {"only": "one"}}},
        {"q": {"type": "score", "instructions": "x", "criteria": ["only-one"]}},
    ):
        try:
            load_questions(bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected ValueError for {bad!r}")
    assert load_state('{"a": 1}') == {"a": 1} and load_state("plain text") == "plain text"

    # Jev: payload shape + error handling (no network)
    from tryon.api.typesafe import JevAdapter

    adapter = JevAdapter(api_key="test")
    fake = mock.Mock(status_code=200)
    fake.json.return_value = {"model": "jev-1.13.0", "answers": {"refund": {"type": "noul", "noul": 0.9}},
                              "usage": {"input_tokens": 12, "output_tokens": 0}}
    with mock.patch("tryon.api.typesafe.adapter.requests.post", return_value=fake) as post:
        out = adapter.decide(questions=good, state="I want my money back")
    body = post.call_args.kwargs["json"]
    assert post.call_args.args[0].endswith("/v1/systemone")
    assert body["model"] == "jev-latest" and body["state"] == "I want my money back" and body["questions"] == good
    assert post.call_args.kwargs["headers"]["Authorization"] == "Bearer test"
    assert out["answers"]["refund"]["noul"] == 0.9
    try:
        adapter.decide(questions=good, state=None)
    except ValueError:
        pass
    else:
        raise AssertionError("Jev must require a state")
    bad = mock.Mock(status_code=401, text="nope")
    with mock.patch("tryon.api.typesafe.adapter.requests.post", return_value=bad):
        try:
            adapter.decide(questions=good, state="x")
        except RuntimeError as exc:
            assert "401" in str(exc)
        else:
            raise AssertionError("expected RuntimeError on HTTP 401")
    try:
        JevAdapter(api_key="test", model="jev-9")
    except ValueError:
        pass
    else:
        raise AssertionError("unknown Jev model must be rejected")

    # Liquid d1: invalid variant / missing deps raise clear errors before touching weights
    from tryon.models.liquid_d1 import LiquidD1Adapter

    try:
        LiquidD1Adapter(variant="d1-70B")
    except ValueError:
        pass
    else:
        raise AssertionError("unknown d1 variant must be rejected")
    print("\u2713 decide: question schema validation, Jev request/response, d1 variant checks")


def check_embeddings_packaging_and_adapters():
    from pathlib import Path

    import numpy as np

    from tryon.cli.registry import get_model
    from tryon.cli.runner import _package_embeddings

    with tempfile.TemporaryDirectory() as tmp:
        dense = {"model": "m", "kind": "dense", "labels": ["a", "b"],
                 "embeddings": np.arange(6, dtype="float32").reshape(2, 3), "scores": [0.5, 0.25]}
        packaged = _package_embeddings(dense, Path(tmp), "embed_test")
        assert packaged["output_kind"] == "embeddings" and packaged["count"] == 2 and packaged["dim"] == 3
        assert packaged["shapes"] == [[3], [3]] and packaged["scores"] == [0.5, 0.25]
        saved = np.load(packaged["output_path"])
        assert saved["emb_1"].tolist() == [3.0, 4.0, 5.0]

        multi = {"model": "m", "kind": "multi_vector", "labels": ["p1"],
                 "embeddings": [np.ones((5, 128), dtype="float32")]}
        packaged = _package_embeddings(multi, Path(tmp), "embed_multi")
        assert packaged["dim"] == 128 and packaged["shapes"] == [[5, 128]] and packaged["kind"] == "multi_vector"
    assert get_model("embed", "embeddinggemma-2").output_kind == "embeddings"

    from tryon.models.embeddinggemma import EmbeddingGemma2Adapter
    from tryon.models.pplx_embed import PplxEmbedLateAdapter

    for factory in (lambda: EmbeddingGemma2Adapter(modalities="audio-only"), lambda: PplxEmbedLateAdapter(variant="3b")):
        try:
            factory()
        except ValueError:
            pass
        else:
            raise AssertionError("invalid option must be rejected before heavy imports")
    print("\u2713 embed: .npz packaging for dense + multi-vector, adapter option validation")


def check_haiku_and_relight_adapters():
    from unittest import mock

    from tryon.api.claude import ClaudeUnderstandAdapter
    from tryon.api.fal import FalH3MaxAdapter

    adapter = ClaudeUnderstandAdapter(api_key="test")
    block = mock.Mock(type="text", text="cotton, navy, slim fit")
    message = mock.Mock(content=[block], model="claude-haiku-5-5", stop_reason="end_turn", usage=None)
    with mock.patch.object(adapter.client.messages, "create", return_value=message) as create:
        out = adapter.understand(image="https://example.com/a.png", prompt="describe", effort="high", thinking=False)
    kwargs = create.call_args.kwargs
    assert out["text"] == "cotton, navy, slim fit"
    assert kwargs["model"] == "claude-haiku-5-5" and kwargs["thinking"] == {"type": "disabled"}
    assert kwargs["extra_body"] == {"output_config": {"effort": "high"}}
    assert "temperature" not in kwargs and "top_p" not in kwargs  # non-default values return 400 on Haiku 5.5
    assert kwargs["messages"][0]["content"][0] == {"type": "image", "source": {"type": "url", "url": "https://example.com/a.png"}}
    for bad in ({"effort": "max", "thinking": False}, {"effort": "turbo"}):
        try:
            adapter.understand(prompt="x", **bad)
        except ValueError:
            pass
        else:
            raise AssertionError(bad)
    try:
        ClaudeUnderstandAdapter(api_key="test", model="claude-haiku-4-5")
    except ValueError:
        pass
    else:
        raise AssertionError("only claude-haiku-5-5 is registered")

    fal = FalH3MaxAdapter(api_key="test")
    with mock.patch.object(fal, "_run_endpoint", return_value=b"mp4") as run:
        assert fal.generate_relight("https://e.com/v.mp4", "https://e.com/sphere.png", resolution="2K", seed=7) == b"mp4"
    endpoint, payload = run.call_args.args
    assert endpoint == "minimax/h3-max/relight"
    assert payload["video_url"] == "https://e.com/v.mp4" and payload["reference_image_url"] == "https://e.com/sphere.png"
    assert payload["resolution"] == "2K" and payload["aspect_ratio"] == "16:9" and payload["seed"] == 7
    assert "prompt" not in payload  # the relight endpoint has no prompt field
    for bad in ({"resolution": "4K"}, {"aspect_ratio": "5:4"}):
        try:
            fal.generate_relight("https://e.com/v.mp4", "https://e.com/s.png", **bad)
        except ValueError:
            pass
        else:
            raise AssertionError(bad)
    print("\u2713 Claude Haiku 5.5 request shape + H3 Max Relight payload/validation")


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
        (["generate", "--model", "p-image-ideogram", "--prompt", "atelier noir poster"],
         "PImageIdeogramAdapter", "generate_text_to_image"),
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
        (["video-generate", "--model", "minimax-h3-max", "--prompt", "runway walk"],
         "MiniMaxH3Adapter", "generate_text_to_video"),
        (["video-generate", "--model", "minimax-h3-max", "--prompt", "animate",
          "--image", "data/model-1.jpg"],
         "MiniMaxH3Adapter", "generate_image_to_video"),
        (["video-generate", "--model", "fal-h3-max", "--prompt", "runway walk"],
         "FalH3MaxAdapter", "generate_text_to_video"),
        (["video-generate", "--model", "fal-h3-max", "--prompt", "animate",
          "--image", "data/model-1.jpg"],
         "FalH3MaxAdapter", "generate_image_to_video"),
        (["video-generate", "--model", "fal-h3-max", "--prompt", "Image 1 is the model",
          "--reference-image", "data/model-1.jpg"],
         "FalH3MaxAdapter", "generate_text_to_video"),
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
        (["video-generate", "--model", "cosmos3", "--prompt", "runway walk"],
         "Cosmos3VideoAdapter", "generate_text_to_video"),
        (["video-generate", "--model", "cosmos3", "--prompt", "animate",
          "--image", "data/model-1.jpg"],
         "Cosmos3VideoAdapter", "generate_image_to_video"),
        (["vton", "--model", "leffa",
          "--person-image", "data/model-1.jpg", "--garment-image", "data/garment.png"],
         "LeffaAdapter", "generate_and_decode"),
        (["vton", "--model", "catvton",
          "--person-image", "data/model-1.jpg", "--garment-image", "data/garment.png"],
         "CatVTONAdapter", "generate_and_decode"),
    ]
    for argv, expect_cls, expect_method in cases:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = cli_main([*argv, "--dry-run"])
        printed = buf.getvalue()
        assert code == 0, printed
        assert expect_cls in printed and f".{expect_method}(" in printed, printed
        if "minimax-h3-max" in argv:
            assert "MiniMax-H3-Max" in printed, printed
        if "fal-h3-max" in argv and "--reference-image" in argv:
            assert "reference_image" in printed, printed
    print("\u2713 new Seedance/Seedream/Ideogram/Grok/Kling/Ray3.2/Pruna/LTX/Hailuo/MiniMax-H3/Muse/Wan/Runway --dry-run calls resolve")


if __name__ == "__main__":
    check_decide_embed_haiku_relight_dry_runs()
    check_decision_helpers_and_adapters()
    check_embeddings_packaging_and_adapters()
    check_haiku_and_relight_adapters()
    check_video_wave_dry_runs()
    check_veo_seedance_validation()
    check_registry_has_no_flag_collisions()
    check_wan3_model_aliases()
    check_seedance_25_model_id()
    check_p_image_ideogram_thinking_aliases()
    check_every_model_parser_builds()
    check_flux_vto_dry_run()
    check_flux_vto_real_call()
    check_p_image_tryon_dry_run()
    check_nano_banana_2_lite_dry_runs()
    check_gpt_image_25_dry_runs()
    check_fashn_dry_runs()
    check_google_vton_dry_run()
    check_outfitanyone_plus_dry_run()
    check_photoroom_dry_runs()
    check_gemini_omni_dry_runs()
    check_new_media_models_dry_runs()
    check_kimi_dry_runs()
    check_qwen_dry_runs()
    check_hy4_dry_runs()
    check_nvidia_nim_dry_runs()
    check_qwen_image_dry_runs()
    check_qwen_image_local_helpers()
    check_qwen_image_local_dry_runs()
    check_kimi_understand_requires_image_or_video()
    check_qwen_understand_requires_image_or_video()
    check_hy4_requires_prompt_or_image()
    check_nvidia_understand_requires_media()
    check_qwen_image_requires_prompt_and_tryon_inputs()
    check_minimax_h3_requires_prompt()
    check_fal_h3_max_requires_prompt()
    check_fal_h3_max_lipsync_requires_valid_resolution()
    check_p_video_2_pro_requires_valid_duration()
    check_qwen_omni_flash_audio_requires_omni_model()
    check_glm_rejects_invalid_reasoning_effort()
    check_deepseek_flash_requires_image()
    check_ternary_bonsai_reports_connection_errors_clearly()
    check_new_model_integrations_dry_runs()
    check_deepseek_local_dry_runs()
    check_limite_dry_run_and_requires_prompt()
    check_elevenlabs_requires_text_and_valid_choices()
    check_audio_extension_sniffing()
    check_tts_dry_runs()
    check_muse_image_requires_prompt()
    check_kimi_k26_real_call()
    print("\nAll CLI checks passed.")
