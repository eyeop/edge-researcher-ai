from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable

from researcher_ai.utils.text_clean import normalize_text


TEXT_EXTENSIONS = {".txt", ".md"}
PDF_EXTENSIONS = {".pdf"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif"}
SUPPORTED_EXTENSIONS = TEXT_EXTENSIONS | PDF_EXTENSIONS | IMAGE_EXTENSIONS


@dataclass
class IngestRecord:
    doc_id: str
    source_path: str
    source_type: str
    page: int
    item_index: int
    citation: str
    text: str


def _clean_text(text: str) -> str:
    return normalize_text(text)


def _iter_files(input_path: Path) -> Iterable[Path]:
    if input_path.is_file():
        yield input_path
        return

    for path in sorted(input_path.rglob("*")):
        if path.is_file():
            yield path


def _extract_text_file(path: Path) -> list[tuple[int, str]]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    return [(1, text)]


def _extract_pdf(path: Path) -> list[tuple[int, str]]:
    try:
        import fitz  # PyMuPDF
    except ImportError as exc:
        raise RuntimeError(
            "PDF parsing requires PyMuPDF. Install with: pip install pymupdf"
        ) from exc

    output: list[tuple[int, str]] = []
    with fitz.open(path) as doc:
        for page_idx, page in enumerate(doc, start=1):
            output.append((page_idx, page.get_text("text") or ""))
    return output


def _extract_image_ocr(path: Path) -> list[tuple[int, str]]:
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("Image OCR requires Pillow. Install with: pip install pillow") from exc

    try:
        import pytesseract
    except ImportError as exc:
        raise RuntimeError(
            "Image OCR requires pytesseract. Install with: pip install pytesseract"
        ) from exc

    text = pytesseract.image_to_string(Image.open(path))
    return [(1, text)]


def ingest_materials(input_path: str, output_path: str, min_chars: int = 20) -> dict:
    base = Path(input_path).expanduser().resolve()
    if not base.exists():
        raise FileNotFoundError(f"Input path does not exist: {base}")

    records: list[IngestRecord] = []
    skipped: list[str] = []

    for file_path in _iter_files(base):
        ext = file_path.suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            skipped.append(str(file_path))
            continue

        doc_id = uuid.uuid4().hex[:12]

        if ext in TEXT_EXTENSIONS:
            extracted = _extract_text_file(file_path)
            source_type = "text"
        elif ext in PDF_EXTENSIONS:
            extracted = _extract_pdf(file_path)
            source_type = "pdf"
        else:
            extracted = _extract_image_ocr(file_path)
            source_type = "image"

        for item_index, (page, raw_text) in enumerate(extracted, start=1):
            cleaned = _clean_text(raw_text)
            if len(cleaned) < min_chars:
                continue
            citation = f"{file_path.name}:p{page}:i{item_index}"
            records.append(
                IngestRecord(
                    doc_id=doc_id,
                    source_path=str(file_path),
                    source_type=source_type,
                    page=page,
                    item_index=item_index,
                    citation=citation,
                    text=cleaned,
                )
            )

    destination = Path(output_path).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(asdict(record), ensure_ascii=True) + "\n")

    return {
        "input": str(base),
        "output": str(destination),
        "records": len(records),
        "skipped_files": len(skipped),
    }
