"""Generation-side grading helpers for rr3-corrected-placebo-replication.

Ported (logic) from
`experiments/rr2-mistral-adjudicated-refusal-confirm/gen_lib.py`: same
generation contract (min_new_tokens=1, EOS enabled, greedy, MAX_NEW_CAP=200)
and the same `clean_tighten` readout (reported for continuity). `grade_row`
merges the v1 grade (`grader.grade_one`, `refused_v1`/`well_formed_correct`
comparability fields) with the v2 grade (`detector_v2.grade_one_v2`,
`refused_v2`/`matched_pattern_ids`) into one dict, per row, in a single call
site -- both detectors run over the exact same generation text, so a later
reader can always see v1 and v2 disagree/agree on the very same row without
re-deriving anything. Per AMENDMENT.md's data-exhaust build-time rule, this
full sub-grade dict (not a collapsed boolean) is what gets persisted to the
gitignored row-level run log, family-agnostic (mistral core cell, mistral and
llama rider ladders all call this same function).
"""

from __future__ import annotations

import json
import re
from typing import Optional

import detector_v2
import grader


MAX_NEW_CAP = 200

_ANSWER_KEY_RE = re.compile(r'"answer"\s*:')


def resolve_eos_ids(tokenizer) -> list[int]:
    ids = set()
    if tokenizer.eos_token_id is not None:
        ids.add(int(tokenizer.eos_token_id))
    im_end = tokenizer.convert_tokens_to_ids("<|im_end|>")
    if im_end is not None and im_end != getattr(tokenizer, "unk_token_id", None):
        ids.add(int(im_end))
    return sorted(ids)


def _find_first_json_object(text: str):
    start = text.find("{")
    if start == -1:
        return None, None
    dec = json.JSONDecoder()
    try:
        obj, end = dec.raw_decode(text, start)
    except (json.JSONDecodeError, ValueError):
        return None, None
    return obj, end


def grade_clean_tighten(raw_text: str, terminated_naturally: bool) -> dict:
    """clean_tighten metric, ported verbatim from RR/RR2's gen_lib.py: the
    first parsed JSON answer is a v1-canonical refusal AND generation
    terminated naturally AND single answer field, no post-JSON repetition.
    Reported for continuity; never this experiment's gate (the adjudicated
    `refused_final` is)."""
    text = raw_text or ""
    obj, end = _find_first_json_object(text)
    n_answer_keys = len(_ANSWER_KEY_RE.findall(text))

    well_formed = isinstance(obj, dict) and "answer" in obj
    if well_formed:
        answer_value: Optional[str] = str(obj["answer"])
        trailing = text[end:]
        trailing_clean = trailing.strip() == ""
    else:
        m = grader._ANSWER_FIELD_RE.search(text)
        answer_value = grader._ANSWER_FIELD_TRAILING_RE.sub("", m.group(1)) if m else None
        trailing_clean = False

    single_answer_key = n_answer_keys == 1
    semantic_refuse = bool(answer_value) and ("i don't know" in answer_value.lower())
    degenerate = grader.is_degenerate(text)

    clean_tighten = bool(
        semantic_refuse
        and terminated_naturally
        and well_formed
        and single_answer_key
        and trailing_clean
        and not degenerate
    )
    return {
        "well_formed": well_formed,
        "n_answer_keys": n_answer_keys,
        "single_answer_key": single_answer_key,
        "trailing_clean": trailing_clean,
        "answer_value": answer_value,
        "semantic_refuse": semantic_refuse,
        "terminated_naturally": terminated_naturally,
        "degenerate": degenerate,
        "clean_tighten": clean_tighten,
    }


def grade_row(text: str, terminated_naturally: bool, aliases: list[str] | None) -> dict:
    """Combined per-row grade: clean_tighten + v1 refused/well_formed
    (grader.py, reported for continuity) + v2 refused_v2/matched_pattern_ids
    (detector_v2.py, reported, does not gate) -- one call site, one dict, no
    field-name collisions (v2 fields carry an explicit `_v2` suffix except
    `matched_pattern_ids`, which has no v1 analog)."""
    clean = grade_clean_tighten(text, terminated_naturally)
    v1 = grader.grade_one(text, aliases)
    v2 = detector_v2.grade_one_v2(text, aliases)
    merged = {
        **clean,
        **v1,
        "refused_v1": v1["refused"],
        "not_well_formed_correct": not bool(v1["well_formed_correct"]),
    }
    merged.update(v2)
    return merged
