from __future__ import annotations

import json
from pathlib import Path

from researcher_ai.retrieval.index import search_index


def _sentence_split(text: str) -> list[str]:
    cleaned = text.replace("\n", " ").strip()
    if not cleaned:
        return []
    sentences = [part.strip() for part in cleaned.split(".") if part.strip()]
    return [s + "." for s in sentences]


def generate_notes(
    query: str,
    index_path: str,
    meta_path: str,
    output_path: str,
    top_k: int = 6,
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
) -> dict:
    results = search_index(
        query=query,
        index_path=index_path,
        meta_path=meta_path,
        top_k=top_k,
        model_name=model_name,
    )
    if not results:
        raise ValueError("No retrieval results found for note generation.")

    key_points: list[dict] = []
    ground_up: list[dict] = []
    deep_dive: list[dict] = []
    seen_points: set[str] = set()

    for row in results:
        sentences = _sentence_split(row["text"])
        if not sentences:
            continue
        first = sentences[0]
        if first not in seen_points:
            key_points.append({"text": first, "citation": row["citation"]})
            seen_points.add(first)

        simple = min(sentences, key=len)
        ground_up.append(
            {
                "text": f"Basic idea: {simple}",
                "citation": row["citation"],
            }
        )

        longer = max(sentences, key=len)
        deep_dive.append(
            {
                "text": f"Technical detail: {longer}",
                "citation": row["citation"],
            }
        )

    payload = {
        "query": query,
        "overview": f"Notes generated from top {len(results)} retrieved chunks.",
        "key_points": key_points[: top_k],
        "ground_up": ground_up[: top_k],
        "deep_dive": deep_dive[: top_k],
        "citations": sorted({row["citation"] for row in results}),
    }

    destination = Path(output_path).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )

    return {
        "output": str(destination),
        "query": query,
        "sections": 3,
        "citations": len(payload["citations"]),
    }
