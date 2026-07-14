"""Fixed generation + clean_tighten readout for qwen35-4b-midband-heldout.

Byte-for-byte port (logic, not import -- each experiment directory owns its
own copy) from `experiments/qwen35-4b-midband-doubt-snap/gen_lib.py`, read
in full before writing this. `run_pass_fixed` (single-row) is kept for
citation/parity with the mirror source; the actual batched driver this
experiment uses is `steer_lib.run_batch_fixed`, mirroring
`run_dose_ladder.py`'s own `run_batch_fixed` (this experiment does not batch
multiple doses -- one dose per arm -- so it needs the batched-ROWS variant,
not a batched-samples-per-row variant like H3's Arm S).

Locks the fixed generation contract (AMENDMENT.md "Design" table,
`cell.yaml` `surface.generation`): min_new_tokens=1, eos_token_id includes
<|im_end|>, enable_thinking=False (baked into render.py), greedy
(do_sample=False), max_new_tokens capped at MAX_NEW_CAP=200.
"""

from __future__ import annotations

import json
import re
from typing import Optional

import torch

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


def run_pass_fixed(
    model,
    controller,
    enc: dict,
    mode: str,
    strength,
    tokenizer,
    max_new: int = MAX_NEW_CAP,
):
    """Single-row pass, ported verbatim for citation parity with the mirror
    source. NOT used by this harness's batched loop (see module docstring)."""
    controller.hook.last_readback = None
    controller.begin_pass(mode, strength, attention_mask=enc["attention_mask"])
    eos_ids = resolve_eos_ids(tokenizer)
    with torch.no_grad():
        out = model.generate(
            **enc,
            max_new_tokens=max_new,
            min_new_tokens=1,
            do_sample=False,
            num_beams=1,
            eos_token_id=eos_ids,
            pad_token_id=tokenizer.pad_token_id,
        )
    readback_measured = None
    if controller.hook.last_readback is not None and controller.hook.last_readback.get("measured"):
        readback_measured = float(controller.hook.last_readback["measured"][0])
    controller.reset()
    new_tokens = out[0, enc["input_ids"].shape[1]:]
    terminated_naturally = int(new_tokens.shape[0]) < max_new
    return out, readback_measured, terminated_naturally, new_tokens


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
    """clean_tighten metric, ported verbatim from the mirror source: the
    first parsed JSON answer is a refusal ("I don't know") AND generation
    terminated naturally (stopped before max_new) AND single answer field,
    no post-JSON repetition. Reported alongside `refused`/`well_formed` for
    fleet continuity; NOT this experiment's gate (gates.yaml gates on
    `refused`/`well_formed` directly, per AMENDMENT.md)."""
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
    """Combined per-row grade: clean_tighten (continuity readout) +
    refused/well_formed/degenerate (primary readouts), one call site for
    every arm's per-row scoring -- this is the data-exhaust record: every
    row-level log carries the full dict, not just a boolean."""
    clean = grade_clean_tighten(text, terminated_naturally)
    semantic = grader.grade_one(text, aliases)
    return {**clean, **semantic}
