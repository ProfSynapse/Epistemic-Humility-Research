"""Batched generation + activation-write driver for qwen35-4b-midband-heldout.

Direct InterventionHook/GenerationInterventionController/RunLog driving,
mirroring `qwen35-4b-midband-doubt-snap/run_dose_ladder.py`'s
`run_batch_fixed` (read in full before writing this) and
`rr-cross-family-raw-refusal/steer_lib.py`'s `load_model`
render-env-setting convention (read in full before writing this): every
call site that loads the generation model also sets render.py's env vars in
the SAME place, so the two can never drift apart or be forgotten by a
caller -- this closed the exact render-env gap the RR build shipped (its
CPU smoke never exercised the render module; this experiment's own smoke
does, see test_qw35_heldout_smoke.py).

Single dose per arm (this cell is a confirmation of one frozen operating
point, not a dose ladder), so `run_batch_fixed` takes a scalar `strength`
for the whole batch, not a per-row gain vector -- simpler than
run_dose_ladder.py's own signature needs to be, since every row in one
batched call here always shares the same arm and the same dose.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any, Optional

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
TUNER_DIR = REPO_ROOT / "synaptic-tuner"
for _p in (str(TUNER_DIR), str(HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import gen_lib  # noqa: E402
import render as render_mod  # noqa: E402

MODEL_NAME = "Qwen/Qwen3.5-4B"
MODEL_REVISION = "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a"
HIDDEN_DIM = 2560


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


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")


def load_model(model_name: str = MODEL_NAME, revision: str = MODEL_REVISION):
    """Loads the generation model/tokenizer under base conda
    (AMENDMENT.md/cell.yaml `surface.loader_note`: the project's pinned
    unsloth_env transformers 4.57.1 does not recognize model_type qwen3_5;
    this script must be invoked with
    /home/profsynapse/miniconda3/bin/python3), AND sets render.py's
    QW35H_RENDER_MODEL/QW35H_RENDER_REVISION to the SAME model/revision, in
    the same place, so the two can never drift apart or be forgotten by a
    caller -- every pipeline.py call site already calls this before any row
    is rendered. Left padding keeps every row's real last prompt token in
    the same trailing column so decode steps stay synchronized across the
    batch (see run_batch_fixed)."""
    import os

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    os.environ["QW35H_RENDER_MODEL"] = model_name
    os.environ["QW35H_RENDER_REVISION"] = revision or ""

    tokenizer = AutoTokenizer.from_pretrained(model_name, revision=revision, trust_remote_code=True)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
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
    under GenerationInterventionController's "gen_stream" mode -- identical
    construction to the ladder's run_dose_ladder.py and H3's model_lib."""
    from MechInterp.intervention import GenerationInterventionController, InterventionHook

    hook = InterventionHook(
        law="erase_write", direction=direction_vec, sigma=sigma,
        position="anchor_onward", measure_readback=True,
    )
    return hook, GenerationInterventionController(hook)


def render_prompt(row: dict[str, Any]) -> str:
    return render_mod.render(row)


def run_batch_fixed(
    model, tokenizer, device, controller, prompts: list[str],
    mode: str, strength, max_new: int,
) -> tuple[list[dict[str, Any]], Optional[dict[str, Any]]]:
    """Batched analog of gen_lib.run_pass_fixed. `controller=None` is a true
    no-write pass (no hook registered at all -- used for baseline); a
    non-None controller is armed via begin_pass exactly as the single-row
    ported function does. `strength` is a SCALAR (one dose, one arm, one
    call): every row in `prompts` shares the same arm and dose, so callers
    partition rows into per-arm active batches rather than passing a
    per-row gain vector (ported structure from run_dose_ladder.py's own
    `run_batch_fixed`).

    Left-padding (see load_model) keeps every row's own prompt end at the
    same trailing column; each row's own EOS position within its own tail
    is located explicitly (HF pads shorter rows with pad_token_id after
    their own EOS while longer rows keep decoding).

    Returns `(results, raw_readback)`: `results` is the per-row list as
    before; `raw_readback` is the hook's full per-batch readback dict
    (commanded/measured/offtarget_abs_max, InterventionHook._readback's own
    schema) or None when `controller is None`, exposed so callers can run it
    through the project's own G0 smoke-tolerance check
    (`MechInterp.cell.evaluate_smoke_readback`) rather than re-deriving a
    tolerance here.
    """
    import torch

    enc = tokenizer(prompts, return_tensors="pt", padding=True).to(device)
    eos_ids = gen_lib.resolve_eos_ids(tokenizer)
    if controller is not None:
        controller.hook.last_readback = None
        controller.begin_pass(mode, strength, attention_mask=enc["attention_mask"])
    with torch.no_grad():
        out = model.generate(
            **enc, max_new_tokens=max_new, min_new_tokens=1, do_sample=False,
            num_beams=1, eos_token_id=eos_ids, pad_token_id=tokenizer.pad_token_id,
        )
    readback = None
    raw_readback = None
    if controller is not None:
        rb = controller.hook.last_readback
        raw_readback = rb
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
            "text": text,
            "n_new_tokens": n_new,
            "terminated_naturally": terminated_naturally,
            "readback_measured": (readback[b] if readback is not None and b < len(readback) else None),
        })
    return results, raw_readback


def run_rows(
    model, tokenizer, device, controller, mode: str,
    rows: list[dict[str, Any]], strength, max_new: int, batch_size: int,
    run_log,
    readback_collector: Optional[list[dict[str, Any]]] = None,
) -> None:
    """Generic batched runner for ONE arm's rows (every row passed in
    shares `mode`/`strength`): renders, generates, grades (full sub-grade
    dict via gen_lib.grade_row, never booleans-only -- the data-exhaust
    principle), and RunLog-records each row keyed by row_key. Resumable:
    already-recorded row_keys are skipped.

    `readback_collector`, when given a list, gets each batch's raw readback
    dict appended (only for active/controller passes) -- pipeline.py's
    smoke mode uses this to run the G0 `readback_within_tolerance` check
    over every batch of the gated/random_direction arms, per gates.yaml."""
    done = run_log.done_keys()
    pending = [r for r in rows if r["row_key"] not in done]
    t0 = time.time()
    for i in range(0, len(pending), batch_size):
        batch = pending[i:i + batch_size]
        prompts = [render_prompt(r) for r in batch]
        gen, raw_rb = run_batch_fixed(model, tokenizer, device, controller, prompts, mode, strength, max_new)
        if readback_collector is not None and raw_rb is not None:
            readback_collector.append(raw_rb)
        for row, res in zip(batch, gen):
            grade = gen_lib.grade_row(res["text"], res["terminated_naturally"], row.get("aliases"))
            run_log.record(row["row_key"], {
                "row_key": row["row_key"], "role": row["role"], "split": row.get("split"),
                "category_canon": row.get("category_canon"),
                "n_new_tokens": res["n_new_tokens"], "terminated_naturally": res["terminated_naturally"],
                "readback_measured": res["readback_measured"], "answer_text": res["text"], **grade,
            })
        print(f"[steer_lib] {min(i + batch_size, len(pending))}/{len(pending)} ({time.time() - t0:.0f}s)", flush=True)
