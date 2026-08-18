#!/usr/bin/env python3
"""Pinned instrument for stated-confidence-under-pstruct (CPU-only).

Per arm: parse integrity (SC-G0), confidence-correctness AUROC on answered
rows, 10-bin equal-width ECE on answered rows, refusal separation (median
confidence refused minus answered), and descriptive means/medians/refusal
rate. Bands adjudicated by the lead against gates.yaml; this script only
computes. No question text, prompt text, or generation text is emitted.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score

PSTRUCT_ARMS = [
    "base_pstruct__ambigqa",
    "clean_sft_merged_pstruct__ambigqa",
    "cold_dpo_seed1_pstruct__ambigqa", "cold_dpo_seed2_pstruct__ambigqa", "cold_dpo_seed3_pstruct__ambigqa",
    "cold_kto_seed1_pstruct__ambigqa", "cold_kto_seed2_pstruct__ambigqa", "cold_kto_seed3_pstruct__ambigqa",
    "cold_sft_seed1_pstruct__ambigqa", "cold_sft_seed2_pstruct__ambigqa", "cold_sft_seed3_pstruct__ambigqa",
    "seq_sft_dpo_seed1_pstruct__ambigqa", "seq_sft_dpo_seed2_pstruct__ambigqa", "seq_sft_dpo_seed3_pstruct__ambigqa",
    "seq_sft_kto_seed1_pstruct__ambigqa", "seq_sft_kto_seed2_pstruct__ambigqa", "seq_sft_kto_seed3_pstruct__ambigqa",
    "sft_grpo_seed1_pstruct__ambigqa",
]
REFERENCE_ARMS = ["base_pplain__ambigqa", "base_prc__ambigqa"]
EXPECTED_ROWS = 1832


def score_arm(arm_dir: Path) -> dict:
    rows = [json.loads(l) for l in (arm_dir / "scored_rows.jsonl").open()]
    n = len(rows)
    usable = [r for r in rows if isinstance(r.get("stated_confidence"), (int, float))]
    exhausted = sum(1 for r in rows if r.get("stated_confidence_retry_exhausted"))
    answered = [r for r in usable if not r["refused"]]
    refused = [r for r in usable if r["refused"]]

    out = {
        "n_rows": n,
        "full_row_coverage": n == EXPECTED_ROWS,
        "n_usable_confidence": len(usable),
        "parse_rate": round(len(usable) / n, 4) if n else 0.0,
        "n_retry_exhausted": exhausted,
        "n_answered": len(answered),
        "n_refused": len(refused),
        "refusal_rate": round(len(refused) / len(usable), 4) if usable else None,
        "mean_confidence": round(float(np.mean([r["stated_confidence"] for r in usable])), 4) if usable else None,
        "median_confidence": round(float(np.median([r["stated_confidence"] for r in usable])), 4) if usable else None,
    }

    conf = np.array([r["stated_confidence"] for r in answered], dtype=float)
    corr = np.array([bool(r["correct"]) for r in answered], dtype=int)
    if len(answered) and 0 < corr.sum() < len(corr):
        out["confidence_correctness_auroc"] = round(float(roc_auc_score(corr, conf)), 4)
    else:
        out["confidence_correctness_auroc"] = None  # single-class or empty

    if len(answered):
        bins = np.clip((conf * 10).astype(int), 0, 9)
        ece = 0.0
        for b in range(10):
            m = bins == b
            if m.sum():
                ece += (m.sum() / len(conf)) * abs(conf[m].mean() - corr[m].mean())
        out["ece_10bin"] = round(float(ece), 4)
        out["answered_accuracy"] = round(float(corr.mean()), 4)
        out["median_confidence_answered"] = round(float(np.median(conf)), 4)
    else:
        out["ece_10bin"] = None
        out["answered_accuracy"] = None
        out["median_confidence_answered"] = None

    if refused:
        med_ref = float(np.median([r["stated_confidence"] for r in refused]))
        out["median_confidence_refused"] = round(med_ref, 4)
        out["refusal_separation"] = (
            round(med_ref - out["median_confidence_answered"], 4)
            if out["median_confidence_answered"] is not None else None
        )
    else:
        out["median_confidence_refused"] = None
        out["refusal_separation"] = None
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--results-root", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    result = {"expected_rows": EXPECTED_ROWS, "arms": {}, "reference_arms": {}}
    for arm in PSTRUCT_ARMS:
        result["arms"][arm] = score_arm(args.results_root / arm)
    for arm in REFERENCE_ARMS:
        result["reference_arms"][arm] = score_arm(args.results_root / arm)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
