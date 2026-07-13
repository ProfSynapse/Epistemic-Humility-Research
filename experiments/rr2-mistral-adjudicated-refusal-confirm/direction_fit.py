"""Direction/gate fit module for rr2-mistral-adjudicated-refusal-confirm.

Byte-for-byte port (except this docstring) of
`experiments/rr-cross-family-raw-refusal/direction_fit.py`. This experiment
runs NO fresh FIT stage (cell.yaml: "No FIT stage, no dose ladder, no
selection logic"); this module is reused ONLY by `fit_reuse.py`, which calls
`fit_directions`/`fit_byte_identical`/`fit_gate` to RECONSTRUCT RR's already
-committed hs16 fit deterministically from the same FIT rows and anchors RR
used, then asserts the reconstruction's stats match RR's committed
`hs16_fit_build_manifest.json` field-for-field. No new fit DECISION is made
anywhere in this experiment; see `fit_reuse.py`'s own docstring.

Per cell.yaml `instrument.gate` / `instrument.snap`:
  u_d       = unit(mean(H[known_correct_answered FIT]) - mean(H[unknown_refused]))
  caution   = unit(mean(H[unknown_refused]) - mean(H[confab FIT]))          (mass-mean)
  u_p       = unit(LogisticRegression(saga, C=1.0, tol=1e-3, max_iter=5000,
              random_state=SEED).fit(StandardScaler(H[unknown_refused+confab_fit])
              ).coef_ / scale_)                                            (confab propensity)
  c_hat     = unit(caution orthogonalized against span(u_d, u_p))          (QR erase)
  random_direction = unit(np.random.default_rng(SEED+hidden_dim+layer_idx).normal(...))
  mu_d/sigma_d, mu_c/sigma_c computed over FIT (confab_fit + known_fit) projections.
  neg_z_d gate: z_d = clip((proj_d - mu_d)/sigma_d, -2, 2); score = -z_d;
  tau_frozen via Youden-J on FIT confab (positive) vs known_correct_answered
  (negative).

Every fit is run twice and asserted byte-identical before any artifact is
written (`fit_byte_identical`, G0 `directions_byte_identical` check).
"""

from __future__ import annotations

from typing import Any

import numpy as np


def unit(v: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(v))
    return v / n if n else v


