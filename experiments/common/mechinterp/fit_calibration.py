#!/usr/bin/env python3
"""Fit a calibration map for the correctness DIAL and ship a runtime artifact (CPU).

The dial probe (StandardScaler + LogisticRegression on a layer-L residual-stream
vector) RANKS correctness well (AUROC ~0.834 @ 4B) but is not a calibrated
probability (raw out-of-fold ECE ~0.151, above the 0.15 bar). For a user-facing,
thresholdable trust number the runtime needs a calibration map applied on top.

This script:
  1. Loads a dual-position extraction (default: the Amendment S stage2 surface) at
     the best post-gen layer, reusing the EXACT probe recipe from
     amendment_s_correctness_probe_score.py (no re-derivation).
  2. Honestly evaluates calibration with NESTED CV: an outer fold gives raw
     out-of-fold P(correct); a calibration map fit ONLY on the outer-train fold
     (via inner out-of-fold probabilities) is applied to the outer-test fold. So
     the reported post-calibration ECE never sees its own evaluation data.
  3. Fits the FINAL shipped artifact on ALL rows: scaler + logistic coefficients
     (applied manually in numpy at runtime, no sklearn-pickle dependency) + the
     calibration map fit on full-data inner out-of-fold probabilities.
  4. Saves a portable artifact (.npz vectors + .json manifest with metrics +
     reliability bins) the two_signal_runtime library loads.

This is engineering glue for the reference runtime, not a probe verdict. It does
not change any locked gate or amendment result; it adds the calibration step the
paper plan flagged as the cheapest do-item.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score

REPO_DIR = Path(__file__).resolve().parents[3]
PROBE_DIR = REPO_DIR / "experiment/phase1/probe"
if str(PROBE_DIR) not in sys.path:
    sys.path.insert(0, str(PROBE_DIR))

# Reuse the canonical probe recipe + metrics (identical estimator family).
from amendment_s_correctness_probe_score import (  # noqa: E402
    load_position_layers,
    oof_probe,
    ece,
    selective_prediction_curve,
)
from amendment_u_two_signal_score import load_u_positions  # noqa: E402

_EPS = 1e-6


def _logit(p: np.ndarray) -> np.ndarray:
    p = np.clip(p, _EPS, 1.0 - _EPS)
    return np.log(p / (1.0 - p))


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


# --------------------------------------------------------------------------- #
# Calibration maps. Each fits on (raw P(correct), y) and applies to raw probs.
# Stored as plain arrays/scalars so the runtime applies them in numpy.
# --------------------------------------------------------------------------- #


def fit_platt(p_raw: np.ndarray, y: np.ndarray) -> dict:
    """Platt scaling: logistic regression on the probe LOGIT. p_cal = sigmoid(a*f+b)."""
    f = _logit(p_raw).reshape(-1, 1)
    lr = LogisticRegression(C=1e6, max_iter=2000)  # near-unpenalized 1-D fit
    lr.fit(f, y)
    return {"method": "platt", "a": float(lr.coef_[0, 0]), "b": float(lr.intercept_[0])}


def apply_platt(cal: dict, p_raw: np.ndarray) -> np.ndarray:
    return _sigmoid(cal["a"] * _logit(p_raw) + cal["b"])


def fit_isotonic(p_raw: np.ndarray, y: np.ndarray) -> dict:
    ir = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
    ir.fit(p_raw, y)
    # X_thresholds_/y_thresholds_ define the piecewise-linear map; runtime np.interp.
    return {
        "method": "isotonic",
        "x": np.asarray(ir.X_thresholds_, dtype=np.float64),
        "y": np.asarray(ir.y_thresholds_, dtype=np.float64),
    }


def apply_isotonic(cal: dict, p_raw: np.ndarray) -> np.ndarray:
    return np.interp(p_raw, cal["x"], cal["y"])


def apply_calmap(cal: dict, p_raw: np.ndarray) -> np.ndarray:
    return apply_platt(cal, p_raw) if cal["method"] == "platt" else apply_isotonic(cal, p_raw)


def reliability_bins(prob: np.ndarray, y: np.ndarray, n_bins: int = 15) -> list[dict]:
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    out = []
    for i in range(n_bins):
        lo, hi = edges[i], edges[i + 1]
        m = (prob >= lo) & (prob < hi) if i < n_bins - 1 else (prob >= lo) & (prob <= hi)
        if not m.any():
            continue
        out.append({
            "bin_lo": round(float(lo), 4),
            "bin_hi": round(float(hi), 4),
            "n": int(m.sum()),
            "mean_confidence": round(float(prob[m].mean()), 4),
            "accuracy": round(float(y[m].mean()), 4),
        })
    return out


def nested_calibrated_oof(X: np.ndarray, y: np.ndarray, seed: int, method: str):
    """Outer-OOF raw probs + outer-OOF calibrated probs (calibrator fit on train only)."""
    raw = np.full(len(y), np.nan)
    cal = np.full(len(y), np.nan)
    outer = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
    for tr, te in outer.split(X, y):
        sc = StandardScaler().fit(X[tr])
        clf = LogisticRegression(C=1.0, max_iter=2000).fit(sc.transform(X[tr]), y[tr])
        raw[te] = clf.predict_proba(sc.transform(X[te]))[:, 1]
        # Calibrator trained on the outer-TRAIN fold via its inner out-of-fold probs.
        p_inner = oof_probe(X[tr], y[tr], seed)
        calmap = fit_platt(p_inner, y[tr]) if method == "platt" else fit_isotonic(p_inner, y[tr])
        cal[te] = apply_calmap(calmap, raw[te])
    assert not np.isnan(raw).any() and not np.isnan(cal).any()
    return raw, cal


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--signal", default="dial", choices=["dial", "gate"],
                    help="dial = correctness post-gen (Amendment S surface); "
                         "gate = answerability pre-gen anchor (Amendment W SelfAware)")
    ap.add_argument("--extraction-dir", type=Path, default=None,
                    help="extraction dir; defaults per --signal "
                         "(dial: amendment_s/stage2; gate: amendment_w/stage2)")
    ap.add_argument("--position", default=None, choices=["pre", "post"],
                    help="default: post for dial, pre for gate")
    ap.add_argument("--layer", type=int, default=None,
                    help="layer index; default = best AUROC layer for the position")
    ap.add_argument("--model", default="unsloth/Qwen3-4B-bnb-4bit",
                    help="base model the artifact is for (recorded in the manifest)")
    ap.add_argument("--model-tag", default="qwen3-4b-instruct")
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=REPO_DIR / "experiments" / "common" / "artifacts" / "two_signal_calibration",
    )
    ap.add_argument("--seed", type=int, default=20260630)
    a = ap.parse_args(argv)

    is_gate = a.signal == "gate"
    position = a.position or ("pre" if is_gate else "post")
    default_ext = (PROBE_DIR / "qwen3-4b-instruct" /
                   ("amendment_w" if is_gate else "amendment_s") / "stage2")
    ext = (a.extraction_dir or default_ext).resolve()
    pos_class, neg_class = ("known", "unknown") if is_gate else ("correct", "wrong")

    print(f"[fit-cal] signal={a.signal} loading {position} layers from {ext}", flush=True)
    if is_gate:
        # answerability: known(1) vs unknown(0) on the pre-gen anchor.
        X_by_layer, labels, _out, _keys = load_u_positions(ext, position)
        y = (labels == "known").astype(int)
    else:
        X_by_layer, y, _keys = load_position_layers(ext, position)
    n_pos, n_neg = int((y == 1).sum()), int((y == 0).sum())
    print(f"[fit-cal] n={len(y)} {pos_class}={n_pos} {neg_class}={n_neg}", flush=True)
    a.position = position  # downstream uses a.position for naming/manifest

    # Pick layer: argmax raw OOF AUROC unless pinned.
    if a.layer is not None:
        layer = a.layer
    else:
        aurocs = {L: roc_auc_score(y, oof_probe(X_by_layer[L], y, a.seed))
                  for L in sorted(X_by_layer)}
        layer = max(aurocs, key=aurocs.get)
        print(f"[fit-cal] best {a.position} layer = L{layer} "
              f"(AUROC {aurocs[layer]:.4f})", flush=True)
    X = X_by_layer[layer]
    hidden_dim = X.shape[1]

    # Raw OOF (matches the existing scorer) + honest nested-CV calibrated OOF.
    raw_oof = oof_probe(X, y, a.seed)
    auroc = float(roc_auc_score(y, raw_oof))
    ece_raw = ece(raw_oof, y)
    _, cal_platt = nested_calibrated_oof(X, y, a.seed, "platt")
    _, cal_iso = nested_calibrated_oof(X, y, a.seed, "isotonic")
    ece_platt = ece(cal_platt, y)
    ece_iso = ece(cal_iso, y)
    shipped_method = "isotonic" if ece_iso <= ece_platt else "platt"
    ece_shipped = min(ece_iso, ece_platt)
    print(f"[fit-cal] AUROC={auroc:.4f}  ECE raw={ece_raw:.4f}  "
          f"platt={ece_platt:.4f}  isotonic={ece_iso:.4f}  -> ship {shipped_method}",
          flush=True)

    # FINAL shipped probe: scaler + logistic on ALL rows (applied in numpy at runtime).
    sc = StandardScaler().fit(X)
    clf = LogisticRegression(C=1.0, max_iter=2000).fit(sc.transform(X), y)
    coef = clf.coef_[0].astype(np.float64)
    intercept = float(clf.intercept_[0])
    # FINAL calibration map: fit on full-data inner OOF probs (held-out by construction).
    p_inner_full = oof_probe(X, y, a.seed)
    final_cal = (fit_platt(p_inner_full, y) if shipped_method == "platt"
                 else fit_isotonic(p_inner_full, y))

    out_dir = a.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    npz_path = out_dir / f"{a.signal}__{a.model_tag}__{a.position}_L{layer}.npz"
    arrays = {
        "scaler_mean": sc.mean_.astype(np.float64),
        "scaler_scale": sc.scale_.astype(np.float64),
        "logreg_coef": coef,
    }
    if shipped_method == "platt":
        cal_meta = {"method": "platt", "a": final_cal["a"], "b": final_cal["b"]}
    else:
        arrays["cal_x"] = final_cal["x"]
        arrays["cal_y"] = final_cal["y"]
        cal_meta = {"method": "isotonic", "x_key": "cal_x", "y_key": "cal_y"}
    np.savez(npz_path, **arrays)

    manifest = {
        "artifact": f"two_signal_{a.signal}",
        "signal": a.signal,
        "pos_class": pos_class,
        "neg_class": neg_class,
        "model": a.model,
        "model_tag": a.model_tag,
        "position": a.position,
        "layer": layer,
        "hidden_dim": hidden_dim,
        "n_layers_plus_embed": int(max(X_by_layer) + 1),
        "logreg_intercept": intercept,
        "calibration": cal_meta,
        "npz": npz_path.name,
        "source_extraction": str(ext),
        "n": int(len(y)), "n_pos": n_pos, "n_neg": n_neg,
        "metrics": {
            "auroc": round(auroc, 4),
            "ece_raw": round(ece_raw, 4),
            "ece_platt": round(ece_platt, 4),
            "ece_isotonic": round(ece_iso, 4),
            "ece_shipped": round(ece_shipped, 4),
            "shipped_method": shipped_method,
            "g3_ece<0.15_raw": bool(ece_raw < 0.15),
            "g3_ece<0.15_calibrated": bool(ece_shipped < 0.15),
        },
        "reliability_raw": reliability_bins(raw_oof, y),
        "reliability_calibrated": reliability_bins(
            cal_iso if shipped_method == "isotonic" else cal_platt, y),
        "selective_prediction_raw": selective_prediction_curve(raw_oof, y),
        "seed": a.seed,
    }
    man_path = out_dir / f"{a.signal}__{a.model_tag}__{a.position}_L{layer}.json"
    print(json.dumps(manifest, indent=2, default=str))
    man_path.write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    print(f"\n[fit-cal] wrote {npz_path}\n[fit-cal] wrote {man_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
