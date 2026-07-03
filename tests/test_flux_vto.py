"""
Manual smoke test for FluxVTONAdapter — makes a real call to the BFL FLUX VTO API.

Run:
    python3.10 tests/test_flux_vto.py
"""
import importlib.util
import os
import time

from dotenv import load_dotenv

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(REPO_ROOT, ".env"))

# Load flux_vto.py directly, bypassing tryon/api/__init__.py (which eagerly
# imports every adapter, including heavy ones requiring torch/timm that
# aren't needed just to exercise this module).
_MODULE_PATH = os.path.join(REPO_ROOT, "tryon", "api", "vton", "flux_vto.py")
_spec = importlib.util.spec_from_file_location("flux_vto", _MODULE_PATH)
_flux_vto = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_flux_vto)
FluxVTONAdapter = _flux_vto.FluxVTONAdapter

PERSON_PATH = os.path.join(REPO_ROOT, "data", "model-1.jpg")
GARMENT_PATH = os.path.join(REPO_ROOT, "data", "garment.png")
OUTPUT_PATH = os.path.join(REPO_ROOT, "outputs", "test_flux_vto_result.png")


def main():
    print(f"BFL_API_KEY set: {bool(os.getenv('BFL_API_KEY'))}")
    print(f"Person image: {PERSON_PATH} (exists={os.path.exists(PERSON_PATH)})")
    print(f"Garment image: {GARMENT_PATH} (exists={os.path.exists(GARMENT_PATH)})")

    adapter = FluxVTONAdapter()
    print(f"Adapter endpoint: {adapter.endpoint}")

    start = time.time()
    images = adapter.generate_and_decode(
        person=PERSON_PATH,
        garment=GARMENT_PATH,
        garment_description="black leather biker jacket with silver zippers",
        output_format="png",
    )
    elapsed = time.time() - start
    print(f"Generated {len(images)} image(s) in {elapsed:.1f}s")

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    images[0].save(OUTPUT_PATH)
    print(f"Saved result to {os.path.abspath(OUTPUT_PATH)}")


if __name__ == "__main__":
    main()
