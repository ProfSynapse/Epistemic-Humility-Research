"""Batched generation + activation-write driver for gate-contribution-factorial.

Direct InterventionHook/GenerationInterventionController/RunLog driving
(cell.yaml `execution.model_driving`; NOT the declarative `mechinterp steer`
YAML-recipe path), ported (logic) from
`qwen35-4b-midband-heldout/steer_lib.py` and
`placebo-seed-distribution-census/steer_lib.py` (both read in full before
writing this). Family-agnostic: `load_model(model_name, revision)` takes
whichever of the two factorial families the caller wants, one family loaded
per process, and sets THIS experiment's own namespaced render env vars
(GATEFACT_RENDER_MODEL/GATEFACT_RENDER_REVISION) at the same call site every
caller shares, carrying forward the RR/RR2/RR3/midband-heldout render-env fix.

Single dose per pass (every row in one `run_rows` call shares the same arm
and the same dose -- matching midband-heldout's own convention, which is
also what the permuted-gate construction this experiment reuses assumes:
`gate_construction.draw_permuted_gate_indices`).
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Callable, Optional

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
TUNER_DIR = REPO_ROOT / "synaptic-tuner"
for _p in (str(TUNER_DIR), str(HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import gen_lib  # noqa: E402
import render as render_mod  # noqa: E402


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not Path(path).exists():
        return []
    rows: list[dict[str, Any]] = []
    with Path(path).open(encoding="utf-8") as fh:
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


def load_model(model_name: str, revision: str):
    """Loads the generation model/tokenizer AND sets GATEFACT_RENDER_MODEL/
    GATEFACT_RENDER_REVISION to the SAME model/revision, in the same place,
    so the two can never drift apart. Qwen3.5 requires transformers >= 5.x
    (run under /home/profsynapse/miniconda3/bin/python3, base conda, per
    midband-heldout's own documented deviation-with-cause; cell.yaml
    `execution.qwen_loader_note`)."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    os.environ["GATEFACT_RENDER_MODEL"] = model_name
    os.environ["GATEFACT_RENDER_REVISION"] = revision or ""

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
    """direction_vec: torch.Tensor, unit-norm. InterventionHook(law=
    "erase_write", position="anchor_onward") under
    GenerationInterventionController's "gen_stream" mode (cell.yaml
    `write.law`/`write.position`)."""
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
    """Batched analog of a single-row fixed-generation pass. `controller`
    None (or `mode="off"`) is a true no-write pass. `strength` is a SCALAR:
    every row in `prompts` shares the same arm and dose. Termination rule is
    eos-anywhere, the RR/RR2/RR3/midband-heldout convention."""
    import torch

    enc = tokenizer(prompts, return_tensors="pt", padding=True).to(device)
    eos_ids = gen_lib.resolve_eos_ids(tokenizer)
    if controller is not None and mode != "off":
        controller.hook.last_readback = None
        controller.begin_pass(mode, strength, attention_mask=enc["attention_mask"])
    with torch.no_grad():
        out = model.generate(
            **enc, max_new_tokens=max_new, min_new_tokens=1, do_sample=False,
            num_beams=1, eos_token_id=eos_ids, pad_token_id=tokenizer.pad_token_id,
        )
    readback = None
    raw_readback = None
    if controller is not None and mode != "off":
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
            "text": text, "n_new_tokens": n_new, "terminated_naturally": terminated_naturally,
            "readback_measured": (readback[b] if readback is not None and b < len(readback) else None),
        })
    return results, raw_readback


def run_rows(
    model, tokenizer, device, controller, mode: str,
    rows: list[dict[str, Any]], strength, max_new: int, batch_size: int,
    run_log, readback_collector: Optional[list[dict[str, Any]]] = None,
    after_batch: Optional[Callable[[list[dict[str, Any]]], None]] = None,
) -> None:
    """Generic batched runner for ONE arm's rows (every row passed in shares
    `mode`/`strength`): renders, generates, grades (full sub-grade dict via
    gen_lib.grade_row, data-exhaust rule), RunLog-records each row keyed by
    row_key. Resumable: already-recorded row_keys are skipped.

    `after_batch`, if given, is called once per batch with the list of
    per-row record dicts just written (including `readback_measured`),
    immediately after they are durably recorded. Callers use this for a
    live SC1 assertion on the first batch of a dosed write, so a mis-dosed
    arm (e.g. a sigma/strength wiring defect) hard-aborts before the rest of
    the arm's rows are spent -- the callback is expected to raise
    SystemExit on failure; `run_rows` itself does not interpret the result."""
    done = run_log.done_keys()
    pending = [r for r in rows if r["row_key"] not in done]
    t0 = time.time()
    for i in range(0, len(pending), batch_size):
        batch = pending[i:i + batch_size]
        prompts = [render_prompt(r) for r in batch]
        gen, raw_rb = run_batch_fixed(model, tokenizer, device, controller, prompts, mode, strength, max_new)
        if readback_collector is not None and raw_rb is not None:
            readback_collector.append(raw_rb)
        batch_records = []
        for row, res in zip(batch, gen):
            grade = gen_lib.grade_row(res["text"], res["terminated_naturally"], row.get("aliases"))
            rec = {
                "row_key": row["row_key"], "role": row.get("role"), "split": row.get("split"),
                "category_canon": row.get("category_canon"), "source": row.get("source"),
                "n_new_tokens": res["n_new_tokens"], "terminated_naturally": res["terminated_naturally"],
                "readback_measured": res["readback_measured"], "answer_text": res["text"], **grade,
            }
            run_log.record(row["row_key"], rec)
            batch_records.append(rec)
        if after_batch is not None:
            after_batch(batch_records)
        print(f"[steer_lib] {min(i + batch_size, len(pending))}/{len(pending)} ({time.time() - t0:.0f}s)", flush=True)
