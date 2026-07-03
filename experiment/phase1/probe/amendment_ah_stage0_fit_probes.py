#!/usr/bin/env python3
"""Amendment AH Stage-0 (script 2/4) — frozen probe fitting (CPU).

Pre-registered in
experiment/protocol/AMENDMENT-AH-divergent-pool-own-readout.md (§4 step 2).

Fits the FROZEN doubt probes on the FULL AF-600 pre-gen surface (all 600 rows;
legitimate because every mined candidate is disjoint -> automatically
out-of-sample per §3.1 honest-threshold rule):

  - L20, L24, L28 single probes (StandardScaler + LogisticRegression C=1.0,
    max_iter=5000) — the ah_scout/score_probe.py recipe, one per layer.
  - A 5-fold ENSEMBLE at L24: 5 fold-models fit on 4/5 of AF-600 each
    (StratifiedKFold shuffle random_state=0, matching AG's CV recipe), used as
    a majority-vote alternative consensus instrument.

Label convention (verbatim from the recipe): label "known" == answerable ==
y=1; probe decision_function > 0 => "probe-certain". Operating threshold = 0.

Persists each fitted (scaler, clf) to ah_stage0/probes/ via joblib so the
scorer consumes them after GPU extraction. Reports full-fit AUROC (train) and
per-layer 5-fold OOF AUROC as provenance (must reproduce AG ~0.9945 at L24).
No GPU.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
from safetensors import safe_open
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score
import joblib

CANONICAL = Path("/home/profsynapse/code/Epistemic-Humility-Research")
AF_BASE = CANONICAL / "experiment/phase1/probe/analysis/af_base_pregen"
DEFAULT_OUT = CANONICAL / "experiment/phase1/probe/analysis/ah_stage0"

LAYERS = ["L20", "L24", "L28"]
ENSEMBLE_LAYER = "L24"
N_FOLDS = 5
CV_RANDOM_STATE = 0


def load_af_surface(layer: str):
    rows = {}
    with (AF_BASE / "rows.jsonl").open() as fh:
        for line in fh:
            line = line.strip()
            if line:
                r = json.loads(line)
                rows[r["safe_key"]] = r
    X, y, keys = [], [], []
    for sk, r in rows.items():
        fp = AF_BASE / f"{sk}__pre.safetensors"
        with safe_open(str(fp), "pt") as st:
            v = st.get_tensor(layer).float().numpy()
        X.append(v)
        y.append(1 if r["label"] == "known" else 0)
        keys.append(sk)
    return np.asarray(X), np.asarray(y), np.asarray(keys)


def fit_single(X, y):
    sc = StandardScaler().fit(X)
    clf = LogisticRegression(max_iter=5000, C=1.0).fit(sc.transform(X), y)
    return sc, clf


def oof_auroc(X, y):
    skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=CV_RANDOM_STATE)
    oof = np.zeros(len(y))
    for tr, te in skf.split(X, y):
        sc = StandardScaler().fit(X[tr])
        clf = LogisticRegression(max_iter=5000, C=1.0).fit(sc.transform(X[tr]), y[tr])
        oof[te] = clf.decision_function(sc.transform(X[te]))
    return roc_auc_score(y, oof), oof


def run(args) -> int:
    out_dir = Path(args.out_dir).resolve()
    probes_dir = out_dir / "probes"
    probes_dir.mkdir(parents=True, exist_ok=True)

    report = {"amendment": "AH", "stage": "stage0_fit_probes",
              "af_surface": str(AF_BASE), "layers": {}, "ensemble": {}}

    for layer in LAYERS:
        X, y, keys = load_af_surface(layer)
        sc, clf = fit_single(X, y)
        proj = clf.decision_function(sc.transform(X))
        train_auroc = roc_auc_score(y, proj)
        oof_a, _ = oof_auroc(X, y)
        joblib.dump({"scaler": sc, "clf": clf, "layer": layer},
                    probes_dir / f"probe_{layer}.joblib")
        report["layers"][layer] = {
            "n": int(len(y)), "n_known": int(y.sum()),
            "train_auroc": round(float(train_auroc), 4),
            "oof_auroc": round(float(oof_a), 4),
            "mean_proj_known": round(float(proj[y == 1].mean()), 3),
            "mean_proj_unknown": round(float(proj[y == 0].mean()), 3),
        }
        print(f"[ah/fit] {layer}: train_auroc={train_auroc:.4f} "
              f"oof_auroc={oof_a:.4f}", flush=True)

    # 5-fold ensemble at L24: persist all 5 fold (scaler, clf) pairs.
    Xe, ye, _ = load_af_surface(ENSEMBLE_LAYER)
    skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=CV_RANDOM_STATE)
    fold_models = []
    for fi, (tr, _te) in enumerate(skf.split(Xe, ye)):
        sc = StandardScaler().fit(Xe[tr])
        clf = LogisticRegression(max_iter=5000, C=1.0).fit(sc.transform(Xe[tr]), ye[tr])
        fold_models.append({"scaler": sc, "clf": clf, "fold": fi})
    joblib.dump({"folds": fold_models, "layer": ENSEMBLE_LAYER, "n_folds": N_FOLDS,
                 "cv_random_state": CV_RANDOM_STATE},
                probes_dir / f"ensemble_{ENSEMBLE_LAYER}.joblib")
    report["ensemble"] = {
        "layer": ENSEMBLE_LAYER, "n_folds": N_FOLDS,
        "cv_random_state": CV_RANDOM_STATE,
        "note": "majority-vote of 5 fold-models (each fit on 4/5 of AF-600)",
    }
    print(f"[ah/fit] ensemble {ENSEMBLE_LAYER}: {N_FOLDS} fold-models saved",
          flush=True)

    (out_dir / "probes_report.json").write_text(json.dumps(report, indent=2),
                                                encoding="utf-8")
    print(json.dumps(report, indent=2), flush=True)
    print(f"[ah/fit] DONE -> {probes_dir}", flush=True)
    return 0


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT))
    return ap.parse_args(argv)


if __name__ == "__main__":
    sys.exit(run(parse_args()))
