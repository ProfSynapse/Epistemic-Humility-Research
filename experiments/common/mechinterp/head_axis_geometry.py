#!/usr/bin/env python3
"""Tier-1 geometry falsifier for H_monitor (offline, GPU-free).

The Step A.4 failure axis (``unknown_answered_wrong`` vs ``unknown_refused``,
built per-head as a mass-mean direction) steers with an INVERTED sign: adding it
RAISES abstention. H_monitor reads it as a graded UNCERTAINTY monitor;
H_refusal_motor says it is just the refuse-vs-answer "motor" direction.

This script discriminates the two cheaply by comparing, on the SAME 11 localized
heads, the failure axis ``F`` against two reference axes built with the identical
mass-mean machinery (``build_directions``):

- ``R`` = refuse-vs-answer, pooled over known+unknown (the refusal-motor axis):
  positive ``{refused: true}`` vs negative ``{refused: false}``.
- ``K`` = knowledge-boundary, behavior-agnostic (the uncertainty axis):
  positive ``{label: unknown}`` vs negative ``{label: known}``.

Predictions:
- H_refusal_motor  -> cos(F, R) ~ 1 (F IS the refusal motor).
- H_monitor        -> |cos(F, K)| > |cos(F, R)| and cos(F, R) well below 1
  (F is more an uncertainty/knowledge-boundary axis than a refusal command).

A self-check rebuilds F from the same extraction and asserts it matches the
stored theta per head (methodology parity), so the cosines are trustworthy.

Reuses ``phase3_head_steering_directions.build_directions`` end-to-end, so the
head-slicing, mass-mean, and unit-normalisation are byte-for-byte the same as the
artifact A.4 actually steered.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
PROBE_DIR = ROOT / "experiment/phase1/probe"
if str(PROBE_DIR) not in sys.path:
    sys.path.insert(0, str(PROBE_DIR))

from head_steering_directions import build_directions  # noqa: E402
from sae_smoke import resolve_path  # noqa: E402

DEFAULT_FAILURE = (
    "experiment/phase1/probe/analysis/"
    "current_clean_grpo_v2_unknown_failure_prompt_matched_head_steering_directions/"
    "clean_sft_grpo_v2_seed1_unknown_failure_prompt_matched_steering/steering_directions.json"
)
DEFAULT_OUT = (
    "experiment/phase1/probe/analysis/"
    "current_clean_grpo_v2_unknown_failure_prompt_matched_head_axis_geometry"
)


def _cos(a: np.ndarray, b: np.ndarray) -> float:
    a = a.astype(np.float64)
    b = b.astype(np.float64)
    na = float(np.linalg.norm(a))
    nb = float(np.linalg.norm(b))
    if na <= 1e-12 or nb <= 1e-12:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def _theta_map(artifact: dict[str, Any]) -> dict[tuple[int, int], np.ndarray]:
    out: dict[tuple[int, int], np.ndarray] = {}
    for d in artifact["directions"]:
        out[(int(d["layer"]), int(d["head"]))] = np.asarray(d["theta"], dtype=np.float64)
    return out


def _spec_from_failure(failure: dict[str, Any], *, label: str, contrast: dict[str, Any]) -> dict[str, Any]:
    targets = [{"layer": int(d["layer"]), "head": int(d["head"])} for d in failure["directions"]]
    return {
        "label": label,
        "behavior_arm": failure["behavior_arm"],
        "arm_role": failure.get("arm_role", "h_lora"),
        "extraction_dir": failure["extraction_dir"],
        "extraction_manifest": failure.get("extraction_manifest"),
        "rows_path": failure.get("rows_path"),
        "contrast": contrast,
        "targets": targets,
    }


def run(failure_path: Path, out_root: Path, *, min_rows: int = 16) -> dict[str, Any]:
    failure = json.loads(failure_path.read_text(encoding="utf-8"))
    F = _theta_map(failure)

    # Reference axes, same 11 heads, identical mass-mean machinery.
    contrasts = {
        "refuse_vs_answer": {
            "name": "refused_vs_answered_pooled",
            "positive_label": "refused",
            "negative_label": "answered",
            "min_rows_per_group": min_rows,
            "positive": {"refused": True},
            "negative": {"refused": False},
        },
        "knowledge_boundary": {
            "name": "unknown_vs_known_behavior_agnostic",
            "positive_label": "unknown",
            "negative_label": "known",
            "min_rows_per_group": min_rows,
            "positive": {"label": "unknown"},
            "negative": {"label": "known"},
        },
        # parity self-check: rebuild the failure axis itself.
        "failure_rebuild": {
            "name": "unknown_answered_wrong_vs_unknown_refused",
            "positive_label": "unknown_answered_wrong",
            "negative_label": "unknown_refused",
            "min_rows_per_group": min_rows,
            "positive": {"label": "unknown", "refused": False, "correct": False},
            "negative": {"label": "unknown", "refused": True},
        },
    }

    built: dict[str, dict[str, Any]] = {}
    for label, contrast in contrasts.items():
        spec = _spec_from_failure(failure, label=label, contrast=contrast)
        built[label] = build_directions(spec, output_root=out_root)

    R = _theta_map(built["refuse_vs_answer"])
    K = _theta_map(built["knowledge_boundary"])
    Frebuilt = _theta_map(built["failure_rebuild"])

    per_head = []
    parity = []
    for (layer, head), f in F.items():
        key = (layer, head)
        cos_fr = _cos(f, R[key])
        cos_fk = _cos(f, K[key])
        cos_parity = _cos(f, Frebuilt[key])
        parity.append(cos_parity)
        per_head.append(
            {
                "layer": layer,
                "head": head,
                "cos_failure_refuse_motor": round(cos_fr, 4),
                "cos_failure_knowledge_boundary": round(cos_fk, 4),
                "abs_cos_refuse_motor": round(abs(cos_fr), 4),
                "abs_cos_knowledge_boundary": round(abs(cos_fk), 4),
                "parity_cos_failure_rebuild": round(cos_parity, 4),
            }
        )

    abs_fr = np.array([h["abs_cos_refuse_motor"] for h in per_head])
    abs_fk = np.array([h["abs_cos_knowledge_boundary"] for h in per_head])
    signed_fr = np.array([h["cos_failure_refuse_motor"] for h in per_head])
    parity_arr = np.array(parity)
    parity_ok = bool(np.all(parity_arr > 0.999))

    n_uncertainty_dominant = int(np.count_nonzero(abs_fk > abs_fr))
    summary = {
        "ok": True,
        "analysis_type": "phase3_head_axis_geometry",
        "failure_directions": str(failure_path),
        "n_heads": len(per_head),
        "contrast_counts": {
            label: {
                "positive": built[label]["contrast"]["positive_count"],
                "negative": built[label]["contrast"]["negative_count"],
            }
            for label in built
        },
        "parity_self_check": {
            "min_cos_failure_rebuild": round(float(parity_arr.min()), 6),
            "all_heads_match": parity_ok,
        },
        "aggregate": {
            "mean_abs_cos_refuse_motor": round(float(abs_fr.mean()), 4),
            "median_abs_cos_refuse_motor": round(float(np.median(abs_fr)), 4),
            "max_abs_cos_refuse_motor": round(float(abs_fr.max()), 4),
            "mean_abs_cos_knowledge_boundary": round(float(abs_fk.mean()), 4),
            "median_abs_cos_knowledge_boundary": round(float(np.median(abs_fk)), 4),
            "max_abs_cos_knowledge_boundary": round(float(abs_fk.max()), 4),
            "n_heads_uncertainty_dominant": n_uncertainty_dominant,
            "n_heads": len(per_head),
            "mean_signed_cos_refuse_motor": round(float(signed_fr.mean()), 4),
            "refuse_motor_dominance_ratio": round(
                float(abs_fr.mean() / abs_fk.mean()) if abs_fk.mean() > 1e-6 else float("inf"), 2
            ),
        },
        "verdict": _verdict(abs_fr, abs_fk, parity_ok, mean_signed_fr=float(signed_fr.mean())),
        "per_head": per_head,
    }
    out_path = out_root / "axis_geometry.json"
    out_root.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    summary["_written"] = str(out_path)
    return summary


def _verdict(abs_fr: np.ndarray, abs_fk: np.ndarray, parity_ok: bool, *, mean_signed_fr: float) -> str:
    """Which reference axis dominates the failure axis, and what that implies.

    The test is "which reference axis is F closest to". A large gap between
    mean|cos(F,refuse-motor)| and mean|cos(F,knowledge-boundary)| settles it; the
    SIGN of cos(F,refuse-motor) then says whether F's *construction* points with
    or against the refusal direction -- which, read against the A.4 causal result
    (adding +F RAISES refusal), is where the sign inversion lives.
    """
    if not parity_ok:
        return "INVALID: failure-axis rebuild did not match the stored theta; cosines untrusted."
    mfr, mfk = float(abs_fr.mean()), float(abs_fk.mean())
    dominance = mfr / mfk if mfk > 1e-6 else float("inf")
    if mfr > 0.95:
        base = (
            "H_refusal_motor (naive) NOT REFUTED on alignment alone: failure axis is "
            "~collinear with the refuse-vs-answer motor (mean |cos| > 0.95)."
        )
    elif dominance >= 3.0:
        sign = "ANTI-aligned" if mean_signed_fr < 0 else "aligned"
        base = (
            f"DECISION-AXIS DOMINANT: failure axis lives on the refuse<->answer decision "
            f"axis (mean |cos|={mfr:.2f}), {dominance:.1f}x stronger than the static "
            f"knowledge-boundary axis (mean |cos|={mfk:.2f}), and is {sign} to the refusal "
            f"direction by construction. It is NOT a distinct knowledge-boundary/uncertainty "
            f"subspace (refutes the clean H_monitor geometry) and NOT the naive +parallel "
            f"refusal motor. Read against the A.4 causal result (+F RAISES refusal), the open "
            f"puzzle is a READ/WRITE SIGN INVERSION on the decision axis itself."
        )
    elif mfk > mfr:
        base = (
            "H_monitor SUPPORTED (geometry): failure axis aligns MORE with the "
            "knowledge-boundary/uncertainty axis than with the refuse-vs-answer motor."
        )
    else:
        base = (
            "MIXED: failure axis splits between the refuse-answer and knowledge-boundary "
            "axes without a dominant one; report both cosines and escalate."
        )
    return base


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--failure-directions", type=Path, default=Path(DEFAULT_FAILURE))
    parser.add_argument("--out", type=Path, default=Path(DEFAULT_OUT))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    summary = run(resolve_path(str(args.failure_directions)), resolve_path(str(args.out)))
    # Compact human-readable table to stderr; machine JSON to stdout.
    print(
        f"parity_ok={summary['parity_self_check']['all_heads_match']} "
        f"(min cos {summary['parity_self_check']['min_cos_failure_rebuild']})",
        file=sys.stderr,
    )
    print(
        f"{'layer':>5} {'head':>4} {'cos(F,refuse)':>14} {'cos(F,knowledge)':>17}",
        file=sys.stderr,
    )
    for h in summary["per_head"]:
        print(
            f"{h['layer']:>5} {h['head']:>4} {h['cos_failure_refuse_motor']:>14} "
            f"{h['cos_failure_knowledge_boundary']:>17}",
            file=sys.stderr,
        )
    agg = summary["aggregate"]
    print(
        f"\nmean|cos(F,refuse-motor)|     = {agg['mean_abs_cos_refuse_motor']}\n"
        f"mean|cos(F,knowledge-bound)| = {agg['mean_abs_cos_knowledge_boundary']}\n"
        f"uncertainty-dominant heads   = {agg['n_heads_uncertainty_dominant']}/{agg['n_heads']}\n"
        f"VERDICT: {summary['verdict']}",
        file=sys.stderr,
    )
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
