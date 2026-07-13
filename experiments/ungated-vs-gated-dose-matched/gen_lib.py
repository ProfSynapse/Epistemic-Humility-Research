"""Fixed generation + honest clean_tighten metric, reused for H4
ungated-vs-gated-dose-matched.

Copied verbatim (byte-identical, not imported cross-experiment per this
repo's own convention) from
`experiments/doubt-gated-caution-tighten/gen_lib.py` -- AMENDMENT.md's Design
requires reusing that cell's grading unchanged. Do not edit the logic here
without also updating the resolved cell's copy; a divergence would break the
H4-G0 reproduction gate's premise that both cells score identically.

That module's own docstring (preserved below) documents its further
provenance: ported (logic, not import) from the sibling two-signal
experiment's `analysis/tighten_gen_lib.py` (worktree
`/home/profsynapse/code/ehr-worktrees/two-signal`, branch
`exp/two-signal-caution-regulation-instruct`, commit 8f277410, read in full
before writing this). That module fixed a forced-continuation generation bug
confirmed in two prior scripts (`min_new_tokens == max_new_tokens`, which
forces the model to keep emitting tokens after a clean answer and defeats
early stopping on EOS). This instrument LOCKS the fixed generation contract
(AMENDMENT.md "GENERATION"): min_new_tokens=1, eos_token_id includes
<|im_end|>, enable_thinking=False (baked into the render function), greedy
(do_sample=False), max_new_tokens capped at MAX_NEW_CAP=200.

Only the anchor_onward write scope is implemented (LOCKED design: "Scope =
anchor_onward ... prompt-only/decay are much weaker" per the sibling
diagnostic's step2 dose x scope sweep) -- the sibling's prompt_only/decay6
scope machinery is intentionally NOT ported here, since this instrument does
not use them.
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
    """mode: "off" (no write) | "gen_stream" (anchor_onward: edit every decode
    step). Returns (out, readback_measured, terminated_naturally, new_tokens).
    min_new_tokens is 1 (not max_new), so nothing forces the model to keep
    going -- terminated_naturally is True iff the model stopped on its own
    strictly before the max_new_tokens cap."""
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
    """clean_tighten metric, LOCKED (AMENDMENT.md "Metric"): the first parsed
    JSON answer is a refusal ("I don't know") AND generation terminated
    naturally (stopped before max_new) AND single answer field, no
    post-JSON repetition. Ported verbatim from the sibling two-signal
    diagnostic's own tighten_gen_lib.grade_clean_tighten."""
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
