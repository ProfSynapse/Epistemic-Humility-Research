"""Batched generation + activation-write driver for
rr3-corrected-placebo-replication.

Ported (logic) from
`experiments/rr2-mistral-adjudicated-refusal-confirm/steer_lib.py`: same
direct InterventionHook/GenerationInterventionController/RunLog driving (not
the declarative `mechinterp steer` YAML-recipe path), same batched
fixed-generation contract. `load_model` sets THIS experiment's namespaced
render env vars (RR3_RENDER_MODEL/RR3_RENDER_REVISION, matching this
experiment's own `render.py`) rather than RR2's RR2_RENDER_MODEL/
RR2_RENDER_REVISION or RR's RR_RENDER_MODEL/RR_RENDER_REVISION -- carrying
forward RR's own late-discovered fix (RENDER-ENV-VAR FIX: `load_model` must
set these BEFORE loading, at the one call site every caller already shares,
so the two can never drift apart or be forgotten) rather than reintroducing
the gap it closed.

Family-agnostic: `load_model(model_name, revision)` takes whichever
family/revision the caller wants (mistral core cell or llama rider cell), one
family loaded per process. Both substrates fit bf16 in 24GB (AMENDMENT.md
"Execution") and are plain-attention AutoModelForCausalLM, so this module
does not impose a CUDA_LAUNCH_BLOCKING requirement.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
TUNER_DIR = REPO_ROOT / "synaptic-tuner"
for _p in (str(TUNER_DIR), str(HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import gen_lib  # noqa: E402
import render as render_mod  # noqa: E402


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_model(model_name: str, revision: str):
    """Loads the generation model/tokenizer AND sets this experiment's
    render-side env vars (RR3_RENDER_MODEL/RR3_RENDER_REVISION) to the SAME
    model/revision, in the same place, so the two can never drift apart or
    be forgotten by a caller -- carrying forward RR/RR2's fix for the exact
    same gap (RENDER-ENV-VAR FIX)."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    os.environ["RR3_RENDER_MODEL"] = model_name
    os.environ["RR3_RENDER_REVISION"] = revision or ""

    tokenizer = AutoTokenizer.from_pretrained(model_name, revision=revision, trust_remote_code=True)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    # Left padding keeps every row's real last prompt token in the same
    # trailing column so decode steps stay synchronized across the batch
    # (see run_batch_fixed).
    tokenizer.padding_side = "left"
    model = AutoModelForCausalLM.from_pretrained(
        model_name, revision=revision, dtype=torch.bfloat16, device_map="cuda", trust_remote_code=True,
    )
    model.eval()
    device = next(model.parameters()).device
    return model, tokenizer, device


def build_hook_and_controller(direction_vec, sigma: float):
    """direction_vec: torch.Tensor, unit-norm. Returns (hook, controller)
    driving InterventionHook(law="erase_write", position="anchor_onward")
    under GenerationInterventionController's "gen_stream" mode."""
    from MechInterp.intervention import InterventionHook, GenerationInterventionController

    hook = InterventionHook(
        law="erase_write", direction=direction_vec, sigma=sigma,
        position="anchor_onward", measure_readback=True,
    )
    return hook, GenerationInterventionController(hook)


