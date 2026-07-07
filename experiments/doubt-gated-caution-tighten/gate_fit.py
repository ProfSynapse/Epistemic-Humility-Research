#!/usr/bin/env python3
"""Doubt-gated caution snap -- gate (tau) fit on the FIT split ONLY
(CPU-only, no GPU, no new activations).

The GATE is a doubt threshold. Per AMENDMENT.md's Design section: confab
rows have LOW doubt relative to known_correct_answered rows, so the score
that separates them is `neg_z_d = -z_d` (higher = more confab-like = fire).
This mirrors the sibling two-signal diagnostic's own step1_tau_fit.py finding
(neg_z_d AUC 0.976 on the FULL, non-split pool) -- this script re-derives
that AUC and tau on the FIT split only, so the frozen tau is never chosen
using any row this instrument later grades.

z_d is standardized using build_directions.py's own FIT-pool mu_d/sigma_d
(analysis-committed/build_manifest.json), clipped to [-2, +2] -- same
standardization convention as the sibling two-signal build.

Youden-J tau is the primary (pre-registered) choice; precision-target
(precision >= 0.9) is also reported for audit, per AMENDMENT.md's "Youden-J
or a precision-target" wording, but Youden-J is the one gate_fit.json marks
`tau_frozen` and pipeline.py reads.

Output: analysis-committed/gate_fit.json (tau, AUC on FIT, sign convention,
Youden stats, precision-target stats -- no row text).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ANALYSIS = HERE / "analysis"
COMMITTED = HERE / "analysis-committed"

EXTRACT_TENSORS = ANALYSIS / "l34_anchor_extract.safetensors"
EXTRACT_MANIFEST = ANALYSIS / "l34_anchor_extract_manifest.json"
SPLIT_MANIFEST = COMMITTED / "split_manifest.json"
U_D_PATH = COMMITTED / "u_d_L34.json"
BUILD_MANIFEST = COMMITTED / "build_manifest.json"

OUT_PATH = COMMITTED / "gate_fit.json"


def _sanitize_key(row_key: str) -> str:
    return row_key.replace(":", "_")


def load_direction(p: Path) -> np.ndarray:
    d = json.loads(p.read_text())
    return np.asarray(d["vector"], dtype=np.float64)


def roc_auc(scores: np.ndarray, labels: np.ndarray) -> float:
    try:
        from sklearn.metrics import roc_auc_score
        return float(roc_auc_score(labels, scores))
    except ImportError:
        pos = scores[labels == 1]
        neg = scores[labels == 0]
        n_pos, n_neg = len(pos), len(neg)
        count = 0.0
        for p in pos:
            count += (p > neg).sum() + 0.5 * (p == neg).sum()
        return float(count / (n_pos * n_neg))


def youden_tau(scores: np.ndarray, labels: np.ndarray) -> tuple[float, dict]:
    candidates = np.unique(scores)
    best_tau = None
    best_j = -1e9
    best_stats = None
    for tau in candidates:
        pred = scores >= tau
        tp = int(np.sum(pred & (labels == 1)))
        fn = int(np.sum(~pred & (labels == 1)))
        fp = int(np.sum(pred & (labels == 0)))
        tn = int(np.sum(~pred & (labels == 0)))
        tpr = tp / (tp + fn) if (tp + fn) else 0.0
        fpr = fp / (fp + tn) if (fp + tn) else 0.0
        j = tpr - fpr
        if j > best_j:
            best_j = j
            best_tau = float(tau)
            best_stats = {"tpr_confab_caught": tpr, "fpr_known_correct_flagged": fpr,
                          "tp": tp, "fn": fn, "fp": fp, "tn": tn, "youden_j": j}
    return best_tau, best_stats


def precision_tau(scores: np.ndarray, labels: np.ndarray, target_precision: float = 0.9
                   ) -> tuple[float | None, dict | None]:
    best_tau = None
    best_stats = None
    for tau in np.unique(scores):
        pred = scores >= tau
        tp = int(np.sum(pred & (labels == 1)))
        fp = int(np.sum(pred & (labels == 0)))
        fn = int(np.sum(~pred & (labels == 1)))
        tn = int(np.sum(~pred & (labels == 0)))
        n_flagged = tp + fp
        if n_flagged == 0:
            continue
        precision = tp / n_flagged
        if precision >= target_precision:
            tpr = tp / (tp + fn) if (tp + fn) else 0.0
            fpr = fp / (fp + tn) if (fp + tn) else 0.0
            stats = {"precision": precision, "tpr_confab_caught": tpr,
                      "fpr_known_correct_flagged": fpr, "tp": tp, "fn": fn,
                      "fp": fp, "tn": tn, "n_flagged": n_flagged}
            if best_tau is None or tau < best_tau:
                best_tau = float(tau)
                best_stats = stats
    return best_tau, best_stats


def main() -> int:
    extract_manifest = json.loads(EXTRACT_MANIFEST.read_text())
    role_by_key = {rm["row_key"]: rm["role"] for rm in extract_manifest["rows"]}
    split_manifest = json.loads(SPLIT_MANIFEST.read_text())
    split_by_key = {r["row_key"]: r["split"] for r in split_manifest["rows"]}

    confab_fit = [rk for rk, role in role_by_key.items()
                  if role == "confab" and split_by_key.get(rk) == "fit"]
    known_fit = [rk for rk, role in role_by_key.items()
                 if role == "known_correct_answered" and split_by_key.get(rk) == "fit"]

    from safetensors.numpy import load_file
    tensors = load_file(str(EXTRACT_TENSORS))
    fresh = {k: np.asarray(v, dtype=np.float64) for k, v in tensors.items()}

    u_d = load_direction(U_D_PATH)
    build_manifest = json.loads(BUILD_MANIFEST.read_text())
    mu_d, sigma_d = build_manifest["mu_d"], build_manifest["sigma_d"]

    def z_d_for(keys: list[str]) -> np.ndarray:
        H = np.stack([fresh[_sanitize_key(rk)] for rk in keys])
        proj_d = H @ u_d
        return np.clip((proj_d - mu_d) / sigma_d, -2.0, 2.0)

    z_d_confab = z_d_for(confab_fit)
    z_d_known = z_d_for(known_fit)

    z_d = np.concatenate([z_d_confab, z_d_known])
    labels = np.concatenate([np.ones(len(confab_fit)), np.zeros(len(known_fit))]).astype(int)
    score = -z_d  # neg_z_d: LOW doubt -> HIGH score -> confab-like -> fire

    auc = roc_auc(score, labels)
    auc_raw_zd = roc_auc(z_d, labels)

    y_tau, y_stats = youden_tau(score, labels)
    p_tau, p_stats = precision_tau(score, labels, target_precision=0.9)

    report = {
        "population": {
            "positive_class": f"confab FIT (n={len(confab_fit)})",
            "negative_class": f"known_correct_answered FIT (n={len(known_fit)})",
        },
        "score_definition": "neg_z_d = -z_d (z_d clipped to [-2,+2], standardized with "
                             "build_directions.py's FIT-pool mu_d/sigma_d)",
        "sign_convention": "confab rows have LOW doubt (low z_d) vs known_correct_answered; "
                            "fire iff neg_z_d >= tau, i.e. z_d <= -tau",
        "auc_neg_z_d_on_fit": auc,
        "auc_raw_z_d_on_fit": auc_raw_zd,
        "youden_tau": {"tau": y_tau, "stats": y_stats},
        "precision_tau_target_0.9": {"tau": p_tau, "stats": p_stats},
        "tau_frozen": y_tau,
        "tau_frozen_method": "youden_j",
    }
    OUT_PATH.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
