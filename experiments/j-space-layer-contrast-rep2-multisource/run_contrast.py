#!/usr/bin/env python3
"""Ceiling-robust multi-source replication of the calibrated J-space layer
contrast.

This is rep2 of `j-space-layer-contrast-replication-qwen3-4b` (rep1). Rep1
registered a G1 fail on a ceiling-saturated, single-source fresh pool (hs34
itself reached 94.12% clean_tighten, leaving only 5.9pp of arithmetic
headroom against the registered +10pp bar). Its Outcome's "Consequences
carried forward" (b) mandated that a successor replace the fixed point-
estimate G1 bar with a ceiling-robust contrast (CI separation plus a
failure-ratio measure) and mine a multi-source confab pool hard enough to
keep the reference arm off the ceiling. This script implements that
contrast (G1' McNemar paired test) over the multi-source pool mined by
`mine_multisource_pool.py`.

Directions, gates, and calibrated doses are frozen exactly as rep1 froze
them (from `j-space-midband-write-sweep-qwen3-4b` and
`j-space-midband-dose-calibration-qwen3-4b`). The known_correct_answered
side is not regenerated: it is rep1's own 1,957 rows and anchors, reused
verbatim via `materialize_known_side_reuse.py`. Per-row outcomes are
persisted through the tuner's RunLog (see `pipeline_multisource.py`); a
crash mid-arm loses at most the in-flight row.
"""

from __future__ import annotations

import argparse
import json
import random as pyrandom
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "j-space-midband-write-sweep-qwen3-4b"
CALIBRATION = HERE.parent / "j-space-midband-dose-calibration-qwen3-4b"
ANALYSIS = HERE / "analysis"
COMMITTED = HERE / "analysis-committed"

for p in (str(SOURCE), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

# `layers` is pure stdlib (no torch/MechInterp): safe to import at module
# level so lightweight, GPU-free consumers (e.g. analyze_paired_outcomes.py)
# can `from run_contrast import mcnemar_exact, paired_confab_outcomes`
# without pulling in torch. `model_lib` / `pipeline_multisource` (both
# torch+MechInterp dependent) are imported lazily inside `run_layers`, the
# only function that actually needs them.
from layers import HS_INDICES, LATE_REFERENCE_HS, layer_dir_name  # noqa: E402

FRESH_CONFAB_ROWS = ANALYSIS / "multisource_confab_rows.jsonl"
FRESH_CONFAB_TENSORS = ANALYSIS / "multisource_confab_anchor_extract.safetensors"
KNOWN_REUSED_ROWS = ANALYSIS / "known_correct_answered_reused.jsonl"
KNOWN_REUSED_TENSORS = ANALYSIS / "known_correct_answered_anchor_reused.safetensors"

EXPECTED_SELECTED_DOSES = {
    "hs23": 25.0,
    "hs26": 75.0,
    "hs29": 125.0,
    "hs34": 175.0,
}
G3_LOWER_FLOOR = 0.40
G3_UPPER_CEILING_GUARD = 0.90
G1_FAILURE_RATIO_MIN = 3.0
ALPHA = 0.05


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.open(encoding="utf-8") if line.strip()]


def load_selected_doses() -> dict[str, float]:
    path = CALIBRATION / "analysis-committed" / "dose_calibration_summary.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    selected = {str(k): float(v) for k, v in data["selected_doses"].items()}
    if selected != EXPECTED_SELECTED_DOSES:
        raise ValueError(
            "calibration selected_doses drifted; expected "
            f"{EXPECTED_SELECTED_DOSES}, got {selected}"
        )
    if not data.get("all_layers_have_usable_dose"):
        raise ValueError("calibration summary says not all layers have usable doses")
    if not data.get("collapsed_at_200_recovered"):
        raise ValueError("calibration summary says dose-200 collapse was not recovered")
    return selected


def selected_rows(n_rows: int | None) -> list[dict]:
    import pipeline_multisource as pms

    confab = load_jsonl(FRESH_CONFAB_ROWS)
    known = load_jsonl(KNOWN_REUSED_ROWS)
    if n_rows is None:
        return confab + known
    n_confab = n_rows // 2
    n_known = n_rows - n_confab
    return (
        pms.stratified_subset(confab, n_confab)
        + pms.stratified_subset(known, n_known)
    )


