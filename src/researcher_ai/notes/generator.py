from __future__ import annotations

import json
from pathlib import Path

from researcher_ai.retrieval.index import search_index
from researcher_ai.utils.text_clean import is_useful_sentence, normalize_text, split_sentences


def _pick_sentences(text: str) -> list[str]:
    sentences = split_sentences(text)
    useful = [s for s in sentences if is_useful_sentence(s, min_chars=45)]
    return useful if useful else sentences


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
        diversify_citations=True,
    )
    if not results:
        raise ValueError("No retrieval results found for note generation.")

    key_points: list[dict] = []
    ground_up: list[dict] = []
    deep_dive: list[dict] = []
    seen_points: set[str] = set()

    for row in results:
        sentences = _pick_sentences(row["text"])
        if not sentences:
            continue
        first = normalize_text(sentences[0])
        if first not in seen_points:
            key_points.append({"text": first, "citation": row["citation"]})
            seen_points.add(first)

        simple = normalize_text(min(sentences, key=len))
        ground_up.append(
            {
                "text": f"Basic idea: {simple}",
                "citation": row["citation"],
            }
        )

        longer = normalize_text(max(sentences, key=len))
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
