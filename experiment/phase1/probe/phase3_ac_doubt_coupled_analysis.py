#!/usr/bin/env python3
"""Amendment AC — CPU analysis: does the doubt->caution coupling carry
information beyond deleting the gate?

SPEC: experiment/protocol/AMENDMENT-AC-doubt-regulated-caution.md §4/§5.

Reads the intervention runner's rows.jsonl (arms x rows, paired by
probe_pool_row_key) and computes:

- per (arm, cell): n, refusal_rate, correct_rate
- per interventional arm: de-refusal vs the baseline arm per cell, and the
  SELECTIVITY GAP := de_refusal(known_refused) - de_refusal(unknown_refused)
- AC-G1 (primary): coupled - permuted on the selectivity gap, paired
  row-level bootstrap CI (resample row keys within each cell); pass =
  margin >= +0.05 and 95% CI excluding 0
- AC-G2 (estimate only, NO pass/fail): coupled - ablate on the same gap +
  per-de-refused correctness, with CIs
- specificity guard on the coupled arm: known_correct_answered refusal rise
  <= 0.05 and correctness drop <= 0.03 vs baseline
- descriptive dose curve: refusal vs written gain (binned), coupled arm

Verdict: PASS / FALSIFIER-FIRED / INCONCLUSIVE per the pre-stated gates.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

KR = "known_refused"
KA = "known_correct_answered"
UR = "unknown_refused"

BASELINE = "baseline"
COUPLED = "coupled"
PERMUTED = "permuted"
ABLATE = "ablate"

G1_MARGIN = 0.05
SPEC_REFUSAL_RISE_TOL = 0.05
SPEC_CORRECT_DROP_TOL = 0.03
N_BOOT = 10_000
BOOT_SEED = 20260702


def _index(rows: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, Any]]]:
    """arm_id -> row_key -> record."""
    out: dict[str, dict[str, dict[str, Any]]] = {}
    for r in rows:
        out.setdefault(r["arm_id"], {})[r["probe_pool_row_key"]] = r
    return out


def _cell_keys(rows: list[dict[str, Any]], cell: str) -> list[str]:
    return sorted({r["probe_pool_row_key"] for r in rows
                   if r.get("behavior_cell") == cell})


def _refusal(by_arm: dict[str, dict[str, dict[str, Any]]], arm: str,
             keys: list[str]) -> float:
    vals = [bool(by_arm[arm][k].get("refused")) for k in keys if k in by_arm.get(arm, {})]
    return float(np.mean(vals)) if vals else float("nan")


def selectivity_gap(by_arm: dict[str, dict[str, dict[str, Any]]], arm: str,
                    kr_keys: list[str], ur_keys: list[str]) -> float:
    """de_refusal(kr) - de_refusal(ur) vs the baseline arm, on the given keys."""
    de_kr = _refusal(by_arm, BASELINE, kr_keys) - _refusal(by_arm, arm, kr_keys)
    de_ur = _refusal(by_arm, BASELINE, ur_keys) - _refusal(by_arm, arm, ur_keys)
    return de_kr - de_ur


def bootstrap_gap_diff(by_arm: dict[str, dict[str, dict[str, Any]]],
                       arm_a: str, arm_b: str,
                       kr_keys: list[str], ur_keys: list[str], *,
                       n_boot: int = N_BOOT, seed: int = BOOT_SEED) -> dict[str, float]:
    """Paired row-level bootstrap of selectivity_gap(arm_a) - selectivity_gap(arm_b).

    Rows are shared across arms, so resampling row KEYS within each cell keeps
    the pairing intact.
    """
    rng = np.random.default_rng(seed)
    kr = np.asarray(kr_keys)
    ur = np.asarray(ur_keys)
    point = (selectivity_gap(by_arm, arm_a, kr_keys, ur_keys)
             - selectivity_gap(by_arm, arm_b, kr_keys, ur_keys))
    boots = np.empty(n_boot)
    for i in range(n_boot):
        skr = list(rng.choice(kr, size=len(kr), replace=True))
        sur = list(rng.choice(ur, size=len(ur), replace=True))
        boots[i] = (selectivity_gap(by_arm, arm_a, skr, sur)
                    - selectivity_gap(by_arm, arm_b, skr, sur))
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return {"point": float(point), "ci_lo": float(lo), "ci_hi": float(hi)}


def de_refused_correctness(by_arm: dict[str, dict[str, dict[str, Any]]], arm: str,
                           kr_keys: list[str]) -> dict[str, float]:
    """Among known_refused rows that the arm de-refused (baseline refused,
    arm answered): fraction correct."""
    de = [k for k in kr_keys
          if bool(by_arm[BASELINE][k].get("refused"))
          and not bool(by_arm[arm][k].get("refused"))]
    corr = [bool(by_arm[arm][k].get("correct")) for k in de]
    return {"n_de_refused": len(de),
            "correct_rate": float(np.mean(corr)) if corr else float("nan")}


def dose_curve(by_arm: dict[str, dict[str, dict[str, Any]]], arm: str,
               *, n_bins: int = 5) -> list[dict[str, float]]:
    recs = list(by_arm.get(arm, {}).values())
    gains = np.asarray([float(r.get("arm_alpha", 0.0)) for r in recs])
    refused = np.asarray([bool(r.get("refused")) for r in recs])
    if not len(recs):
        return []
    edges = np.quantile(gains, np.linspace(0, 1, n_bins + 1))
    out = []
    for i in range(n_bins):
        m = (gains >= edges[i]) & (gains <= edges[i + 1] if i == n_bins - 1
                                   else gains < edges[i + 1])
        if m.sum():
            out.append({"gain_lo": float(edges[i]), "gain_hi": float(edges[i + 1]),
                        "n": int(m.sum()), "refusal_rate": float(refused[m].mean())})
    return out


def analyze(rows: list[dict[str, Any]], *, n_boot: int = N_BOOT,
            g1_margin: float = G1_MARGIN) -> dict[str, Any]:
    by_arm = _index(rows)
    for arm in (BASELINE, COUPLED, PERMUTED):
        if arm not in by_arm:
            raise ValueError(f"required arm {arm!r} missing from rows")
    kr_keys = _cell_keys(rows, KR)
    ur_keys = _cell_keys(rows, UR)
    ka_keys = _cell_keys(rows, KA)
    if not kr_keys or not ur_keys:
        raise ValueError("need known_refused AND unknown_refused rows for the selectivity gap")

    table: dict[str, Any] = {}
    for arm in sorted(by_arm):
        table[arm] = {}
        for cell, keys in ((KR, kr_keys), (KA, ka_keys), (UR, ur_keys)):
            vals = [by_arm[arm][k] for k in keys if k in by_arm[arm]]
            table[arm][cell] = {
                "n": len(vals),
                "refusal_rate": round(float(np.mean([bool(v.get("refused")) for v in vals])), 4) if vals else None,
                "correct_rate": round(float(np.mean([bool(v.get("correct")) for v in vals])), 4) if vals else None,
            }

    gaps = {arm: round(selectivity_gap(by_arm, arm, kr_keys, ur_keys), 4)
            for arm in sorted(by_arm) if arm != BASELINE}

    g1 = bootstrap_gap_diff(by_arm, COUPLED, PERMUTED, kr_keys, ur_keys, n_boot=n_boot)
    g1_pass = g1["point"] >= g1_margin and g1["ci_lo"] > 0.0

    g2 = None
    if ABLATE in by_arm:
        g2 = {
            "gap_diff": bootstrap_gap_diff(by_arm, COUPLED, ABLATE, kr_keys, ur_keys, n_boot=n_boot),
            "de_refused_correctness": {
                COUPLED: de_refused_correctness(by_arm, COUPLED, kr_keys),
                ABLATE: de_refused_correctness(by_arm, ABLATE, kr_keys),
            },
            "note": "estimate only; ~0 pre-stated as EXPECTED (no pass/fail)",
        }

    base_ka_ref = _refusal(by_arm, BASELINE, ka_keys) if ka_keys else float("nan")
    coup_ka_ref = _refusal(by_arm, COUPLED, ka_keys) if ka_keys else float("nan")
    base_ka_corr = float(np.mean([bool(by_arm[BASELINE][k].get("correct")) for k in ka_keys])) if ka_keys else float("nan")
    coup_ka_corr = float(np.mean([bool(by_arm[COUPLED][k].get("correct")) for k in ka_keys])) if ka_keys else float("nan")
    spec_pass = ((coup_ka_ref - base_ka_ref) <= SPEC_REFUSAL_RISE_TOL
                 and (base_ka_corr - coup_ka_corr) <= SPEC_CORRECT_DROP_TOL) if ka_keys else None

    if g1_pass and spec_pass:
        verdict = (f"AC-G1 PASS: coupled beats permuted on the selectivity gap by "
                   f"{g1['point']:+.3f} (CI [{g1['ci_lo']:+.3f}, {g1['ci_hi']:+.3f}] excludes 0); "
                   f"specificity guard PASS. The doubt wire carries information.")
    elif g1_pass and spec_pass is False:
        verdict = (f"INCONCLUSIVE: AC-G1 margin {g1['point']:+.3f} passes but the coupled arm "
                   f"violates the specificity guard on known_correct_answered.")
    else:
        verdict = (f"FALSIFIER-FIRED: coupled - permuted selectivity margin {g1['point']:+.3f} "
                   f"(CI [{g1['ci_lo']:+.3f}, {g1['ci_hi']:+.3f}]) does not clear "
                   f"+{g1_margin:.2f} with CI excluding 0. The doubt readout adds nothing "
                   f"at this intervention site; report negative, no rescue runs (per §4).")

    return {
        "ok": True,
        "analysis_type": "phase3_ac_doubt_coupled",
        "n_rows": len(rows),
        "cells": {"known_refused": len(kr_keys), "known_correct_answered": len(ka_keys),
                  "unknown_refused": len(ur_keys)},
        "by_arm": table,
        "selectivity_gaps": gaps,
        "ac_g1": {**g1, "margin_required": g1_margin, "pass": bool(g1_pass)},
        "ac_g2": g2,
        "specificity_guard": {
            "ka_refusal_rise": round(coup_ka_ref - base_ka_ref, 4) if ka_keys else None,
            "ka_correct_drop": round(base_ka_corr - coup_ka_corr, 4) if ka_keys else None,
            "pass": spec_pass,
        },
        "dose_curve_coupled": dose_curve(by_arm, COUPLED),
        "verdict": verdict,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rows", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--n-boot", type=int, default=N_BOOT)
    args = ap.parse_args(argv)
    rows = [json.loads(l) for l in args.rows.open(encoding="utf-8") if l.strip()]
    summary = analyze(rows, n_boot=args.n_boot)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"VERDICT: {summary['verdict']}", file=sys.stderr)
    print(json.dumps({k: summary[k] for k in ("selectivity_gaps", "ac_g1", "specificity_guard")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
