"""Batched generation + activation-write driver for
placebo-seed-distribution-census.

Ported (logic) from `experiments/rr3-corrected-placebo-replication/
steer_lib.py`: same direct InterventionHook/GenerationInterventionController/
RunLog driving (cell.yaml `execution.model_driving`; NOT the declarative
`mechinterp steer` YAML-recipe path), same batched fixed-generation contract
(cell.yaml `write.generation`). `load_model` sets THIS experiment's
namespaced render env vars (CENSUS_RENDER_MODEL/CENSUS_RENDER_REVISION,
matching this experiment's own `render.py`) BEFORE loading, at the one call
site every caller already shares, carrying forward RR/RR2/RR3's
RENDER-ENV-VAR FIX.

Family-agnostic: `load_model(model_name, revision)` takes whichever of the
three census families the caller wants, one family loaded per process.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

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


def load_model(model_name: str, revision: str):
    """Loads the generation model/tokenizer AND sets this experiment's
    render-side env vars (CENSUS_RENDER_MODEL/CENSUS_RENDER_REVISION) to the
    SAME model/revision, in the same place, so the two can never drift apart
    -- carrying forward RR/RR2/RR3's fix for the exact same gap."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    os.environ["CENSUS_RENDER_MODEL"] = model_name
    os.environ["CENSUS_RENDER_REVISION"] = revision or ""

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
    "erase_write", position="anchor_onward") under GenerationInterventionController's
    "gen_stream" mode (cell.yaml `write.law`/`write.position`)."""
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
    None or `mode="off"` is a true no-write pass. Termination rule is
    eos-anywhere (first EOS-family token anywhere in the tail), the same rule
    RR/RR2/RR3's own harnesses used."""
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


def run_rows(
    model, tokenizer, device, controller, mode: str,
    rows: list[dict[str, Any]], gains: dict[str, float],
    max_new: int, batch_size: int, run_log, log_key_fn,
) -> None:
    """Generic batched runner: `gains` maps row_key -> per-row gain. The FULL
    sub-grade dict (gen_lib.grade_row) is persisted per row (data-exhaust
    rule), keyed by `log_key_fn(row)` (row_key+seed for the K-seed
    random_direction arm), so one run log directory holds every generation
    pass without key collisions across seeds."""
    done = run_log.done_keys()
    pending = [r for r in rows if log_key_fn(r) not in done]
    t0 = time.time()
    for i in range(0, len(pending), batch_size):
        batch = pending[i:i + batch_size]
        prompts = [render_prompt(r) for r in batch]
        gain_vec = [gains[r["row_key"]] for r in batch]
        gen = run_batch_fixed(model, tokenizer, device, controller, prompts, mode, gain_vec, max_new)
        for row, res in zip(batch, gen):
            grade = gen_lib.grade_row(res["text"], res["terminated_naturally"], row.get("aliases"))
            run_log.record(log_key_fn(row), {
                "row_key": row["row_key"], "role": row.get("role"), "split": row.get("split"),
                "source": row.get("source"), "category_canon": row.get("category_canon"),
                "gain": gains[row["row_key"]],
                "n_new_tokens": res["n_new_tokens"], "terminated_naturally": res["terminated_naturally"],
                "readback_measured": res["readback_measured"], "answer_text": res["text"], **grade,
            })
        print(f"[steer_lib] {min(i + batch_size, len(pending))}/{len(pending)} ({time.time() - t0:.0f}s)", flush=True)
