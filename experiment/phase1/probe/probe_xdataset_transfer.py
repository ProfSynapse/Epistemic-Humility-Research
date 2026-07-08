#!/usr/bin/env python3
"""Amendment P — cross-dataset answerability-probe transfer test (CPU-only).

Pre-registered in experiments/xdataset-probe-transfer/AMENDMENT.md.
Exploratory, single-model, single-seed; reported separately from the locked matrix.

Question (the de-risking pre-check for the confidence-head engine change):
Amendment O showed a linear readout of the internal axis IS a passing policy, but
fit the probe *in-distribution* (5-fold CV on SelfAware itself). The deployment
question is stricter: does an answerability probe fit on ONE QA distribution transfer
COLD to the reporting surface (SelfAware)? If the axis is dataset-specific, the
proposed head needs an OOD-robust target before it is justified.

Design (checkpoint-consistent, fully cached):
  * FIT set:  KUQ      (known/unknown gold labels), grpo-v2 checkpoint, h_base L35.
  * TEST set: SelfAware(known/unknown gold labels), grpo-v2 checkpoint, h_base L35.
  Both extracted on the SAME checkpoint, so the feature space is shared (no
  cross-checkpoint mismatch). Fit StandardScaler+LogisticRegression on ALL of KUQ;
  apply COLD to SelfAware -> factual_p; score transfer AUROC / ECE and the oracle
  action policy (answer iff factual_p >= tau).

PRIMARY (locked) falsifier metric: transfer AUROC (KUQ-fit -> SelfAware
appropriateness). Threshold-free, so it isolates transfer-of-the-axis from
transfer-of-the-operating-point. Action gates at a fixed tau are reported but
SECONDARY/descriptive, because a fixed tau across a base-rate shift (KUQ 60% known
vs SelfAware 45% known) conflates threshold calibration with axis transfer; the
honest single number is the AUROC. Sanity arms: in-distribution 5-fold CV AUROC on
each set (should reproduce KUQ ~0.97 / SelfAware ~0.99) to confirm both feature
spaces are healthy before reading the cold-transfer number.

Verdict thresholds are read from the amendment and are NOT tunable here.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from safetensors.numpy import load_file
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score

# ---- pre-registered gates (Amendment P §4) — reference only, not tunable --------
GATES = {
    "transfer_auroc_min": 0.70,    # PRIMARY falsifier: cold KUQ-fit -> SelfAware
    "ece_max": 0.30,
    "over_refusal_max": 67.5,      # SECONDARY (descriptive at fixed tau)
    "refusal_recall_min": 82.0,    # SECONDARY (descriptive at fixed tau)
}


def load_extraction(ext_dir: Path, layer: int, source: str = "h_base"):
    rows = [json.loads(l) for l in (ext_dir / "rows.jsonl").open(encoding="utf-8") if l.strip()]
    X, y, keep = [], [], []
    lname = f"L{layer}"
    for r in rows:
        label = str(r.get("label", "")).lower()
        if label not in ("known", "unknown"):
            continue
        safe = str(r["probe_pool_row_key"]).replace("::", "__").replace("|", "_")
        shard = ext_dir / f"{safe}__{source}.safetensors"
        if not shard.exists():
            continue
        t = load_file(str(shard))
        if lname not in t:
            raise KeyError(f"{shard} missing {lname}")
        X.append(np.asarray(t[lname], dtype=np.float64))
        y.append(1 if label == "known" else 0)  # factual_p = P(known/answerable)
        keep.append(r)
    return np.vstack(X), np.asarray(y, dtype=int), keep


def cv_auroc(X: np.ndarray, y: np.ndarray, seed: int = 20260629) -> float:
    """In-distribution 5-fold CV AUROC (sanity that the feature space is healthy)."""
    p = np.full(len(y), np.nan)
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
    for tr, te in skf.split(X, y):
        sc = StandardScaler().fit(X[tr])
        clf = LogisticRegression(C=1.0, max_iter=2000).fit(sc.transform(X[tr]), y[tr])
        p[te] = clf.predict_proba(sc.transform(X[te]))[:, 1]
    return float(roc_auc_score(y, p))


def fit_full(X: np.ndarray, y: np.ndarray):
    """Fit on ALL rows (the fit/train distribution); return (scaler, clf)."""
    sc = StandardScaler().fit(X)
    clf = LogisticRegression(C=1.0, max_iter=2000).fit(sc.transform(X), y)
    return sc, clf


def ece(prob: np.ndarray, y: np.ndarray, n_bins: int = 15) -> float:
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    e, n = 0.0, len(y)
    for i in range(n_bins):
        lo, hi = edges[i], edges[i + 1]
        m = (prob >= lo) & (prob < hi) if i < n_bins - 1 else (prob >= lo) & (prob <= hi)
        if not m.any():
            continue
        e += (m.sum() / n) * abs(prob[m].mean() - y[m].mean())
    return float(e)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fit-dir", type=Path, required=True, help="KUQ extraction dir (fit)")
    ap.add_argument("--test-dir", type=Path, required=True, help="SelfAware extraction dir (cold test)")
    ap.add_argument("--layer", type=int, default=35)
    ap.add_argument("--source", default="h_base", choices=["h_base", "h_lora"])
    ap.add_argument("--tau", type=float, default=0.5)
    ap.add_argument("--scan-layers", action="store_true")
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args(argv)

    fit_dir, test_dir = a.fit_dir.resolve(), a.test_dir.resolve()
    Xf, yf, _ = load_extraction(fit_dir, a.layer, a.source)
    Xt, yt, rows_t = load_extraction(test_dir, a.layer, a.source)

    # in-distribution CV sanity (both feature spaces)
    cv_fit = cv_auroc(Xf, yf)
    cv_test = cv_auroc(Xt, yt)

    # cold transfer: fit on ALL fit-set rows, apply to test set
    sc, clf = fit_full(Xf, yf)
    fp = clf.predict_proba(sc.transform(Xt))[:, 1]  # factual_p on SelfAware (cold)

    transfer_auroc = float(roc_auc_score(yt, fp))   # PRIMARY falsifier metric
    ece_val = ece(fp, yt)
    std_val = float(fp.std())

    # oracle action at tau on the cold-transferred scores (SECONDARY/descriptive)
    answer = fp >= a.tau
    km, um = (yt == 1), (yt == 0)
    over_refusal = 100.0 * float((~answer)[km].mean())
    refusal_recall = 100.0 * float((~answer)[um].mean())
    ar_known = 100.0 * float(answer[km].mean())
    ar_unknown = 100.0 * float(answer[um].mean())
    action_margin = ar_known - ar_unknown

    result = {
        "amendment": "P",
        "fit_dir": str(fit_dir), "test_dir": str(test_dir),
        "layer": a.layer, "source": a.source, "tau": a.tau,
        "n_fit": int(len(yf)), "n_fit_known": int((yf == 1).sum()),
        "n_test": int(len(yt)), "n_test_known": int((yt == 1).sum()),
        "in_distribution_cv_sanity": {
            "fit_set_cv_auroc": cv_fit, "test_set_cv_auroc": cv_test,
        },
        "transfer": {
            "transfer_auroc": transfer_auroc,   # PRIMARY (locked falsifier)
            "ece": ece_val, "factual_p_std": std_val,
        },
        "oracle_action_secondary": {
            "over_refusal_pct": over_refusal,
            "refusal_recall_pct": refusal_recall,
            "answer_rate_known_pct": ar_known,
            "answer_rate_unknown_pct": ar_unknown,
            "action_margin_pts": action_margin,
        },
    }

    if a.scan_layers:
        scan = {}
        for L in range(37):
            try:
                XfL, yfL, _ = load_extraction(fit_dir, L, a.source)
                XtL, ytL, _ = load_extraction(test_dir, L, a.source)
            except KeyError:
                continue
            scL, clfL = fit_full(XfL, yfL)
            scan[L] = float(roc_auc_score(ytL, clfL.predict_proba(scL.transform(XtL))[:, 1]))
        result["transfer_auroc_by_layer"] = scan

    # ---- verdict vs pre-registered gates (PRIMARY = transfer AUROC) ----
    tr = result["transfer"]; act = result["oracle_action_secondary"]
    checks_primary = {
        "transfer_auroc>=0.70": tr["transfer_auroc"] >= GATES["transfer_auroc_min"],
        "ece<0.30": tr["ece"] < GATES["ece_max"],
    }
    checks_secondary = {
        "over_refusal<=67.5": act["over_refusal_pct"] <= GATES["over_refusal_max"],
        "refusal_recall>=82.0": act["refusal_recall_pct"] >= GATES["refusal_recall_min"],
    }
    result["gate_checks_primary"] = checks_primary
    result["gate_checks_secondary_descriptive"] = checks_secondary
    result["falsifier_fired"] = not checks_primary["transfer_auroc>=0.70"]
    result["primary_gates_pass"] = all(checks_primary.values())

    out = a.out or (test_dir.parent / "amendment_p_xdataset_transfer.json")
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
