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


if __name__ == "__main__":
    check_registry_has_no_flag_collisions()
    check_every_model_parser_builds()
    check_flux_vto_dry_run()
    check_flux_vto_real_call()
    print("\nAll CLI checks passed.")
