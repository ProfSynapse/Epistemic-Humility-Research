#!/usr/bin/env python3
"""Standalone GPU diagnostic for the M1 SC1 mandatory-preflight readback
FAIL at the bottom ladder rung (0.0625x reference dose).

DIAGNOSTIC DATA ONLY. Does not modify gates.yaml, cell.yaml, AMENDMENT.md,
experiment.yaml, NOTEBOOK.md, anything in harness/ other than this new file,
or anything in analysis/preflight/ or analysis-committed/. Never re-runs
`run_margin.py preflight` (that would overwrite the governed preflight_report.
json / PASS marker). All outputs go under this script's own new directory,
analysis/preflight_diag/.

Reuses the SAME dosing + readback code path the preflight used, imported
directly rather than reimplemented: `steer_lib.load_model` /
`build_hook_and_controller` / `render_prompt` / `run_batch_fixed`,
`dose_ladder.rung_dose_abs` / `c_hat_write_params`, `sc1_checks.
check_readback`, `config` for every numeric constant, and `run_margin.
population_row_keys` / `resolve_model_revision` / `load_c_hat_vector` (pure
read-only helpers, safe to import -- run_margin.py has no import-time side
effects; only its `cmd_*` functions touch disk, and none of those are called
here).

Two questions this characterizes for the failing bottom rung:

  1. REPEATABILITY: dose the SAME 4 rows the mandatory preflight used, at
     the SAME 0.0625x rung, THREE separate times (three independent forward
     passes, each with a freshly built hook/controller -- the same
     per-rung-instantiation pattern `cmd_preflight` itself uses). If each
     row's abs_delta is identical (up to float roundoff) across repeats, the
     error is deterministic (quantization/content interaction); if it
     varies materially, it is stochastic run-to-run noise.

  2. BREADTH: dose 12 additional confab rows (from the SC0-committed
     `subsample_ids_<family>.json`, sorted, excluding the 4 preflight rows)
     at 0.0625x, 0.125x, and 0.25x, once each, to see the abs_delta
     distribution and how many rows would fail the registered rel<=0.005
     criterion at each rung.

Outputs:
  analysis/preflight_diag/rows.jsonl     one line per dosed row, flushed
                                          immediately (progress-visible)
  analysis/preflight_diag/diag_report.json   full records + summary stats
  analysis/preflight_diag/SUMMARY.txt    short plain-text summary
"""

from __future__ import annotations