def run_batch_fixed(
    model, tokenizer, device, controller, prompts: list[str],
    mode: str, gain_per_row, max_new: int,
) -> list[dict[str, Any]]:
    """Batched analog of a single-row fixed-generation pass. `controller`
    None or `mode="off"` is a true no-write pass. `gain_per_row` is a scalar
    or length-batch sequence broadcast to InterventionHook's per-row
    `strength`; a row with gain 0.0 is a no-op by construction
    (`hooks.py:_resolve_active`), so callers select which rows are active by
    setting their gain to 0.0 rather than needing `force_active`.

    The termination rule below is eos-anywhere (first EOS-family token
    anywhere in the tail, not merely a final-position check) -- the same rule
    RR/RR2's own harness used; this is NOT reintroduced here."""
    import torch

    enc = tokenizer(prompts, return_tensors="pt", padding=True).to(device)
    eos_ids = gen_lib.resolve_eos_ids(tokenizer)
    if controller is not None and mode != "off":
        controller.hook.last_readback = None
        controller.begin_pass(mode, gain_per_row, attention_mask=enc["attention_mask"])
    with torch.no_grad():
        out = model.generate(
            **enc, max_new_tokens=max_new, min_new_tokens=1, do_sample=False,
            num_beams=1, eos_token_id=eos_ids, pad_token_id=tokenizer.pad_token_id,
        )
    readback = None
    if controller is not None and mode != "off":
        rb = controller.hook.last_readback
        if rb is not None and rb.get("measured"):
            readback = list(rb["measured"])
        controller.reset()

    prompt_len = int(enc["input_ids"].shape[1])
    results = []
    for b in range(out.shape[0]):
        tail = out[b, prompt_len:]
        tail_ids = tail.tolist()
        eos_pos = next((i for i, t in enumerate(tail_ids) if int(t) in eos_ids), None)
        if eos_pos is not None:
            n_new = eos_pos + 1
            terminated_naturally = True
        else:
            n_new = len(tail_ids)
            terminated_naturally = n_new < max_new
        text = tokenizer.decode(tail[:n_new], skip_special_tokens=True)
        results.append({
            "text": text, "n_new_tokens": n_new, "terminated_naturally": terminated_naturally,
            "readback_measured": (readback[b] if readback is not None and b < len(readback) else None),
        })
    return results


def render_prompt(row: dict[str, Any]) -> str:
    return render_mod.render(row)


def grade_row(text: str, terminated_naturally: bool, aliases) -> dict[str, Any]:
    return gen_lib.grade_row(text, terminated_naturally, aliases)


def run_rows(
    model, tokenizer, device, controller, mode: str,
    rows: list[dict[str, Any]], gains: dict[str, float],
    max_new: int, batch_size: int, run_log, log_key_fn,
) -> None:
    """Generic batched runner: `gains` maps row_key -> per-row gain. Callers
    partition rows into an active-only batch call (gain != 0 for every row)
    plus a separate baseline lookup for inactive rows, mirroring RR/RR2's own
    `known_all_covered` pattern -- this function assumes every row passed IN
    is active for THIS call.

    Per the data-exhaust build-time rule (AMENDMENT.md), the FULL sub-grade
    dict from `grade_row` (v1 AND v2 fields, matched_pattern_ids) is persisted
    per row, not a collapsed boolean -- this is what makes the row-level run
    log usable as the source for `build_adjudication_pool.py`'s detector-v2
    screen without any re-generation. `log_key_fn` lets callers key the run
    log by anything derivable from the row (row_key alone for single-pass
    arms; row_key+seed for the K-seed random_direction arm; row_key+dose for
    the rider dose ladders), so the same run log directory can hold every
    generation pass this experiment needs without key collisions."""
    done = run_log.done_keys()
    pending = [r for r in rows if log_key_fn(r) not in done]
    t0 = time.time()
    for i in range(0, len(pending), batch_size):
        batch = pending[i:i + batch_size]
        prompts = [render_prompt(r) for r in batch]
        gain_vec = [gains[r["row_key"]] for r in batch]
        gen = run_batch_fixed(model, tokenizer, device, controller, prompts, mode, gain_vec, max_new)
        for row, res in zip(batch, gen):
            grade = grade_row(res["text"], res["terminated_naturally"], row.get("aliases"))
            run_log.record(log_key_fn(row), {
                "row_key": row["row_key"], "role": row["role"], "split": row.get("split"),
                "source": row.get("source"), "category_canon": row.get("category_canon"),
                "gain": gains[row["row_key"]],
                "n_new_tokens": res["n_new_tokens"], "terminated_naturally": res["terminated_naturally"],
                "readback_measured": res["readback_measured"], "answer_text": res["text"], **grade,
            })
        print(f"[steer_lib] {min(i + batch_size, len(pending))}/{len(pending)} ({time.time() - t0:.0f}s)", flush=True)
