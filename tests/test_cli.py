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


def check_kimi_dry_runs():
    for model_id, expect_kwarg in [
        ("kimi-k2.6", "'thinking': True"),
        ("kimi-k2.7-code", "'model': 'kimi-k2.7-code'"),
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
    print("\u2713 understand kimi-k2.6 / kimi-k2.7-code / kimi-vl --dry-run resolve the expected calls")


def check_kimi_understand_requires_image_or_video():
    from tryon.api.kimi import KimiUnderstandAdapter

    try:
        KimiUnderstandAdapter(api_key="fake-key-for-validation-test").understand(prompt="hi")
    except ValueError as e:
        assert "image" in str(e) and "video" in str(e)
        print("\u2713 KimiUnderstandAdapter.understand() rejects missing image/video")
    else:
        raise AssertionError("expected ValueError when neither image nor video is given")


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


if __name__ == "__main__":
    check_registry_has_no_flag_collisions()
    check_every_model_parser_builds()
    check_flux_vto_dry_run()
    check_flux_vto_real_call()
    check_p_image_tryon_dry_run()
    check_nano_banana_2_lite_dry_runs()
    check_kimi_dry_runs()
    check_kimi_understand_requires_image_or_video()
    check_kimi_k26_real_call()
    print("\nAll CLI checks passed.")
