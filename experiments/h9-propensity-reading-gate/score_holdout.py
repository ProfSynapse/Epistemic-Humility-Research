#!/usr/bin/env python3
"""H9 step 4 (CPU, no GPU): score the frozen direction on the held-out draw.

DRAFT SKELETON. Runs AFTER the Modal GPU lane (cloud/modal_h9_holdout.py) has
produced held-out extraction (L24/L35 per row) and graded behavior labels,
pulled back from the Modal Volume into the gitignored analysis/holdout_run/ tree.

Applies the frozen scorer (directions/frozen_scorer/, produced by
freeze_scorer.py) to each held-out row, then evaluates the pre-stated gates in
gates.yaml. Emits an aggregates-only gate report (no question text, no per-row
generations) to analysis-committed/.

Gates (AMENDMENT.md section 5):
  H9-G0 evaluability: >= 20 confabs AND >= 20 unanswerable-refusals, else
    inconclusive-by-power.
  H9-G2 caution floor: AUROC(refused vs not, all graded rows) >= 0.90, else the
    draw is a pipeline failure and G1 is not adjudicated.
  H9-G1 reading: AUROC(confab vs unanswerable-refused) with a 1,000-resample row
    bootstrap 95% CI; PASS / FAIL / INCONCLUSIVE per the gates.yaml bands.
  Sensitivity (section 8.1): recompute G1 with near-duplicate KUQ rows excluded;
    report alongside, never pooled.

Output:
  analysis-committed/holdout_run/gate_report.json
    {auroc_prop, ci_prop, auroc_caution, n_confab, n_un_refused, g0, g1, g2,
     sensitivity: {n_flagged, auroc_prop_excl, verdict_flip}, fidelity_ref}

Usage:
  python score_holdout.py --cell cell.yaml --gates gates.yaml [--sensitivity]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import yaml


def bootstrap_auroc_ci(y: np.ndarray, s: np.ndarray, n: int, ci: float, seed: int):
    """Row-bootstrap AUROC CI. TODO(sign): resample rows with replacement n times,
    recompute roc_auc_score each time, return (lo, hi) percentiles."""
    raise NotImplementedError


def score(cell: dict, gates: dict, do_sensitivity: bool) -> dict:
    """Load frozen scorer + held-out extraction/labels, evaluate the gates.

    TODO(sign): concrete steps.
      1. Load frozen objects from cell['scorer']['frozen_out']: pca24, scaler24,
         caution_clf (full-sample), caution_residualizer, d_confab_full,
         prop_zscale (mean/std).
      2. Load held-out extraction (L24/L35 per row) from
         cell['scoring']['holdout_extract_dir'] and graded labels from
         cell['scoring']['holdout_graded']; align by row_key to the committed
         ID-manifest.
      3. For each row: prop_z = zscale( residualize( scaler24.transform(
         pca24.transform(X24)), caution_clf, caution_residualizer ) @
         d_confab_full ); caution_z = caution_clf.decision_function(PCA128(X35)).
      4. Behavior labels: confab = (gold unanswerable & answered);
         un_ref = (gold unanswerable & refused); refused = graded refusal.
      5. H9-G0: count confab, un_ref against gates['evaluability'].
      6. H9-G2: auroc(refused-vs-not, caution_z) vs gates['caution_control'].
      7. H9-G1: auroc(confab vs un_ref, prop_z) + bootstrap CI; classify
         PASS/FAIL/INCONCLUSIVE per gates['reading_gate'].
      8. if do_sensitivity: flag held-out KUQ rows whose near-dup metric vs the
         fit-surface KUQ questions exceeds gates['sensitivity_near_dup'];
         recompute G1 excluding them; record verdict_flip.
      9. Write aggregates-only gate_report.json.
    """
    raise NotImplementedError(
        "score_holdout draft skeleton: wire the frozen-scorer application + gate "
        "evaluation per the TODO(sign) block; gates are locked in gates.yaml."
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cell", default="cell.yaml")
    ap.add_argument("--gates", default="gates.yaml")
    ap.add_argument("--sensitivity", action="store_true")
    args = ap.parse_args()
    cell = yaml.safe_load(Path(args.cell).read_text())
    gates = yaml.safe_load(Path(args.gates).read_text())
    report = score(cell, gates, args.sensitivity)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
