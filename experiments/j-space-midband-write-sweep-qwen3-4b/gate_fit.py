#!/usr/bin/env python3
"""Fit one frozen doubt gate threshold per candidate layer on the FIT split."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from layers import HS_INDICES, layer_dir_name

HERE = Path(__file__).resolve().parent
ANALYSIS = HERE / "analysis"
COMMITTED = HERE / "analysis-committed"

EXTRACT_TENSORS = ANALYSIS / "layer_sweep_anchor_extract.safetensors"
EXTRACT_MANIFEST = ANALYSIS / "layer_sweep_anchor_extract_manifest.json"
SPLIT_MANIFEST = (
    HERE.parent / "common" / "doubt-gated-caution-tighten-heldout-split" / "split_manifest.json"
)
BUILD_MANIFEST = COMMITTED / "build_manifest_layers.json"
OUT_PATH = COMMITTED / "gate_fit_layers.json"


def _sanitize_key(row_key: str) -> str:
    return row_key.replace(":", "_")


def tensor_key(hs_index: int, row_key: str) -> str:
    return f"hs{hs_index}__{_sanitize_key(row_key)}"


def load_direction(path: Path) -> np.ndarray:
    data = json.loads(path.read_text())
    return np.asarray(data["vector"], dtype=np.float64)


def roc_auc(scores: np.ndarray, labels: np.ndarray) -> float:
    try:
        from sklearn.metrics import roc_auc_score

        return float(roc_auc_score(labels, scores))
    except ImportError:
        pos = scores[labels == 1]
        neg = scores[labels == 0]
        count = 0.0
        for p in pos:
            count += (p > neg).sum() + 0.5 * (p == neg).sum()
        return float(count / (len(pos) * len(neg)))


def youden_tau(scores: np.ndarray, labels: np.ndarray) -> tuple[float, dict]:
    best_tau = None
    best_j = -1e9
    best_stats = None
    for tau in np.unique(scores):
        pred = scores >= tau
        tp = int(np.sum(pred & (labels == 1)))
        fn = int(np.sum(~pred & (labels == 1)))
        fp = int(np.sum(pred & (labels == 0)))
        tn = int(np.sum(~pred & (labels == 0)))
        tpr = tp / (tp + fn) if (tp + fn) else 0.0
        fpr = fp / (fp + tn) if (fp + tn) else 0.0
        j = tpr - fpr
        if j > best_j:
            best_tau = float(tau)
            best_j = j
            best_stats = {
                "tpr_confab_caught": tpr,
                "fpr_known_correct_flagged": fpr,
                "tp": tp,
                "fn": fn,
                "fp": fp,
                "tn": tn,
                "youden_j": j,
            }
    assert best_tau is not None and best_stats is not None
    return best_tau, best_stats


def precision_tau(
    scores: np.ndarray, labels: np.ndarray, target_precision: float = 0.9
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
            stats = {
                "precision": precision,
                "tpr_confab_caught": tpr,
                "fpr_known_correct_flagged": fpr,
                "tp": tp,
                "fn": fn,
                "fp": fp,
                "tn": tn,
                "n_flagged": n_flagged,
            }
            if best_tau is None or tau < best_tau:
                best_tau = float(tau)
                best_stats = stats
    return best_tau, best_stats


def main() -> int:
    from safetensors.numpy import load_file

    extract_manifest = json.loads(EXTRACT_MANIFEST.read_text())
    role_by_key = {rm["row_key"]: rm["role"] for rm in extract_manifest["rows"]}
    split_manifest = json.loads(SPLIT_MANIFEST.read_text())
    split_by_key = {r["row_key"]: r["split"] for r in split_manifest["rows"]}

    confab_fit = [
        rk for rk, role in role_by_key.items()
        if role == "confab" and split_by_key.get(rk) == "fit"
    ]
    known_fit = [
        rk for rk, role in role_by_key.items()
        if role == "known_correct_answered" and split_by_key.get(rk) == "fit"
    ]

    fresh = {k: np.asarray(v, dtype=np.float64) for k, v in load_file(str(EXTRACT_TENSORS)).items()}
    build_manifest = json.loads(BUILD_MANIFEST.read_text())
    labels = np.concatenate([np.ones(len(confab_fit)), np.zeros(len(known_fit))]).astype(int)

    report = {
        "population": {
            "positive_class": f"confab FIT (n={len(confab_fit)})",
            "negative_class": f"known_correct_answered FIT (n={len(known_fit)})",
        },
        "score_definition": (
            "neg_z_d = -z_d; z_d clipped to [-2,+2] and standardized with "
            "each layer's FIT-pool mu_d/sigma_d"
        ),
        "sign_convention": (
            "confab rows have LOW doubt; fire iff neg_z_d >= tau, "
            "equivalently z_d <= -tau"
        ),
        "tau_frozen_method": "youden_j",
        "layers": {},
    }

    for hs_index in HS_INDICES:
        layer_name = layer_dir_name(hs_index)
        u_d = load_direction(COMMITTED / "layers" / layer_name / f"u_d_{layer_name}.json")
        layer_build = build_manifest["layers"][layer_name]
        mu_d = layer_build["mu_d"]
        sigma_d = layer_build["sigma_d"]

        def z_d_for(keys: list[str]) -> np.ndarray:
            h = np.stack([fresh[tensor_key(hs_index, rk)] for rk in keys])
            proj = h @ u_d
            return np.clip((proj - mu_d) / sigma_d, -2.0, 2.0)

        z_d = np.concatenate([z_d_for(confab_fit), z_d_for(known_fit)])
        score = -z_d
        y_tau, y_stats = youden_tau(score, labels)
        p_tau, p_stats = precision_tau(score, labels)
        report["layers"][layer_name] = {
            "hs_index": hs_index,
            "auc_neg_z_d_on_fit": roc_auc(score, labels),
            "auc_raw_z_d_on_fit": roc_auc(z_d, labels),
            "youden_tau": {"tau": y_tau, "stats": y_stats},
            "precision_tau_target_0.9": {"tau": p_tau, "stats": p_stats},
            "tau_frozen": y_tau,
        }

    OUT_PATH.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