import argparse
import datetime
import gc
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
EXPERIMENT_DIR = HERE.parent
REPO_ROOT = HERE.parents[2]
TUNER_DIR = REPO_ROOT / "synaptic-tuner"
for _p in (str(TUNER_DIR), str(HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import config  # noqa: E402
import common  # noqa: E402
import row_pool  # noqa: E402
import sc1_checks  # noqa: E402
import dose_ladder  # noqa: E402
import run_margin  # noqa: E402  (read-only helpers only; no cmd_* invoked)

DIAG_DIR = EXPERIMENT_DIR / "analysis" / "preflight_diag"
ROWS_JSONL = DIAG_DIR / "rows.jsonl"
REPORT_PATH = DIAG_DIR / "diag_report.json"
SUMMARY_PATH = DIAG_DIR / "SUMMARY.txt"
SUBSAMPLE_PATH = {
    fam: EXPERIMENT_DIR / "analysis-committed" / f"subsample_ids_{fam}.json"
    for fam in config.FAMILIES
}

# Exactly the 4 rows the mandatory preflight dosed per family (preflight_row_keys
# in analysis/preflight/preflight_report.json, read not touched).
PREFLIGHT_ROW_KEYS = {
    "qwen35_4b": ["kuq_unknowns_all:1009", "kuq_unknowns_all:1023", "kuq_unknowns_all:1036", "kuq_unknowns_all:1039"],
    "mistral7b_v03": ["kuq_unknowns_all:1000", "kuq_unknowns_all:1009", "kuq_unknowns_all:1011", "kuq_unknowns_all:1018"],
}
# The row that failed SC1 at 0.0625x in the mandatory preflight, per family.
FAILING_ROW = {"qwen35_4b": "kuq_unknowns_all:1039", "mistral7b_v03": "kuq_unknowns_all:1018"}

REPEAT_RUNG = 0.0625
N_REPEATS = 3
BREADTH_RUNGS = (0.0625, 0.125, 0.25)
N_BREADTH_ROWS = 12

# A row's abs_delta is called "deterministic across repeats" if its spread
# (max-min over the 3 repeats) is below this float-roundoff-scale threshold;
# above it, we report the raw spread and call it stochastic rather than
# silently rounding a real difference away.
DETERMINISM_ABS_SPREAD_THRESHOLD = 1e-6


def _append_row(rec: dict[str, Any]) -> None:
    DIAG_DIR.mkdir(parents=True, exist_ok=True)
    with ROWS_JSONL.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")


def _breadth_row_keys(family: str, exclude: list[str], n: int) -> list[str]:
    subsample = common.load_json(SUBSAMPLE_PATH[family])
    confab_sorted = sorted(subsample["confab_subsample"]["row_keys"])
    exclude_set = set(exclude)
    picked = [rk for rk in confab_sorted if rk not in exclude_set][:n]
    if len(picked) != n:
        raise SystemExit(f"[diag] {family}: only found {len(picked)} breadth rows (wanted {n}) after excluding preflight rows.")
    return picked


def _dose_once(model, tokenizer, device, layer_module, c_hat, sigma: float, family: str, rows: list[dict[str, Any]], setpoint: float):
    """One forward pass over `rows`, all sharing `setpoint`. Fresh hook +
    controller per call (cmd_preflight's own per-rung-instantiation pattern),
    so repeats never share mutable controller state."""
    import torch
    import steer_lib

    _, gain = dose_ladder.c_hat_write_params(family, setpoint)
    hook, ctrl = steer_lib.build_hook_and_controller(torch.tensor(c_hat, dtype=torch.float32), sigma)
    handle = layer_module.register_forward_hook(ctrl)
    try:
        prompts = [steer_lib.render_prompt(r) for r in rows]
        gen, _raw_rb = steer_lib.run_batch_fixed(model, tokenizer, device, ctrl, prompts, "gen_stream", gain, config.GEN_MAX_NEW_TOKENS)
    finally:
        handle.remove()
        ctrl.reset()
    return gen


def run_family(family: str) -> dict[str, Any]:
    import torch
    import steer_lib
    from MechInterp.intervention import get_decoder_layer

    print(f"[diag] {family}: loading model", flush=True)
    model_name, revision = run_margin.resolve_model_revision(family)
    model, tokenizer, device = steer_lib.load_model(model_name, revision)
    layer_module = get_decoder_layer(model, config.DECODER_BLOCK_INDEX[family])

    c_hat = run_margin.load_c_hat_vector(family)
    sigma = config.SIGMA_C[family]
    qpool = row_pool.question_pool(family)

    preflight_keys = PREFLIGHT_ROW_KEYS[family]
    breadth_keys = _breadth_row_keys(family, preflight_keys, N_BREADTH_ROWS)

    results: dict[str, Any] = {"family": family, "repeatability": {}, "breadth": {}}

    try:
        # -------------------- 1. Repeatability --------------------
        setpoint_repeat = dose_ladder.rung_dose_abs(family, REPEAT_RUNG)
        rows_repeat = [{"row_key": rk, **qpool[rk]} for rk in preflight_keys]
        repeat_records: dict[str, list[dict[str, Any]]] = {rk: [] for rk in preflight_keys}
        for rep in range(1, N_REPEATS + 1):
            gen = _dose_once(model, tokenizer, device, layer_module, c_hat, sigma, family, rows_repeat, setpoint_repeat)
            for row, res in zip(rows_repeat, gen):
                check = sc1_checks.check_readback(row["row_key"], family, res.get("readback_measured"), setpoint_repeat)
                rec = {"phase": "repeatability", "family": family, "rung": REPEAT_RUNG, "repeat": rep, **check}
                repeat_records[row["row_key"]].append(rec)
                _append_row(rec)
            print(f"[diag] {family} repeatability rep {rep}/{N_REPEATS} done", flush=True)
        results["repeatability"] = repeat_records

        # -------------------- 2. Breadth --------------------
        rows_breadth = [{"row_key": rk, **qpool[rk]} for rk in breadth_keys]
        breadth_records: dict[str, list[dict[str, Any]]] = {str(m): [] for m in BREADTH_RUNGS}
        for multiplier in BREADTH_RUNGS:
            setpoint = dose_ladder.rung_dose_abs(family, multiplier)
            gen = _dose_once(model, tokenizer, device, layer_module, c_hat, sigma, family, rows_breadth, setpoint)
            for row, res in zip(rows_breadth, gen):
                check = sc1_checks.check_readback(row["row_key"], family, res.get("readback_measured"), setpoint)
                rec = {"phase": "breadth", "family": family, "rung": multiplier, **check}
                breadth_records[str(multiplier)].append(rec)
                _append_row(rec)
            print(f"[diag] {family} breadth {multiplier}x done", flush=True)
        results["breadth"] = breadth_records
    finally:
        del model
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        print(f"[diag] {family}: model released", flush=True)

    return results


def _summarize_breadth(breadth_records: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    import numpy as np

    summary = {}
    for rung_str, recs in breadth_records.items():
        have_readback = [r for r in recs if r.get("readback_measured") is not None]
        abs_deltas = np.asarray([r["abs_delta"] for r in have_readback], dtype=np.float64)
        rel_deltas = np.asarray([r["rel_delta"] for r in have_readback], dtype=np.float64)
        n_fail = sum(1 for r in recs if not r.get("passed", False))
        summary[rung_str] = {
            "n": len(recs),
            "n_missing_readback": len(recs) - len(have_readback),
            "n_fail_rel_0.005": n_fail,
            "frac_fail": (n_fail / len(recs)) if recs else None,
            "abs_delta_min": float(abs_deltas.min()) if abs_deltas.size else None,
            "abs_delta_median": float(np.median(abs_deltas)) if abs_deltas.size else None,
            "abs_delta_p90": float(np.percentile(abs_deltas, 90)) if abs_deltas.size else None,
            "abs_delta_max": float(abs_deltas.max()) if abs_deltas.size else None,
            "rel_delta_max": float(rel_deltas.max()) if rel_deltas.size else None,
        }
    return summary


def _summarize_repeatability(repeat_records: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    summary = {}
    for row_key, recs in repeat_records.items():
        abs_deltas = [r["abs_delta"] for r in recs if r.get("abs_delta") is not None]
        rel_deltas = [r["rel_delta"] for r in recs if r.get("rel_delta") is not None]
        readbacks = [r["readback_measured"] for r in recs if r.get("readback_measured") is not None]
        spread = (max(abs_deltas) - min(abs_deltas)) if abs_deltas else None
        summary[row_key] = {
            "abs_deltas": abs_deltas,
            "rel_deltas": rel_deltas,
            "readback_measured_values": readbacks,
            "abs_delta_spread": spread,
            "deterministic": (spread is not None and spread < DETERMINISM_ABS_SPREAD_THRESHOLD),
            "all_passed": all(r.get("passed") for r in recs),
            "any_passed": any(r.get("passed") for r in recs),
        }
    return summary


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--family", choices=config.FAMILIES, help="default: run both families")
    ap.add_argument("--i-know-this-runs-on-gpu", action="store_true", required=True)
    args = ap.parse_args()

    families = [args.family] if args.family else list(config.FAMILIES)

    DIAG_DIR.mkdir(parents=True, exist_ok=True)
    # Fresh rows.jsonl each invocation (this is a new diagnostic dir, not a
    # governed/resumable RunLog; re-running this script is expected to
    # re-dose from scratch).
    if ROWS_JSONL.is_file():
        ROWS_JSONL.unlink()

    report: dict[str, Any] = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "purpose": "M1 SC1 preflight bottom-rung (0.0625x) readback FAIL diagnostic -- diagnostic data only, no governed file touched",
        "repeat_rung": REPEAT_RUNG,
        "n_repeats": N_REPEATS,
        "breadth_rungs": list(BREADTH_RUNGS),
        "n_breadth_rows": N_BREADTH_ROWS,
        "determinism_abs_spread_threshold": DETERMINISM_ABS_SPREAD_THRESHOLD,
        "families": {},
    }

    for family in families:
        fam_results = run_family(family)
        report["families"][family] = {
            "preflight_row_keys": PREFLIGHT_ROW_KEYS[family],
            "originally_failing_row": FAILING_ROW[family],
            "repeatability_raw": fam_results["repeatability"],
            "repeatability_summary": _summarize_repeatability(fam_results["repeatability"]),
            "breadth_raw": fam_results["breadth"],
            "breadth_summary": _summarize_breadth(fam_results["breadth"]),
        }
        common.write_json(REPORT_PATH, report)  # write incrementally after each family

    # -------------------- SUMMARY.txt --------------------
    lines = [
        "M1 SC1 preflight bottom-rung (0.0625x) readback FAIL -- diagnostic summary",
        f"generated_at: {report['generated_at']}",
        "",
    ]
    for family in families:
        fam = report["families"][family]
        lines.append(f"== {family} ==")
        lines.append(f"originally failing row: {fam['originally_failing_row']}")
        lines.append("-- repeatability (0.0625x, 3 repeats, 4 preflight rows) --")
        for row_key, s in fam["repeatability_summary"].items():
            flag = "FAILING-ROW" if row_key == fam["originally_failing_row"] else ""
            lines.append(
                f"  {row_key} {flag}: abs_deltas={['%.6g' % d for d in s['abs_deltas']]} "
                f"spread={s['abs_delta_spread']:.3g} deterministic={s['deterministic']} "
                f"all_passed={s['all_passed']}"
            )
        lines.append("-- breadth (12 rows, once each) --")
        for rung in BREADTH_RUNGS:
            b = fam["breadth_summary"][str(rung)]
            lines.append(
                f"  {rung}x: n={b['n']} n_fail={b['n_fail_rel_0.005']} frac_fail={b['frac_fail']:.3f} "
                f"abs_delta[min/median/p90/max]={b['abs_delta_min']:.6g}/{b['abs_delta_median']:.6g}/"
                f"{b['abs_delta_p90']:.6g}/{b['abs_delta_max']:.6g} rel_delta_max={b['rel_delta_max']:.6g}"
            )
        lines.append("")

    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"[diag] wrote {REPORT_PATH}", flush=True)
    print(f"[diag] wrote {SUMMARY_PATH}", flush=True)
    print(f"[diag] wrote {ROWS_JSONL}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
