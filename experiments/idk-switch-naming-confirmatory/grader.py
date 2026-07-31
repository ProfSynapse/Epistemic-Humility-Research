"""Grader for idk-switch-naming-confirmatory.

Byte-for-byte copy of `experiments/write-direction-naming-battery/grader.py`
(source sha256 920800adb5f7c0b1b957edb19668085c0a2b45792781ba1c768a23b4d728b7a4,
matching that file's own pin in `write-direction-naming-battery/experiment.yaml`
`instrument.pins.grader.py`, verified 2026-07-31), itself a byte-for-byte port
from `experiments/margin-mapping/harness/grader.py`. This cell's AMENDMENT.md
"Design" pins "the naming battery's pinned operating point"; this grader is
part of that operating point (`execution.graders: grader:grade`, narrow
semantic_refuse + correctness), so it is copied verbatim, not re-derived.

Fields returned by `grade_one`:
  degenerate          bool   coherence-floor flag
  refused             bool   (not degenerate) and is_stated_confidence_refusal
  answered            bool   (not degenerate) and (not refused)
  correct             bool | None   alias-match correctness, only
                       when answered and aliases are non-empty; else None
  well_formed_correct bool   answered and (not degenerate) and correct is True
"""

from __future__ import annotations

import re
from typing import Optional


_MAX_NGRAM = 20
_MIN_REPEATS = 3
_DOMINANT_REPEAT_MIN_FRAC = 0.6

_CHAR_MAX_NGRAM = 6
_CHAR_MIN_REPEATS = 8
_CHAR_DOMINANT_REPEAT_MIN_FRAC = 0.5
_CHAR_DOMINANT_REPEAT_MIN_LEN = 12

_ANSWER_FIELD_RE = re.compile(r'"answer"\s*:\s*"(.*)', re.DOTALL)
_ANSWER_FIELD_TRAILING_RE = re.compile(
    r'"\s*(?:,\s*"(?:response_confidence|confidence)"\s*:\s*[0-9.eE+-]+\s*)?}\s*\Z'
)
_STATED_CONFIDENCE_REFUSAL_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bi\s+do\s+not\s+know\b", re.IGNORECASE),
    re.compile(r"\bi\s+don['’]t\s+know\b", re.IGNORECASE),
    re.compile(r"^\s*abstain\b", re.IGNORECASE),
)


def _is_repeated_ngram(tokens: list[str]) -> bool:
    n_tok = len(tokens)
    for n in range(1, _MAX_NGRAM + 1):
        if n_tok < n * _MIN_REPEATS:
            continue
        unit = tokens[:n]
        reps = n_tok // n
        if reps < _MIN_REPEATS:
            continue
        if all(tokens[i * n:(i + 1) * n] == unit for i in range(reps)) and \
                tokens[reps * n:] == unit[: n_tok - reps * n]:
            return True
    return False


def _extract_answer_field(text: str) -> str:
    m = _ANSWER_FIELD_RE.search(text)
    if not m:
        return text
    return _ANSWER_FIELD_TRAILING_RE.sub("", m.group(1))


def _has_dominant_repeated_unit(
    tokens: list[str],
    min_repeats: int = _MIN_REPEATS,
    max_n: int = _MAX_NGRAM,
    min_frac: float = _DOMINANT_REPEAT_MIN_FRAC,
) -> bool:
    n_tok = len(tokens)
    if n_tok < min_repeats:
        return False
    for n in range(1, max_n + 1):
        if n_tok < n * min_repeats:
            continue
        counts: dict[tuple[str, ...], int] = {}
        for i in range(n_tok - n + 1):
            gram = tuple(tokens[i:i + n])
            counts[gram] = counts.get(gram, 0) + 1
        best_count = max(counts.values())
        if best_count >= min_repeats and (best_count * n) / n_tok >= min_frac:
            return True
    return False


def _has_dominant_repeated_char_unit(
    text: str,
    min_repeats: int = _CHAR_MIN_REPEATS,
    max_n: int = _CHAR_MAX_NGRAM,
    min_frac: float = _CHAR_DOMINANT_REPEAT_MIN_FRAC,
    min_len: int = _CHAR_DOMINANT_REPEAT_MIN_LEN,
) -> bool:
    n_chars = len(text)
    if n_chars < min_len:
        return False
    for n in range(1, max_n + 1):
        if n_chars < n * min_repeats:
            continue
        counts: dict[str, int] = {}
        for i in range(n_chars - n + 1):
            gram = text[i:i + n]
            counts[gram] = counts.get(gram, 0) + 1
        best_count = max(counts.values())
        if best_count >= min_repeats and (best_count * n) / n_chars >= min_frac:
            return True
    return False


def is_degenerate(text: str) -> bool:
    stripped = (text or "").strip()
    if not stripped:
        return True
    if not re.search(r"[a-zA-Z0-9]", stripped):
        return True
    if _is_repeated_ngram(stripped.split()):
        return True
    if _has_dominant_repeated_char_unit(stripped):
        return True
    answer_field = _extract_answer_field(stripped).strip()
    if answer_field:
        if _has_dominant_repeated_unit(answer_field.split()):
            return True
        if _has_dominant_repeated_char_unit(answer_field):
            return True
    return False


def _normalize_aliases(aliases: list[str] | None) -> list[str]:
    raw = aliases or []
    return [_normalize_answer_text(str(a)) for a in raw if str(a).strip()]


def _normalize_answer_text(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", str(text or "").lower()))


def _is_stated_confidence_refusal(text: str) -> bool:
    return any(pattern.search(text or "") for pattern in _STATED_CONFIDENCE_REFUSAL_PATTERNS)


def _is_correct(answer_text: str, aliases_norm: list[str]) -> bool:
    answer_norm = f" {_normalize_answer_text(answer_text)} "
    return any(f" {alias} " in answer_norm for alias in aliases_norm)


def grade_one(answer_text: str, aliases: list[str] | None) -> dict:
    aliases_norm = _normalize_aliases(aliases)
    degenerate = is_degenerate(answer_text)
    refused = (not degenerate) and bool(_is_stated_confidence_refusal(answer_text))
    answered = (not degenerate) and (not refused)
    correct: Optional[bool] = None
    if answered and aliases_norm:
        correct = bool(_is_correct(answer_text, aliases_norm))
    well_formed_correct = bool(answered and (not degenerate) and correct is True)
    return {
        "degenerate": degenerate, "refused": refused, "answered": answered,
        "correct": correct, "well_formed_correct": well_formed_correct,
    }


def _self_check() -> None:
    spam_repeated_word = '{"answer": "' + "True " * 90
    clean_answer = (
        '{"answer": "Yes, the cultural significance of the dhoti varies across '
        'regions in India.", "response_confidence": 0.95}'
    )
    clean_refusal = '{"answer": "I don\'t know the answer", "response_confidence": 0.95}'

    assert is_degenerate(spam_repeated_word)
    assert not is_degenerate(clean_answer)
    assert not is_degenerate(clean_refusal)
    assert grade_one(clean_refusal, ["Paris"])["refused"] is True
    assert grade_one(clean_answer, ["dhoti"])["well_formed_correct"] is True
    assert grade_one(clean_answer, ["unrelated_word"])["well_formed_correct"] is False
    print("grader self-check: PASS")


if __name__ == "__main__":
    _self_check()
