from __future__ import annotations

import json
from pathlib import Path

from researcher_ai.retrieval.index import search_index


def _sentence_split(text: str) -> list[str]:
    cleaned = text.replace("\n", " ").strip()
    if not cleaned:
        return []
    parts = [p.strip() for p in cleaned.split(".") if p.strip()]
    return [p + "." for p in parts]


def _fallback_definition(text: str) -> str:
    tokens = text.split()
    return " ".join(tokens[: min(len(tokens), 12)]).strip()


def generate_quiz(
    query: str,
    index_path: str,
    meta_path: str,
    output_path: str,
    question_count: int = 5,
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
) -> dict:
    top_k = max(question_count, 3)
    rows = search_index(
        query=query,
        index_path=index_path,
        meta_path=meta_path,
        top_k=top_k,
        model_name=model_name,
    )
    if not rows:
        raise ValueError("No retrieval results found for quiz generation.")

    questions: list[dict] = []
    qid = 1
    for row in rows:
        if len(questions) >= question_count:
            break
        sentences = _sentence_split(row["text"])
        if not sentences:
            continue

        definition = sentences[0]
        answer_text = definition.replace(".", "")
        keyword = answer_text.split(" ")[0] if answer_text else "concept"

        mcq = {
            "id": f"Q{qid}",
            "type": "mcq",
            "question": f"Which statement best matches the source about '{keyword}'?",
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
