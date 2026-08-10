#!/usr/bin/env python3
"""Top-level driver for the caution-install-bounded-site-sweep harness.

Two modes:

  --stage N [--substrate ...]  Runs one registered Run-plan stage (AMENDMENT.md
      "Run plan and GPU budget" table) via its dedicated script, in the
      documented sequential order. GPU stages (2, 4, 5, 6, 7, 8) refuse to run
      without --i-know-this-runs-on-gpu (forwarded to the stage script) and
      are expected to run one at a time (cell.yaml execution.concurrency).
      This driver does NOT auto-advance past a failing stage: a nonzero
      return code from a stage script halts the sequence (hard stop, per the
      pre-stated STOP-gate discipline), it never "proceeds to see what
      happens."

  --smoke-harness   CPU-only, no model inference anywhere (never imports
      torch/transformers/peft for generation). Exercises, against a
      SEPARATE synthetic namespace under `analysis/_smoke_harness/` (never
      touches real `analysis/rows_with_text.jsonl` or
      `analysis-committed/*`), exactly the four things the lead's task asked
      this dry run to prove:
        1. pool construction  -- synthesizes a tiny labeled row pool with the
           real role/split shape (confab / known_correct_answered /
           unknown_refused), using the SAME `sweep_lib.grade_role` /
           `split_fit_heldout.stratified_split` logic the real pipeline uses,
           not a hand-rolled stand-in.
        2. site iteration     -- walks the real `cell.yaml` sites/substrates
           via `sweep_lib.sites_for`, so a site-table edit is exercised by
           this smoke too.
        3. checkpoint/resume  -- writes a resumable JSONL via
           `sweep_lib.write_jsonl_row`, simulates an interruption partway
           through (process-level kill/resume is drilled separately with
           `experiments/common/launch_detached.sh`, per
           `.skills/mechinterp-cells/reference/organization.md`'s mandatory
           pre-sign kill-resume drill for any `persistence: incremental`
           module -- NOT reproduced here), and asserts the second pass only
           processes the rows the first pass left pending.
        4. report generation  -- runs `adjudicate_gates.py`'s primitive
           functions (rate_over_population / effect_ratio_over_draws /
           interval_containment math) over synthetic per-cell numbers shaped
           like the real `held_out_summary.json` / `controls_summary.json`,
           and writes a synthetic `gate_report.json` under the smoke
           namespace.
      Every phase's wall clock is recorded in the returned/printed summary.
      `--smoke-harness` never calls `--i-know-this-runs-on-gpu` anywhere and
      never imports a GPU stage script's model-loading path.
"""

from __future__ import annotations

import argparse
import json
import random
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import adjudicate_gates  # noqa: E402
from sweep_lib import (  # noqa: E402
    ANALYSIS,
    COMMITTED,
    load_cell,
    sites_for,
    substrate_config,
    wilson_ci_point,
    write_json,
    write_jsonl_row,
)

# Stage registry mirrors AMENDMENT.md "Run plan and GPU budget" table exactly.
# device: "cpu" | "gpu"; script: file in this directory; substrates: which
# substrate args to invoke it for (some stages are trained-only).
#
# F5 fix: split_fit_heldout.py is a registered Run-plan stage in its own
# right (Stage 1b: CPU, FIT/HELD-OUT split over the pool mine_pool.py just
# wrote, trained-substrate only, between Stage 1 mining and Stage 2
# extraction) but had no entry here at all -- the driver could run every
# other stage in sequence and skip it entirely. String keys ("1", "1b", "2",
# ..., "9") replace the previous integer keys so "1b" can sit between "1"
# and "2" in both the dict and STAGE_ORDER without forcing a fractional or
# renumbered integer scheme. split_fit_heldout.py takes no --substrate flag
# (it is hardcoded to the trained substrate; see its own module docstring
# and sweep_lib.rows_with_text_path's F8 note), so its substrates list is
# [None] like the substrate-agnostic adjudicate_gates.py stage.
STAGES = {
    "1": {"name": "mine_pool", "script": "mine_pool.py", "device": "gpu", "substrates": ["trained"]},
    "1b": {"name": "split_fit_heldout", "script": "split_fit_heldout.py", "device": "cpu", "substrates": [None]},
    "2": {"name": "extract_anchor", "script": "extract_anchor.py", "device": "gpu", "substrates": ["trained", "raw_base"]},
    "3": {"name": "build_directions", "script": ["build_directions.py", "alin_profile.py", "build_random_directions.py"],
          "device": "cpu", "substrates": ["trained", "raw_base"]},
    "4": {"name": "write_smoke", "script": "write_smoke.py", "device": "gpu", "substrates": ["trained", "raw_base"]},
    "5": {"name": "dose_calibrate", "script": "dose_calibrate.py", "device": "gpu", "substrates": ["trained", "raw_base"]},
    "6": {"name": "run_held_out", "script": "run_held_out.py", "device": "gpu", "substrates": ["trained", "raw_base"]},
    "7": {"name": "run_controls", "script": "run_controls.py", "device": "gpu", "substrates": ["trained"]},
    "8": {"name": "run_pairs", "script": "run_pairs.py", "device": "gpu", "substrates": ["trained"]},
    "9": {"name": "adjudicate_gates", "script": "adjudicate_gates.py", "device": "cpu", "substrates": [None]},
}

