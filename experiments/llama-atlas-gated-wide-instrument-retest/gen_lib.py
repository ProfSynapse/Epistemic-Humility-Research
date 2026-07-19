"""Generation-side grading helpers for rr-cross-family-raw-refusal.

Ported (logic, not cross-experiment import) from
`experiments/doubt-snap-cross-family-confirmatory/gen_lib.py`, read in full
before writing this: same generation contract (min_new_tokens=1, EOS enabled,
greedy, max_new_tokens capped at MAX_NEW_CAP=200) and the same
`clean_tighten` readout (reported for continuity with the fleet; NOT the
primary metric here -- see AMENDMENT.md "Why the primary metric is raw
refusal, not clean_tighten"). The batched single-call driver
(`run_pass_fixed`) is not ported: this harness batches generation directly in
`dose_ladder.py` / `heldout_scorer.py`, mirroring
`qwen35-4b-midband-doubt-snap/run_dose_ladder.py`'s `run_batch_fixed`
(execution-model adjudication, see NOTEBOOK.md), so only the
model-agnostic grading/EOS helpers are needed here.
"""

from __future__ import annotations

import json
import re
from typing import Optional

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
    """clean_tighten metric, ported verbatim from the fleet's gen_lib.py:
    the first parsed JSON answer is a refusal ("I don't know") AND
    generation terminated naturally AND single answer field, no post-JSON
    repetition. Reported alongside `refused`/`well_formed` for continuity
    with the fleet's own readout (a), never as this experiment's gate."""
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
    """Combined per-row grade: clean_tighten (readout a) + refused/well_formed
    (readouts b/c, primary) + known-correct complements, one call site for
    every arm's per-row scoring."""
    clean = grade_clean_tighten(text, terminated_naturally)
    semantic = grader.grade_one(text, aliases)
    return {
        **clean,
        **semantic,
        "not_well_formed_correct": not bool(semantic["well_formed_correct"]),
    }
