#!/usr/bin/env python3
"""Top-level CLI for write-direction-naming-battery: smoke -> baselines (G1
halt-and-lift) -> full 14-arm sweep -> per-arm summary.

Every direction, scalar, and dose is loaded verbatim from the resolved
qwen35-4b-midband-doubt-snap ladder's committed artifacts (cell.yaml
`readouts`/`law`); this script refits nothing. Arms are exactly cell.yaml
`arms` (14 total, 6105 planned generations): Arm A (P_CONFAB, c_hat @
0/0.25/0.5/0.75/1.0 + random_direction placebo @ 0.5/1.0), Arm B (P_REFUSE,
c_hat @ 0/-0.5/-1.0/-2.0 + random_direction placebo @ -1.0), Arm C (P_KNOWN,
c_hat @ 0/1.0).

Convention (this lineage, e.g. doubt-snap's run_dose_ladder.py,
qwen35-4b-midband-heldout's steer_lib.py, read in full before writing this):
multiplier == 0.0 is a TRUE no-hook baseline pass (controller=None), never a
zero-gain hook call -- baseline means untouched generation, not "erase and
write to the standardized mean".

GPU scripts run under /home/profsynapse/miniconda3/bin/python3 (base conda;
transformers >= 5.x for the qwen3_5 architecture), per cell.yaml
`execution.python`.
"""

from __future__ import annotations