STAGE_ORDER = ["1", "1b", "2", "3", "4", "5", "6", "7", "8", "9"]


def run_stage(stage_num: str, substrate: str | None, gpu_ack: bool) -> int:
    spec = STAGES[stage_num]
    scripts = spec["script"] if isinstance(spec["script"], list) else [spec["script"]]
    for script in scripts:
        cmd = [sys.executable, str(HERE / script)]
        if substrate is not None:
            cmd += ["--substrate", substrate]
        if spec["device"] == "gpu":
            if not gpu_ack:
                print(f"[run-sweep] stage {stage_num} ({spec['name']}) is a GPU stage; "
                      "pass --i-know-this-runs-on-gpu to actually run it.", file=sys.stderr)
                return 2
            cmd.append("--i-know-this-runs-on-gpu")
        print(f"[run-sweep] stage {stage_num} ({spec['name']}): {' '.join(cmd)}", flush=True)
        rc = subprocess.call(cmd)
        if rc != 0:
            print(f"[run-sweep] stage {stage_num} ({spec['name']}) failed rc={rc}. HARD STOP.", file=sys.stderr)
            return rc
    return 0


def run_sequence(gpu_ack: bool) -> int:
    for stage_num in STAGE_ORDER:
        for substrate in STAGES[stage_num]["substrates"]:
            rc = run_stage(stage_num, substrate, gpu_ack)
            if rc != 0:
                return rc
    return 0


# --------------------------------------------------------------------------
# --smoke-harness: CPU-only, no model inference, synthetic namespace
# --------------------------------------------------------------------------

SMOKE_ROOT = ANALYSIS / "_smoke_harness"
SMOKE_COMMITTED = COMMITTED / "_smoke_harness"


def smoke_pool_construction(cell: dict, n_confab: int = 6, n_known: int = 8, n_unknown_refused: int = 4) -> dict:
    """Phase 1: synthesize a labeled pool with the real role shape, using
    sweep_lib.grade_role on synthetic model outputs (never a real model
    call) so the SAME grading code path the real mining uses is exercised."""
    t0 = time.perf_counter()
    import sweep_lib

    rng = random.Random(20260707)
    rows = []
    for i in range(n_confab):
        row = {"row_key": f"smoke::confab::{i}", "label": "unknown",
               "aliases": ["not-the-answer"], "category": f"cat{i % 3}"}
        completion = json.dumps({"answer": f"synthetic answer {i}", "response_confidence": 0.8})
        graded = sweep_lib.grade_role(row, completion)
        assert graded["role"] == "confab", graded
        rows.append({**row, **graded})
    for i in range(n_known):
        row = {"row_key": f"smoke::known::{i}", "label": "known",
               "aliases": [f"gold{i}"], "category": f"cat{i % 3}"}
        completion = json.dumps({"answer": f"gold{i}", "response_confidence": 0.9})
        graded = sweep_lib.grade_role(row, completion)
        assert graded["role"] == "known_correct_answered", graded
        rows.append({**row, **graded})
    for i in range(n_unknown_refused):
        row = {"row_key": f"smoke::refused::{i}", "label": "unknown",
               "aliases": [], "category": f"cat{i % 3}"}
        completion = json.dumps({"answer": "I don't know the answer", "response_confidence": 0.1})
        graded = sweep_lib.grade_role(row, completion)
        assert graded["role"] == "unknown_refused", graded
        rows.append({**row, **graded})

    SMOKE_ROOT.mkdir(parents=True, exist_ok=True)
    pool_path = SMOKE_ROOT / "rows_with_text.jsonl"
    if pool_path.exists():
        pool_path.unlink()
    for r in rows:
        write_jsonl_row(pool_path, r)

    # exercise the real stratified split logic
    from split_fit_heldout import stratified_split
    confab_rows = [r for r in rows if r["role"] == "confab"]
    known_rows = [r for r in rows if r["role"] == "known_correct_answered"]
    split_confab = stratified_split(confab_rows, fit_frac=0.40, seed=20260707)
    split_known = stratified_split(known_rows, fit_frac=0.40, seed=20260707)

    return {
        "wall_clock_s": time.perf_counter() - t0,
        "n_confab": len(confab_rows), "n_known": len(known_rows),
        "n_unknown_refused": n_unknown_refused,
        "split_confab_counts": {v: list(split_confab.values()).count(v) for v in ("fit", "held_out")},
        "split_known_counts": {v: list(split_known.values()).count(v) for v in ("fit", "held_out")},
        "pool_path": str(pool_path),
    }


