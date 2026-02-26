from __future__ import annotations

import json
from pathlib import Path


def _split_text(text: str, max_chars: int, overlap_chars: int) -> list[str]:
    cleaned = " ".join(text.split()).strip()
    if not cleaned:
        return []
    if len(cleaned) <= max_chars:
        return [cleaned]

    chunks: list[str] = []
    start = 0
    step = max(max_chars - overlap_chars, 1)
    while start < len(cleaned):
        end = min(start + max_chars, len(cleaned))
        chunk = cleaned[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(cleaned):
            break
        start += step
    return chunks


def chunk_ingested_records(
    ingest_path: str,
    chunk_output_path: str,
    coverage_output_path: str,
    max_chars: int = 700,
    overlap_chars: int = 120,
    min_chunk_chars: int = 40,
) -> dict:
    source = Path(ingest_path).expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(f"Ingest file does not exist: {source}")

    all_records: list[dict] = []
    with source.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            all_records.append(json.loads(line))

    chunks: list[dict] = []
    coverage: dict[str, bool] = {}

    for record in all_records:
        citation = record["citation"]
        coverage[citation] = False
        split_items = _split_text(
            text=record["text"],
            max_chars=max_chars,
            overlap_chars=overlap_chars,
        )
        valid = 0
        for idx, chunk_text in enumerate(split_items, start=1):
            if len(chunk_text) < min_chunk_chars:
                continue
            valid += 1
            chunks.append(
                {
                    "chunk_id": f"{record['doc_id']}-{record['item_index']}-{idx}",
                    "doc_id": record["doc_id"],
                    "source_path": record["source_path"],
                    "source_type": record["source_type"],
                    "page": record["page"],
                    "citation": citation,
                    "chunk_index": idx,
                    "text": chunk_text,
                }
            )
        if valid > 0:
            coverage[citation] = True

    chunk_dest = Path(chunk_output_path).expanduser().resolve()
    chunk_dest.parent.mkdir(parents=True, exist_ok=True)
    with chunk_dest.open("w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=True) + "\n")

    covered = [key for key, value in coverage.items() if value]
    uncovered = [key for key, value in coverage.items() if not value]
    coverage_payload = {
        "total_records": len(coverage),
        "covered_records": len(covered),
        "uncovered_records": len(uncovered),
        "coverage_ratio": (len(covered) / len(coverage)) if coverage else 0.0,
        "uncovered_citations": uncovered,
    }

    coverage_dest = Path(coverage_output_path).expanduser().resolve()
    coverage_dest.parent.mkdir(parents=True, exist_ok=True)
    coverage_dest.write_text(
        json.dumps(coverage_payload, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )

    return {
        "input": str(source),
        "chunk_output": str(chunk_dest),
        "coverage_output": str(coverage_dest),
        "chunks": len(chunks),
        "covered_records": len(covered),
        "uncovered_records": len(uncovered),
    }
