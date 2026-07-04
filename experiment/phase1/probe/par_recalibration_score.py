#!/usr/bin/env python3
"""PAR recalibration PASS 2 — on-checkpoint p-distribution + flip curves (CPU).

Lab-notebook work (no amendment letter). Team-lead task #64, branch
par-mining-recalibration.

The PAR design constants in par_design/REPORT.md were estimated from RAW-BASE
hidden states read through the frozen AF-600 L24 probe (standing caveat). The
PAR reward will instead read clean-SFT-lineage states at TRAIN time. This pass
recomputes the p distribution, |2p-1| saturation, the D1/D1b flip curves, and
the 8-cell gold-cube occupancy from the ON-CHECKPOINT pre-gen L24 states —
p = sigmoid(-score_L24) via the frozen probe — and flags any constant that moves.

Surfaces (states already materialized by amendments T and S):
  T  qwen3-4b-clean-sft-grpo-v2/amendment_t/stage2/  (clean-SFT->GRPO-v2)
  S  qwen3-4b-instruct/amendment_s/stage2/           (Instruct base)

Coverage note (see the manifest.answered_only flag): the T extractor only
persisted pre-gen states for ANSWERED rows (1,488 of 8,548; the 7,060 refused
rows have no saved states and the checkpoint is not local to re-extract). The T
recalibration here therefore covers the ANSWERED subset only — the D1 E[correct|
answered] curve and the answer-side flip curve are complete, but the D4/D4b
abstain cells (the over-refusal quadrant) are NOT reconstructable from the
answered subset and are reported as UNAVAILABLE for T. The S surface is complete
(all 1,836 rows have states).

Writes analysis/par_recalibration/:
  <tag>_recal_rows.jsonl   per-row p, |2p-1|, label, correct (gitignored)
  recalibration.json       committed result copy (probe-dir top): per-checkpoint
                           p summary, saturation, D1 flip curve, D1b (S full /
                           T answered), cube occupancy where available, and a
                           constant-drift table vs REPORT.md estimates.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from safetensors import safe_open
import joblib

PROBE_DIR = Path(__file__).resolve().parent
CANONICAL = Path("/home/profsynapse/code/Epistemic-Humility-Research")
PROBE_ROOT = CANONICAL / "experiment/phase1/probe"
STAGE0 = PROBE_ROOT / "analysis/ah_stage0"
PROBES = STAGE0 / "probes"
OUT_DIR = PROBE_ROOT / "analysis/par_recalibration"
RESULT_COPY = PROBE_DIR / "par_recalibration.json"

SURFACES = {
    "T_grpo_v2": {
        "dir": PROBE_ROOT / "qwen3-4b-clean-sft-grpo-v2/amendment_t/stage2",
        "checkpoint": "clean-SFT->GRPO-v2",
        "answered_only": True,   # refused rows have no saved states
    },
    "S_instruct": {
        "dir": PROBE_ROOT / "qwen3-4b-instruct/amendment_s/stage2",
        "checkpoint": "Qwen3-4B-Instruct base",
        "answered_only": False,  # all rows answered on this surface
    },
}

# REPORT.md raw-base design estimates to compare against (constant-drift check)
REPORT_ESTIMATES = {
    "p_saturation_frac_bimodal": 0.93,      # 93% at p<0.1 or p>0.9 (union)
    "mean_abs_2p_minus_1": 0.956,
    "E_correct_given_answered_pooled": 0.544,
    "correctness_bonus_cap_w": 0.20,        # cap to keep unanswerable-stratum flips <=2%
    "abstention_bonus_w_a": 0.20,
    "unanswerable_flip_at_w020_pct": 4.35,  # concentrated stratum, pre-cap concern
}

W_GRID = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]


def load_probe_L24():
    return joblib.load(PROBES / "probe_L24.joblib")


def score_L24(probe, X):
    return probe["clf"].decision_function(probe["scaler"].transform(X))


def load_rows(d: Path):
    return [json.loads(l) for l in (d / "rows.jsonl").open() if l.strip()]


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def p_bin(p):
    # 10 bins [0,0.1),...,[0.9,1.0]; bin index 0..9
    return min(9, int(p * 10))


def flip_curve_answer_side(p, w_grid):
    """D1: correctness bonus w on the ANSWER side. Flip when the outcome bonus
    overturns the pre-generation agreement preference: |2p-1| < w * E[outcome].
    E[outcome] upper-bounded at 1.0 (design worst case). Report flip fraction
    over the population, matching REPORT.md's flip_fraction_conditioned."""
    margin = np.abs(2 * p - 1)
    out = {}
    for w in w_grid:
        out[f"{w:.2f}"] = round(float(np.mean(margin < w)), 4)
    return out


