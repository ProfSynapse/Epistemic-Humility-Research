#!/usr/bin/env python3
"""H3 lab-notebook diagnostic -- text-persisting single-seed Arm S re-run.

Registered in NOTEBOOK.md's 2026-07-13 entry "Lab-notebook: boolean-level
failure decomposition + text-persistence gap (lead)": the resolved H3 run
persisted only final booleans (clean_tighten, well_formed_correct) per
sample and discarded gen_lib.grade_clean_tighten's own sub-grade dict
(well_formed, single_answer_key, trailing_clean, semantic_refuse,
degenerate, terminated_naturally, answer_value) and all generation text.
That leaves the 75.9% NEITHER bucket of fired confab samples (neither
clean_tighten nor answered-with-gold-alias) undecomposed, and leaves the
batched termination rule (gen_lib._first_eos_position) unaudited -- the
notebook names both as open questions this diagnostic exists to close.

This script re-runs Arm S (sampled decode, N=8 identical-prompt copies per
row in one batched model.generate() call) for ONE seed only (20260710, the
first registered seed) over the SAME 443 held-out rows as the resolved run,
using the SAME pinned generation/grading stack (gen_lib, grader, model_lib,
and pipeline.py's own row-materialization / gate-decision / derive_seed
helpers, imported unchanged -- none of those pinned modules are copied or
edited here). Per sample it persists: row_key, role, fire, readback, the
generation text (both the truncated text gen_lib itself would grade, and
the untruncated raw decode), n_new_tokens (raw tensor width before any
truncation), the raw termination inputs (the eos position exactly as
gen_lib._first_eos_position reports it, not just the derived boolean), the
FULL gen_lib.grade_clean_tighten sub-grade dict, and the full
grader.grade_one dict.

Why a local wrapper instead of calling gen_lib.run_batched_sampled_pass
directly: that pinned function's return contract is (texts,
terminated_flags, readback) -- it computes the eos position internally via
gen_lib._first_eos_position and discards the integer position (and the
untruncated text) once it has derived the boolean. This diagnostic needs
that discarded integer (to bound how often the ambiguous "eos only at the
last column" boundary case -- called not-terminated, conservatively -- is
occurring, per the notebook's open question). run_arm_s_sampled_diagnostic
below therefore makes the IDENTICAL model.generate() call (same
controller.begin_pass/reset sequence, same eos_token_id set, same
generation_kwargs) and calls gen_lib's own public
resolve_batched_eos_ids/_first_eos_position helpers directly rather than
reimplementing their logic -- gen_lib.py itself is not copied or modified,
only its call arguments and helper functions are reused, exactly as
gen_lib.run_batched_sampled_pass itself does internally. The terminated
boolean derived here uses gen_lib's own criterion (eos_pos is not None and
eos_pos < n - 1) so grading is byte-identical to what the resolved
pipeline.py would have graded for the same draw.

Reuses (imported unchanged, none copied/modified):
  - pipeline.load_rows_and_gate_decisions, pipeline.derive_seed,
    pipeline.N_SAMPLES, pipeline.SAMPLED_GENERATION_KWARGS,
    pipeline.REGISTERED_SEEDS, pipeline.DOSE_TARGET,
    pipeline.BUILD_MANIFEST_PATH, pipeline.C_HAT_PATH
  - gen_lib.resolve_batched_eos_ids, gen_lib._first_eos_position,
    gen_lib.grade_clean_tighten, gen_lib.MAX_NEW_CAP
  - grader.grade_one
  - model_lib.load_model, model_lib.setup_hook_from_path

Row text (question/aliases) and all generations stay under this
experiment's gitignored analysis/ (the repo-wide `analysis/` rule in
.gitignore already covers the new output file; no question, alias, or
generation text is committed).

This is lab-notebook tier per the task instructions: no gates computed, no
AMENDMENT.md/experiment.yaml edits, pinned modules untouched.

--mode smoke: tiny end-to-end GPU pass (a handful of rows), proving wiring.
--mode full: the real 443-row x N=8 sweep for one seed. Gated behind
--i-know-this-runs-on-gpu (the lead launches this after the card frees; the
harness build task that authored this script does not run it).
"""

from __future__ import annotations

import argparse
import gc
import json
import sys
from pathlib import Path
from typing import Optional

import torch

HERE = Path(__file__).resolve().parent
ANALYSIS = HERE / "analysis"
TUNER_DIR = HERE.parent.parent / "synaptic-tuner"

