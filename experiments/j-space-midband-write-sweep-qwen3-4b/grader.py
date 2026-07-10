"""Grader for the J-space mid-band write sweep.

Ported from the resolved doubt-gated-caution-tighten predecessor.
`is_degenerate` is the coherence-floor check (empty / no-alnum / repeated word
n-gram / repeated character n-gram), and `grade_one` adds
`well_formed_correct` for the known-correct cost-control population.

Fields returned by `grade_one`:
  degenerate          bool   coherence-floor flag
  refused             bool   (not degenerate) and is_stated_confidence_refusal
  answered            bool   (not degenerate) and (not refused)
  correct             bool | None   scorers.is_correct against aliases, only
                       when answered and aliases are non-empty; else None
  well_formed_correct bool   answered and (not degenerate) and correct is True
                       -- the known-correct false-refusal complement.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Optional

EVAL_DIR = Path("/home/profsynapse/code/Epistemic-Humility-Research/experiment/phase1/eval")
if str(EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(EVAL_DIR))
import scorers  # noqa: E402  (eval/scorers.py -- Cheng-validated port, dependency-free)


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
    return [scorers.normalize(str(a)) for a in raw if str(a).strip()]


def grade_one(answer_text: str, aliases: list[str] | None) -> dict:
    aliases_norm = _normalize_aliases(aliases)
    degenerate = is_degenerate(answer_text)
    refused = (not degenerate) and bool(scorers.is_stated_confidence_refusal(answer_text))
    answered = (not degenerate) and (not refused)
    correct: Optional[bool] = None
    if answered and aliases_norm:
        correct = bool(scorers.is_correct(answer_text, aliases_norm))
    well_formed_correct = bool(answered and (not degenerate) and correct is True)
    return {
        "degenerate": degenerate, "refused": refused, "answered": answered,
        "correct": correct, "well_formed_correct": well_formed_correct,
    }


def _self_check() -> None:
    spam_repeated_word = '{"answer": "' + "True " * 90
    spam_repeated_phrase = (
        '{\n  "answer": "I don\'t know the answer"I don\'t know the answer"'
        'I don\'t know the answer"I donI don\'t know the answer"I don\'t know '
        'the answer"I don\'t know the answer"I don\'t know the answer"I don\'t '
        'know the answer"I don\'t know the answer"I don\'t know the answer"I '
        'don\'t know the answer"I don\'t know the answer"I don\'t know'
    )
    clean_answer = (
        '{"answer": "Yes, the cultural significance of the dhoti varies across '
        'regions in India.", "response_confidence": 0.95}'
    )
    clean_refusal = '{"answer": "I don\'t know the answer", "response_confidence": 0.95}'

    assert is_degenerate(spam_repeated_word)
    assert is_degenerate(spam_repeated_phrase)
    assert not is_degenerate(clean_answer)
    assert not is_degenerate(clean_refusal)
    print("grader self-check: PASS (spam flagged degenerate, clean text passes)")


if __name__ == "__main__":
    _self_check()
