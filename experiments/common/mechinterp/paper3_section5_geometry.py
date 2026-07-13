#!/usr/bin/env python3
"""Reconstruction of the paper3 Section 5 two-axis geometry numbers.

The original computations lived in two ephemeral session-scratchpad scripts
(`scratchpad/confidence_vs_axes.py`, `scratchpad/caution_residual_geometry.py`,
session 0026 checkpoints 002/003) that were lost with the session temp dirs;
this checked-in script recomputes the same quantities from the durable inputs
so the paper's citations resolve to a runnable source.

Cited values (paper3 Section 5 / session 0026 003-result):
  raw mass-mean cosine(caution, doubt)              -0.83
  whitened/Mahalanobis cosine (shrinkage lam = 0.1) -0.565
  residual (doubt-orthogonal) fraction of caution    0.557
  held-out refuse/answer AUROC, doubt axis           0.875
  held-out refuse/answer AUROC, caution_perp         0.825
  held-out refuse/answer AUROC, full caution         0.894

Protocol (identified by reconstruction sweep, 2026-07-04):
  rows: kr = all 168 known_refused; ka = 300 of 373 known_correct_answered;
        ur = 300 of 676 unknown_refused (subsample seed of the lost script
        unknown; a seed spread is reported and agreement judged against it)
  directions: doubt = unit(mean(ka) - mean(ur)); caution = mean(kr) - mean(ka)
  whitened cosine: POOLED WITHIN-CLASS covariance over the three cells
        (Mahalanobis), shrunk (1-lam)*S + lam*(tr(S)/d)*I with lam = 0.1;
        this reproduces the cited -0.565 (marginal covariance gives ~-0.43
        and is reported for reference)
  AUROCs: 5-fold held-out on the subsample; directions refit per fold on
        train rows, test knowns scored by projection; caution_perp reported
        in both raw-space and whitened-space orthogonalization variants

Lab-notebook tier: reproduces published numbers, no new claims. CPU-only.
"""

import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
ROWS = (
    REPO
    / "archive/experiment/phase1/probe/legacy-wrapper-tree/analysis/current_selfaware_behavior_rows/clean_sft_grpo_v2/rows.jsonl"
)
EXTRACTION = (
    REPO
    / "archive/experiment/phase1/probe/legacy-wrapper-tree/qwen3-4b-clean-sft-grpo-v2-seed1-selfaware/hidden_states_selfaware_clean_sft_grpo_v2_full/extraction__55254a04aa1f"
)
LAYER = "L35"
KA_N = 300
UR_N = 300
SEEDS = [0, 1, 2, 20260704]
LAMBDA = 0.1
CITED = {
    "raw_cos": -0.83,
    "whitened_cos": -0.565,
    "residual_fraction": 0.557,
    "auroc_doubt": 0.875,
    "auroc_caution_perp": 0.825,
    "auroc_caution": 0.894,
}


def unit(v):
    return v / np.linalg.norm(v)


def cov(M):
    Mc = M - M.mean(0)
    return (Mc.T @ Mc) / len(M)


def whiten_mat(S, lam=LAMBDA):
    d = S.shape[0]
    S = (1 - lam) * S + lam * (np.trace(S) / d) * np.eye(d)
    w, V = np.linalg.eigh(S)
    return (V / np.sqrt(np.clip(w, 1e-12, None))) @ V.T


def load():
    from safetensors.numpy import load_file

    X, cells = [], []
    with open(ROWS) as f:
        for line in f:
            r = json.loads(line)
            key = (r.get("probe_pool_row_key") or r["row_key"]).replace(
                "::", "__"
            )
            p = EXTRACTION / f"{key}__h_lora.safetensors"
            if not p.exists():
                continue
            X.append(load_file(str(p))[LAYER].astype(np.float64).reshape(-1))
            cells.append(r["behavior_cell"])
    return np.stack(X), np.asarray(cells)


def subsample(X, cells, seed):
    rng = np.random.default_rng(seed)
    parts = {"kr": X[cells == "known_refused"]}
    for name, cell, n in (
        ("ka", "known_correct_answered", KA_N),
        ("ur", "unknown_refused", UR_N),
    ):
        pool = np.flatnonzero(cells == cell)
        parts[name] = X[rng.choice(pool, size=min(n, len(pool)), replace=False)]
    return parts