for p in (str(TUNER_DIR), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

import gen_lib as gl  # noqa: E402
import grader  # noqa: E402
import model_lib as ml  # noqa: E402
import pipeline as pl  # noqa: E402
from MechInterp.intervention import get_decoder_layer  # noqa: E402
from shared.utilities.run_log import RunLog  # noqa: E402

DIAGNOSTIC_SEED = 20260710  # first registered seed (NOTEBOOK.md successor entry), K=1 here
N_SAMPLES = pl.N_SAMPLES  # 8, unchanged
MAX_NEW = gl.MAX_NEW_CAP  # 200, unchanged
GENERATION_KWARGS = dict(pl.SAMPLED_GENERATION_KWARGS)  # do_sample/temperature/top_p, unchanged


def _out_path(seed: int) -> Path:
    return ANALYSIS / f"diagnostic_arm_s_text_seed{seed}.jsonl"


def run_batched_sampled_pass_diagnostic(
    model, controller, tokenizer, enc: dict, mode: str, strength,
    generation_kwargs: dict, max_new: int = MAX_NEW,
) -> tuple[list[dict], Optional[dict]]:
    """Identical call sequence to gen_lib.run_batched_sampled_pass (see
    module docstring for why this is a diagnostic mirror, not a copy of that
    pinned function): same controller.begin_pass/reset bracketing, same
    resolve_batched_eos_ids() eos set, same model.generate() kwargs. Unlike
    the pinned function, returns one dict PER SAMPLE with every intermediate
    value the pinned function computes and discards, plus the readback dict.
    """
    controller.hook.last_readback = None
    controller.begin_pass(mode, strength, attention_mask=enc["attention_mask"])
    eos_ids = set(gl.resolve_batched_eos_ids(tokenizer))
    with torch.no_grad():
        out = model.generate(
            **enc,
            max_new_tokens=max_new,
            min_new_tokens=1,
            num_beams=1,
            eos_token_id=sorted(eos_ids),
            pad_token_id=tokenizer.pad_token_id,
            **generation_kwargs,
        )
    readback = controller.hook.last_readback if mode != "off" else None
    controller.reset()

    prompt_len = enc["input_ids"].shape[1]
    samples: list[dict] = []
    for i in range(out.shape[0]):
        new_tokens = out[i, prompt_len:]
        n_new_tokens_raw = int(new_tokens.shape[0])
        eos_pos = gl._first_eos_position(new_tokens, eos_ids)
        terminated_naturally = eos_pos is not None and eos_pos < n_new_tokens_raw - 1
        content = new_tokens[: eos_pos + 1] if terminated_naturally else new_tokens
        text = tokenizer.decode(content, skip_special_tokens=True)
        raw_text_untruncated = tokenizer.decode(new_tokens, skip_special_tokens=True)
        samples.append({
            "sample_idx": i,
            "text": text,
            "raw_text_untruncated": raw_text_untruncated,
            "n_new_tokens_raw": n_new_tokens_raw,
            "eos_pos": eos_pos,
            "terminated_naturally": bool(terminated_naturally),
        })
    return samples, readback


def grade_samples(samples: list[dict], aliases: list[str] | None) -> list[dict]:
    """Attaches the FULL gen_lib.grade_clean_tighten sub-grade dict and the
    full grader.grade_one dict to each sample, using the text gen_lib itself
    would grade (the truncated `text` field) -- so `clean_tighten` here
    reproduces exactly what the resolved run_batch_sampled_for_row would
    have scored for the same draw."""
    out = []
    for s in samples:
        ct = gl.grade_clean_tighten(s["text"], s["terminated_naturally"])
        wfc = grader.grade_one(s["text"], aliases)
        rec = dict(s)
        rec["grade_clean_tighten"] = ct
        rec["grade_one"] = wfc
        out.append(rec)
    return out


def run_row_diagnostic(
    model, controller, tokenizer, dev, row: dict, seed: int, strength_c_hat: float,
) -> dict:
    fire = bool(row["fire"])
    prompt = ml.render(row)
    enc1 = tokenizer(prompt, return_tensors="pt")
    input_ids = enc1["input_ids"].repeat(N_SAMPLES, 1).to(dev)
    attention_mask = enc1["attention_mask"].repeat(N_SAMPLES, 1).to(dev)
    enc_batch = {"input_ids": input_ids, "attention_mask": attention_mask}

    mode = "gen_stream" if fire else "off"
    strength = strength_c_hat if fire else 0.0
    derived_seed = pl.derive_seed(seed, row["row_key"])
    torch.manual_seed(derived_seed)

    samples, readback = run_batched_sampled_pass_diagnostic(
        model, controller, tokenizer, enc_batch, mode, strength,
        generation_kwargs=GENERATION_KWARGS, max_new=MAX_NEW,
    )
    graded_samples = grade_samples(samples, row.get("aliases"))

    return {
        "row_key": row["row_key"], "role": row["role"], "fire": fire,
        "seed": seed, "derived_seed": derived_seed,
        "readback": readback,
        "samples": graded_samples,
    }


# ---------------------------------------------------------------------------
# GPU smoke.
# ---------------------------------------------------------------------------

def run_smoke(n_rows: int, dose_target: float) -> dict:
    rows = pl.load_rows_and_gate_decisions()
    confab_rows = [r for r in rows if r["role"] == "confab"][: n_rows // 2]
    known_rows = [r for r in rows if r["role"] == "known_correct_answered"][: n_rows - len(confab_rows)]
    sample_rows = confab_rows + known_rows

    build_manifest = json.loads(pl.BUILD_MANIFEST_PATH.read_text())
    sigma_c = build_manifest["sigma_c"]
    strength_c_hat = dose_target / sigma_c

    hook, controller, layer_idx, _sigma, _rec = ml.setup_hook_from_path(pl.C_HAT_PATH)
    model, tokenizer = ml.load_model()
    dev = next(model.parameters()).device
    layer_module = get_decoder_layer(model, layer_idx)
    h_ctrl = layer_module.register_forward_hook(controller)

    recs = []
    try:
        for r in sample_rows:
            recs.append(run_row_diagnostic(model, controller, tokenizer, dev, r, DIAGNOSTIC_SEED, strength_c_hat))
    finally:
        h_ctrl.remove()
        del model
        gc.collect()
        torch.cuda.empty_cache()

    summary = {
        "seed": DIAGNOSTIC_SEED, "dose_target": dose_target, "sigma_c": sigma_c,
        "n_rows": len(sample_rows),
        "fires": sum(1 for r in recs if r["fire"]),
        "sample_counts": [len(r["samples"]) for r in recs],
    }
    ANALYSIS.mkdir(parents=True, exist_ok=True)
    (ANALYSIS / "diagnostic_smoke_summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print("\n=== DIAGNOSTIC SMOKE SUMMARY ===")
    print(json.dumps(summary, indent=2, default=str))
    return summary


# ---------------------------------------------------------------------------
# Full single-seed sweep (lab-notebook diagnostic; not a gated run).
# ---------------------------------------------------------------------------

def run_full(dose_target: float, seed: int) -> dict:
    rows = pl.load_rows_and_gate_decisions()
    confab_rows = [r for r in rows if r["role"] == "confab"]
    known_rows = [r for r in rows if r["role"] == "known_correct_answered"]
    assert len(confab_rows) == 185, f"expected 185 confab held-out rows, got {len(confab_rows)}"
    assert len(known_rows) == 258, f"expected 258 known_correct_answered held-out rows, got {len(known_rows)}"

    build_manifest = json.loads(pl.BUILD_MANIFEST_PATH.read_text())
    sigma_c = build_manifest["sigma_c"]
    strength_c_hat = dose_target / sigma_c

    ANALYSIS.mkdir(parents=True, exist_ok=True)
    hook, controller, layer_idx, _sigma, _rec = ml.setup_hook_from_path(pl.C_HAT_PATH)
    model, tokenizer = ml.load_model()
    dev = next(model.parameters()).device
    layer_module = get_decoder_layer(model, layer_idx)
    h_ctrl = layer_module.register_forward_hook(controller)

    out_path = _out_path(seed)
    run_log = RunLog(
        out_path,
        {"seed": seed, "dose_target": dose_target, "n_samples": N_SAMPLES, "gen_kwargs": GENERATION_KWARGS},
        key_field="row_key",
    )
    try:
        pending = list(run_log.iter_pending(rows, key_fn=lambda r: r["row_key"]))
        print(f"[diagnostic] seed={seed}: {len(rows)} rows, {len(rows) - len(pending)} done, {len(pending)} pending")
        for i, r in enumerate(pending):
            rec = run_row_diagnostic(model, controller, tokenizer, dev, r, seed, strength_c_hat)
            run_log.record(r["row_key"], rec)
            if (i + 1) % 25 == 0 or (i + 1) == len(pending):
                print(f"[diagnostic] {i + 1}/{len(pending)}", flush=True)
        run_log.finalize({"n_rows": len(rows), "seed": seed})
    finally:
        run_log.close()
        h_ctrl.remove()
        del model
        gc.collect()
        torch.cuda.empty_cache()

    print(f"[diagnostic] wrote {out_path}")
    return {"n_rows": len(rows), "seed": seed, "out_path": str(out_path)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["smoke", "full"], required=True)
    ap.add_argument("--n-rows", type=int, default=8, help="smoke mode only")
    ap.add_argument("--dose", type=float, default=pl.DOSE_TARGET)
    ap.add_argument("--seed", type=int, default=DIAGNOSTIC_SEED,
                     help="single seed only (this is a lab-notebook diagnostic, "
                          "not the K=5 registered sweep)")
    ap.add_argument("--i-know-this-runs-on-gpu", action="store_true")
    args = ap.parse_args()

    if not args.i_know_this_runs_on_gpu:
        print(
            "[diagnostic] refusing to run without --i-know-this-runs-on-gpu "
            "(this loads the model and generates on GPU; the lead launches "
            "this, not the harness-build task).",
            file=sys.stderr,
        )
        return 2

    if args.mode == "smoke":
        run_smoke(args.n_rows, args.dose)
    else:
        run_full(args.dose, args.seed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
