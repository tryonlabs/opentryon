"""Offline tests for BEN2 image loading (no model weights / GPU).

Run:
    conda run -n opentryon python tests/test_ben2_load_image.py
"""

from __future__ import annotations

import base64
import io
import os
import tempfile

from PIL import Image

from tryon.api.ben2.adapter import BEN2BackgroundRemoverAdapter


def _png_bytes() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (8, 8), (240, 89, 65)).save(buf, format="PNG")
    return buf.getvalue()


def _jpg_bytes() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (8, 8), (15, 1, 52)).save(buf, format="JPEG")
    return buf.getvalue()


def check_load_image_png_and_jpg_encodings():
    png = _png_bytes()
    jpg = _jpg_bytes()
    load = BEN2BackgroundRemoverAdapter.load_image

    from_bytes = load(png)
    assert from_bytes.size == (8, 8) and from_bytes.mode == "RGB"

    from_b64 = load(base64.b64encode(png).decode("ascii"))
    assert from_b64.size == (8, 8)

    from_data_url = load("data:image/png;base64," + base64.b64encode(png).decode("ascii"))
    assert from_data_url.size == (8, 8)

    from_jpg_b64 = load(base64.b64encode(jpg).decode("ascii"))
    assert from_jpg_b64.size == (8, 8) and from_jpg_b64.mode == "RGB"

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp.write(png)
        path = tmp.name
    try:
        from_path = load(path)
        assert from_path.size == (8, 8)
    finally:
        os.unlink(path)

    print("\u2713 BEN2 load_image accepts path, bytes, PNG/JPG base64, and data URLs")


def check_load_image_rejects_garbage():
    try:
        BEN2BackgroundRemoverAdapter.load_image("not-an-image")
    except ValueError as exc:
        assert "Unsupported image input type" in str(exc)
        print("\u2713 BEN2 load_image rejects non-image strings")
        return
    raise AssertionError("expected ValueError for garbage input")


def main():
    check_load_image_png_and_jpg_encodings()
    check_load_image_rejects_garbage()
    print("\nAll BEN2 load_image checks passed.")


if __name__ == "__main__":
    main()
