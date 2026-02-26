from __future__ import annotations

import json
from pathlib import Path

from researcher_ai.utils.text_clean import (
    best_topic_phrase,
    contains_hard_noise,
    is_useful_sentence,
    normalize_text,
    trim_for_display,
)


def _load_json(path: str) -> dict:
    target = Path(path).expanduser().resolve()
    if not target.exists():
        raise FileNotFoundError(f"File not found: {target}")
    return json.loads(target.read_text(encoding="utf-8"))


def _clean_items(items: list[dict], text_key: str = "text", limit: int = 6) -> list[dict]:
    cleaned: list[dict] = []
    seen: set[str] = set()
    for item in items:
        text = normalize_text(str(item.get(text_key, "")))
        if not text:
            continue
        if contains_hard_noise(text):
            continue
        if not is_useful_sentence(text, min_chars=30):
            continue
        text = trim_for_display(text, max_chars=170)
        if text in seen:
            continue
        seen.add(text)
        cleaned.append(
            {
                "text": text,
                "citation": item.get("citation", ""),
            }
        )
        if len(cleaned) >= limit:
            break
    return cleaned


def _format_mcq(question: dict, qid: int) -> dict:
    choices = [trim_for_display(normalize_text(str(c)), max_chars=120) for c in question.get("choices", [])]
    answer_text = choices[0] if choices else ""
    topic = best_topic_phrase(answer_text)
    stem = f"Which statement best matches the lecture's explanation of {topic}?"
    return {
        "id": f"P{qid}",
        "type": "mcq",
        "question": stem,
        "choices": choices[:4],
        "answer": question.get("answer", "A"),
        "explanation": trim_for_display(normalize_text(str(question.get("explanation", ""))), max_chars=160),
        "citation": question.get("citation", ""),
    }


def _format_short(question: dict, qid: int) -> dict:
    answer = trim_for_display(normalize_text(str(question.get("answer", ""))), max_chars=170)
    return {
        "id": f"P{qid}",
        "type": "short_answer",
        "question": "In your own words, summarize the core point in 1-2 sentences.",
        "answer": answer,
        "citation": question.get("citation", ""),
    }


def prepare_presentation(
    notes_input_path: str,
    quiz_input_path: str,
    notes_output_path: str,
    quiz_output_path: str,
) -> dict:
    notes = _load_json(notes_input_path)
    quiz = _load_json(quiz_input_path)

    key_points = _clean_items(notes.get("key_points", []), limit=6)
    ground_up = _clean_items(notes.get("ground_up", []), limit=5)
    deep_dive = _clean_items(notes.get("deep_dive", []), limit=5)
    exam_focus = _clean_items(
        notes.get("structured_notes", {}).get("exam_focus", []),
        limit=4,
    )

    if not exam_focus:
        exam_focus = _clean_items(key_points, limit=3)

    presentation_notes = {
        "query": notes.get("query", ""),
        "summary": "Presentation-ready notes generated from grounded citations.",
        "fundamentals": ground_up[:4],
        "core_points": key_points[:5],
        "deep_dive": deep_dive[:4],
        "exam_focus": exam_focus[:4],
        "citations": sorted(set(notes.get("citations", []))),
    }

    raw_quiz = quiz.get("quiz", [])
    formatted_quiz: list[dict] = []
    qid = 1
    for row in raw_quiz:
        qtype = row.get("type")
        if qtype == "mcq":
            formatted = _format_mcq(row, qid)
        elif qtype == "short_answer":
            formatted = _format_short(row, qid)
        else:
            continue
        if not formatted.get("citation"):
            continue
        formatted_quiz.append(formatted)
        qid += 1
        if len(formatted_quiz) >= 8:
            break

    presentation_quiz = {
        "query": quiz.get("query", ""),
        "summary": "Presentation-ready quiz set with concise prompts.",
        "question_count": len(formatted_quiz),
        "quiz": formatted_quiz,
        "citations": sorted({q["citation"] for q in formatted_quiz}),
    }

    notes_out = Path(notes_output_path).expanduser().resolve()
    notes_out.parent.mkdir(parents=True, exist_ok=True)
    notes_out.write_text(json.dumps(presentation_notes, ensure_ascii=True, indent=2), encoding="utf-8")

    quiz_out = Path(quiz_output_path).expanduser().resolve()
    quiz_out.parent.mkdir(parents=True, exist_ok=True)
    quiz_out.write_text(json.dumps(presentation_quiz, ensure_ascii=True, indent=2), encoding="utf-8")

    return {
        "notes_output": str(notes_out),
        "quiz_output": str(quiz_out),
        "notes_points": len(presentation_notes["core_points"]),
        "quiz_questions": len(formatted_quiz),
    }
