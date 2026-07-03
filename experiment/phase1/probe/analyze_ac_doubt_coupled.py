"""Amendment AC analysis: selectivity gaps, AC-G1/AC-G2, specificity guard, dose-response.

SPEC: experiment/protocol/AMENDMENT-AC-doubt-regulated-caution.md §4-§5.

Definitions (pre-registered):
- de-refusal(arm, cell) = refusal_rate(baseline, cell) - refusal_rate(arm, cell)
- selectivity gap(arm)  = de-refusal(arm, known_refused) - de-refusal(arm, unknown_refused)
- AC-G1 (pass/fail): gap(coupled) - gap(permuted) >= 5pt AND row-level bootstrap
  95% CI (10k resamples) excludes 0.
- AC-G2 (estimate only, no pass/fail): gap(coupled) - gap(ablate), and
  per-de-refused correctness per arm, with CIs.
- Specificity guard (pass/fail, coupled arm): known_correct_answered refusal
  rise <= 5pt and correctness drop <= 3pt vs baseline.
- Dose-response (descriptive, coupled arm only): refusal rate vs written gain,
  binned g_i.

Bootstrap is row-level and PAIRED across arms: every row appears in all four
arms, so we resample row keys within each cell and recompute all arm rates on
the same resampled keys.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

KR, KA, UR = "known_refused", "known_correct_answered", "unknown_refused"
ARMS = ("baseline", "coupled", "permuted", "ablate")
INTERVENTIONAL = ("coupled", "permuted", "ablate")


class ACAnalysisError(RuntimeError):
    pass


def load_rows(path: Path) -> dict[str, dict[str, dict]]:
    """rows[cell][row_key][arm_id] -> record."""
    by_cell: dict[str, dict[str, dict]] = defaultdict(lambda: defaultdict(dict))
    with path.open(encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            by_cell[r["behavior_cell"]][r["probe_pool_row_key"]][r["arm_id"]] = r
    for cell, rows in by_cell.items():
        for key, arms in rows.items():
            missing = [a for a in ARMS if a not in arms]
            if missing:
                raise ACAnalysisError(f"row {key} ({cell}) missing arms: {missing}")
    return {c: dict(v) for c, v in by_cell.items()}


def _rate(rows: dict[str, dict], keys: list[str], arm: str, field: str) -> float:
    return float(np.mean([bool(rows[k][arm][field]) for k in keys]))


def selectivity_gaps(by_cell, kr_keys, ur_keys) -> dict[str, float]:
    base_kr = _rate(by_cell[KR], kr_keys, "baseline", "refused")
    base_ur = _rate(by_cell[UR], ur_keys, "baseline", "refused")
    gaps = {}
    for arm in INTERVENTIONAL:
        de_kr = base_kr - _rate(by_cell[KR], kr_keys, arm, "refused")
        de_ur = base_ur - _rate(by_cell[UR], ur_keys, arm, "refused")
        gaps[arm] = de_kr - de_ur
    return gaps


def bootstrap_gap_diff(by_cell, arm_a: str, arm_b: str, n_boot: int, seed: int):
    """CI for gap(arm_a) - gap(arm_b), resampling row keys within each cell."""
    rng = np.random.default_rng(seed)
    kr_keys = sorted(by_cell[KR])
    ur_keys = sorted(by_cell[UR])
    diffs = np.empty(n_boot)
    for i in range(n_boot):
        kr_s = [kr_keys[j] for j in rng.integers(0, len(kr_keys), len(kr_keys))]
        ur_s = [ur_keys[j] for j in rng.integers(0, len(ur_keys), len(ur_keys))]
        g = selectivity_gaps(by_cell, kr_s, ur_s)
        diffs[i] = g[arm_a] - g[arm_b]
    lo, hi = np.percentile(diffs, [2.5, 97.5])
    return float(lo), float(hi)


def de_refused_correctness(by_cell, arm: str, n_boot: int, seed: int):
    """Among known_refused rows the arm answered, fraction correct (+ CI)."""
    rows = by_cell[KR]
    answered = [k for k in sorted(rows) if not rows[k][arm]["refused"]]
    if not answered:
        return {"n_de_refused": 0, "correct_rate": None, "ci95": None}
    vals = np.array([bool(rows[k][arm]["correct"]) for k in answered], dtype=float)
    rng = np.random.default_rng(seed)
    boots = [float(np.mean(vals[rng.integers(0, len(vals), len(vals))]))
             for _ in range(n_boot)]
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return {"n_de_refused": len(answered), "correct_rate": float(np.mean(vals)),
            "ci95": [float(lo), float(hi)]}


def dose_response(by_cell, gain_map: dict, bin_edges: list[float]):
    """Coupled-arm refusal rate binned by written gain g_i (descriptive)."""
    out = []
    pooled = [(k, r["coupled"]) for cell in (KR, KA, UR) if cell in by_cell
              for k, r in by_cell[cell].items()]
    gains = {}
    for k, rec in pooled:
        if k not in gain_map:
            raise ACAnalysisError(f"row {k} missing from gain map")
        gains[k] = gain_map[k]["gain"]
    for lo, hi in zip(bin_edges[:-1], bin_edges[1:]):
        keys = [k for k, _ in pooled if lo <= gains[k] < hi]
        if not keys:
            out.append({"bin": [lo, hi], "n": 0, "refusal_rate": None})
            continue
        rate = float(np.mean([bool(dict(pooled)[k]["refused"]) for k in keys]))
        out.append({"bin": [lo, hi], "n": len(keys), "refusal_rate": rate})
    return out


def analyze(rows_path: Path, gain_map_path: Path, n_boot: int, seed: int) -> dict:
    by_cell = load_rows(rows_path)
    for cell in (KR, KA, UR):
        if cell not in by_cell:
            raise ACAnalysisError(f"missing cell {cell}")
    gain_map = json.loads(gain_map_path.read_text(encoding="utf-8"))["gains"]

    table = {
        arm: {cell: {
            "n": len(by_cell[cell]),
            "refusal_rate": _rate(by_cell[cell], sorted(by_cell[cell]), arm, "refused"),
            "correct_rate": _rate(by_cell[cell], sorted(by_cell[cell]), arm, "correct"),
        } for cell in (KR, KA, UR)}
        for arm in ARMS
    }

    kr_keys, ur_keys = sorted(by_cell[KR]), sorted(by_cell[UR])
    gaps = selectivity_gaps(by_cell, kr_keys, ur_keys)

    g1_margin = gaps["coupled"] - gaps["permuted"]
    g1_lo, g1_hi = bootstrap_gap_diff(by_cell, "coupled", "permuted", n_boot, seed)
    g1_pass = bool(g1_margin >= 0.05 and g1_lo > 0)

    g2_margin = gaps["coupled"] - gaps["ablate"]
    g2_lo, g2_hi = bootstrap_gap_diff(by_cell, "coupled", "ablate", n_boot, seed + 1)

    base_ka_ref = table["baseline"][KA]["refusal_rate"]
    base_ka_cor = table["baseline"][KA]["correct_rate"]
    ref_rise = table["coupled"][KA]["refusal_rate"] - base_ka_ref
    cor_drop = base_ka_cor - table["coupled"][KA]["correct_rate"]
    guard_pass = bool(ref_rise <= 0.05 and cor_drop <= 0.03)

    correctness = {arm: de_refused_correctness(by_cell, arm, n_boot, seed + 2)
                   for arm in INTERVENTIONAL}

    edges = [-2.0, -1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.01]
    dose = dose_response(by_cell, gain_map, edges)

    falsifier_fired = not g1_pass
    return {
        "table": table,
        "selectivity_gaps": gaps,
        "ac_g1": {"margin": g1_margin, "ci95": [g1_lo, g1_hi],
                  "threshold": 0.05, "pass": g1_pass},
        "ac_g2_estimate_only": {"margin_vs_ablate": g2_margin, "ci95": [g2_lo, g2_hi]},
        "specificity_guard": {"ka_refusal_rise": ref_rise, "ka_correct_drop": cor_drop,
                              "pass": guard_pass},
        "de_refused_correctness_known_refused": correctness,
        "dose_response_coupled": dose,
        "falsifier_fired": falsifier_fired,
        "n_boot": n_boot,
        "bootstrap_seed": seed,
        "rows_file": str(rows_path),
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--rows", required=True, type=Path)
    p.add_argument("--gain-map", required=True, type=Path)
    p.add_argument("--n-boot", type=int, default=10_000)
    p.add_argument("--seed", type=int, default=20260703)
    p.add_argument("--out", type=Path, default=None)
    a = p.parse_args(argv)
    try:
        result = analyze(a.rows, a.gain_map, a.n_boot, a.seed)
    except ACAnalysisError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    text = json.dumps(result, indent=2, sort_keys=True)
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
