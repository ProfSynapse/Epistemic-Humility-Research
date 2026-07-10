#!/usr/bin/env python3
"""Discriminate directional anti-steering from OOD-collapse on an ITI alpha sweep.

The A.4 per-head intervention sweep steers the failure axis F at coefficients
spanning both signs (e.g. ``[-8,-4,-2,0,+4]``). Two competing explanations of
its inverted causal sign make OPPOSITE predictions for the refusal-vs-alpha
curve:

- ``directional`` (Tan 2407.12404 anti-steerability): refusal is MONOTONE in
  alpha. One sign raises refusal, the other lowers it. The mass-mean direction
  simply steers with the opposite sign to how it reads.
- ``ood_collapse`` (H_OOD_default): any large |alpha| breaks the computation and
  the model falls back to its safe default, so refusal is U-SHAPED — BOTH
  extremes sit above the no-vector baseline.

This reads an existing head-intervention ``summary.json`` (no GPU, no new
generation) and classifies the curve. ``refusal_metric`` defaults to
``unknown_refusal_rate``; ``over_refusal_on_known`` is reported alongside.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ALPHA_RE = re.compile(r"alpha_([+-]?\d+(?:\.\d+)?)")


def alpha_of(arm_id: str) -> float:
    """no_vector_baseline -> 0.0; per_head_iti_alpha_+4 -> 4.0."""
    if "no_vector" in arm_id or "baseline" in arm_id:
        return 0.0
    m = ALPHA_RE.search(arm_id)
    if m is None:
        raise ValueError(f"cannot parse alpha from arm id {arm_id!r}")
    return float(m.group(1))


def curve(metrics_by_arm: dict[str, dict[str, Any]], *, refusal_metric: str) -> list[dict[str, Any]]:
    points = []
    for arm_id, m in metrics_by_arm.items():
        if refusal_metric not in m:
            raise KeyError(f"arm {arm_id!r} has no metric {refusal_metric!r}")
        points.append({
            "alpha": alpha_of(arm_id),
            "arm_id": arm_id,
            "refusal": float(m[refusal_metric]),
            "over_refusal_on_known": float(m.get("over_refusal_on_known")) if m.get("over_refusal_on_known") is not None else None,
        })
    points.sort(key=lambda p: p["alpha"])
    return points


def classify(points: list[dict[str, Any]], *, baseline_tol: float = 1.0) -> dict[str, Any]:
    """Return {verdict, classification, detail} from the sorted curve.

    ``ood_collapse`` requires BOTH the most-negative and most-positive arms to sit
    ABOVE the alpha=0 baseline by more than ``baseline_tol``. Otherwise a strictly
    ordered (monotone) curve is ``directional``; anything else is ``mixed``.
    """
    if len(points) < 3:
        return {"classification": "insufficient", "verdict": "need >=3 alpha points (including 0).",
                "detail": {"n_points": len(points)}}
    baseline = next((p["refusal"] for p in points if p["alpha"] == 0.0), None)
    if baseline is None:
        return {"classification": "insufficient", "verdict": "no alpha=0 baseline arm present.",
                "detail": {}}
    lo, hi = points[0], points[-1]
    refusals = [p["refusal"] for p in points]
    non_decreasing = all(b >= a for a, b in zip(refusals, refusals[1:]))
    non_increasing = all(b <= a for a, b in zip(refusals, refusals[1:]))
    both_extremes_up = (lo["refusal"] > baseline + baseline_tol) and (hi["refusal"] > baseline + baseline_tol)

    detail = {"baseline_refusal": round(baseline, 3),
              "most_negative": {"alpha": lo["alpha"], "refusal": round(lo["refusal"], 3)},
              "most_positive": {"alpha": hi["alpha"], "refusal": round(hi["refusal"], 3)}}

    if both_extremes_up:
        return {"classification": "ood_collapse",
                "verdict": (f"OOD-COLLAPSE: both extremes (alpha {lo['alpha']:g}: {lo['refusal']:.1f}, "
                            f"alpha {hi['alpha']:g}: {hi['refusal']:.1f}) sit above the no-vector baseline "
                            f"({baseline:.1f}); large |alpha| in EITHER sign raises refusal -> the inversion "
                            f"is a safe-default collapse, not a directional steer."),
                "detail": detail}
    if non_decreasing or non_increasing:
        direction = "raises" if hi["refusal"] > lo["refusal"] else "lowers"
        return {"classification": "directional",
                "verdict": (f"DIRECTIONAL (anti-steerable): refusal is monotone in alpha "
                            f"(alpha {lo['alpha']:g}: {lo['refusal']:.1f} -> alpha {hi['alpha']:g}: "
                            f"{hi['refusal']:.1f}); +alpha {direction} refusal while one sign lowers it. "
                            f"A genuine directional refusal motor whose steering sign is INVERTED relative "
                            f"to the prompt-token read (cf. Tan 2407.12404), NOT an OOD collapse."),
                "detail": detail}
    return {"classification": "mixed",
            "verdict": "MIXED: curve is neither monotone nor a clean U-shape; inspect per-alpha points.",
            "detail": detail}


def run(summary_path: Path, *, refusal_metric: str = "unknown_refusal_rate") -> dict[str, Any]:
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    metrics_by_arm = summary.get("metrics_by_arm")
    if not isinstance(metrics_by_arm, dict) or not metrics_by_arm:
        raise ValueError(f"{summary_path} has no metrics_by_arm")
    points = curve(metrics_by_arm, refusal_metric=refusal_metric)
    verdict = classify(points)
    return {
        "ok": True,
        "analysis_type": "phase3_head_intervention_sign_curve",
        "summary": str(summary_path),
        "refusal_metric": refusal_metric,
        "curve": points,
        **verdict,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", required=True, type=Path, help="head-intervention sweep summary.json")
    parser.add_argument("--refusal-metric", default="unknown_refusal_rate")
    parser.add_argument("--out", type=Path, default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = run(args.summary, refusal_metric=args.refusal_metric)
    for p in result["curve"]:
        ork = p["over_refusal_on_known"]
        print(f"  alpha {p['alpha']:>5g}  refusal={p['refusal']:6.2f}"
              f"  over_refusal_known={ork:6.2f}" if ork is not None else
              f"  alpha {p['alpha']:>5g}  refusal={p['refusal']:6.2f}", file=sys.stderr)
    print(f"\nVERDICT [{result['classification']}]: {result['verdict']}", file=sys.stderr)
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
