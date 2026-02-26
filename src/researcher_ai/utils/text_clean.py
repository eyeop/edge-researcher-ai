from __future__ import annotations

import re

NOISE_PATTERNS = [
    r"\bcourse administration\b",
    r"\bbefore the lecture\b",
    r"\bnext time\b",
    r"\bsummary\b",
    r"^\d+\s+",
]


def normalize_text(text: str) -> str:
    text = text.replace("\u25aa", " ").replace("\u2022", " ")
    text = text.replace("\u2013", "-").replace("\u2014", "-")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def split_sentences(text: str) -> list[str]:
    cleaned = normalize_text(text)
    if not cleaned:
        return []
    parts = re.split(r"(?<=[.!?])\s+", cleaned)
    out: list[str] = []
    for part in parts:
        sentence = part.strip()
        if not sentence:
            continue
        if sentence[-1] not in ".!?":
            sentence += "."
        out.append(sentence)
    return out


def is_useful_sentence(sentence: str, min_chars: int = 35) -> bool:
    s = normalize_text(sentence)
    if len(s) < min_chars:
        return False
    words = s.split()
    if len(words) < 6:
        return False
    alpha_words = sum(any(ch.isalpha() for ch in token) for token in words)
    if alpha_words < max(4, int(0.5 * len(words))):
        return False
    if re.match(r"^[\d\W_]+$", s):
        return False
    lower = s.lower()
    for pattern in NOISE_PATTERNS:
        if re.search(pattern, lower):
            return False
    return True


def score_sentence(sentence: str) -> float:
    s = normalize_text(sentence)
    if not s:
        return 0.0
    words = s.split()
    length_score = min(len(words) / 24.0, 1.0)
    keyword_bonus = 0.0
    for token in [
        "classification",
        "regression",
        "clustering",
        "evaluation",
        "embedding",
        "topic",
        "exam",
        "pipeline",
        "model",
        "learning",
    ]:
        if token in s.lower():
            keyword_bonus += 0.08
    punctuation_penalty = 0.2 if s.count("-") > 7 else 0.0
    return max(length_score + keyword_bonus - punctuation_penalty, 0.0)


def best_topic_phrase(text: str) -> str:
    cleaned = normalize_text(text)
    words = [w.strip(".,:;()[]{}'\"") for w in cleaned.split()]
    candidates = [w for w in words if len(w) >= 4 and any(ch.isalpha() for ch in w)]
    if not candidates:
        return "the topic"
    phrase = " ".join(candidates[:3]).lower()
    return phrase