def smoke_site_iteration(cell: dict) -> dict:
    """Phase 2: walk the real cell.yaml site/substrate tables."""
    t0 = time.perf_counter()
    seen = []
    for substrate in ("trained", "raw_base"):
        for site in sites_for(substrate, cell):
            seen.append({"substrate": substrate, "site": site.name, "hs_index": site.hs_index,
                         "decoder_block": site.decoder_block, "status": site.status})
    return {"wall_clock_s": time.perf_counter() - t0, "n_site_substrate_cells": len(seen), "cells": seen}


def smoke_checkpoint_resume(n_rows: int = 20) -> dict:
    """Phase 3: write a resumable JSONL, simulate an interruption partway,
    assert the resumed pass only processes what's left pending."""
    t0 = time.perf_counter()
    ckpt_path = SMOKE_ROOT / "checkpoint.jsonl"
    if ckpt_path.exists():
        ckpt_path.unlink()

    row_keys = [f"row{i}" for i in range(n_rows)]

    def completed_keys() -> set[str]:
        if not ckpt_path.exists():
            return set()
        return {json.loads(line)["row_key"] for line in ckpt_path.open() if line.strip()}

    # first "pass": process the first half, then simulate an interruption
    first_half = row_keys[: n_rows // 2]
    t_pass1 = time.perf_counter()
    for rk in first_half:
        write_jsonl_row(ckpt_path, {"row_key": rk, "phase": "pass1"})
    pass1_wall_clock_s = time.perf_counter() - t_pass1

    # "resume": a fresh process would recompute completed_keys() from disk
    done = completed_keys()
    pending = [rk for rk in row_keys if rk not in done]
    assert pending == row_keys[n_rows // 2:], (pending, row_keys[n_rows // 2:])

    t_pass2 = time.perf_counter()
    for rk in pending:
        write_jsonl_row(ckpt_path, {"row_key": rk, "phase": "pass2_resumed"})
    pass2_wall_clock_s = time.perf_counter() - t_pass2

    final = completed_keys()
    assert final == set(row_keys), (len(final), len(row_keys))

    return {
        "wall_clock_s": time.perf_counter() - t0,
        "n_rows": n_rows, "n_pass1": len(first_half), "n_pass2_resumed": len(pending),
        "pass1_wall_clock_s": pass1_wall_clock_s, "pass2_wall_clock_s": pass2_wall_clock_s,
        "resume_correct": pending == row_keys[n_rows // 2:], "final_complete": final == set(row_keys),
        "checkpoint_path": str(ckpt_path),
    }


def smoke_report_generation() -> dict:
    """Phase 4: exercise the gate-primitive math (rate_over_population,
    effect_ratio_over_draws, interval_containment shapes) over synthetic
    numbers, and write a synthetic gate_report.json -- no real held-out /
    controls artifacts are read or written."""
    t0 = time.perf_counter()

    # rate_over_population (G1/G2 primitive)
    g1_synth = wilson_ci_point(31, 50)  # rate 0.62, matches AMENDMENT.md's schematic pass shape
    g2_synth = wilson_ci_point(1, 40)   # rate 0.025, n_fired_known=40 >= 35 adjudicable

    # effect_ratio_over_draws (G3 primitive). F1/F13 fix: the registered
    # criterion is RG1 -- a LIFT ratio (rate minus that arm's OWN undosed
    # baseline), aggregated as max-over-draws, NOT a raw-rate ratio. These
    # synthetic numbers reproduce the worked example in
    # .skills/mechinterp-cells/reference/read-then-actuate.md section 5.1
    # (RR3/RG1 row): gated lift +40.9 points (baseline 0.286 -> 0.694),
    # three draws at +13.3, -7.4, +21.8 points, ratio 1.87x -> FAIL.
    #
    # NEW DEFECT #3 (2026-08-10 lead adjudication): this used to
    # re-implement the lift/ratio/guard math inline -- a second copy of
    # adjudicate_gates.g3_direction_specificity's logic that could silently
    # drift from the real one and validate a formula the real path no longer
    # runs. It now CALLS that function directly, on in-memory ctrl/ho dicts
    # shaped like controls_summary.json / held_out_summary.json (never
    # touching real analysis-committed/*, preserving this smoke's
    # containment invariant), so a real regression in the gate's math shows
    # up here too.
    gated_baseline = 0.286
    gated_rate = 0.694
    draw_baseline = 0.10
    draw_lifts_target = [0.133, -0.074, 0.218]
    draw_rates = [draw_baseline + lift for lift in draw_lifts_target]
    cell_key = "smoke:worked_example"
    synth_ho = {"cells": {cell_key: {"arms": {
        "gated": {"confab_held_out": {"rate": gated_rate}},
        "baseline_undosed": {"confab_held_out": {"rate": gated_baseline}},
    }}}}
    synth_ctrl = {"cells": {cell_key: {"status": "RAN", "random_direction": [
        {"draw": i, "random_direction": {"confab_held_out": {"rate": rate}},
         "baseline_undosed": {"confab_held_out": {"rate": draw_baseline}}}
        for i, rate in enumerate(draw_rates)
    ]}}}
    g3_out = adjudicate_gates.g3_direction_specificity("smoke", ctrl=synth_ctrl, ho=synth_ho)
    g3_synth = g3_out[cell_key]
    ratio = g3_synth["ratio"]
    assert isinstance(ratio, float) and 1.87 <= ratio <= 1.88, (
        f"G3 smoke regression: expected adjudicate_gates.g3_direction_specificity "
        f"to reproduce the RG1 worked example's ratio (~1.87-1.88, FAIL), got "
        f"{ratio!r}. The bug this guards against: the OLD raw-rate-ratio "
        f"formula (gated_rate / min(draw_rate), no baseline subtraction) "
        f"produced a spuriously PASSING ratio on numbers shaped like these."
    )
    assert g3_synth["pass"] is False, (
        "G3 smoke regression: worked example must FAIL (ratio < 3.0), not pass"
    )

    # interval_containment (G4 primitive)
    from sweep_lib import wilson_ci
    lo, hi = wilson_ci(194, 221)
    g4_synth = {"reference_wilson_95": [lo, hi], "observed_rate": 0.90, "contained": lo <= 0.90 <= hi}

    report = {
        "synthetic": True,
        "g1_rate_over_population": g1_synth,
        "g2_rate_over_population": {**g2_synth, "adjudicable": True},
        "g3_effect_ratio_over_draws": g3_synth,
        "g4_interval_containment": g4_synth,
    }
    SMOKE_COMMITTED.mkdir(parents=True, exist_ok=True)
    out_path = SMOKE_COMMITTED / "gate_report.json"
    write_json(out_path, report)
    return {"wall_clock_s": time.perf_counter() - t0, "report_path": str(out_path), "report": report}


def run_smoke_harness(cleanup: bool) -> dict:
    t_start = time.perf_counter()
    cell = load_cell()

    results = {}
    print("[smoke-harness] phase 1: pool construction", flush=True)
    results["pool_construction"] = smoke_pool_construction(cell)
    print("[smoke-harness] phase 2: site iteration", flush=True)
    results["site_iteration"] = smoke_site_iteration(cell)
    print("[smoke-harness] phase 3: checkpoint/resume", flush=True)
    results["checkpoint_resume"] = smoke_checkpoint_resume()
    print("[smoke-harness] phase 4: report generation", flush=True)
    results["report_generation"] = smoke_report_generation()

    results["total_wall_clock_s"] = time.perf_counter() - t_start
    results["gpu_touched"] = False

    if cleanup:
        shutil.rmtree(SMOKE_ROOT, ignore_errors=True)
        shutil.rmtree(SMOKE_COMMITTED, ignore_errors=True)
        results["cleaned_up"] = True
    else:
        results["cleaned_up"] = False
        results["smoke_namespace"] = {"analysis": str(SMOKE_ROOT), "committed": str(SMOKE_COMMITTED)}

    return results


def run_preflight() -> int:
    """`run_sweep.py preflight` (ALSO(a), 2026-08-10 lead adjudication):
    checks every launch-prep input the GPU stages need and NAMES exactly
    what is missing, before any GPU budget is spent -- rather than a stage
    script failing partway through with a less legible error.

    Checks:
      1. F16's expansion corpus (mine_pool.EXPANSION_CANDIDATES,
         REPO_ROOT-relative so it resolves both on the host checkout and
         under the container /workspace mount) is staged into the worktree.
      2. analysis/rows_with_text_raw_base.jsonl exists and covers all 221 of
         rep2's registered raw_base anchor pool row_keys, each carrying
         role: "confab" -- not just row_key presence (the same role
         requirement extract_anchor.py._raw_base_joined_rows and
         dose_calibrate.py.calibration_pool now hard-fail on, named here too
         so it surfaces before either stage script runs).
    """
    problems = []

    from mine_pool import EXPANSION_CANDIDATES
    if not EXPANSION_CANDIDATES.exists():
        problems.append(
            f"F16 expansion corpus not staged: {EXPANSION_CANDIDATES} does "
            "not exist (see mine_pool.py for the resolved, REPO_ROOT-relative "
            "path; this file must be staged into the worktree before Stage 1 "
            "mining can run)."
        )

    from sweep_lib import load_jsonl, raw_base_anchor_pool, rows_with_text_path

    text_path = rows_with_text_path("raw_base")
    try:
        pool = raw_base_anchor_pool()
    except RuntimeError as exc:
        problems.append(f"raw_base anchor pool unavailable: {exc}")
        pool = None

    if pool is not None:
        text_by_key = {r["row_key"]: r for r in load_jsonl(text_path)}
        missing = [r["row_key"] for r in pool["rows"] if r["row_key"] not in text_by_key]
        wrong_role = [
            r["row_key"] for r in pool["rows"]
            if r["row_key"] in text_by_key and text_by_key[r["row_key"]].get("role") != "confab"
        ]
        if missing:
            problems.append(
                f"{text_path} is missing question text for {len(missing)}/"
                f"{pool['n_confab']} of rep2's registered raw_base anchor "
                f"pool row_keys (first 5: {missing[:5]})."
            )
        if wrong_role:
            problems.append(
                f"{text_path} has {len(wrong_role)}/{pool['n_confab']} "
                f"present row_keys carrying a role other than 'confab' "
                f"(first 5: {wrong_role[:5]}); every one of rep2's 221 "
                "registered row_keys must carry role: \"confab\"."
            )
    else:
        problems.append(
            f"cannot check {text_path} for row_key coverage / role: raw_base "
            "anchor pool itself is unavailable (see the pool problem above)."
        )

    result = {"ok": not problems, "problems": problems}
    print(json.dumps(result, indent=2))
    return 0 if not problems else 1


def run(args: argparse.Namespace) -> int:
    if args.smoke_harness:
        results = run_smoke_harness(cleanup=not args.keep_smoke_artifacts)
        print(json.dumps(results, indent=2, default=str))
        return 0

    if args.stage is not None:
        return run_stage(args.stage, args.substrate, args.i_know_this_runs_on_gpu)

    return run_sequence(args.i_know_this_runs_on_gpu)


def parse_args(argv=None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stage", choices=STAGE_ORDER, default=None,
                     help="run exactly one Run-plan stage (e.g. '1', '1b', '2', ..., '9'); "
                          "omit to run the full sequence")
    ap.add_argument("--substrate", choices=["trained", "raw_base"], default=None,
                     help="required for --stage on a per-substrate stage")
    ap.add_argument("--i-know-this-runs-on-gpu", action="store_true")
    ap.add_argument("--smoke-harness", action="store_true",
                     help="CPU-only dry run: pool construction, site iteration, "
                          "checkpoint/resume, report generation. No model inference.")
    ap.add_argument("--keep-smoke-artifacts", action="store_true",
                     help="do not delete the _smoke_harness/ namespace after --smoke-harness")
    return ap.parse_args(argv)


if __name__ == "__main__":
    # `run_sweep.py preflight` is a dedicated subcommand (ALSO(a)), checked
    # before the flag-based parse_args() schema so it does not need a
    # --stage/--substrate pair to invoke.
    if len(sys.argv) > 1 and sys.argv[1] == "preflight":
        raise SystemExit(run_preflight())
    raise SystemExit(run(parse_args()))
