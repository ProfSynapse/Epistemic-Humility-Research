"""Detector v2 (wide, diverse-idiom automatic screen) for
write-direction-naming-battery.

Byte-for-byte port (logic, not import) from
`experiments/margin-mapping/harness/detector_v2.py`, read in full before
writing this -- the exact lineage cell.yaml `execution.graders` names
(`detector_v2:grade_one_v2`) and the amendment's disclosure D-4 computes
against ("wide detector (`refused_v2`, detector_v2 diverse idioms)").
`is_refused_v2` is a strict superset of the narrow `grader._is_stated_
confidence_refusal` match (canonical 3-phrase OR any diverse idiom stem).
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
    if grader._is_stated_confidence_refusal(text):
        return True
    cfg = config if config is not None else load_patterns()
    norm = _normalize(text)
    return any(entry["pattern"] in norm for entry in _idiom_entries(cfg))


def matched_pattern_ids(text: str, config: Optional[dict[str, Any]] = None) -> list[str]:
    cfg = config if config is not None else load_patterns()
    hits: list[str] = []
    if grader._is_stated_confidence_refusal(text):
        for pattern, entry in zip(grader._STATED_CONFIDENCE_REFUSAL_PATTERNS, cfg.get("canonical", [])):
            if pattern.search(text or ""):
                hits.append(entry["id"])
    norm = _normalize(text)
    for entry in _idiom_entries(cfg):
        if entry["pattern"] in norm:
            hits.append(entry["id"])
    return hits


def grade_one_v2(answer_text: str, aliases: list[str] | None, config: Optional[dict[str, Any]] = None) -> dict:
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