def fit_directions(
    rows: list[dict[str, Any]],
    H: dict[str, np.ndarray],
    layer_idx: int,
    hidden_dim: int,
    seed: int,
) -> dict[str, Any]:
    """rows carry role in {"known_correct_answered", "confab", "unknown_refused"}
    and split in {"fit", "held_out", "fit_only"}. H maps row_key -> float64
    hidden-state vector at this layer's anchor position."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    known_fit = [r["row_key"] for r in rows if r["role"] == "known_correct_answered" and r["split"] == "fit"]
    confab_fit = [r["row_key"] for r in rows if r["role"] == "confab" and r["split"] == "fit"]
    unknown = [r["row_key"] for r in rows if r["role"] == "unknown_refused"]
    if not known_fit or not confab_fit or not unknown:
        raise RuntimeError("cannot fit directions with an empty FIT role")

    h_known = np.stack([H[k] for k in known_fit])
    h_unknown = np.stack([H[k] for k in unknown])
    u_d = unit(h_known.mean(0) - h_unknown.mean(0))

    ak_keys = unknown + confab_fit
    h_ak = np.stack([H[k] for k in ak_keys])
    y_confab = np.array([0] * len(unknown) + [1] * len(confab_fit), dtype=int)
    caution = unit(h_ak[y_confab == 0].mean(0) - h_ak[y_confab == 1].mean(0))
    scaler = StandardScaler().fit(h_ak)
    clf = LogisticRegression(solver="saga", tol=1e-3, max_iter=5000, C=1.0, random_state=seed)
    clf.fit(scaler.transform(h_ak), y_confab)
    u_p = unit(clf.coef_.ravel() / scaler.scale_)

    q, _ = np.linalg.qr(np.stack([u_d, u_p], axis=1))
    c_hat = unit(caution - q @ (q.T @ caution))

    fit_keys = confab_fit + known_fit
    h_fit = np.stack([H[k] for k in fit_keys])
    proj_d = h_fit @ u_d
    proj_c = h_fit @ c_hat
    rng = np.random.default_rng(seed + hidden_dim + layer_idx)
    random_dir = unit(rng.normal(size=hidden_dim))

    labels = np.array([1] * len(confab_fit) + [0] * len(known_fit), dtype=int)

    return {
        "u_d": u_d, "u_p": u_p, "caution_dir": caution, "c_hat": c_hat,
        "random_direction": random_dir,
        "known_fit": known_fit, "confab_fit": confab_fit, "unknown_refused": unknown,
        "stats": {
            "layer": layer_idx, "hidden_dim": hidden_dim,
            "n_known_fit": len(known_fit), "n_confab_fit": len(confab_fit),
            "n_unknown_refused": len(unknown),
            "mu_d": float(proj_d.mean()), "sigma_d": float(proj_d.std() or 1.0),
            "mu_c": float(proj_c.mean()), "sigma_c": float(proj_c.std() or 1.0),
        },
        "proj_d_fit": proj_d, "labels": labels,
    }


def fit_byte_identical(left: dict[str, Any], right: dict[str, Any]) -> bool:
    for key in ("u_d", "u_p", "caution_dir", "c_hat", "random_direction"):
        if not np.array_equal(left[key], right[key]):
            return False
    return left["stats"] == right["stats"]


def roc_auc(scores: np.ndarray, labels: np.ndarray) -> float:
    try:
        from sklearn.metrics import roc_auc_score
        return float(roc_auc_score(labels, scores))
    except ImportError:
        pos = scores[labels == 1]
        neg = scores[labels == 0]
        if len(pos) == 0 or len(neg) == 0:
            return 0.5
        count = sum((p > neg).sum() + 0.5 * (p == neg).sum() for p in pos)
        return float(count / (len(pos) * len(neg)))


def youden_tau(scores: np.ndarray, labels: np.ndarray) -> tuple[float, dict]:
    """Youden-J tau on FIT confab (label 1, positive/"fire") vs FIT
    known_correct_answered (label 0, negative), mirroring
    prep_tuner_cell.py:attach_gate / fit_midband_directions.py:_youden_tau."""
    best_tau, best_j, best_stats = None, -1e9, None
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
            best_tau, best_j = float(tau), j
            best_stats = {
                "tp": tp, "fn": fn, "fp": fp, "tn": tn,
                "tpr_confab_caught": tpr, "fpr_known_correct_flagged": fpr,
                "youden_j": j,
            }
    assert best_tau is not None
    return best_tau, best_stats


def fit_gate(fit: dict[str, Any]) -> dict[str, Any]:
    """Score neg_z_d on FIT confab/known_correct_answered, compute AUC and
    freeze tau via Youden-J. Returns the gate summary for G0's
    fit_gate_auc_floor check and later fire-decision scoring."""
    stats = fit["stats"]
    z_d = np.clip((fit["proj_d_fit"] - stats["mu_d"]) / stats["sigma_d"], -2.0, 2.0)
    score = -z_d
    labels = fit["labels"]
    auc = roc_auc(score, labels)
    tau, tau_stats = youden_tau(score, labels)
    return {
        "auc_neg_z_d_on_fit": auc,
        "tau_frozen": tau,
        "youden_tau_stats": tau_stats,
    }


def score_and_fire(
    rows: list[dict[str, Any]], H: dict[str, np.ndarray], fit: dict[str, Any], tau: float,
) -> list[dict[str, Any]]:
    """Apply the frozen gate to an arbitrary row set (FIT or held-out)."""
    u_d = fit["u_d"]
    mu = fit["stats"]["mu_d"]
    sigma = fit["stats"]["sigma_d"] or 1.0
    out = []
    for row in rows:
        proj = float(H[row["row_key"]] @ u_d)
        z_d = float(np.clip((proj - mu) / sigma, -2.0, 2.0))
        score = -z_d
        out.append({**row, "proj_d": proj, "z_d": z_d, "score_neg_z_d": score, "fire": bool(score >= tau)})
    return out
