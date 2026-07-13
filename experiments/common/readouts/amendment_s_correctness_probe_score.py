#!/usr/bin/env python3
"""Amendment S — correctness-probe fit + locked-gate scoring (CPU-only).

Pre-registered in experiments/correctness-confidence-probe/AMENDMENT.md
(SIGNED 2026-06-30). Reads the extraction produced by
amendment_s_correctness_probe_extract.py and answers the §4 gates.

Method (§3 steps 3-4):
  * Per (position in {pre, post}) x layer: logistic probe on correct(1)/wrong(0)
    over standardized hidden states, 5-fold stratified CV, out-of-fold P(correct).
    Reuses the Amendment O probe-fit recipe (StandardScaler + LogisticRegression,
    out-of-fold) so pre-gen and post-gen are scored by the IDENTICAL estimator.
  * correctness-AUROC surface over all (position, layer).
  * Headline: best post-gen layer vs best pre-gen layer; delta = post - pre with a
    PAIRED bootstrap 95% CI over rows on the fixed out-of-fold scores.
  * ECE of the best post-gen surfaced confidence vs correctness.
  * Selective-prediction curve (accuracy vs coverage) ranked by best post-gen prob.

LOCKED gates (§4, not tunable here):
  G1 usefulness floor : best post-gen AUROC >= 0.70
  G2 PRIMARY self-eval: (best post - best pre) >= +0.05 AND bootstrap 95% CI > 0
  G3 calibration      : ECE(best post) < 0.15
  SUCCESS  : G2 AND G1.
  FALSIFIER: best post AUROC < 0.70 AND (post - pre) <= +0.05.
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

# Locked gates (Amendment S §4). Reference only — NOT tunable here.
GATES = {
    "g1_post_auroc_min": 0.70,
    "g2_delta_min": 0.05,
    "g3_ece_max": 0.15,
}
POSITIONS = ("pre", "post")


def load_position_layers(ext_dir: Path, position: str):
    """Return (layer -> X[n,d]), y[n], row_keys for one read position.

    Only rows with label in {correct, wrong} AND a present safetensors shard are
    kept; the per-row tensors hold keys L0..L<N>.
    """
    rows = [json.loads(l) for l in (ext_dir / "rows.jsonl").open(encoding="utf-8")
            if l.strip()]
    by_layer: dict[int, list[np.ndarray]] = {}
    y: list[int] = []
    keys: list[str] = []
    for r in rows:
        label = r.get("label")
        if label not in ("correct", "wrong"):
            continue
        safe = str(r["row_key"]).replace("::", "__").replace("|", "_")
        shard = ext_dir / f"{safe}__{position}.safetensors"
        if not shard.exists():
            continue
        t = load_file(str(shard))
        for name, vec in t.items():
            layer = int(name[1:])  # 'L35' -> 35
            by_layer.setdefault(layer, []).append(np.asarray(vec, dtype=np.float64))
        y.append(1 if label == "correct" else 0)
        keys.append(r["row_key"])
    X = {layer: np.vstack(vs) for layer, vs in by_layer.items()}
    return X, np.asarray(y, dtype=int), keys


def oof_probe(X: np.ndarray, y: np.ndarray, seed: int) -> np.ndarray:
    """5-fold stratified CV logistic regression; out-of-fold P(correct).

    Identical recipe to Amendment O's oof_probe (StandardScaler + C=1.0 logistic),
    so pre and post positions are read by the same estimator family.
    """
    p = np.full(len(y), np.nan)
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
    for tr, te in skf.split(X, y):
        sc = StandardScaler().fit(X[tr])
        clf = LogisticRegression(C=1.0, max_iter=2000)
        clf.fit(sc.transform(X[tr]), y[tr])
        p[te] = clf.predict_proba(sc.transform(X[te]))[:, 1]
    assert not np.isnan(p).any()
    return p


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


def selective_prediction_curve(prob: np.ndarray, y: np.ndarray,
                               coverages=(1.0, 0.9, 0.75, 0.5, 0.25, 0.1)) -> list[dict]:
    """Accuracy among the top-coverage fraction ranked by descending confidence."""
    order = np.argsort(-prob)
    y_sorted = y[order]
    n = len(y)
    out = []
    for cov in coverages:
        k = max(1, int(round(cov * n)))
        out.append({"coverage": cov, "n": k,
                    "accuracy": float(y_sorted[:k].mean())})
    return out


def paired_bootstrap_delta(y, p_post, p_pre, n_boot: int, seed: int):
    """Paired bootstrap over rows of (AUROC_post - AUROC_pre) on fixed oof scores."""
    rng = np.random.default_rng(seed)
    n = len(y)
    deltas = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        yb = y[idx]
        if len(np.unique(yb)) < 2:
            continue
        deltas.append(roc_auc_score(yb, p_post[idx]) - roc_auc_score(yb, p_pre[idx]))
    deltas = np.asarray(deltas, dtype=float)
    return {
        "n_boot_effective": int(len(deltas)),
        "ci_lo": float(np.percentile(deltas, 2.5)),
        "ci_hi": float(np.percentile(deltas, 97.5)),
        "mean": float(deltas.mean()) if len(deltas) else float("nan"),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("extraction_dir", type=Path)
    ap.add_argument("--seed", type=int, default=20260630)
    ap.add_argument("--n-boot", type=int, default=2000)
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args(argv)
    ext = a.extraction_dir.resolve()

    surface: dict[str, dict[int, float]] = {}
    oof: dict[str, dict[int, np.ndarray]] = {}
    y_ref = None
    keys_ref = None
    for pos in POSITIONS:
        X, y, keys = load_position_layers(ext, pos)
        if y_ref is None:
            y_ref, keys_ref = y, keys
        else:
            # pre/post must align row-for-row (same answered rows, same order).
            assert keys == keys_ref, f"{pos} row keys diverge from {POSITIONS[0]}"
        surface[pos] = {}
        oof[pos] = {}
        for layer in sorted(X):
            p = oof_probe(X[layer], y, a.seed)
            surface[pos][layer] = float(roc_auc_score(y, p))
            oof[pos][layer] = p

    y = y_ref
    n_correct = int((y == 1).sum())
    n_wrong = int((y == 0).sum())

    best_post_layer = max(surface["post"], key=surface["post"].get)
    best_pre_layer = max(surface["pre"], key=surface["pre"].get)
    auroc_post = surface["post"][best_post_layer]
    auroc_pre = surface["pre"][best_pre_layer]
    delta = auroc_post - auroc_pre

    p_post = oof["post"][best_post_layer]
    p_pre = oof["pre"][best_pre_layer]
    boot = paired_bootstrap_delta(y, p_post, p_pre, a.n_boot, a.seed)
    ece_post = ece(p_post, y)
    selective = selective_prediction_curve(p_post, y)

    g1 = auroc_post >= GATES["g1_post_auroc_min"]
    g2 = (delta >= GATES["g2_delta_min"]) and (boot["ci_lo"] > 0.0)
    g3 = ece_post < GATES["g3_ece_max"]
    success = g1 and g2
    falsifier = (auroc_post < GATES["g1_post_auroc_min"]) and (delta <= GATES["g2_delta_min"])

    result = {
        "amendment": "S",
        "extraction_dir": str(ext),
        "n_answered_labeled": int(len(y)),
        "n_correct": n_correct,
        "n_wrong": n_wrong,
        "data_adequacy_ok": (n_correct >= 150 and n_wrong >= 150),
        "auroc_surface": {
            pos: {str(k): round(v, 4) for k, v in sorted(surface[pos].items())}
            for pos in POSITIONS
        },
        "headline": {
            "best_post_layer": best_post_layer,
            "best_pre_layer": best_pre_layer,
            "auroc_post": round(auroc_post, 4),
            "auroc_pre": round(auroc_pre, 4),
            "delta_post_minus_pre": round(delta, 4),
            "delta_bootstrap_ci": boot,
            "ece_post": round(ece_post, 4),
        },
        "selective_prediction": selective,
        "gates": {
            "G1_post_auroc>=0.70": g1,
            "G2_delta>=0.05_and_ci>0": g2,
            "G3_ece<0.15": g3,
        },
        "verdict": {
            "SUCCESS": success,
            "FALSIFIER_FIRED": falsifier,
            "AMBIGUOUS": (not success) and (not falsifier),
        },
    }

    # Print FIRST so a read-only extraction dir (docker-root-owned outputs on the
    # 9P Windows mount) never loses the computed result.
    print(json.dumps(result, indent=2))
    out = a.out or (ext / "amendment_s_score.json")
    try:
        out.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"\nwrote {out}")
    except OSError as exc:
        print(f"\n[warn] could not write {out} ({exc}); result printed above. "
              "Pass --out <writable path> to persist.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
