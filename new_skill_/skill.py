"""Dependency-free text quality analysis for skill content."""

import re
from collections import Counter


_SENTENCE_PATTERN = re.compile(r"[^.!?]+[.!?]?")
_WORD_PATTERN = re.compile(r"[A-Za-z][A-Za-z'-]*")


def analyze_text(value: str) -> dict:
    """Return clarity metrics and deterministic warnings for plain text."""
    normalized = " ".join(value.split())
    if not normalized:
        return _report(0, 0, 0, [], ["Text is empty."])

    sentences = [sentence.strip() for sentence in _SENTENCE_PATTERN.findall(normalized) if sentence.strip()]
    words = _WORD_PATTERN.findall(normalized.lower())
    sentence_lengths = [len(_WORD_PATTERN.findall(sentence)) for sentence in sentences]
    warnings = _warnings(words, sentence_lengths)
    return _report(len(words), len(sentences), _reading_minutes(len(words)), sentence_lengths, warnings)


def _warnings(words: list[str], sentence_lengths: list[int]) -> list[str]:
    warnings = []
    if len(words) < 20:
        warnings.append("Add detail to make the content more useful.")
    if any(length > 30 for length in sentence_lengths):
        warnings.append("Split sentences longer than 30 words.")
    repeated_words = [word for word, count in Counter(words).items() if count >= 5 and len(word) > 3]
    if repeated_words:
        warnings.append("Reduce repeated terminology: " + ", ".join(sorted(repeated_words)[:3]) + ".")
    return warnings


def _report(
    word_count: int,
    sentence_count: int,
    reading_minutes: int,
    sentence_lengths: list[int],
    warnings: list[str],
) -> dict:
    average_sentence_length = round(sum(sentence_lengths) / sentence_count, 1) if sentence_count else 0
    return {
        "word_count": word_count,
        "sentence_count": sentence_count,
        "average_sentence_length": average_sentence_length,
        "estimated_reading_minutes": reading_minutes,
        "warnings": warnings,
    }


def _reading_minutes(word_count: int) -> int:
    return max(1, (word_count + 199) // 200) if word_count else 0