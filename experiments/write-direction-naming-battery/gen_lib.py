"""Generation-side grading helpers for write-direction-naming-battery.

Byte-identical LOGIC to `margin-mapping/harness/gen_lib.py` (read in full
before writing this): `grade_row` merges the clean_tighten sub-grade
(well_formed via the plain JSON-parse rule, semantic_refuse via the narrow
literal-"i don't know" check) with the detector_v2 sub-grade (refused_v2 via
the wide diverse-idiom detector, correct_v2 via alias match). This is the
exact schema the amendment's disclosures D-1 through D-4 were computed
against, and it is what cell.yaml's `execution.graders` (`grader:grade` +
`detector_v2:grade_one_v2`) names collectively.

form_taxonomy.py (task #3's build, F1-F5 output-form classes) is NOT wired
into this harness: per the lead's phase-2 instructions it exists only in the
main checkout (untracked, not on this run branch) and is applied post-hoc,
offline, against the generation text this harness's runlog would otherwise
carry -- this cell generates with grader:grade + detector_v2:grade_one_v2
only.
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
    """One dict per row (data-exhaust rule): clean_tighten sub-grade +
    detector_v2 sub-grade. NOTE: this dict still carries `answer_value`
    (from clean_tighten) -- the caller (steer_lib.run_rows) is responsible
    for applying cell.yaml `execution.redact_fields` (question, aliases,
    answer_text, answer_value) before persisting to the runlog; grading
    itself needs the full text and is computed before redaction."""
    clean = grade_clean_tighten(text, terminated_naturally)
    v2 = detector_v2.grade_one_v2(text, aliases)
    return {
        "terminated_naturally": terminated_naturally,
        **clean,
        **v2,
    }
