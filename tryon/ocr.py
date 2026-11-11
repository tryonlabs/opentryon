"""
Shared helpers for OCR models on the ``parse`` service (LightOnOCR-3).

- :func:`load_pages` turns an image path / URL / PIL image, or a PDF, into a list of page
  images (PDFs are rendered with ``pypdfium2`` so the longest side is 2048 px, LightOn's
  recommended setting).
- :func:`parse_grounding` reads LightOnOCR's grounding output, where every block starts
  with a marker ``![label](x1,y1,x2,y2)`` (coordinates normalised to 0-1000) and a
  ``label+`` marks a block that continues the previous one (e.g. across columns).
- :func:`blocks_to_markdown` joins parsed blocks back into plain markdown.
"""

from __future__ import annotations

import io
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

from PIL import Image

PageInput = Union[str, Path, bytes, Image.Image]
PDF_LONGEST_SIDE = 2048

_MARKER = re.compile(
    r"!\[(?P<label>[A-Za-z_][\w-]*?)(?P<cont>\+)?\]"
    r"\(\s*(?P<x1>\d+)\s*,\s*(?P<y1>\d+)\s*,\s*(?P<x2>\d+)\s*,\s*(?P<y2>\d+)\s*\)"
)


def parse_page_spec(spec: Optional[Union[str, Sequence[int]]], page_count: int) -> List[int]:
    """``"1-3,5"`` -> ``[0, 1, 2, 4]`` (1-based in, 0-based out). ``None`` means all pages."""
    if spec is None or spec == "":
        return list(range(page_count))
    if not isinstance(spec, str):
        numbers = [int(n) for n in spec]
    else:
        numbers = []
        for part in spec.replace(" ", "").split(","):
            if not part:
                continue
            if "-" in part:
                start, _, end = part.partition("-")
                lo, hi = int(start), int(end)
                if lo > hi:
                    raise ValueError(f"Invalid page range {part!r}.")
                numbers.extend(range(lo, hi + 1))
            else:
                numbers.append(int(part))
    for n in numbers:
        if not 1 <= n <= page_count:
            raise ValueError(f"Page {n} is out of range (document has {page_count} page(s)).")
    return [n - 1 for n in dict.fromkeys(numbers)]


def _render_pdf(data: bytes, pages: Optional[Union[str, Sequence[int]]], longest_side: int) -> List[Image.Image]:
    try:
        import pypdfium2 as pdfium
    except ImportError as exc:
        raise ImportError("PDF input needs pypdfium2: pip install pypdfium2") from exc
    pdf = pdfium.PdfDocument(data)
    images: List[Image.Image] = []
    for index in parse_page_spec(pages, len(pdf)):
        page = pdf[index]
        width, height = page.get_size()  # PDF points
        scale = longest_side / max(width, height)
        images.append(page.render(scale=scale).to_pil().convert("RGB"))
    return images


def load_pages(
    source: PageInput,
    pages: Optional[Union[str, Sequence[int]]] = None,
    longest_side: int = PDF_LONGEST_SIDE,
) -> List[Image.Image]:
    """Return RGB page images for an image (path, URL, bytes, PIL) or a PDF (path, URL, bytes)."""
    if isinstance(source, Image.Image):
        if pages not in (None, "", "1"):
            raise ValueError("pages only applies to PDF input.")
        return [source.convert("RGB")]
    if isinstance(source, (bytes, bytearray)):
        data = bytes(source)
    else:
        text = str(source)
        if text.startswith(("http://", "https://")):
            import requests

            resp = requests.get(text, timeout=120)
            resp.raise_for_status()
            data = resp.content
        else:
            path = Path(text)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {text}")
            data = path.read_bytes()
    if data[:5] == b"%PDF-":
        return _render_pdf(data, pages, longest_side)
    if pages not in (None, "", "1"):
        raise ValueError("pages only applies to PDF input.")
    return [Image.open(io.BytesIO(data)).convert("RGB")]


def parse_grounding(raw: str) -> List[Dict[str, Any]]:
    """Split LightOnOCR grounding output into ``{label, bbox, text, continues}`` blocks.

    ``bbox`` is ``[x1, y1, x2, y2]`` normalised to 0-1000. Text before the first marker
    (rare) is returned as a block with label ``None`` and no bbox.
    """
    blocks: List[Dict[str, Any]] = []
    matches = list(_MARKER.finditer(raw or ""))
    lead = (raw or "")[: matches[0].start()].strip() if matches else (raw or "").strip()
    if lead:
        blocks.append({"label": None, "bbox": None, "text": lead, "continues": False})
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(raw)
        blocks.append({
            "label": m.group("label"),
            "bbox": [int(m.group(k)) for k in ("x1", "y1", "x2", "y2")],
            "text": raw[m.end():end].strip(),
            "continues": bool(m.group("cont")),
        })
    return blocks


def blocks_to_markdown(blocks: Sequence[Dict[str, Any]], drop: Sequence[str] = ()) -> str:
    """Join block texts into markdown; continuation blocks are appended to the previous one."""
    parts: List[str] = []
    for block in blocks:
        if block.get("label") in drop or not block.get("text"):
            continue
        if block.get("continues") and parts:
            parts[-1] = f"{parts[-1]} {block['text']}"
        else:
            parts.append(block["text"])
    return "\n\n".join(parts)


def package_pages(model: str, endpoint: str, grounding: bool, raw_pages: Sequence[str]) -> Dict[str, Any]:
    """Build the ``parse`` result: per-page markdown (+ blocks with grounding) and a joined document."""
    pages: List[Dict[str, Any]] = []
    for number, raw in enumerate(raw_pages, start=1):
        if grounding:
            blocks = parse_grounding(raw)
            pages.append({"page": number, "markdown": blocks_to_markdown(blocks), "blocks": blocks, "raw": raw})
        else:
            pages.append({"page": number, "markdown": (raw or "").strip(), "blocks": []})
    return {
        "model": model,
        "endpoint": endpoint,
        "grounding": grounding,
        "page_count": len(pages),
        "markdown": "\n\n".join(p["markdown"] for p in pages if p["markdown"]),
        "blocks": [dict(b, page=p["page"]) for p in pages for b in p["blocks"]],
        "pages": pages,
    }

