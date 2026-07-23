"""Generation-side grading helpers for margin-separation-fine-ladder (M1b).

Byte-identical LOGIC to `margin-mapping/gen_lib.py` (read in full before
writing this; only this docstring differs): `final_rate_rule` is
`detector_v2_refused OR adjudicated_abstention` (cell.yaml
`readout.refused_final_rule`), well_formed is the plain JSON-parse rule
(unchanged from M1, "not adjudicated"), and `grade_row` merges the same two
sub-grades (clean_tighten + detector_v2) the deliverables are computed from.
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
    """`well_formed` (plain JSON-parse check -- this is the field M1b's
    tipping_dose/collapse_dose deliverables are computed from, cell.yaml
    `deliverables.collapse_dose`) plus the rest of the `clean_tighten`
    sub-grade, ported verbatim (logic) from M1's gen_lib.py."""
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
    """clean_tighten sub-grade (well_formed, JSON-parse fields) + detector_v2
    sub-grade (refused_v2, well_formed_correct_v2, degenerate,
    matched_pattern_ids) -- one dict per row (data-exhaust rule). `refused_v2`
    is the `detector_v2_refused` half of M1b's `refused_final_rule`
    (cell.yaml: `detector_v2_refused OR adjudicated_abstention`; the
    adjudicated half applies only to the calibration slice, scored
    separately)."""
    clean = grade_clean_tighten(text, terminated_naturally)
    v2 = detector_v2.grade_one_v2(text, aliases)
    return {
        "terminated_naturally": terminated_naturally,
        **clean,
        **v2,
    }
