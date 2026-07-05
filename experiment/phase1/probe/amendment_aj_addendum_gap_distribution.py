#!/usr/bin/env python3
"""Amendment AJ Addendum A1: sampling distribution of the G2 gap statistic.

Descriptive and gate-free. The AJ run landed in the pre-registered ambiguous
zone (caution 0.858 >= 0.70, but random-control gap 0.053 > 0.05 by 0.003
with CI95 [0.032, 0.076] straddling the threshold). This addendum
characterizes how much of that miss is instrument noise vs a stable estimate,
as input to the user's ambiguous-zone adjudication. No gate constant changes.

Two questions, two instruments:

1. CV-seed stability: rerun the identical LEACE pipeline (no INLP) across
   SWEEP_SEEDS distinct fold assignments / random-control draws. Reports the
   distribution of gap POINT ESTIMATES: if they cluster at ~0.053 the miss is
   stable; if they scatter across 0.05 the primary result was partly fold luck.
2. Row-sampling probability mass: at the primary seed (20260704, 20 random
   repeats, as in the main run) recompute the 2000-resample bootstrap and
   report P(gap <= 0.05) directly, plus the percentile ladder, instead of
   only the CI endpoints.

Reuses the committed AJ harness verbatim (LeaceEraser, fold construction,
fit/score machinery); the only omission is the descriptive INLP curve.
"""

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from amendment_aj_subspace_erasure import (  # noqa: E402
    BOOTSTRAP,
    CAUTION_NEG,
    CAUTION_POS,
    DEFAULT_EXTRACTION,
    DEFAULT_OUT,
    DEFAULT_ROWS,
    G2_DELTA_VS_RANDOM_MAX,
    LeaceEraser,
    N_FOLDS,
    SEED,
    _auroc,
    _fit_score,
    load_real_surface,
)

SWEEP_SEEDS = list(range(1, 25))  # 24 fold assignments, distinct from primary
SWEEP_N_RANDOM = 10               # per-seed control repeats (20 at primary)
PRIMARY_N_RANDOM = 20


def lean_run(X, z, cell, seed, n_random, keep_oof=False):
    """Baselines + LEACE + random controls, identical to run_surface minus INLP."""
    from sklearn.model_selection import StratifiedKFold

    n = len(X)
    caution_mask = np.isin(cell, [CAUTION_POS, CAUTION_NEG])
    caution_y = (cell == CAUTION_POS).astype(int)
    strat = z * 10 + np.where(caution_mask, caution_y + 1, 0)
    skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=seed)
    rng = np.random.default_rng(seed)

    oof_cert = np.full(n, np.nan)
    oof_leace = np.full(n, np.nan)
    oof_base = np.full(n, np.nan)
    oof_random = np.full((n_random, n), np.nan)

    for tr, te in skf.split(X, strat):
        Xtr, Xte = X[tr].astype(np.float64), X[te].astype(np.float64)
        ctr_m, cte_m = caution_mask[tr], caution_mask[te]

        def caution_fit_score(A_tr, A_te):
            return _fit_score(A_tr[ctr_m], caution_y[tr][ctr_m], A_te[cte_m])

        oof_base[te[cte_m]] = caution_fit_score(Xtr, Xte)
        eraser = LeaceEraser(Xtr, z[tr])
        Etr, Ete = eraser.apply(Xtr), eraser.apply(Xte)
        oof_cert[te] = _fit_score(Etr, z[tr], Ete)
        oof_leace[te[cte_m]] = caution_fit_score(Etr, Ete)
        for r in range(n_random):
            rc = eraser.with_random_direction(rng)
            oof_random[r, te[cte_m]] = caution_fit_score(
                rc.apply(Xtr), rc.apply(Xte)
            )

    cm = caution_mask
    yc = caution_y[cm]
    random_aurocs = [_auroc(yc, oof_random[r, cm]) for r in range(n_random)]
    out = {
        "seed": int(seed),
        "certificate_auroc": _auroc(z, oof_cert),
        "caution_auroc_baseline": _auroc(yc, oof_base[cm]),
        "caution_auroc_post_leace": _auroc(yc, oof_leace[cm]),
        "caution_auroc_post_random_mean": float(np.mean(random_aurocs)),
        "caution_auroc_post_random_std": float(np.std(random_aurocs)),
    }
    out["gap"] = float(
        out["caution_auroc_post_random_mean"]
        - out["caution_auroc_post_leace"]
    )
    if keep_oof:
        out["_oof"] = (cm, yc, oof_leace, oof_random)
    return out


def bootstrap_gap_distribution(oof_pack, n_random, seed):
    """Row-resampled gap distribution at one seed; mirrors the main harness."""
    cm, yc, oof_leace, oof_random = oof_pack
    rows_c = np.flatnonzero(cm)
    brng = np.random.default_rng(seed + 1)
    gaps = []
    for _ in range(BOOTSTRAP):
        idx = brng.integers(0, len(rows_c), len(rows_c))
        yb = yc[idx]
        if yb.min() == yb.max():
            continue
        a_le = _auroc(yb, oof_leace[rows_c][idx])
        a_rn = np.mean(
            [
                _auroc(yb, oof_random[r, rows_c][idx])
                for r in range(n_random)
            ]
        )
        gaps.append(a_rn - a_le)
    gaps = np.asarray(gaps)
    pct = {
        str(p): float(np.percentile(gaps, p))
        for p in (2.5, 5, 10, 25, 50, 75, 90, 95, 97.5)
    }
    return {
        "n_resamples": int(len(gaps)),
        "p_gap_le_threshold": float(
            np.mean(gaps <= G2_DELTA_VS_RANDOM_MAX)
        ),
        "threshold": G2_DELTA_VS_RANDOM_MAX,
        "percentiles": pct,
    }


def main():
    X, z, cell = load_real_surface(DEFAULT_ROWS, DEFAULT_EXTRACTION)
    print(f"loaded {len(X)} rows, dim {X.shape[1]}", flush=True)

    res = {"sweep_n_random": SWEEP_N_RANDOM, "per_seed": []}

    # Primary seed: full control count + bootstrap probability mass
    primary = lean_run(
        X, z, cell, SEED, PRIMARY_N_RANDOM, keep_oof=True
    )
    oof_pack = primary.pop("_oof")
    primary["bootstrap"] = bootstrap_gap_distribution(
        oof_pack, PRIMARY_N_RANDOM, SEED
    )
    res["primary"] = primary
    print(json.dumps(primary), flush=True)

    for seed in SWEEP_SEEDS:
        row = lean_run(X, z, cell, seed, SWEEP_N_RANDOM)
        res["per_seed"].append(row)
        print(json.dumps(row), flush=True)

    gaps = np.asarray([r["gap"] for r in res["per_seed"]])
    res["sweep_summary"] = {
        "n_seeds": len(SWEEP_SEEDS),
        "gap_mean": float(gaps.mean()),
        "gap_std": float(gaps.std(ddof=1)),
        "gap_min": float(gaps.min()),
        "gap_max": float(gaps.max()),
        "frac_seeds_gap_le_threshold": float(
            np.mean(gaps <= G2_DELTA_VS_RANDOM_MAX)
        ),
        "threshold": G2_DELTA_VS_RANDOM_MAX,
    }
    print(json.dumps(res["sweep_summary"], indent=2), flush=True)

    out_dir = Path(DEFAULT_OUT)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "addendum_a1_gap_distribution.json"
    with open(out, "w") as f:
        json.dump(res, f, indent=2)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
