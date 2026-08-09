#!/usr/bin/env python3
"""G7 internal-readout-transfer computation (cell.yaml `internal_panel`,
gates.yaml `g7_internal_readout_transfer`). CPU-only stage 7 (probe fit).

Reuses, rather than reimplements:
  - `experiments/selfaware-latent-knowledge-controls/latent_knowledge_probe.py`
    `load_layers` / `cv_auroc` for the held-out logistic probe (StandardScaler
    + L2 LogisticRegression(C=0.5) + StratifiedKFold(5), decision-function
    AUROC) -- this is paper 3's OWN probe-fit protocol (cell.yaml `internal_
    panel.probe_fit`, decision #9 in AMENDMENT.md "reuse paper 3's fit
    protocol"), not the tuner's PCA-based `MechInterp/probe/fit.py::cv_auroc`.
    `load_layers`' `source` parameter is generic (builds
    `f"{stem}__{source}.safetensors"`); passing `source="anchor"` reads
    exactly the files `MechInterp/extraction/capture.py::extract_rows` writes
    for the `anchor` position family, so this is a direct, unmodified reuse --
    not a reimplementation with a different naming convention.
  - `archive/experiment/phase1/eval/analysis/calibration_gap_report.py`'s
    `auroc()` (rank-based, tie-safe Mann-Whitney AUROC) for the emitted-vs-
    known-label AUROC on the shared rows, so the internal and emitted numbers
    are computed by the exact same rank statistic.

Two quantities, per gates.yaml g7:
  1. `heldout_probe_auroc`: 5-fold CV AUROC of the L35 anchor-position probe on
     known/unknown, over the FULL 2748-row panel (behavior surface + train
     top-up). Threshold: >= 0.90.
  2. `margin_over_emitted`: the panel's out-of-fold probe score, RESTRICTED to
     the 1832 `validation_behavior_surface` rows (the ones that were also
     generated in the behavior panel -- cell.yaml `internal_panel.
     superset_property`), scored as AUROC against known/unknown; minus the
     SAME arm's emitted-`response_confidence`-to-known-label AUROC on those
     same 1832 rows, read from that arm's AmbigQA `scored_rows.jsonl`.
     Threshold: >= 0.15. This mirrors manuscript.md lines 359-364's
     like-for-like construction (both channels scored against the SAME
     known/unknown label on the SAME joined rows), not the appropriateness
     label calibration_gap_report.py's Analysis A reports by default.

CPU-only; the GPU work (extraction) already happened in stage 6.

Usage:
    python3 experiments/ood-breadth-beyond-selfaware/internal_panel_probe_gate.py \
        --arm A1 \
        --extraction-dir experiments/ood-breadth-beyond-selfaware/analysis/extraction/A1 \
        --scored-rows archive/experiment/phase1/eval/results_ood_breadth_clean_schema_sft_merged_seed1_full_4b/clean_schema_sft_merged_seed1__ambigqa/scored_rows.jsonl \
        --out experiments/ood-breadth-beyond-selfaware/analysis/gate/g7_A1.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
LATENT_CONTROLS_DIR = REPO_ROOT / "experiments" / "selfaware-latent-knowledge-controls"
EVAL_ANALYSIS_DIR = REPO_ROOT / "archive" / "experiment" / "phase1" / "eval" / "analysis"

sys.path.insert(0, str(LATENT_CONTROLS_DIR))
sys.path.insert(0, str(EVAL_ANALYSIS_DIR))

PANEL_POOL_PATH = REPO_ROOT / "experiments" / "ood-breadth-beyond-selfaware" / "analysis" / "screen" / "internal_panel_pool.jsonl"
LAYER = 35


def load_panel_pool() -> list[dict]:
    rows = []
    with PANEL_POOL_PATH.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_scored_rows(path: Path) -> dict[str, dict]:
    """id -> scored row, from an AmbigQA scored_rows.jsonl (run_eval.py output)."""
    out = {}
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                r = json.loads(line)
                out[str(r["id"])] = r
    return out


def compute(extraction_dir: Path, scored_rows_path: Path) -> dict:
    import latent_knowledge_probe as lkp
    from calibration_gap_report import auroc as rank_auroc

    panel = load_panel_pool()
    row_keys = [r["row_key"] for r in panel]
    y = np.array([1 if r["label"] == "unknown" else 0 for r in panel])
    shared_mask = np.array([r["panel_component"] == "validation_behavior_surface" for r in panel])

    n_known = int((y == 0).sum())
    n_unknown = int((y == 1).sum())
    if len(panel) != 2748 or n_known != 1245 or n_unknown != 1503:
        raise SystemExit(
            f"G2 CONTRADICTION: internal panel pool is n={len(panel)} "
            f"(known={n_known}, unknown={n_unknown}); gates.yaml g2_surface_"
            "construction.thresholds.retained_n_must_equal.internal_panel "
            "requires total=2748, known=1245, unknown=1503. STOP; do not proceed."
        )

    mats = lkp.load_layers(extraction_dir, row_keys, [LAYER], source="anchor")
    X = mats[LAYER]
    if X.ndim == 3:
        # MechInterp/extraction/capture.py stacks over the position list even
        # for a single-index family ("anchor" -> exactly one index), so each
        # row's saved tensor is shape (1, hidden), not (hidden,).
        # latent_knowledge_probe.load_layers (written against the legacy
        # phase1/probe backend, which saves (hidden,) directly) stacks those
        # into (n, 1, hidden); squeeze the singleton position axis before
        # handing X to sklearn.
        if X.shape[1] != 1:
            raise SystemExit(
                f"expected exactly 1 captured position per row for the anchor "
                f"family, got {X.shape[1]}; extraction spec drifted from "
                "extract_A1.yaml/extract_A4.yaml (families: [anchor])"
            )
        X = X[:, 0, :]

    mean_auc, std_auc, oof = _cv_auroc_with_oof(X, y, folds=5, C=0.5, seed=0)

    shared_oof = oof[shared_mask]
    shared_y = y[shared_mask]
    if shared_mask.sum() != 1832:
        raise SystemExit(
            f"G2 CONTRADICTION: shared (validation_behavior_surface) rows = "
            f"{int(shared_mask.sum())}, expected 1832. STOP."
        )
    internal_auroc_shared = rank_auroc(shared_oof, shared_y)

    scored = load_scored_rows(scored_rows_path)
    shared_keys = [row_keys[i] for i in range(len(panel)) if shared_mask[i]]
    emitted_conf, emitted_known = [], []
    missing = 0
    for rk, yk in zip(shared_keys, shared_y):
        sr = scored.get(rk)
        if sr is None or sr.get("stated_confidence") is None:
            missing += 1
            continue
        emitted_conf.append(float(sr["stated_confidence"]))
        emitted_known.append(1 if yk == 0 else 0)  # known=1 for the emitted-to-known AUROC direction
    emitted_conf = np.asarray(emitted_conf)
    emitted_known = np.asarray(emitted_known)
    emitted_auroc_known = rank_auroc(emitted_conf, emitted_known)

    margin = internal_auroc_shared - emitted_auroc_known

    return {
        "gate": "G7",
        "layer": LAYER,
        "n_panel": len(panel),
        "n_panel_known": n_known,
        "n_panel_unknown": n_unknown,
        "heldout_probe_auroc": round(float(mean_auc), 4),
        "heldout_probe_auroc_std_across_folds": round(float(std_auc), 4),
        "heldout_probe_auroc_pass": bool(mean_auc >= 0.90),
        "n_shared_rows": int(shared_mask.sum()),
        "internal_auroc_on_shared_rows": round(float(internal_auroc_shared), 4),
        "emitted_auroc_to_known_on_shared_rows": round(float(emitted_auroc_known), 4),
        "emitted_missing_confidence_rows": missing,
        "margin": round(float(margin), 4),
        "margin_pass": bool(margin >= 0.15),
        "gate_pass": bool(mean_auc >= 0.90 and margin >= 0.15),
    }


def _cv_auroc_with_oof(X: np.ndarray, y: np.ndarray, *, folds: int = 5, C: float = 0.5, seed: int = 0):
    """Same recipe as latent_knowledge_probe.cv_auroc, but also returns
    per-row out-of-fold decision-function scores (needed for the shared-rows
    restriction, which cv_auroc's mean-AUROC-only return does not expose).
    """
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import StratifiedKFold
    from sklearn.preprocessing import StandardScaler

    y = np.asarray(y).astype(int)
    n_min = int(min(np.bincount(y)))
    k = max(2, min(folds, n_min))
    skf = StratifiedKFold(n_splits=k, shuffle=True, random_state=seed)
    oof = np.zeros(len(y), dtype=float)
    fold_aucs = []
    for tr, te in skf.split(X, y):
        sc = StandardScaler().fit(X[tr])
        clf = LogisticRegression(C=C, max_iter=2000)
        clf.fit(sc.transform(X[tr]), y[tr])
        s = clf.decision_function(sc.transform(X[te]))
        oof[te] = s
        fold_aucs.append(roc_auc_score(y[te], s))
    return float(np.mean(fold_aucs)), float(np.std(fold_aucs)), oof


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arm", required=True, choices=["A1", "A4"])
    ap.add_argument("--extraction-dir", required=True, type=Path)
    ap.add_argument("--scored-rows", required=True, type=Path, help="that arm's AmbigQA scored_rows.jsonl")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    result = compute(args.extraction_dir, args.scored_rows)
    result["arm"] = args.arm
    text = json.dumps(result, indent=2)
    print(text)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
        print(f"\nwrote {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
