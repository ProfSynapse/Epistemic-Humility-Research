"""Detector v2 (automatic screen) for rr2-mistral-adjudicated-refusal-confirm.

Per cell.yaml `detector_v2` / AMENDMENT.md "Design" item 1: a deterministic,
frozen pattern list -- RR's three canonical patterns (reused verbatim via
`grader.py`, imported directly rather than re-transcribed so the two can
never drift) plus a diverse abstention vocabulary pinned in
`detector_v2_patterns.yaml`. Matching is a lowercase substring check after
apostrophe normalization (curly quotes folded to straight), applied
IDENTICALLY to both populations -- there is no population-conditional branch
anywhere in this module, which is what makes the symmetry argument in the
AMENDMENT ("the lane cannot widen the benefit vocabulary without widening the
cost vocabulary") hold at the code level, not just by intent.

detector_v2 is reported alongside the locked v1 rates for every gate
(cell.yaml `detector_v2.gates: false`); it never gates on its own. The
PRIMARY instrument is the blinded adjudication lane
(`build_adjudication_pool.py` / `apply_adjudication.py`), which starts from
exactly the rows this module marks non-refused.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional

import yaml

import grader

HERE = Path(__file__).resolve().parent
DEFAULT_PATTERNS_PATH = HERE / "detector_v2_patterns.yaml"

_CURLY_APOSTROPHE_RE = re.compile("[‘’ʼ]")

_loaded_cache: dict[str, dict[str, Any]] = {}


def _normalize(text: Optional[str]) -> str:
    """Lowercase + fold curly/typographic apostrophes to a straight `'` so a
    single stem like "i don't have" matches both apostrophe styles a model
    might emit, without needing a regex character class at every call site."""
    return _CURLY_APOSTROPHE_RE.sub("'", (text or "")).lower()


def load_patterns(path: Optional[Path] = None) -> dict[str, Any]:
    p = path or DEFAULT_PATTERNS_PATH
    key = str(p)
    if key not in _loaded_cache:
        with p.open(encoding="utf-8") as fh:
            _loaded_cache[key] = yaml.safe_load(fh)
    return _loaded_cache[key]


def _idiom_entries(config: dict[str, Any]) -> list[dict[str, Any]]:
    return config.get("diverse_idioms", [])


def is_refused_v2(text: str, config: Optional[dict[str, Any]] = None) -> bool:
    """canonical (RR's locked 3-phrase detector, via
    grader._is_stated_confidence_refusal) OR any diverse idiom stem. Always a
    superset of the v1 canonical-only match, never a subset, so
    refused_v2 >= refused_v1 pointwise on every row."""
    if grader._is_stated_confidence_refusal(text):
        return True
    cfg = config if config is not None else load_patterns()
    norm = _normalize(text)
    return any(entry["pattern"] in norm for entry in _idiom_entries(cfg))


def matched_pattern_ids(text: str, config: Optional[dict[str, Any]] = None) -> list[str]:
    """Every pattern id that fired on this text (canonical id(s) plus any
    diverse-idiom ids). Used for the row-level data-exhaust sub-grade dict so
    a later reviewer can see WHICH idiom(s) drove a refused_v2=True verdict
    without needing to re-run this module."""
    cfg = config if config is not None else load_patterns()
    hits: list[str] = []
    if grader._is_stated_confidence_refusal(text):
        # Determine which of the three canonical patterns actually matched,
        # for diagnostic granularity (grader's own patterns list, in order).
        for pattern, entry in zip(grader._STATED_CONFIDENCE_REFUSAL_PATTERNS, cfg.get("canonical", [])):
            if pattern.search(text or ""):
                hits.append(entry["id"])
    norm = _normalize(text)
    for entry in _idiom_entries(cfg):
        if entry["pattern"] in norm:
            hits.append(entry["id"])
    return hits


def grade_one_v2(answer_text: str, aliases: list[str] | None, config: Optional[dict[str, Any]] = None) -> dict:
    """Same output shape/semantics as `grader.grade_one`, but the refusal
    surface is `is_refused_v2` instead of the locked 3-phrase detector.
    `degenerate` and correctness matching are UNCHANGED (ported from
    `grader.py`, not re-derived), per AMENDMENT.md: "Well-formedness is
    graded by the unchanged JSON parse rule and is not adjudicated." Only the
    refusal-phrase surface differs between v1 and v2."""
    cfg = config if config is not None else load_patterns()
    aliases_norm = grader._normalize_aliases(aliases)
    degenerate = grader.is_degenerate(answer_text)
    refused_v2 = (not degenerate) and is_refused_v2(answer_text, cfg)
    answered_v2 = (not degenerate) and (not refused_v2)
    correct_v2: Optional[bool] = None
    if answered_v2 and aliases_norm:
        correct_v2 = bool(grader._is_correct(answer_text, aliases_norm))
    well_formed_correct_v2 = bool(answered_v2 and (not degenerate) and correct_v2 is True)
    return {
        "degenerate": degenerate,
        "refused_v2": refused_v2,
        "answered_v2": answered_v2,
        "correct_v2": correct_v2,
        "well_formed_correct_v2": well_formed_correct_v2,
        "not_well_formed_correct_v2": not well_formed_correct_v2,
        "matched_pattern_ids": matched_pattern_ids(answer_text, cfg),
    }


def _self_check() -> None:
    cfg = load_patterns()
    assert is_refused_v2("I don't know the answer.", cfg) is True
    assert is_refused_v2("It is impossible to predict the outcome.", cfg) is True
    assert is_refused_v2("Paris is the capital of France.", cfg) is False
    print("detector_v2 self-check: PASS")


if __name__ == "__main__":
    _self_check()
