#!/usr/bin/env python3
"""Amendment AJ: knowledge-subspace erasure test of caution's reducibility.

Pre-registered in experiment/protocol/AMENDMENT-AJ-knowledge-subspace-erasure.md.
CPU-only, runs on the cached L35 h_lora states of the clean-SFT -> GRPO-v2
SelfAware extraction (extraction__55254a04aa1f) and the frozen behavior rows.

Headline instrument: LEACE (Belrose et al. 2023) erasure of the gold
answerability concept, fit out-of-fold, with an empirical erasure certificate
(a freshly fit knowledge probe on erased held-out rows must read <= 0.55
AUROC). Primary contrast: held-out refuse/answer (caution) AUROC on erased
states vs an equal-rank random-direction erasure control run through the
identical machinery. Descriptive companion: an INLP rank curve (k = 1..40)
with a matched random-rank curve.

Smoke mode (--smoke) runs the full pipeline on synthetic data in two planted
regimes (caution partially independent of knowledge; caution identical to
knowledge) and asserts the instrument detects both, without touching real data.
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
DEFAULT_ROWS = (
    REPO
    / "experiment/phase1/probe/analysis/current_selfaware_behavior_rows/clean_sft_grpo_v2/rows.jsonl"
)
DEFAULT_EXTRACTION = (
    REPO
    / "experiment/phase1/probe/qwen3-4b-clean-sft-grpo-v2-seed1-selfaware/hidden_states_selfaware_clean_sft_grpo_v2_full/extraction__55254a04aa1f"
)
DEFAULT_OUT = (
    REPO / "experiment/phase1/probe/analysis/amendment_aj_subspace_erasure"
)

LAYER = "L35"
TENSOR_SUFFIX = "__h_lora.safetensors"
SEED = 20260704
N_FOLDS = 5
N_RANDOM = 20          # random-direction erasure repeats (LEACE-rank control)
INLP_MAX_K = 40
INLP_RANDOM_REPEATS = 5
BOOTSTRAP = 2000
CAUTION_POS = "known_refused"
CAUTION_NEG = "known_correct_answered"

# Locked gate constants (mirrored in the amendment doc; do not edit post-launch)
G1_CERT_MAX = 0.55
G2_CAUTION_MIN = 0.70
G2_DELTA_VS_RANDOM_MAX = 0.05
FALSIFIER_CAUTION_BELOW = 0.65


def _logistic():
    from sklearn.linear_model import LogisticRegression

    return LogisticRegression(C=0.5, max_iter=2000)


def _fit_score(X_tr, y_tr, X_te):
    """Standardize on train, fit logistic, return held-out scores."""
    from sklearn.preprocessing import StandardScaler

    sc = StandardScaler().fit(X_tr)
    clf = _logistic().fit(sc.transform(X_tr), y_tr)
    return clf.predict_proba(sc.transform(X_te))[:, 1]


def _auroc(y, s):
    from sklearn.metrics import roc_auc_score

    return float(roc_auc_score(y, s))


class LeaceEraser:
    """Closed-form rank-1 LEACE eraser for a binary concept.

    x' = x - b * ((x - mu) @ a) with a = Sigma^-1/2 u, b = Sigma^1/2 u and
    u the whitened cross-covariance direction; guarantees zero cross-covariance
    between x' and z (linear guardedness), verified empirically by the
    certificate probe.
    """

    def __init__(self, X, z, shrink=1e-2):
        X = np.asarray(X, dtype=np.float64)
        self.mu = X.mean(axis=0)
        Xc = X - self.mu
        d = X.shape[1]
        Sigma = (Xc.T @ Xc) / len(X)
        lam = shrink * np.trace(Sigma) / d
        Sigma[np.diag_indices(d)] += lam
        w, V = np.linalg.eigh(Sigma)
        w = np.clip(w, 1e-12, None)
        self._s_half = (V * np.sqrt(w)) @ V.T
        self._s_ihalf = (V / np.sqrt(w)) @ V.T
        zc = np.asarray(z, dtype=np.float64) - np.mean(z)
        sigma_xz = Xc.T @ zc / len(X)
        u = self._s_ihalf @ sigma_xz
        n = np.linalg.norm(u)
        if n < 1e-12:
            raise ValueError("degenerate concept direction")
        self.u = u / n
        self._set_direction(self.u)

    def _set_direction(self, u):
        self.a = self._s_ihalf @ u
        self.b = self._s_half @ u

    def with_random_direction(self, rng):
        """Same whitening, random whitened unit direction (control eraser)."""
        import copy

        other = copy.copy(self)
        u = rng.standard_normal(len(self.mu))
        other._set_direction(u / np.linalg.norm(u))
        return other

    def apply(self, X):
        Xc = np.asarray(X, dtype=np.float64) - self.mu
        coef = Xc @ self.a
        return X - np.outer(coef, self.b)


def inlp_directions(X_tr, z_tr, k_max, seed):
    """Iterative nullspace projection: k logistic directions fit on train."""
    from sklearn.preprocessing import StandardScaler

    sc = StandardScaler().fit(X_tr)
    Xt = sc.transform(X_tr)
    dirs = []
    rng_state = seed
    for _ in range(k_max):
        clf = _logistic()
        clf.random_state = rng_state
        clf.fit(Xt, z_tr)
        w = clf.coef_[0].astype(np.float64)
        for d0 in dirs:
            w = w - (w @ d0) * d0
        n = np.linalg.norm(w)
        if n < 1e-10:
            break
        w /= n
        dirs.append(w)
        Xt = Xt - np.outer(Xt @ w, w)
    return sc, dirs


def project_out(X_std, dirs, k):
    Xp = X_std.copy()
    for w in dirs[:k]:
        Xp = Xp - np.outer(Xp @ w, w)
    return Xp


def load_real_surface(rows_path, extraction_dir):
    from safetensors.numpy import load_file

    rows = []
    with open(rows_path) as f:
        for line in f:
            rows.append(json.loads(line))
    X, z, cell = [], [], []
    missing = 0
    for r in rows:
        key = r.get("probe_pool_row_key") or r["row_key"]
        p = Path(extraction_dir) / f"{key}{TENSOR_SUFFIX}"
        if not p.exists():
            missing += 1
            continue
        X.append(load_file(str(p))[LAYER].astype(np.float32).reshape(-1))
        z.append(1 if r["label"] == "unknown" else 0)
        cell.append(r["behavior_cell"])
    if missing:
        print(f"WARN: {missing} rows had no tensor file", file=sys.stderr)
    return np.stack(X), np.asarray(z), np.asarray(cell)


def make_synthetic(regime, n=1200, d=64, seed=SEED):
    """Two planted regimes for the smoke test.

    'independent': caution has a component orthogonal to knowledge (survives).
    'identical'  : caution IS the knowledge direction (collapses).
    """
    rng = np.random.default_rng(seed)
    g = rng.standard_normal(d)
    g /= np.linalg.norm(g)
    if regime == "independent":
        c = rng.standard_normal(d)
        c -= (c @ g) * g
        c /= np.linalg.norm(c)
        c = 0.6 * g + 0.8 * c  # partial overlap, like the observed geometry
    elif regime == "identical":
        c = g.copy()
    else:
        raise ValueError(regime)
    X = rng.standard_normal((n, d))
    z = (X @ g + 0.5 * rng.standard_normal(n) > 0).astype(int)
    X += np.outer(z - z.mean(), 2.0 * g)  # make z strongly readable
    refuse_logit = X @ c + 0.75 * rng.standard_normal(n)
    refuse = (refuse_logit > np.quantile(refuse_logit, 0.65)).astype(int)
    cell = np.where(
        z == 1,
        "unknown_refused",
        np.where(refuse == 1, CAUTION_POS, CAUTION_NEG),
    )
    return X.astype(np.float32), z, cell


def run_surface(X, z, cell, seed=SEED, inlp_max_k=INLP_MAX_K,
                n_random=N_RANDOM, inlp_random_repeats=INLP_RANDOM_REPEATS):
    from sklearn.model_selection import StratifiedKFold

    n = len(X)
    caution_mask = np.isin(cell, [CAUTION_POS, CAUTION_NEG])
    caution_y = (cell == CAUTION_POS).astype(int)
    strat = z * 10 + np.where(caution_mask, caution_y + 1, 0)
    skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=seed)
    rng = np.random.default_rng(seed)

    oof = {
        "knowledge_baseline": np.full(n, np.nan),
        "knowledge_post_leace": np.full(n, np.nan),
        "caution_baseline": np.full(n, np.nan),
        "caution_post_leace": np.full(n, np.nan),
        "caution_post_random": np.full((n_random, n), np.nan),
    }
    inlp_curve = {
        k: {"cert": np.full(n, np.nan), "caution": np.full(n, np.nan)}
        for k in range(1, inlp_max_k + 1)
    }
    inlp_random = {
        k: [np.full(n, np.nan) for _ in range(inlp_random_repeats)]
        for k in range(1, inlp_max_k + 1)
    }

    for tr, te in skf.split(X, strat):
        Xtr, Xte = X[tr].astype(np.float64), X[te].astype(np.float64)
        ctr_m, cte_m = caution_mask[tr], caution_mask[te]

        def caution_fit_score(A_tr, A_te):
            return _fit_score(
                A_tr[ctr_m], caution_y[tr][ctr_m], A_te[cte_m]
            )

        # Baselines (no erasure)
        oof["knowledge_baseline"][te] = _fit_score(Xtr, z[tr], Xte)
        oof["caution_baseline"][te[cte_m]] = caution_fit_score(Xtr, Xte)

        # LEACE erasure of the knowledge concept
        eraser = LeaceEraser(Xtr, z[tr])
        Etr, Ete = eraser.apply(Xtr), eraser.apply(Xte)
        oof["knowledge_post_leace"][te] = _fit_score(Etr, z[tr], Ete)
        oof["caution_post_leace"][te[cte_m]] = caution_fit_score(Etr, Ete)

        # Equal-rank random-direction control (same whitening machinery)
        for r in range(n_random):
            rc = eraser.with_random_direction(rng)
            Rtr, Rte = rc.apply(Xtr), rc.apply(Xte)
            oof["caution_post_random"][r, te[cte_m]] = caution_fit_score(
                Rtr, Rte
            )

        # INLP rank curve (descriptive)
        sc, dirs = inlp_directions(Xtr, z[tr], inlp_max_k, seed)
        Xtr_s, Xte_s = sc.transform(Xtr), sc.transform(Xte)
        for k in range(1, min(inlp_max_k, len(dirs)) + 1):
            Ptr, Pte = project_out(Xtr_s, dirs, k), project_out(Xte_s, dirs, k)
            inlp_curve[k]["cert"][te] = _fit_score(Ptr, z[tr], Pte)
            inlp_curve[k]["caution"][te[cte_m]] = caution_fit_score(Ptr, Pte)
        d = X.shape[1]
        for rep in range(inlp_random_repeats):
            Q = np.linalg.qr(
                rng.standard_normal((d, min(inlp_max_k, d)))
            )[0].T
            for k in range(1, inlp_max_k + 1):
                Ptr = project_out(Xtr_s, list(Q), k)
                Pte = project_out(Xte_s, list(Q), k)
                inlp_random[k][rep][te[cte_m]] = caution_fit_score(Ptr, Pte)

    cm = caution_mask
    res = {
        "n_rows": int(n),
        "n_caution_rows": int(cm.sum()),
        "knowledge_auroc_baseline": _auroc(z, oof["knowledge_baseline"]),
        "certificate_auroc_post_leace": _auroc(z, oof["knowledge_post_leace"]),
        "caution_auroc_baseline": _auroc(
            caution_y[cm], oof["caution_baseline"][cm]
        ),
        "caution_auroc_post_leace": _auroc(
            caution_y[cm], oof["caution_post_leace"][cm]
        ),
        "caution_auroc_post_random_mean": float(
            np.mean(
                [
                    _auroc(caution_y[cm], oof["caution_post_random"][r, cm])
                    for r in range(n_random)
                ]
            )
        ),
    }

    # Bootstrap CI on (random-control mean - LEACE) caution gap, row-resampled
    rows_c = np.flatnonzero(cm)
    yc = caution_y[cm]
    brng = np.random.default_rng(seed + 1)
    gaps, leace_boot = [], []
    for _ in range(BOOTSTRAP):
        idx = brng.integers(0, len(rows_c), len(rows_c))
        yb = yc[idx]
        if yb.min() == yb.max():
            continue
        sl = oof["caution_post_leace"][rows_c][idx]
        a_le = _auroc(yb, sl)
        a_rn = np.mean(
            [
                _auroc(yb, oof["caution_post_random"][r, rows_c][idx])
                for r in range(n_random)
            ]
        )
        leace_boot.append(a_le)
        gaps.append(a_rn - a_le)
    res["caution_post_leace_ci95"] = [
        float(np.percentile(leace_boot, 2.5)),
        float(np.percentile(leace_boot, 97.5)),
    ]
    res["random_minus_leace_gap"] = float(
        res["caution_auroc_post_random_mean"] - res["caution_auroc_post_leace"]
    )
    res["random_minus_leace_gap_ci95"] = [
        float(np.percentile(gaps, 2.5)),
        float(np.percentile(gaps, 97.5)),
    ]

    res["inlp_curve"] = {
        str(k): {
            "certificate_auroc": _auroc(z, v["cert"]),
            "caution_auroc": _auroc(caution_y[cm], v["caution"][cm]),
            "caution_auroc_random_mean": float(
                np.mean(
                    [
                        _auroc(caution_y[cm], inlp_random[k][rep][cm])
                        for rep in range(inlp_random_repeats)
                    ]
                )
            ),
        }
        for k, v in inlp_curve.items()
        if not np.isnan(v["cert"]).any()
    }

    res["gates"] = {
        "AJ_G1_certificate_pass": bool(
            res["certificate_auroc_post_leace"] <= G1_CERT_MAX
        ),
        "AJ_G2_caution_survives": bool(
            res["caution_auroc_post_leace"] >= G2_CAUTION_MIN
            and res["random_minus_leace_gap"] <= G2_DELTA_VS_RANDOM_MAX
        ),
        "falsifier_fired": bool(
            res["caution_auroc_post_leace"] < FALSIFIER_CAUTION_BELOW
        ),
        "locked": {
            "G1_CERT_MAX": G1_CERT_MAX,
            "G2_CAUTION_MIN": G2_CAUTION_MIN,
            "G2_DELTA_VS_RANDOM_MAX": G2_DELTA_VS_RANDOM_MAX,
            "FALSIFIER_CAUTION_BELOW": FALSIFIER_CAUTION_BELOW,
        },
    }
    return res


def smoke():
    print("SMOKE regime A: caution partially independent of knowledge")
    Xa, za, ca = make_synthetic("independent")
    ra = run_surface(
        Xa, za, ca, inlp_max_k=8, n_random=8, inlp_random_repeats=3
    )
    print(json.dumps({k: ra[k] for k in list(ra)[:8]}, indent=2))
    assert ra["knowledge_auroc_baseline"] > 0.9, "planted z not readable"
    assert ra["gates"]["AJ_G1_certificate_pass"], (
        f"certificate failed in regime A: {ra['certificate_auroc_post_leace']}"
    )
    assert ra["gates"]["AJ_G2_caution_survives"], (
        "independent caution should survive erasure"
    )

    print("SMOKE regime B: caution identical to knowledge")
    Xb, zb, cb = make_synthetic("identical")
    rb = run_surface(
        Xb, zb, cb, inlp_max_k=8, n_random=8, inlp_random_repeats=3
    )
    print(json.dumps({k: rb[k] for k in list(rb)[:8]}, indent=2))
    assert rb["gates"]["AJ_G1_certificate_pass"], (
        f"certificate failed in regime B: {rb['certificate_auroc_post_leace']}"
    )
    assert rb["gates"]["falsifier_fired"], (
        f"identical caution should collapse, got "
        f"{rb['caution_auroc_post_leace']}"
    )
    print("SMOKE PASS: both regimes detected correctly")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--rows", default=str(DEFAULT_ROWS))
    ap.add_argument("--extraction", default=str(DEFAULT_EXTRACTION))
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT))
    args = ap.parse_args()

    if args.smoke:
        smoke()
        return 0

    X, z, cell = load_real_surface(args.rows, args.extraction)
    print(f"loaded {len(X)} rows, dim {X.shape[1]}")
    res = run_surface(X, z, cell)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "result.json"
    with open(out, "w") as f:
        json.dump(res, f, indent=2)
    print(json.dumps({k: v for k, v in res.items() if k != "inlp_curve"},
                     indent=2))
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