import argparse
import gc
import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
LADDER_COMMITTED = REPO_ROOT / "experiments" / "qwen35-4b-midband-doubt-snap" / "analysis-committed"
for _p in (str(REPO_ROOT / "synaptic-tuner"), str(HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import steer_lib  # noqa: E402

ANALYSIS = HERE / "analysis"
COMMITTED = HERE / "analysis-committed"
ROWS_PATH = ANALYSIS / "naming_battery_rows.jsonl"

HS_INDEX = 20
DECODER_BLOCK_INDEX = 19
MAX_NEW = 200
BATCH_SIZE = 8

REFERENCE_DOSE_ABS = 12.608187917799976  # cell.yaml law.reference_dose_abs
SIGMA_C = 1.576023489724997               # cell.yaml law.standardization.mu_c/sigma_c (verified vs build_manifest hs20)
SIGMA_RANDOM = 1.0                         # random_direction.json's own convention

# cell.yaml `arms` block, transcribed literally.
ARMS: list[dict[str, Any]] = [
    {"name": "a_baseline",      "population": "P_CONFAB", "readout": "c_hat",            "multiplier": 0.0},
    {"name": "a_dose_0p25",     "population": "P_CONFAB", "readout": "c_hat",            "multiplier": 0.25},
    {"name": "a_dose_0p5",      "population": "P_CONFAB", "readout": "c_hat",            "multiplier": 0.5},
    {"name": "a_dose_0p75",     "population": "P_CONFAB", "readout": "c_hat",            "multiplier": 0.75},
    {"name": "a_dose_1",        "population": "P_CONFAB", "readout": "c_hat",            "multiplier": 1.0},
    {"name": "a_placebo_0p5",   "population": "P_CONFAB", "readout": "random_direction", "multiplier": 0.5},
    {"name": "a_placebo_1",     "population": "P_CONFAB", "readout": "random_direction", "multiplier": 1.0},
    {"name": "b_baseline",      "population": "P_REFUSE", "readout": "c_hat",            "multiplier": 0.0},
    {"name": "b_neg_0p5",       "population": "P_REFUSE", "readout": "c_hat",            "multiplier": -0.5},
    {"name": "b_neg_1",         "population": "P_REFUSE", "readout": "c_hat",            "multiplier": -1.0},
    {"name": "b_neg_2",         "population": "P_REFUSE", "readout": "c_hat",            "multiplier": -2.0},
    {"name": "b_placebo_neg_1", "population": "P_REFUSE", "readout": "random_direction", "multiplier": -1.0},
    {"name": "c_baseline",      "population": "P_KNOWN",  "readout": "c_hat",            "multiplier": 0.0},
    {"name": "c_dose_1",        "population": "P_KNOWN",  "readout": "c_hat",            "multiplier": 1.0},
]
BASELINE_ARMS = {"a_baseline", "b_baseline", "c_baseline"}

# G1 halt-and-lift (gates.yaml): compared against qwen35-4b-midband-heldout's
# OWN baseline pass over the same 1,332-row confab_held_out pool P_CONFAB is
# drawn from (heldout_summary.json baseline.confab.refused.rate == 0.0).
HELDOUT_BASELINE_CONFAB_REFUSED_RATE = 0.0
G1_CONFAB_TOLERANCE = 0.05
G1_KNOWN_CORRECTNESS_MIN = 0.90


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return steer_lib.load_jsonl(path)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")


def runlog_path(tag: str, namespace: str = "runlog") -> Path:
    return ANALYSIS / namespace / f"{tag}.jsonl"


def _run_log(tag: str, run_config: dict[str, Any], namespace: str = "runlog"):
    from shared.utilities.run_log import RunLog

    return RunLog(runlog_path(tag, namespace), run_config=run_config)


def load_rows() -> dict[str, list[dict]]:
    if not ROWS_PATH.is_file():
        raise SystemExit(f"missing {ROWS_PATH}; run materialize_rows.py first")
    rows = load_jsonl(ROWS_PATH)
    by_pop: dict[str, list[dict]] = {"P_CONFAB": [], "P_REFUSE": [], "P_KNOWN": []}
    for r in rows:
        by_pop[r["population"]].append(r)
    for pop, expected_n in (("P_CONFAB", 400), ("P_REFUSE", 421), ("P_KNOWN", 600)):
        if len(by_pop[pop]) != expected_n:
            raise SystemExit(f"{pop}: expected {expected_n} rows, got {len(by_pop[pop])}")
    return by_pop


def load_directions() -> dict[str, Any]:
    directions_dir = LADDER_COMMITTED / "directions" / "hs20"
    c_hat = np.asarray(json.loads((directions_dir / "c_hat.json").read_text())["vector"], dtype=np.float64)
    random_dir = np.asarray(json.loads((directions_dir / "random_direction.json").read_text())["vector"], dtype=np.float64)
    return {"c_hat": c_hat, "random_direction": random_dir}


def rate(records: list[dict], field: str) -> dict[str, Any]:
    n = len(records)
    successes = sum(1 for r in records if bool(r.get(field)))
    return {"n": n, "successes": successes, "rate": (successes / n) if n else None}


def summarize_arm(records: list[dict]) -> dict[str, Any]:
    return {
        "n": len(records),
        "refused": rate(records, "refused") if any("refused" in r for r in records) else None,
        "refused_v2": rate(records, "refused_v2"),
        "correct": rate([r for r in records if r.get("correct") is not None], "correct") if any(r.get("correct") is not None for r in records) else {"n": 0, "successes": 0, "rate": None},
        "correct_v2": rate([r for r in records if r.get("correct_v2") is not None], "correct_v2") if any(r.get("correct_v2") is not None for r in records) else {"n": 0, "successes": 0, "rate": None},
        "well_formed": rate(records, "well_formed"),
        "degenerate": rate(records, "degenerate"),
        "semantic_refuse": rate(records, "semantic_refuse"),
        "terminated_naturally": rate(records, "terminated_naturally"),
        "mean_new_tokens": (sum(r.get("n_new_tokens", 0) for r in records) / len(records)) if records else None,
    }


def readback_stats(records: list[dict], target: float) -> dict[str, Any]:
    measured = [r["readback_measured"] for r in records if r.get("readback_measured") is not None]
    if not measured:
        return {"n": 0, "target": target, "mean_measured": None, "max_abs_err": None}
    errs = [abs(m - target) for m in measured]
    return {
        "n": len(measured), "target": target,
        "mean_measured": sum(measured) / len(measured),
        "max_abs_err": max(errs),
    }


def gain_for(readout: str, multiplier: float) -> tuple[float, float]:
    """Returns (dose_abs, gain). gain is strength in sigma units passed to
    begin_pass; dose_abs is the raw commanded projection (gain * sigma)."""
    dose_abs = REFERENCE_DOSE_ABS * multiplier
    sigma = SIGMA_C if readout == "c_hat" else SIGMA_RANDOM
    gain = dose_abs / sigma if sigma else 0.0
    return dose_abs, gain


def run_arm(
    model, tokenizer, device, controllers: dict[str, Any], layer_module,
    arm: dict[str, Any], rows_by_pop: dict[str, list[dict]], batch_size: int,
    namespace: str = "runlog", readback_collector: list[dict] | None = None,
) -> list[dict]:
    import torch

    name = arm["name"]
    population = arm["population"]
    readout = arm["readout"]
    multiplier = arm["multiplier"]
    rows = rows_by_pop[population]
    dose_abs, gain = gain_for(readout, multiplier)

    log = _run_log(name, {"stage": "wdnb", "arm": name, "population": population, "readout": readout, "multiplier": multiplier}, namespace)
    if multiplier == 0.0:
        steer_lib.run_rows(
            model, tokenizer, device, None, "off", rows, 0.0, MAX_NEW, batch_size, log,
            arm=name, multiplier=multiplier, dose_abs=0.0, readout=readout,
        )
    else:
        ctrl = controllers[readout]
        handle = layer_module.register_forward_hook(ctrl)
        try:
            steer_lib.run_rows(
                model, tokenizer, device, ctrl, "gen_stream", rows, gain, MAX_NEW, batch_size, log,
                arm=name, multiplier=multiplier, dose_abs=dose_abs, readout=readout,
                readback_collector=readback_collector,
            )
        finally:
            handle.remove()
            ctrl.reset()
    log.finalize({"n_rows": len(rows), "gain": gain, "dose_abs": dose_abs})
    log.close()
    records = load_jsonl(runlog_path(name, namespace))
    if len(records) != len(rows):
        raise SystemExit(f"[pipeline] runlog_growth FAILED for arm {name!r}: expected {len(rows)} rows, got {len(records)}")
    return records


def build_controllers(directions: dict[str, Any]) -> dict[str, Any]:
    import torch

    hook_c, ctrl_c = steer_lib.build_hook_and_controller(torch.tensor(directions["c_hat"], dtype=torch.float32), SIGMA_C)
    hook_r, ctrl_r = steer_lib.build_hook_and_controller(torch.tensor(directions["random_direction"], dtype=torch.float32), SIGMA_RANDOM)
    return {"c_hat": ctrl_c, "random_direction": ctrl_r}


def cmd_smoke(args: argparse.Namespace) -> int:
    if not args.i_know_this_runs_on_gpu:
        print("[pipeline] smoke loads the model and generates on GPU; refusing without --i-know-this-runs-on-gpu.", file=sys.stderr)
        return 2
    from MechInterp.cell import evaluate_smoke_readback
    from MechInterp.config import SmokeConfig
    from MechInterp.intervention import get_decoder_layer

    rows_by_pop = load_rows()
    directions = load_directions()

    smoke_cfg = SmokeConfig(n_rows=8, write_rel_tol=0.02, write_abs_floor=0.05)

    n_each = 4
    confab_sample = rows_by_pop["P_CONFAB"][:n_each]
    refuse_sample = rows_by_pop["P_REFUSE"][:n_each]

    model, tokenizer, device = steer_lib.load_model()
    layer_module = get_decoder_layer(model, DECODER_BLOCK_INDEX)
    controllers = build_controllers(directions)

    import torch

    results: dict[str, Any] = {}
    try:
        # Positive smoke: P_CONFAB @ 1.0x c_hat -> target +12.608187917799976
        pos_collector: list[dict] = []
        pos_records = run_arm(
            model, tokenizer, device, controllers, layer_module,
            {"name": "smoke_pos", "population": "__smoke_confab__", "readout": "c_hat", "multiplier": 1.0},
            {"__smoke_confab__": confab_sample}, min(n_each, len(confab_sample)),
            namespace="runlog_smoke", readback_collector=pos_collector,
        )
        for rb in pos_collector:
            verdict = evaluate_smoke_readback(rb, smoke_cfg)
            if not verdict["passed"]:
                raise SystemExit(f"[pipeline] G0 FAILED readback (positive, +{REFERENCE_DOSE_ABS}): {verdict}")
        results["positive"] = {"n": len(pos_records), "readback": readback_stats(pos_records, REFERENCE_DOSE_ABS), "verdicts": [evaluate_smoke_readback(rb, smoke_cfg) for rb in pos_collector]}

        # Negative smoke: P_REFUSE @ -1.0x c_hat -> target -12.608187917799976
        neg_collector: list[dict] = []
        neg_records = run_arm(
            model, tokenizer, device, controllers, layer_module,
            {"name": "smoke_neg", "population": "__smoke_refuse__", "readout": "c_hat", "multiplier": -1.0},
            {"__smoke_refuse__": refuse_sample}, min(n_each, len(refuse_sample)),
            namespace="runlog_smoke", readback_collector=neg_collector,
        )
        for rb in neg_collector:
            verdict = evaluate_smoke_readback(rb, smoke_cfg)
            if not verdict["passed"]:
                raise SystemExit(f"[pipeline] G0 FAILED readback (negative, -{REFERENCE_DOSE_ABS}): {verdict}")
        results["negative"] = {"n": len(neg_records), "readback": readback_stats(neg_records, -REFERENCE_DOSE_ABS), "verdicts": [evaluate_smoke_readback(rb, smoke_cfg) for rb in neg_collector]}
    finally:
        del model
        gc.collect()
        torch.cuda.empty_cache()

    write_json(ANALYSIS / "smoke_summary.json", results)
    print(json.dumps(results, indent=2, default=str), flush=True)
    print("[pipeline] SMOKE PASSED (readback within tolerance on both positive and negative arms)", flush=True)
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    if not args.i_know_this_runs_on_gpu:
        print("[pipeline] run is the full 6105-generation sweep; refusing without --i-know-this-runs-on-gpu.", file=sys.stderr)
        return 2

    t0 = time.time()
    rows_by_pop = load_rows()
    directions = load_directions()

    model, tokenizer, device = steer_lib.load_model()
    from MechInterp.intervention import get_decoder_layer

    layer_module = get_decoder_layer(model, DECODER_BLOCK_INDEX)
    controllers = build_controllers(directions)

    import torch

    all_summaries: dict[str, Any] = {}
    try:
        # --- Baselines first (G1 halt-and-lift) ---
        baseline_records: dict[str, list[dict]] = {}
        for arm in ARMS:
            if arm["name"] in BASELINE_ARMS:
                print(f"[pipeline] running baseline arm {arm['name']!r} ({len(rows_by_pop[arm['population']])} rows)", flush=True)
                records = run_arm(model, tokenizer, device, controllers, layer_module, arm, rows_by_pop, args.batch_size)
                baseline_records[arm["name"]] = records
                all_summaries[arm["name"]] = summarize_arm(records)

        a_summary = all_summaries["a_baseline"]
        c_summary = all_summaries["c_baseline"]
        a_refused_v2_rate = a_summary["refused_v2"]["rate"] or 0.0
        c_correct_v2_rate = c_summary["correct_v2"]["rate"] if c_summary["correct_v2"]["rate"] is not None else 0.0

        g1_confab_pass = abs(a_refused_v2_rate - HELDOUT_BASELINE_CONFAB_REFUSED_RATE) <= G1_CONFAB_TOLERANCE
        g1_known_pass = c_correct_v2_rate >= G1_KNOWN_CORRECTNESS_MIN
        g1_report = {
            "a_baseline_refused_v2_rate": a_refused_v2_rate,
            "heldout_baseline_confab_refused_rate": HELDOUT_BASELINE_CONFAB_REFUSED_RATE,
            "g1_confab_pass": g1_confab_pass,
            "c_baseline_correct_v2_rate": c_correct_v2_rate,
            "g1_known_pass": g1_known_pass,
        }
        write_json(ANALYSIS / "g1_baseline_check.json", g1_report)
        print(f"[pipeline] G1 check: {json.dumps(g1_report, indent=2)}", flush=True)

        if not (g1_confab_pass and g1_known_pass):
            print("[pipeline] G1 HALT-AND-LIFT: baseline reproduction FAILED. Stopping before dosed arms.", file=sys.stderr)
            write_json(ANALYSIS / "g1_HALTED.json", g1_report)
            return 3

        # --- Dosed + placebo arms ---
        for arm in ARMS:
            if arm["name"] in BASELINE_ARMS:
                continue
            print(f"[pipeline] running arm {arm['name']!r} (population={arm['population']}, readout={arm['readout']}, multiplier={arm['multiplier']})", flush=True)
            records = run_arm(model, tokenizer, device, controllers, layer_module, arm, rows_by_pop, args.batch_size)
            all_summaries[arm["name"]] = summarize_arm(records)
            dose_abs, _ = gain_for(arm["readout"], arm["multiplier"])
            if arm["multiplier"] != 0.0:
                all_summaries[arm["name"]]["readback"] = readback_stats(records, dose_abs)
    finally:
        del model
        gc.collect()
        torch.cuda.empty_cache()

    total_generations = sum(s["n"] for s in all_summaries.values())
    final = {
        "arms": all_summaries,
        "total_generations": total_generations,
        "total_generations_planned": 6105,
        "elapsed_s": time.time() - t0,
    }
    write_json(COMMITTED.parent / "analysis" / "run_summary.json", final)
    print(f"[pipeline] done in {time.time() - t0:.0f}s, total_generations={total_generations}", flush=True)
    print(json.dumps(final, indent=2, default=str), flush=True)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_smoke = sub.add_parser("smoke", help="instrument validation only, tiny row count, namespaced runlog_smoke path")
    p_smoke.add_argument("--i-know-this-runs-on-gpu", action="store_true")
    p_smoke.set_defaults(func=cmd_smoke)

    p_run = sub.add_parser("run", help="the full 14-arm, 6105-generation sweep")
    p_run.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    p_run.add_argument("--i-know-this-runs-on-gpu", action="store_true")
    p_run.set_defaults(func=cmd_run)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
