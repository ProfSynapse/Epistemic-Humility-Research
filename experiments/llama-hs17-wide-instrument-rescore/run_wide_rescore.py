#!/usr/bin/env python3
"""Generation driver for the SIGNED, LOCKED amendment
`llama-hs17-wide-instrument-rescore`.

Regeneration cell (AMENDMENT.md "Motivation"): the resolved
`llama-hs17-direction-specificity` cell's own run logs persisted grades and
flags only -- no generation text (a build defect recorded in that cell's own
NOTEBOOK.md 2026-08-26). The wide instrument grades TEXT, so this driver
regenerates the identical 17-arm set (same frozen site/dose/directions/gate/
row pools, fresh decode seed) with a harness that persists `out_text` per
row, fail-closed.

REUSE, NOT REINVENTION. This module imports
`llama-hs17-direction-specificity/run_specificity.py` (the resolved narrow
cell's own harness, "narrow" below) and calls its functions directly:
`verify_frozen_reuse`, `ensure_parent_local_artifacts`, `load_row_pools`,
`compute_gate_rows`, `random_unit_direction`, `build_arm_specs`,
`load_family_frozen_constants`, `grade_population`,
`min_n_for_wilson_upper_below`. Importing `run_specificity` also re-triggers
its own KNOWLEDGE_PROBE_DIR/backends.py fail-closed existence check and its
own sys.path wiring for the shared parent modules (`family_config`,
`gen_lib`, `model_lib`, `pipeline` -- all from `j-space-cross-family-layer-
contrast`), so this driver never re-derives any of that.

THE ONE NEW THING this driver adds is `run_one_row_with_text`: a copy of
`pipeline.run_one_row`'s control flow (narrow.pl.run_one_row, source read in
full) that ALSO returns `out_text`/`baseline_text`, because narrow's own
`run_one_row` computes `out_text` internally but never puts it in the
returned record (that omission is exactly the build defect this cell exists
to fix). Every model/generation call inside it
(`narrow.ml.render`, `narrow.gl.run_pass_fixed`, `narrow.gl.grade_clean_tighten`,
`narrow.pl.grader.grade_one`) is the SAME pinned function narrow's own
`run_one_row` calls -- nothing here re-implements generation, scoring, or the
KU gate.

RUN-LOG FAIL-CLOSED CONTRACT (AMENDMENT.md "Harness requirement", WR-G0):
every record must carry non-empty `out_text`. `experiments/common/
runlog_contract.py` does not exist in this repo (checked). Instead, tuner
main (synaptic-tuner commit 6b01834b, `RunLog: optional required_fields
contract enforced at record()`, checked into this worktree's submodule
WORKING TREE -- see this build's report) gives RunLog itself a
`required_fields` constructor kwarg that raises `RunLogError` at `record()`
time for any missing/empty-string field. This driver opens every RunLog with
`required_fields=("out_text",)`, which is the native equivalent of the
`runlog_contract.py` fallback the amendment asks for -- implemented via the
tuner primitive rather than a bespoke wrapper, per the "reuse existing
project machinery" rule.

PUBLIC REPO CONTAINMENT: row-level records (including `out_text`,
`answer_value`) are written ONLY under the gitignored `analysis/` tree. This
script writes NOTHING under `analysis-committed/` except aggregate counts/
provenance (no text) -- `score_wide_rescore.py` computes and commits the
scored rates.

GPU GATE: real (non --smoke) runs load the model and call model.generate().
Do not invoke without explicit GPU-GO authorization from the lead.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent  # experiments/llama-hs17-wide-instrument-rescore
REPO_ROOT = HERE.parents[1]
NARROW_DIR = REPO_ROOT / "experiments" / "llama-hs17-direction-specificity"
sys.path.insert(0, str(NARROW_DIR))

import run_specificity as narrow  # noqa: E402  (the resolved narrow cell's own harness)

FAMILY = narrow.FAMILY
HS_INDEX = narrow.HS_INDEX
LAYER_NAME = narrow.LAYER_NAME
HIDDEN_DIM = narrow.HIDDEN_DIM
SEEDS = narrow.SEEDS

CELL_YAML = HERE / "cell.yaml"
GATES_YAML = HERE / "gates.yaml"

ANALYSIS = HERE / "analysis" / FAMILY               # gitignored raw/checkpoint scratch (HOLDS TEXT)
ANALYSIS_COMMITTED = HERE / "analysis-committed" / FAMILY  # committable, counts/rates/provenance only


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str))


# --------------------------------------------------------------------------
# WR-G0 dosed-readback tolerance: formula reused verbatim from pipeline.py's
# own run_layer() ("within = abs(rb - dose_target) <= 0.05 * dose_target +
# 0.5"), named here so both the real run and the CPU smoke can exercise the
# identical arithmetic.
# --------------------------------------------------------------------------

def readback_within_tolerance(readback: float, dose_target: float) -> bool:
    return abs(readback - dose_target) <= 0.05 * dose_target + 0.5


# --------------------------------------------------------------------------
# THE ONE NEW THING: a text-persisting copy of narrow.pl.run_one_row's
# control flow. See module docstring -- every call inside is the SAME
# pinned function narrow's own run_one_row calls; only the returned dict
# gains `out_text`/`baseline_text` (the fields the resolved cell's harness
# silently dropped).
# --------------------------------------------------------------------------

def run_one_row_with_text(model, controller, tokenizer, dev, eos_ids: list[int],
                           row: dict, strength_if_dosed: float) -> dict:
    pl, gl = narrow.pl, narrow.pl.gl
    prompt = narrow.ml.render(FAMILY, tokenizer, row)
    enc = tokenizer(prompt, return_tensors="pt").to(dev)

    base_out, _rb, base_terminated, base_new = gl.run_pass_fixed(
        model, controller, enc, "off", 0.0, tokenizer, eos_ids, max_new=pl.MAX_NEW
    )
    base_text = tokenizer.decode(base_new, skip_special_tokens=True)

    if row["fire"]:
        dosed_out, readback, terminated_naturally, dosed_new = gl.run_pass_fixed(
            model, controller, enc, "gen_stream", strength_if_dosed, tokenizer, eos_ids,
            max_new=pl.MAX_NEW,
        )
        out_text = tokenizer.decode(dosed_new, skip_special_tokens=True)
        n_new = int(dosed_new.shape[0])
    else:
        out_text, readback, terminated_naturally, n_new = (
            base_text, None, base_terminated, int(base_new.shape[0])
        )

    ct = gl.grade_clean_tighten(out_text, terminated_naturally)
    old_grade = pl.grader.grade_one(out_text, row.get("aliases"))
    return {
        "row_key": row["row_key"], "role": row["role"], "category_canon": row.get("category_canon"),
        "hs_index": row["hs_index"], "fire": row["fire"], "readback_measured": readback,
        "n_new_tokens": n_new, "terminated_naturally": terminated_naturally,
        "out_text": out_text, "baseline_text": base_text,
        "clean_tighten": ct["clean_tighten"], "semantic_refuse": ct["semantic_refuse"],
        "well_formed_correct": old_grade["well_formed_correct"],
        "not_well_formed_correct": not old_grade["well_formed_correct"],
        "grade": ct, "old_grade": old_grade,
    }


# --------------------------------------------------------------------------
# Real (GPU) per-arm execution. RunLog opened with required_fields=("out_text",)
# -- fail-closed: a record missing non-empty out_text raises RunLogError
# BEFORE it is written, never silently persisted incomplete.
# --------------------------------------------------------------------------

def run_arm_real(model, tokenizer, arm_id: str, gate_rows: list[dict],
                  strength_if_dosed: float, layer_idx: int, dose_target: float,
                  force_no_fire: bool, checkpoint_dir: Path, direction_vec: np.ndarray,
                  sigma_c: float) -> tuple[list[dict], dict]:
    from MechInterp.intervention import get_decoder_layer

    RunLog, _RunLogError = narrow.ml.load_run_log_class()
    eos_ids = narrow.ml.resolve_eos_ids(FAMILY, tokenizer)
    hook, controller, _hook_layer_idx, _sigma = narrow.ml.setup_hook_from_vector(
        direction_vec, sigma_c, layer_idx
    )
    dev = next(model.parameters()).device
    layer_module = get_decoder_layer(model, layer_idx)
    h_ctrl = layer_module.register_forward_hook(controller)
    log_path = checkpoint_dir / f"{arm_id}.jsonl"
    run_log = RunLog(
        log_path,
        run_config={
            "experiment": "llama-hs17-wide-instrument-rescore", "arm": arm_id,
            "family": FAMILY, "hs_index": HS_INDEX, "dose_target": dose_target,
            "sigma_c": sigma_c, "layer_idx": layer_idx, "force_no_fire": force_no_fire,
        },
        required_fields=("out_text",),
    )
    readbacks: list[float] = []
    try:
        pending = list(run_log.iter_pending(gate_rows, key_fn=lambda r: r["row_key"]))
        t0 = time.time()
        for i, row in enumerate(pending, start=1):
            eff_row = dict(row)
            if force_no_fire:
                eff_row["fire"] = False
            rec = run_one_row_with_text(model, controller, tokenizer, dev, eos_ids, eff_row, strength_if_dosed)
            run_log.record(row["row_key"], rec)
            if rec["readback_measured"] is not None:
                readbacks.append(rec["readback_measured"])
            if i % 50 == 0 or i == len(pending):
                print(f"[run:{arm_id}] {i}/{len(pending)} pending rows done "
                      f"({time.time() - t0:.0f}s)", flush=True)
        on_disk = {json.loads(ln)["key"]: json.loads(ln) for ln in log_path.open(encoding="utf-8") if ln.strip()}
        records = [on_disk[row["row_key"]] for row in gate_rows]
    finally:
        run_log.close()
        h_ctrl.remove()
        controller.reset()
    within = [readback_within_tolerance(rb, dose_target) for rb in readbacks]
    readback_report = {
        "n_dosed": len(readbacks),
        "readback_mean": float(np.mean(readbacks)) if readbacks else None,
        "frac_within_tolerance": (sum(within) / len(within)) if within else None,
    }
    return records, readback_report


# --------------------------------------------------------------------------
# CPU smoke stub: same RunLog(required_fields=...) contract, same
# checkpointing, but out_text/grades come from a deterministic stub instead
# of model.generate(). Never touches torch/model/GPU. `stub_score_row_missing_text`
# exists ONLY so smoke_wide_rescore.py can assert the fail-closed contract
# actually fires.
# --------------------------------------------------------------------------

def stub_score_row_with_text(arm_id: str, row: dict, force_no_fire: bool, bias: float) -> dict:
    fire = False if force_no_fire else bool(row["fire"])
    h = int(hashlib.sha256(f"{arm_id}:{row['row_key']}".encode()).hexdigest(), 16)
    u = (h % 10_000) / 10_000.0
    clean_tighten = bool(u < bias)
    out_text = (
        '{"answer": "I don\'t know the answer", "response_confidence": 0.5}'
        if clean_tighten else
        '{"answer": "a stub answer value", "response_confidence": 0.5}'
    )
    return {
        "row_key": row["row_key"], "role": row["role"], "category_canon": row.get("category_canon"),
        "hs_index": row["hs_index"], "fire": fire, "readback_measured": (4.95 if fire else None),
        "n_new_tokens": 12, "terminated_naturally": True,
        "out_text": out_text, "baseline_text": out_text,
        "clean_tighten": clean_tighten, "semantic_refuse": clean_tighten,
        "well_formed_correct": not clean_tighten, "not_well_formed_correct": clean_tighten,
        "grade": {"well_formed": True, "n_answer_keys": 1, "single_answer_key": True,
                  "trailing_clean": True, "answer_value": ("I don't know the answer" if clean_tighten else "a stub answer value"),
                  "semantic_refuse": clean_tighten, "terminated_naturally": True,
                  "degenerate": False, "clean_tighten": clean_tighten},
        "old_grade": {"degenerate": False, "refused": clean_tighten, "answered": not clean_tighten,
                      "correct": None, "well_formed_correct": not clean_tighten},
        "stub": True,
    }


def run_arm_smoke(arm_id: str, gate_rows: list[dict], force_no_fire: bool, bias: float,
                   checkpoint_dir: Path) -> list[dict]:
    RunLog, _RunLogError = narrow.ml.load_run_log_class()
    log_path = checkpoint_dir / f"{arm_id}.jsonl"
    run_log = RunLog(
        log_path,
        run_config={"experiment": "llama-hs17-wide-instrument-rescore", "arm": arm_id,
                     "mode": "smoke", "force_no_fire": force_no_fire, "bias": bias},
        required_fields=("out_text",),
    )
    try:
        pending = list(run_log.iter_pending(gate_rows, key_fn=lambda r: r["row_key"]))
        for row in pending:
            rec = stub_score_row_with_text(arm_id, row, force_no_fire, bias)
            run_log.record(row["row_key"], rec)
        on_disk = {json.loads(ln)["key"]: json.loads(ln) for ln in log_path.open(encoding="utf-8") if ln.strip()}
        records = [on_disk[row["row_key"]] for row in gate_rows]
    finally:
        run_log.close()
    return records


# --------------------------------------------------------------------------
# Orchestration.
# --------------------------------------------------------------------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--smoke", action="store_true",
                     help="CPU-only: sha verification, direction generation, row-pool loading, "
                          "arm construction, and RunLog round-trip (fail-closed contract included) "
                          "on stubbed generations. Never loads a model, never touches the GPU. "
                          "For the fuller structural smoke (real run_one_row_with_text path with a "
                          "stub model/tokenizer/controller, gate arithmetic on synthetic fixtures), "
                          "use smoke_wide_rescore.py.")
    ap.add_argument("--confirm-gpu-go", action="store_true",
                     help="Required for a real (non-smoke) run. Set only after the lead has "
                          "explicitly messaged GPU GO.")
    ap.add_argument("--arms", default=None,
                     help="Comma-separated subset of arm ids to run (real mode only); default all 17.")
    args = ap.parse_args(argv)

    cell_cfg = load_yaml(CELL_YAML)
    gates_cfg = load_yaml(GATES_YAML)

    verified = narrow.verify_frozen_reuse(cell_cfg)
    narrow.ensure_parent_local_artifacts()

    rows = narrow.load_row_pools()
    rows_both = rows["confab"] + rows["known"]
    gate_rows_both = narrow.compute_gate_rows(rows_both)
    gate_rows_confab = narrow.compute_gate_rows(rows["confab"])
    n_fired_both = sum(1 for r in gate_rows_both if r["fire"])
    n_fired_confab = sum(1 for r in gate_rows_confab if r["fire"])
    print(f"[gate] fired {n_fired_both}/{len(gate_rows_both)} on the 1206-row pool "
          f"(confab+known); {n_fired_confab}/{len(gate_rows_confab)} on the 872-row confab-only pool")

    specs = narrow.build_arm_specs(gates_cfg)
    consts = narrow.load_family_frozen_constants()
    print(f"[constants] dose_target={consts['dose_target']} sigma_c={consts['sigma_c']} "
          f"strength={consts['dose_target']/consts['sigma_c']} layer_idx={consts['layer_idx']}")

    c_hat_vec = narrow.load_vector(
        narrow.PARENT_DIR / "analysis-committed" / FAMILY / "layers" / LAYER_NAME / f"c_hat_{LAYER_NAME}.json"
    )

    if args.smoke:
        checkpoint_dir = ANALYSIS / "smoke" / "runlog"
        arm_records: dict[str, list[dict]] = {}
        for spec in specs:
            rows_for_arm = gate_rows_both if spec["row_set"] == "both" else gate_rows_confab
            bias = {"baseline": 0.10, "c_hat": 0.74}.get(spec["kind"], 0.30)
            arm_records[spec["id"]] = run_arm_smoke(
                spec["id"], rows_for_arm, spec["force_no_fire"], bias, checkpoint_dir,
            )
        n_with_text = sum(1 for recs in arm_records.values() for r in recs if r.get("out_text"))
        n_total = sum(len(recs) for recs in arm_records.values())
        report = {"stub": True, "n_arms": len(arm_records), "n_rows_total": n_total,
                  "n_rows_with_nonempty_out_text": n_with_text,
                  "all_rows_have_text": n_with_text == n_total,
                  "frozen_reuse_verified": verified}
        out_path = ANALYSIS / "smoke" / "generation_smoke_report.json"
        write_json(out_path, report)
        print(json.dumps(report, indent=2))
        print(f"\n[smoke] wrote {out_path} (STUB DATA -- not a real result)")
        return 0

    # --- real GPU path ---
    if not args.confirm_gpu_go:
        print("[main] real run requires --confirm-gpu-go (set only after the lead's explicit "
              "GPU GO message)", file=sys.stderr)
        return 2

    import torch

    wanted_ids = set(args.arms.split(",")) if args.arms else None
    model, tokenizer, hidden_size, n_layers = narrow.ml.load_model_and_tokenizer(FAMILY)
    if hidden_size != HIDDEN_DIM:
        raise SystemExit(f"[main] hidden_size {hidden_size} != locked HIDDEN_DIM {HIDDEN_DIM}")
    checkpoint_dir = ANALYSIS / "runlog" / "wide_rescore"
    readback_reports: dict[str, dict] = {}
    try:
        arm_records = {}
        for spec in specs:
            if wanted_ids is not None and spec["id"] not in wanted_ids:
                continue
            rows_for_arm = gate_rows_both if spec["row_set"] == "both" else gate_rows_confab
            if spec["kind"] == "random":
                direction_vec = narrow.random_unit_direction(spec["seed"])
            else:
                direction_vec = c_hat_vec
            t0 = time.time()
            recs, readback_report = run_arm_real(
                model, tokenizer, spec["id"], rows_for_arm,
                consts["dose_target"] / consts["sigma_c"], consts["layer_idx"], consts["dose_target"],
                spec["force_no_fire"], checkpoint_dir, direction_vec, consts["sigma_c"],
            )
            arm_records[spec["id"]] = recs
            readback_reports[spec["id"]] = readback_report
            print(f"[main] arm {spec['id']} done: {len(recs)} rows in {time.time()-t0:.0f}s "
                  f"readback={readback_report}")
    finally:
        del model
        gc.collect()
        torch.cuda.empty_cache()

    counts = {arm_id: len(recs) for arm_id, recs in arm_records.items()}
    n_missing_text = {arm_id: sum(1 for r in recs if not r.get("out_text"))
                       for arm_id, recs in arm_records.items()}
    manifest = {
        "arms_run_this_invocation": sorted(arm_records), "row_counts": counts,
        "n_missing_out_text": n_missing_text,  # must be all-zero: RunLog would have already raised otherwise
        "readback_reports": readback_reports, "frozen_reuse_verified": verified,
        "dose_target": consts["dose_target"], "sigma_c": consts["sigma_c"], "layer_idx": consts["layer_idx"],
    }
    write_json(ANALYSIS_COMMITTED / "generation_manifest.json", manifest)
    print(json.dumps(manifest, indent=2))
    if wanted_ids is not None:
        print("[main] partial --arms subset run; re-run without --arms once all 17 are checkpointed "
              "before running score_wide_rescore.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
