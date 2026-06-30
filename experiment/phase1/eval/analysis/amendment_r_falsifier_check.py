#!/usr/bin/env python3
"""Amendment R (Phase B) falsifier check — A1 vs A2 (placebo) and A1 vs A0.

GPU-free. Reads the three per-arm calibration_gap_report.py outputs (the JSON each
`--out` writes) and evaluates the LOCKED falsifier on the non-circular primary
metric `A_full_eval.auroc_emitted_to_appropriateness`.

Locked falsifier (run records aux_a1/a2 + AMENDMENT-R §4, 2026-06-29):
  PRIMARY  : A1 emitted-scalar AUROC-to-appropriateness must exceed A2 (placebo)
             by >= +0.05. If (A1 - A2) < 0.05 the treatment claim is FALSIFIED.
  SECONDARY: §4 also requires A1 to improve over the A0 (LM-only) reference, i.e.
             A1 > A0. Reported, but the locked PASS/FAIL gate is the A1-vs-A2 margin.

The margin (+0.05) is the pre-stated candidate, confirmed (not moved) after the
faithful-token gate went GREEN. Do not edit it here to fit a result.

Usage:
  python experiment/phase1/eval/analysis/amendment_r_falsifier_check.py \
    --a0 <calibration_gap_a0.json> \
    --a1 <calibration_gap_a1.json> \
    --a2 <calibration_gap_a2.json> \
    [--margin 0.05] [--out <verdict.json>]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

METRIC = "auroc_emitted_to_appropriateness"
SECTION = "A_full_eval"


def _read_auroc(path: Path) -> float:
    report = json.loads(path.read_text())
    section = report.get(SECTION)
    if not isinstance(section, dict) or METRIC not in section:
        raise SystemExit(
            f"{path}: missing {SECTION}.{METRIC} (got keys: {list(report)})")
    return float(section[METRIC])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--a0", type=Path, required=True,
                    help="calibration_gap report JSON for A0 (LM-only reference)")
    ap.add_argument("--a1", type=Path, required=True,
                    help="calibration_gap report JSON for A1 (joint, real targets)")
    ap.add_argument("--a2", type=Path, required=True,
                    help="calibration_gap report JSON for A2 (joint, placebo targets)")
    ap.add_argument("--margin", type=float, default=0.05,
                    help="LOCKED falsifier margin (default 0.05; do not move to fit a result)")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    a0 = _read_auroc(args.a0)
    a1 = _read_auroc(args.a1)
    a2 = _read_auroc(args.a2)

    margin_vs_placebo = a1 - a2
    margin_vs_reference = a1 - a0
    primary_pass = margin_vs_placebo >= args.margin
    secondary_pass = a1 > a0

    verdict = {
        "metric": f"{SECTION}.{METRIC}",
        "locked_margin": args.margin,
        "auroc": {"a0_lm_only": a0, "a1_joint_real": a1, "a2_joint_placebo": a2},
        "a1_minus_a2_placebo": margin_vs_placebo,
        "a1_minus_a0_reference": margin_vs_reference,
        "primary_pass_a1_gt_a2_by_margin": primary_pass,
        "secondary_pass_a1_gt_a0": secondary_pass,
        "verdict": "SUPPORTED" if primary_pass else "FALSIFIED",
    }

    text = json.dumps(verdict, indent=2)
    print(text)
    print("", file=sys.stderr)
    print(f"A0 (reference)  auroc_emitted_to_appropriateness = {a0:.4f}", file=sys.stderr)
    print(f"A1 (real)       auroc_emitted_to_appropriateness = {a1:.4f}", file=sys.stderr)
    print(f"A2 (placebo)    auroc_emitted_to_appropriateness = {a2:.4f}", file=sys.stderr)
    print(f"A1 - A2 = {margin_vs_placebo:+.4f}  (locked gate: >= +{args.margin})", file=sys.stderr)
    print(f"A1 - A0 = {margin_vs_reference:+.4f}  (secondary: must be > 0)", file=sys.stderr)
    print(f"==> {verdict['verdict']}"
          f"  (primary {'PASS' if primary_pass else 'FAIL'},"
          f" secondary {'PASS' if secondary_pass else 'FAIL'})", file=sys.stderr)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
        print(f"wrote {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
