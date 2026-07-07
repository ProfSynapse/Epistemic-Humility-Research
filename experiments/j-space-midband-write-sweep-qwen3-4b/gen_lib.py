"""Fixed generation + honest clean_tighten metric for the J-space layer sweep.

Ported from the resolved doubt-gated-caution-tighten predecessor. This
instrument locks the fixed generation contract: min_new_tokens=1, eos_token_id includes
<|im_end|>, enable_thinking=False (baked into the render function), greedy
(do_sample=False), max_new_tokens capped at MAX_NEW_CAP=200.

Only the anchor_onward write scope is implemented because the signed design
holds the predecessor mechanism fixed while sweeping layer site.
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
    post-JSON repetition."""
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
