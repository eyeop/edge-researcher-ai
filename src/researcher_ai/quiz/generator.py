from __future__ import annotations

import json
from pathlib import Path

from researcher_ai.retrieval.index import search_index
from researcher_ai.utils.text_clean import (
    best_topic_phrase,
    is_useful_sentence,
    normalize_text,
    split_sentences,
)

def _fallback_definition(text: str) -> str:
    tokens = normalize_text(text).split()
    return " ".join(tokens[: min(len(tokens), 12)]).strip()


def _pick_definition(text: str) -> str:
    sentences = split_sentences(text)
    useful = [s for s in sentences if is_useful_sentence(s, min_chars=45)]
    selected = useful[0] if useful else (sentences[0] if sentences else normalize_text(text))
    return normalize_text(selected)


def generate_quiz(
    query: str,
    index_path: str,
    meta_path: str,
    output_path: str,
    question_count: int = 5,
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
) -> dict:
    top_k = max(question_count * 2, 6)
    rows = search_index(
        query=query,
        index_path=index_path,
        meta_path=meta_path,
        top_k=top_k,
        model_name=model_name,
        diversify_citations=True,
    )
    if not rows:
        raise ValueError("No retrieval results found for quiz generation.")

    questions: list[dict] = []
    qid = 1
    for row in rows:
        if len(questions) >= question_count:
            break
        definition = _pick_definition(row["text"])
        if not definition:
            continue

        answer_text = definition.replace(".", "")
        topic = best_topic_phrase(answer_text)

        mcq = {
            "id": f"Q{qid}",
            "type": "mcq",
            "question": f"Which statement best matches the source about {topic}?",
            "choices": [
                answer_text,
                "It is unrelated to model performance and deployment.",
                "It only applies to cloud-only systems.",
                "It removes the need for data preprocessing.",
            ],
            "answer": "A",
            "explanation": f"Choice A is directly supported by: {row['citation']}",
            "citation": row["citation"],
        }
        questions.append(mcq)
        qid += 1

        if len(questions) >= question_count:
            break

        short_answer = {
            "id": f"Q{qid}",
            "type": "short_answer",
            "question": "Summarize the main claim from this source in 1-2 sentences.",
            "answer": definition,
            "citation": row["citation"],
        }
        questions.append(short_answer)
        qid += 1

        if len(questions) >= question_count:
            break

        explain_why = {
            "id": f"Q{qid}",
            "type": "explain_why",
            "question": "Why does this point matter in building an efficient local AI system?",
            "answer": (
                "Because it impacts real deployment constraints like latency, "
                "memory footprint, and practical reliability."
            ),
            "citation": row["citation"],
            "hint": _fallback_definition(row["text"]),
        }
        questions.append(explain_why)
        qid += 1

    payload = {
        "query": query,
        "question_count": len(questions),
        "quiz": questions[:question_count],
        "citations": sorted({q["citation"] for q in questions}),
    }

    destination = Path(output_path).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )

    return {
        "output": str(destination),
        "questions": len(payload["quiz"]),
        "citations": len(payload["citations"]),
    }
