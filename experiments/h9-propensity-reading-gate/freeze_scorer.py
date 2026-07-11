#!/usr/bin/env python3
"""H9 step 1 (CPU, no GPU): freeze a portable scorer replicating AL's pipeline.

DRAFT SKELETON. The pipeline steps below mirror AL's generating script
    archive/experiment/phase1/probe/amendments/amendment_al_select_and_direction.py
exactly (PCA(128, random_state=20260705) -> StandardScaler -> caution
residualization -> mean-diff confab-vs-unanswerable-refused on L24, caution
logistic on L35). The difference from AL is that AL refit everything in memory
and saved only derived arrays; this script PERSISTS the fit objects so a
genuinely new (held-out) row can be scored later by score_holdout.py.

Two objects AL used cannot be applied to a single new row and are replaced by
full-sample frozen equivalents here (see AMENDMENT.md section 3 and the
spec-conflict note in section 8):
  - the caution score c: AL's is 5-fold OOF; we freeze a FINAL full-sample
    logistic on PCA-128(L35).
  - the propensity readout: AL's in-cell number is OOF; the frozen scorer is the
    FULL-SAMPLE mean-diff direction d_confab_full (the same object that produces
    d_raw.npy), z-scaled by the fit-population mean/std.

FIDELITY GATE (gates.yaml `fidelity`), asserted here before the scorer is
trusted:
  FID-1 (hard): re-derived full-sample d_raw reproduces the on-disk d_raw.npy at
    cosine >= 0.999999 and max|diff| <= 1e-5. This is the exact deterministic
    computation from the pinned script lines 197-204.
  FID-2 (consistency): frozen full-sample prop_z correlates with the on-disk OOF
    prop_z.npy at Pearson r >= 0.98, and the frozen in-cell AUROC is within 0.02
    of AL's 0.6802.

Outputs (all under directions/frozen_scorer/, gitignored):
  pca24.joblib, scaler24.joblib, caution_logistic.joblib,
  caution_residualizer.joblib, d_confab_full.npy, prop_zscale.json,
  d_raw_rederived.npy, fidelity_report.json, scorer_manifest.json (sha256 of each).

Usage:
  python freeze_scorer.py --cell cell.yaml [--gates gates.yaml]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import yaml

# The AL fit helpers are version-controlled and importable without GPU.
ARCHIVE = Path(__file__).resolve().parents[2] / "archive/experiment/phase1/probe/amendments"
if str(ARCHIVE) not in sys.path:
    sys.path.insert(0, str(ARCHIVE))


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def build_frozen_scorer(cell: dict) -> dict:
    """Re-derive AL's pipeline and freeze the objects. Returns a fidelity report.

    TODO(sign): wire the concrete fit. The exact call sequence, verified against
    amendment_al_select_and_direction.py:124-204, is:
      1. rows = load_jsonl(al_graded); assert len == 1662
      2. stack = load_a0_stack(al_extract_dir, row_keys)
         X24 = stack[:, 24, :].astype(float64); X35 = stack[:, 35, :].astype(float64)
      3. pca24 = PCA(128, svd_solver="randomized", random_state=20260705).fit(X24)
         Z24 = pca24.transform(X24); scaler24 = StandardScaler().fit(Z24)
         P24 = scaler24.transform(Z24)
      4. For d_raw REPLICATION (FID-1): reproduce AL's OOF caution c exactly
         (oof_caution(PCA128(X35), y_ref, seed+1)), residualize
         R = P24 - LinearRegression().fit(c, P24).predict(c),
         d_confab_full = unit(R[confab].mean(0) - R[un_ref].mean(0)),
         d_raw = unit((d_confab_full / scaler24.scale_) @ pca24.components_).
         Assert cosine(d_raw, load(d_raw.npy)) and max|diff| against gates.yaml.
      5. For the DEPLOYABLE scorer: fit a FINAL full-sample caution logistic
         caution_clf on PCA128(X35) (non-OOF), compute c_frozen on all rows,
         caution_residualizer = LinearRegression().fit(c_frozen, P24), and the
         residualized R_frozen; keep d_confab_full (from step 4) as the frozen
         direction. prop_full = zscale(R_frozen @ d_confab_full) with mean/std
         stored in prop_zscale.json.
      6. FID-2: pearson(prop_full, load(prop_z.npy)) and
         |auroc(prop_full; confab vs un_ref) - 0.6802| against gates.yaml.
      7. Persist every object + a sha256 manifest to directions/frozen_scorer/.
    """
    raise NotImplementedError(
        "freeze_scorer draft skeleton: wire the fit per the TODO(sign) block; "
        "the pipeline is fully specified against "
        "amendment_al_select_and_direction.py:124-204."
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cell", default="cell.yaml")
    ap.add_argument("--gates", default="gates.yaml")
    args = ap.parse_args()
    cell = yaml.safe_load(Path(args.cell).read_text())
    report = build_frozen_scorer(cell)
    print(json.dumps(report, indent=2))
    return 0 if report.get("fidelity_pass") else 1


if __name__ == "__main__":
    sys.exit(main())