def geometry(parts):
    kr, ka, ur = parts["kr"], parts["ka"], parts["ur"]
    doubt = unit(ka.mean(0) - ur.mean(0))
    caution = kr.mean(0) - ka.mean(0)
    perp = caution - (caution @ doubt) * doubt
    pooled = (
        len(kr) * cov(kr) + len(ka) * cov(ka) + len(ur) * cov(ur)
    ) / (len(kr) + len(ka) + len(ur))
    W = whiten_mat(pooled)
    wc, wd = W @ caution, W @ doubt
    marginal = whiten_mat(cov(np.vstack([kr, ka, ur])))
    mc, md = marginal @ caution, marginal @ doubt
    return {
        "raw_cos": float(unit(caution) @ doubt),
        "whitened_cos_pooled": float(
            wc @ wd / (np.linalg.norm(wc) * np.linalg.norm(wd))
        ),
        "whitened_cos_marginal": float(
            mc @ md / (np.linalg.norm(mc) * np.linalg.norm(md))
        ),
        "residual_fraction": float(
            np.linalg.norm(perp) / np.linalg.norm(caution)
        ),
    }


def heldout_aurocs(parts, seed, n_folds=5):
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import StratifiedKFold

    kr, ka, ur = parts["kr"], parts["ka"], parts["ur"]
    Xs = np.vstack([kr, ka, ur])
    grp = np.r_[
        np.zeros(len(kr), int), np.ones(len(ka), int), 2 * np.ones(len(ur), int)
    ]
    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=seed)
    names = ("doubt", "caution", "perp_raw", "perp_whitened")
    scores = {k: np.full(len(Xs), np.nan) for k in names}
    for tr, te in skf.split(Xs, grp):
        p = {
            "kr": Xs[tr][grp[tr] == 0],
            "ka": Xs[tr][grp[tr] == 1],
            "ur": Xs[tr][grp[tr] == 2],
        }
        doubt = unit(p["ka"].mean(0) - p["ur"].mean(0))
        caution = p["kr"].mean(0) - p["ka"].mean(0)
        perp = caution - (caution @ doubt) * doubt
        pooled = (
            len(p["kr"]) * cov(p["kr"])
            + len(p["ka"]) * cov(p["ka"])
            + len(p["ur"]) * cov(p["ur"])
        ) / len(tr)
        W = whiten_mat(pooled)
        wdoubt = unit(W @ doubt)
        wcaut = W @ caution
        wperp = wcaut - (wcaut @ wdoubt) * wdoubt
        Xte = Xs[te]
        scores["doubt"][te] = Xte @ doubt
        scores["caution"][te] = Xte @ unit(caution)
        scores["perp_raw"][te] = Xte @ unit(perp)
        scores["perp_whitened"][te] = (W @ Xte.T).T @ unit(wperp)
    known = grp < 2
    y = (grp[known] == 0).astype(int)  # refuse = 1 among knowns
    out = {}
    for k in names:
        a = roc_auc_score(y, scores[k][known])
        out[k] = float(max(a, 1 - a))
    return out


def main():
    X, cells = load()
    print(f"loaded {len(X)} rows")
    results = {"cited": CITED, "per_seed": []}
    for seed in SEEDS:
        parts = subsample(X, cells, seed)
        row = {"seed": seed}
        row.update(geometry(parts))
        row["aurocs"] = heldout_aurocs(parts, seed)
        results["per_seed"].append(row)
        print(json.dumps(row))
    # full-sample geometry for reference (no subsampling)
    full = {
        "kr": X[cells == "known_refused"],
        "ka": X[cells == "known_correct_answered"],
        "ur": X[cells == "unknown_refused"],
    }
    results["full_sample_geometry"] = geometry(full)
    print("full sample:", json.dumps(results["full_sample_geometry"]))

    out_dir = REPO / "archive/experiment/phase1/probe/legacy-wrapper-tree/analysis/paper3_section5_geometry"
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "result.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"wrote {out_dir / 'result.json'}")


if __name__ == "__main__":
    main()
