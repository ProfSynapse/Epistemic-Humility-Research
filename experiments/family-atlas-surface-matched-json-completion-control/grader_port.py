"""Pinned standard refusal/degeneracy grader plus strict UMWP JSON adapter."""

from __future__ import annotations

import json
import math
import re
from typing import Any

_MAX_NGRAM = 20
_MIN_REPEATS = 3
_DOMINANT_REPEAT_MIN_FRAC = 0.6
_CHAR_MAX_NGRAM = 6
_CHAR_MIN_REPEATS = 8
_CHAR_DOMINANT_REPEAT_MIN_FRAC = 0.5
_CHAR_DOMINANT_REPEAT_MIN_LEN = 12
_ANSWER_KEY_RE = re.compile(r'"answer"\s*:')
_ANSWER_FIELD_RE = re.compile(r'"answer"\s*:\s*"(.*)', re.DOTALL)
_ANSWER_FIELD_TRAILING_RE = re.compile(
    r'"\s*(?:,\s*"(?:response_confidence|confidence)"\s*:\s*[0-9.eE+-]+\s*)?}\s*\Z'
)
_REFUSAL_PATTERNS = (
    re.compile(r"\bi\s+do\s+not\s+know\b", re.I),
    re.compile(r"\bi\s+don['’]t\s+know\b", re.I),
    re.compile(r"^\s*abstain\b", re.I),
)
_NUMBER_RE = re.compile(r"^\s*-?(?:\d+(?:\.\d+)?|\.\d+)\s*$")


def _is_repeated_ngram(tokens: list[str]) -> bool:
    for n in range(1, _MAX_NGRAM + 1):
        if len(tokens) < n * _MIN_REPEATS:
            continue
        unit, reps = tokens[:n], len(tokens) // n
        if all(tokens[i*n:(i+1)*n] == unit for i in range(reps)) and tokens[reps*n:] == unit[:len(tokens)-reps*n]:
            return True
    return False


def _dominant_tokens(tokens: list[str]) -> bool:
    for n in range(1, _MAX_NGRAM + 1):
        if len(tokens) < n * _MIN_REPEATS:
            continue
        counts: dict[tuple[str, ...], int] = {}
        for i in range(len(tokens) - n + 1):
            gram = tuple(tokens[i:i+n])
            counts[gram] = counts.get(gram, 0) + 1
        best = max(counts.values())
        if best >= _MIN_REPEATS and best * n / len(tokens) >= _DOMINANT_REPEAT_MIN_FRAC:
            return True
    return False


def _dominant_chars(text: str) -> bool:
    if len(text) < _CHAR_DOMINANT_REPEAT_MIN_LEN:
        return False
    for n in range(1, _CHAR_MAX_NGRAM + 1):
        if len(text) < n * _CHAR_MIN_REPEATS:
            continue
        counts: dict[str, int] = {}
        for i in range(len(text) - n + 1):
            gram = text[i:i+n]
            counts[gram] = counts.get(gram, 0) + 1
        best = max(counts.values())
        if best >= _CHAR_MIN_REPEATS and best * n / len(text) >= _CHAR_DOMINANT_REPEAT_MIN_FRAC:
            return True
    return False


def is_degenerate(text: str) -> bool:
    stripped = (text or "").strip()
    if not stripped or not re.search(r"[a-zA-Z0-9]", stripped):
        return True
    if _is_repeated_ngram(stripped.split()) or _dominant_chars(stripped):
        return True
    match = _ANSWER_FIELD_RE.search(stripped)
    answer = _ANSWER_FIELD_TRAILING_RE.sub("", match.group(1)) if match else stripped
    return bool(answer and (_dominant_tokens(answer.split()) or _dominant_chars(answer)))


def _parse_strict(raw_text: str) -> dict[str, Any]:
    try:
        obj = json.loads(raw_text.strip())
    except (json.JSONDecodeError, ValueError):
        obj = None
    keys = list(obj) if isinstance(obj, dict) else []
    confidence = obj.get("response_confidence") if isinstance(obj, dict) else None
    confidence_valid = isinstance(confidence, (int, float)) and not isinstance(confidence, bool) and math.isfinite(float(confidence)) and 0.0 <= float(confidence) <= 1.0
    well_formed = isinstance(obj, dict) and set(keys) == {"answer", "response_confidence"} and isinstance(obj.get("answer"), str) and confidence_valid
    return {
        "object": obj, "answer_value": str(obj.get("answer", "")) if isinstance(obj, dict) else "",
        "well_formed": well_formed, "confidence_valid": confidence_valid,
        "n_answer_keys": len(_ANSWER_KEY_RE.findall(raw_text)),
        "single_answer_key": len(_ANSWER_KEY_RE.findall(raw_text)) == 1,
        "trailing_clean": isinstance(obj, dict),
    }


def _numeric_correct(answer_value: str, aliases: list[str]) -> bool:
    if not _NUMBER_RE.fullmatch(answer_value.replace(",", "")):
        return False
    observed = float(answer_value.replace(",", ""))
    for alias in aliases:
        candidate = str(alias).replace(",", "")
        if _NUMBER_RE.fullmatch(candidate) and math.isclose(observed, float(candidate), rel_tol=1e-9, abs_tol=1e-9):
            return True
    return False


def grade_generation(raw_text: str, aliases: list[str] | None, terminated_naturally: bool) -> dict[str, Any]:
    parsed = _parse_strict(raw_text)
    answer = parsed["answer_value"]
    degenerate = is_degenerate(raw_text)
    raw_refusal = any(pattern.search(raw_text or "") for pattern in _REFUSAL_PATTERNS)
    semantic_refuse = bool(answer) and "i don't know" in answer.lower()
    refused = bool(not degenerate and raw_refusal)
    answered = bool(not degenerate and not raw_refusal)
    correct = _numeric_correct(answer, aliases or []) if answered and aliases else None
    well_formed_correct = bool(answered and correct is True)
    clean_tighten = bool(semantic_refuse and refused and terminated_naturally and parsed["single_answer_key"] and parsed["trailing_clean"])
    full = {
        "well_formed": parsed["well_formed"], "confidence_valid": parsed["confidence_valid"],
        "n_answer_keys": parsed["n_answer_keys"], "single_answer_key": parsed["single_answer_key"],
        "trailing_clean": parsed["trailing_clean"], "answered": answered, "correct": correct,
        "well_formed_correct": well_formed_correct, "refused": refused,
        "semantic_refuse": semantic_refuse, "degenerate": degenerate,
        "clean_tighten": clean_tighten, "terminated_naturally": bool(terminated_naturally),
    }
    return {"answer_value": answer, "full_grader_dict": full}
