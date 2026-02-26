from __future__ import annotations

import json
from pathlib import Path

from researcher_ai.retrieval.index import search_index
from researcher_ai.utils.text_clean import (
    is_useful_sentence,
    normalize_text,
    score_sentence,
    split_sentences,
)


def _pick_sentences(text: str) -> list[str]:
    sentences = split_sentences(text)
    useful = [s for s in sentences if is_useful_sentence(s, min_chars=45)]
    candidates = useful if useful else sentences
    return sorted(candidates, key=score_sentence, reverse=True)


def _topic_bucket(sentence: str) -> str:
    s = sentence.lower()
    if any(k in s for k in ["exam", "mid-term", "final"]):
        return "exam_focus"
    if any(k in s for k in ["what is", "not", "definition", "core ideas"]):
        return "fundamentals"
    if any(k in s for k in ["classification", "regression", "clustering", "embedding", "evaluation", "pipeline"]):
        return "core_methods"
    if any(k in s for k in ["guideline", "never", "plagiarism", "attention"]):
        return "common_mistakes"
    return "core_methods"


def generate_notes(
    query: str,
    index_path: str,
    meta_path: str,
    output_path: str,
    top_k: int = 6,
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
) -> dict:
    requested_k = max(top_k, 6)
    results = search_index(
        query=query,
        index_path=index_path,
        meta_path=meta_path,
        top_k=requested_k * 2,
        model_name=model_name,
        diversify_citations=True,
    )
    if not results:
        raise ValueError("No retrieval results found for note generation.")

    key_points: list[dict] = []
    ground_up: list[dict] = []
    deep_dive: list[dict] = []
    structured = {
        "fundamentals": [],
        "core_methods": [],
        "exam_focus": [],
        "common_mistakes": [],
        "checklist": [],
    }
    seen_points: set[str] = set()

    for row in results:
        sentences = _pick_sentences(row["text"])
        if not sentences:
            continue
        first = normalize_text(sentences[0])
        if first not in seen_points:
            key_points.append({"text": first, "citation": row["citation"]})
            seen_points.add(first)
            bucket = _topic_bucket(first)
            structured[bucket].append({"text": first, "citation": row["citation"]})

        simple = normalize_text(min(sentences, key=len))
        if simple not in seen_points:
            seen_points.add(simple)
            ground_up.append(
                {
                    "text": f"Basic idea: {simple}",
                    "citation": row["citation"],
                }
            )

        longer = normalize_text(max(sentences, key=len))
        if longer not in seen_points:
            seen_points.add(longer)
            deep_dive.append(
                {
                    "text": f"Technical detail: {longer}",
                    "citation": row["citation"],
                }
            )

    for item in key_points[:requested_k]:
        structured["checklist"].append(
            {
                "text": f"Review and be able to explain: {item['text']}",
                "citation": item["citation"],
            }
        )

    payload = {
        "query": query,
        "overview": f"Notes generated from top {len(results)} retrieved chunks.",
        "key_points": key_points[: requested_k],
        "ground_up": ground_up[: requested_k],
        "deep_dive": deep_dive[: requested_k],
        "structured_notes": {
            "fundamentals": structured["fundamentals"][:4],
            "core_methods": structured["core_methods"][:4],
            "exam_focus": structured["exam_focus"][:4],
            "common_mistakes": structured["common_mistakes"][:4],
            "checklist": structured["checklist"][:6],
        },
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