def run_layers(rows: list[dict], selected_doses: dict[str, float], *, mode: str, fresh: bool) -> dict[str, dict]:
    import gc

    import torch
    import pipeline_multisource as pms
    from model_lib import load_model

    tensors = pms.load_tensors([FRESH_CONFAB_TENSORS, KNOWN_REUSED_TENSORS])
    RunLog, _RunLogError = pms.load_run_log_class()
    model, tokenizer = load_model()
    try:
        layer_results: dict[str, dict] = {}
        for hs_index in HS_INDICES:
            layer_name = layer_dir_name(hs_index)
            dose = selected_doses[layer_name]
            print(f"[contrast] layer={layer_name} dose={dose}", flush=True)
            gate_rows = pms.compute_gate_decisions(rows, hs_index, tensors)
            log_path = ANALYSIS / "runlog" / mode / f"{layer_name}.jsonl"
            run_log = RunLog(
                log_path,
                run_config={
                    "experiment": "j-space-layer-contrast-rep2-multisource",
                    "mode": mode,
                    "layer": layer_name,
                    "hs_index": hs_index,
                    "dose_target": dose,
                },
                fresh=fresh,
            )
            try:
                rec = pms.run_layer(model, tokenizer, hs_index, gate_rows, dose, run_log=run_log)
            finally:
                run_log.close()
            rec["dose_target"] = dose
            layer_results[layer_name] = rec
    finally:
        del model
        gc.collect()
        torch.cuda.empty_cache()
    return layer_results


def mcnemar_exact(n01: int, n10: int) -> float:
    """Exact two-sided binomial McNemar test p-value on the discordant
    pairs. n01 = late-only-failure count (mid succeeds, late fails); n10 =
    mid-only-failure count (mid fails, late succeeds). Tries scipy first;
    falls back to a pure-Python exact binomial tail sum (no new hard
    dependency if scipy is unavailable on a given lane)."""
    n = n01 + n10
    if n == 0:
        return 1.0
    try:
        from scipy.stats import binomtest
        return float(binomtest(n01, n, p=0.5, alternative="two-sided").pvalue)
    except ImportError:
        pass
    from math import comb
    k = min(n01, n10)
    tail = sum(comb(n, i) for i in range(0, k + 1)) * (0.5 ** n)
    p = min(1.0, 2.0 * tail)
    return p


def paired_confab_outcomes(mid_records: list[dict], late_records: list[dict]) -> dict:
    mid_by_key = {r["row_key"]: r["clean_tighten"] for r in mid_records if r["role"] == "confab"}
    late_by_key = {r["row_key"]: r["clean_tighten"] for r in late_records if r["role"] == "confab"}
    common = sorted(set(mid_by_key) & set(late_by_key))
    n11 = sum(1 for k in common if mid_by_key[k] and late_by_key[k])
    n01 = sum(1 for k in common if mid_by_key[k] and not late_by_key[k])  # late-only-failure
    n10 = sum(1 for k in common if (not mid_by_key[k]) and late_by_key[k])  # mid-only-failure
    n00 = sum(1 for k in common if (not mid_by_key[k]) and (not late_by_key[k]))
    return {
        "n_paired": len(common),
        "both_tighten": n11,
        "late_only_failure": n01,
        "mid_only_failure": n10,
        "neither_tighten": n00,
        "failure_ratio_late_over_mid": (n01 / n10) if n10 > 0 else (float("inf") if n01 > 0 else None),
        "mcnemar_exact_p": mcnemar_exact(n01, n10),
    }


def evaluate_layer_contrast(layer_results: dict[str, dict]) -> dict:
    late_name = layer_dir_name(LATE_REFERENCE_HS)
    late = layer_results[late_name]
    mid_names = [layer_dir_name(h) for h in HS_INDICES if h != LATE_REFERENCE_HS]
    # Best-mid selection by tighten rate ONLY (pre-stated; the same selected
    # arm is then used for both G1' and G2', no re-selection after seeing
    # the paired outcomes).
    best_mid_name = max(mid_names, key=lambda name: layer_results[name]["confab_tighten"]["rate"])
    best_mid = layer_results[best_mid_name]

    pairing = paired_confab_outcomes(best_mid["records"], late["records"])
    g1_ratio_pass = (
        pairing["mid_only_failure"] == 0
        or pairing["failure_ratio_late_over_mid"] >= G1_FAILURE_RATIO_MIN
    ) and pairing["late_only_failure"] > 0
    g1_p_pass = pairing["mcnemar_exact_p"] < ALPHA
    g1_pass = bool(g1_ratio_pass and g1_p_pass)

    tighten_delta = best_mid["confab_tighten"]["rate"] - late["confab_tighten"]["rate"]
    cost_delta = (
        best_mid["known_correct_cost_control"]["rate"]
        - late["known_correct_cost_control"]["rate"]
    )
    cost_per_tighten_win = (
        cost_delta / pairing["late_only_failure"] if pairing["late_only_failure"] else None
    )
    g2_pass = cost_delta <= 0.02

    late_rate = late["confab_tighten"]["rate"]
    late_ci_lo, late_ci_hi = late["confab_tighten"]["wilson_ci_95"]
    # Locked gate: hs34 confab clean_tighten must land in [40%, 90%].
    # Above 90% -> uninterpretable for magnitude (direction-only reading).
    # Below 40% -> reference-viability failure, as in rep1's G3.
    if late_rate > G3_UPPER_CEILING_GUARD:
        g3_status = "ceiling_uninterpretable_for_magnitude"
    elif late_rate < G3_LOWER_FLOOR:
        g3_status = "reference_viability_failure"
    else:
        g3_status = "viable"
    g3_pass = g3_status == "viable"

    return {
        "best_mid_layer": best_mid_name,
        "late_reference_layer": late_name,
        "tighten_delta_best_mid_minus_late": tighten_delta,
        "cost_delta_best_mid_minus_late": cost_delta,
        "cost_per_late_only_failure_won": cost_per_tighten_win,
        "paired_outcomes": pairing,
        "g1_prime_ratio_component_pass": bool(g1_ratio_pass),
        "g1_prime_pvalue_component_pass": bool(g1_p_pass),
        "g1_prime_pass": g1_pass,
        "g2_prime_pass": bool(g2_pass),
        "g3_prime_status": g3_status,
        "g3_prime_pass": bool(g3_pass),
        "late_confab_tighten_rate": late_rate,
        "late_confab_tighten_wilson_ci_95": [late_ci_lo, late_ci_hi],
    }


