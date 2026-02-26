from __future__ import annotations

import re


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
    return True


def best_topic_phrase(text: str) -> str:
    cleaned = normalize_text(text)
    words = [w.strip(".,:;()[]{}'\"") for w in cleaned.split()]
    candidates = [w for w in words if len(w) >= 4 and any(ch.isalpha() for ch in w)]
    if not candidates:
        return "the topic"
    phrase = " ".join(candidates[:3]).lower()
    return phrase
