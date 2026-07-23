"""Generation-side grading helpers for gate-contribution-factorial.

Ported (logic) from `placebo-seed-distribution-census/gen_lib.py`:
`final_rate_rule` is `detector_v2_refused OR adjudicated_abstention` only
(cell.yaml `wide_instrument.adjudication.final_rate_rule`), so the SCORED
final rate merges only the `detector_v2` sub-grade, not a v1 merge.

EXTENDED beyond census's version: P1's benefit condition needs a row-level
`well_formed` field (AMENDMENT.md "Well-formedness is graded by the
unchanged JSON parse rule and is not adjudicated"; gates.yaml
`p1_gate_benefit_cost.benefit: ... well_formed >= 0.80`). This is NOT
`detector_v2`'s `well_formed_correct_v2` (which requires alias-match
correctness and is structurally 0 on the confab population, which has no
aliases) -- it is the plain JSON-object-parses-with-an-"answer"-key check,
ported verbatim from `rr2-mistral-adjudicated-refusal-confirm/gen_lib.py`
`grade_clean_tighten` (same function RR3 and qwen35-4b-midband-heldout carry
forward unchanged). Census omitted this because census's own gates never
needed a well_formed floor; this experiment's P1 does, so it is restored
here rather than left out.
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
    """`well_formed` (plain JSON-parse check, P1's benefit condition) plus
    the rest of RR's `clean_tighten` sub-grade, ported verbatim from RR2's
    gen_lib.py for full continuity with the precedent's data-exhaust
    convention. `clean_tighten` itself is reported only, never a gate here."""
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
        "degenerate": degenerate,
        "clean_tighten": clean_tighten,
    }


def grade_row(text: str, terminated_naturally: bool, aliases: Optional[list[str]]) -> dict:
    """clean_tighten sub-grade (well_formed, JSON-parse fields, reported) +
    detector_v2 sub-grade (refused_v2, well_formed_correct_v2, degenerate,
    matched_pattern_ids) -- one dict per row (data-exhaust rule: full
    sub-grade persisted, never a collapsed boolean). `degenerate` appears in
    both sub-grades and is byte-identical between them (both call
    `grader.is_degenerate` on the same text); detector_v2's copy wins the
    key collision on merge, which is a no-op given the identical value."""
    clean = grade_clean_tighten(text, terminated_naturally)
    v2 = detector_v2.grade_one_v2(text, aliases)
    return {
        "terminated_naturally": terminated_naturally,
        **clean,
        **v2,
    }