def run(args) -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    probe = load_probe_L24()

    per_ckpt = {}
    for tag, spec in SURFACES.items():
        d = spec["dir"]
        rows = load_rows(d)
        # only rows with a saved pre-state are scoreable
        scoreable = []
        X = []
        for r in rows:
            sk = r["row_key"].replace("::", "__").replace("|", "_")
            pf = d / f"{sk}__pre.safetensors"
            if not pf.exists():
                continue
            with safe_open(str(pf), "pt") as st:
                X.append(st.get_tensor("L24").float().numpy().astype(np.float64))
            scoreable.append(r)
        X = np.vstack(X)
        s = score_L24(probe, X)              # logit, class1 = answerable/known
        p_unans = sigmoid(-s)                # p = P(unanswerable), REPORT p-defn
        margin = np.abs(2 * p_unans - 1)

        # per-row persist (gitignored)
        with (OUT_DIR / f"{tag}_recal_rows.jsonl").open("w", encoding="utf-8") as fh:
            for i, r in enumerate(scoreable):
                fh.write(json.dumps({
                    "row_key": r["row_key"], "dataset": r.get("dataset"),
                    "answered": r.get("answered"), "label": r.get("label"),
                    "correct": r.get("correct"),
                    "score_L24": float(s[i]), "p_unanswerable": float(p_unans[i]),
                    "abs_2p_minus_1": float(margin[i]),
                }, ensure_ascii=False) + "\n")

        # p summary + saturation
        sat = float(np.mean((p_unans < 0.1) | (p_unans > 0.9)))
        summary = {
            "checkpoint": spec["checkpoint"], "answered_only": spec["answered_only"],
            "n_scored": int(len(scoreable)), "n_rows_total": int(len(rows)),
            "n_missing_states": int(len(rows) - len(scoreable)),
            "p_unanswerable": {
                "mean": round(float(p_unans.mean()), 4),
                "median": round(float(np.median(p_unans)), 4),
                "frac_lt_0.1": round(float(np.mean(p_unans < 0.1)), 4),
                "frac_gt_0.9": round(float(np.mean(p_unans > 0.9)), 4),
                "saturation_bimodal_frac": round(sat, 4),
            },
            "mean_abs_2p_minus_1": round(float(margin.mean()), 4),
            "D1_answer_side_flip_curve": flip_curve_answer_side(p_unans, W_GRID),
        }

        # D1 E[correct|answered] by p-bin (answered rows with a correctness label)
        ans = [(i, r) for i, r in enumerate(scoreable)
               if r.get("answered") and r.get("correct") is not None]
        if ans:
            bins = {}
            n_corr = 0
            for i, r in ans:
                b = p_bin(p_unans[i])
                bins.setdefault(b, {"correct": 0, "n": 0})
                bins[b]["n"] += 1
                if r["correct"]:
                    bins[b]["correct"] += 1
                    n_corr += 1
            summary["D1_E_correct_given_answered"] = {
                "n_answered_graded": len(ans),
                "overall_Ecorrect": round(n_corr / len(ans), 4),
                "curve_by_pbin": {str(k): {"correct": v["correct"], "n": v["n"],
                                           "rate": round(v["correct"] / v["n"], 4)}
                                  for k, v in sorted(bins.items())},
            }

        per_ckpt[tag] = summary

    # pooled E[correct|answered] across T+S answered-graded (matches REPORT pooled)
    pooled_corr = pooled_n = 0
    for tag in SURFACES:
        d = per_ckpt[tag].get("D1_E_correct_given_answered")
        if d:
            pooled_corr += round(d["overall_Ecorrect"] * d["n_answered_graded"])
            pooled_n += d["n_answered_graded"]
    pooled_Ecorrect = round(pooled_corr / pooled_n, 4) if pooled_n else None

    # constant-drift table vs REPORT estimates
    drift = {
        "E_correct_given_answered_pooled": {
            "report_estimate": REPORT_ESTIMATES["E_correct_given_answered_pooled"],
            "recalibrated": pooled_Ecorrect,
            "delta": (round(pooled_Ecorrect
                            - REPORT_ESTIMATES["E_correct_given_answered_pooled"], 4)
                      if pooled_Ecorrect is not None else None),
            "note": "pooled over T+S answered-graded; T is answered-subset only",
        },
        "correctness_bonus_cap_w_0.20_survives": {
            "test": "unanswerable-stratum flip fraction at w=0.20 <= 2%",
            "report_estimate_pct": REPORT_ESTIMATES["unanswerable_flip_at_w020_pct"],
            "note": "recalibrated per-checkpoint answer-side flip at w=0.20 in "
                    "each ckpt's D1_answer_side_flip_curve['0.20']; compare there. "
                    "Full gold-unanswerable-stratum flip needs the refused rows "
                    "(T: unavailable — see answered_only).",
        },
    }

    result = {
        "stage": "par_recalibration_pass2",
        "branch": "par-mining-recalibration",
        "p_definition": "p_unanswerable = sigmoid(-score_L24), frozen AF-600 L24 probe",
        "surfaces_scored": {t: {"n": per_ckpt[t]["n_scored"],
                                "missing": per_ckpt[t]["n_missing_states"],
                                "answered_only": per_ckpt[t]["answered_only"]}
                            for t in SURFACES},
        "per_checkpoint": per_ckpt,
        "pooled_E_correct_given_answered": pooled_Ecorrect,
        "report_estimates": REPORT_ESTIMATES,
        "constant_drift": drift,
        "coverage_caveat": "T = answered subset (1,488/8,548); the 7,060 refused "
                           "rows lack saved states and the checkpoint is not local. "
                           "D4/D4b abstain cells (over-refusal quadrant) NOT "
                           "reconstructable for T from this subset. S is complete.",
    }
    (OUT_DIR / "recalibration.json").write_text(json.dumps(result, indent=2),
                                               encoding="utf-8")
    RESULT_COPY.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)
    print(f"[par/recal] DONE -> {OUT_DIR/'recalibration.json'} + {RESULT_COPY}",
          flush=True)
    return 0


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    return ap.parse_args(argv)


if __name__ == "__main__":
    sys.exit(run(parse_args()))