def instrument_pass(layer_results: dict[str, dict]) -> bool:
    for rec in layer_results.values():
        if rec["frac_readback_within_tol"] != 1.0:
            return False
        if rec["collapse_rate_on_dosed"] != 0.0:
            return False
    return True


def strip_records_for_summary(layer_results: dict[str, dict]) -> dict[str, dict]:
    """The committed summary must not carry per-row text; `records` here
    only ever carries grading booleans/floats/row_key/source, never question
    text or raw generations, but we still drop it from the aggregate summary
    to keep the committed artifact small and unambiguous -- per-row detail
    lives in the RunLog files under analysis/runlog/, not in analysis-committed/."""
    out = {}
    for name, rec in layer_results.items():
        out[name] = {k: v for k, v in rec.items() if k != "records"}
    return out


def write_summary(name: str, summary: dict, commit_public: bool) -> None:
    ANALYSIS.mkdir(parents=True, exist_ok=True)
    (ANALYSIS / name).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    if commit_public:
        COMMITTED.mkdir(parents=True, exist_ok=True)
        (COMMITTED / name).write_text(json.dumps(summary, indent=2), encoding="utf-8")


def pool_counts() -> dict:
    confab = load_jsonl(FRESH_CONFAB_ROWS)
    known = load_jsonl(KNOWN_REUSED_ROWS)
    return {"confab": len(confab), "known_correct_answered": len(known), "total": len(confab) + len(known)}


def run_smoke(n_rows: int, fresh: bool) -> dict:
    selected_doses = load_selected_doses()
    rows = selected_rows(n_rows)
    layer_results = run_layers(rows, selected_doses, mode="smoke", fresh=fresh)
    summary = {
        "mode": "smoke",
        "selected_doses": selected_doses,
        "pool_counts": pool_counts(),
        "n_rows": len(rows),
        "layers": strip_records_for_summary(layer_results),
        "g0_smoke_pass": instrument_pass(layer_results),
    }
    write_summary("smoke_summary.json", summary, commit_public=False)
    print(json.dumps(summary, indent=2))
    return summary


def run_full(fresh: bool) -> dict:
    selected_doses = load_selected_doses()
    rows = selected_rows(None)
    rng = pyrandom.Random(20260709)
    rng.shuffle(rows)
    layer_results = run_layers(rows, selected_doses, mode="full", fresh=fresh)
    contrast = evaluate_layer_contrast(layer_results)
    summary = {
        "mode": "full",
        "selected_doses": selected_doses,
        "pool_counts": pool_counts(),
        "n_rows": len(rows),
        "layers": strip_records_for_summary(layer_results),
        "layer_contrast": contrast,
        "instrument_pass": instrument_pass(layer_results),
        "overall_pass": bool(
            instrument_pass(layer_results)
            and contrast["g1_prime_pass"]
            and contrast["g2_prime_pass"]
            and contrast["g3_prime_pass"]
        ),
    }
    write_summary("full_summary.json", summary, commit_public=True)
    print(json.dumps(summary, indent=2))
    return summary


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["smoke", "full"], required=True)
    parser.add_argument("--n-rows", type=int, default=8, help="smoke mode only")
    parser.add_argument(
        "--fresh", action="store_true",
        help="Discard any existing RunLog for this mode's layers and start over.",
    )
    parser.add_argument("--i-know-this-is-the-multisource-replication-run", action="store_true")
    args = parser.parse_args(argv)

    if args.mode == "smoke":
        return 0 if run_smoke(args.n_rows, args.fresh)["g0_smoke_pass"] else 4

    if not args.i_know_this_is_the_multisource_replication_run:
        print(
            "[contrast] full mode is the signed multi-source replication run; "
            "refusing without --i-know-this-is-the-multisource-replication-run",
            file=sys.stderr,
        )
        return 2
    run_full(args.fresh)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
