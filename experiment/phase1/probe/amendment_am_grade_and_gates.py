#!/usr/bin/env python3
"""Amendment AM - CPU analysis + gates verdict (residual-catch veto coverage).

Pre-registered: experiments/residual-catch-veto-coverage/AMENDMENT.md
(SIGNED 2026-07-06; §3 statistics, §4 gates, §6 instrumentation). CPU-only; runs
on the host from the canonical checkout after the Modal extract lands. Never
touches the GPU. Results are reported separately from PROTOCOL v0.3 and from the
PR #205 published veto operating characteristics (§1, §7).

INPUTS (the Modal extract output dir, local or downloaded from staging):
  <in-dir>/rows.jsonl                    graded per-row provenance
  <in-dir>/<safe_key>__post.safetensors  post-gen content-token states {L0..L36}
  (pre states are present but the veto is a POST-L20 readout, matching S/W/U.)

WHAT IT COMPUTES (§3, §4, §6):
  * Residual set: the deterministic gate-miss confabs, score_L24 >= 6.559 on the
    regenerated confab-on-unanswerable rows (report the count; 43 on cached A0).
  * Labels: class 1 (hallucination/low-trust) = confab-on-unanswerable OR
    wrong-on-answerable; class 0 (good) = correct-on-answerable.
  * Veto fit: PCA-128 randomized (seed 20260705) + saga LR, class_weight balanced
    (0.816 base rate), fit OUT-OF-FOLD on the answered population, post-L20. The
    veto score is the NEGATED correctness dial (higher = more likely hallucination).
  * AM-G1: OOF veto AUROC separating the residual (positives) from good
    (negatives), with 1,000-resample bootstrap CI (seed 20260705). Gate: AUROC
    >= 0.62 AND bootstrap CI lower bound > 0.55.
  * AM-G2: permutation null (1,000 permutations, seed 20260705); gate: p <= 0.01.
  * Catch-fraction (descriptive) at the aim-small precision-floor operating point
    (precision >= 0.80, bootstrap CI-LB >= 0.70; PR #205 selection).
  * Flavor breakdown, full-population AUROC, post-L20 layer sweep, oracle-56
    overlap. Emits a gates verdict JSON.

Recipe matches vt_lib.fit_full_probe / cv_auroc (PCA-128 randomized svd, saga LR
tol=1e-3 max_iter=2000) EXACTLY, plus class_weight='balanced' per the doc §3.2.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

SEED = 20260705
N_BOOT = 1000
N_PERM = 1000
GATE_CUT = 6.559          # radial balanced gate_cut; frozen residual rule
POST_L20 = 20             # the veto is a post-L20 readout (S/W/U convention)
LAYER_SWEEP = [18, 19, 20, 21, 22, 23, 24, 35]
PRECISION_FLOOR = 0.80
PRECISION_CI_LB_FLOOR = 0.70
# Gate thresholds (LOCKED at signing, §4).
G1_AUROC_FLOOR = 0.62
G1_CI_LB_FLOOR = 0.55
G2_PERM_P_MAX = 0.01
ORACLE_56 = 56            # radial report mean stochastic residual, for continuity


def load_jsonl(p: Path):
    return [json.loads(l) for l in p.open(encoding="utf-8") if l.strip()]


def load_post_layer(in_dir: Path, safe_keys, layer):
    """Stack post-gen states for `layer` across safe_keys. Returns (X, mask)."""
    from safetensors.torch import load_file
    X, mask = [], []
    key = f"L{layer}"
    for sk in safe_keys:
        f = in_dir / f"{sk}__post.safetensors"
        if not f.is_file():
            mask.append(False)
            continue
        t = load_file(str(f))
        if key not in t:
            mask.append(False)
            continue
        X.append(t[key].float().numpy())
        mask.append(True)
    return (np.vstack(X) if X else np.zeros((0, 0))), np.array(mask)


# ---- PCA-128 + saga probe (vt_lib recipe + class_weight balanced, §3.2) ----
def _fit_probe(Xtr, ytr, seed):
    from sklearn.decomposition import PCA
    from sklearn.linear_model import LogisticRegression
    mu = Xtr.mean(0)
    k = min(128, Xtr.shape[0] - 1, Xtr.shape[1])
    pca = PCA(n_components=k, svd_solver="randomized", random_state=seed)
    Ztr = pca.fit_transform(Xtr - mu)
    lr = LogisticRegression(solver="saga", tol=1e-3, max_iter=2000, C=1.0,
                            class_weight="balanced")
    lr.fit(Ztr, ytr)
    return mu, pca, lr


def oof_scores(X, y, seed=SEED, n_splits=5):
    """OOF decision scores for the CORRECTNESS dial (higher = trust/good).
    y here is y_trust: 1 = good (correct-answerable), 0 = hallucination."""
    from sklearn.model_selection import StratifiedKFold
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    oof = np.zeros(len(y))
    for tr, te in skf.split(X, y):
        mu, pca, lr = _fit_probe(X[tr], y[tr], seed)
        Zte = pca.transform(X[te] - mu)
        oof[te] = lr.decision_function(Zte)
    return oof


def auroc(y, s):
    from sklearn.metrics import roc_auc_score
    return float(roc_auc_score(y, s))


def bootstrap_auroc_ci(y, s, n=N_BOOT, seed=SEED):
    rng = np.random.default_rng(seed)
    y = np.asarray(y); s = np.asarray(s)
    idx_pos = np.where(y == 1)[0]
    idx_neg = np.where(y == 0)[0]
    vals = []
    for _ in range(n):
        bp = rng.choice(idx_pos, size=len(idx_pos), replace=True)
        bn = rng.choice(idx_neg, size=len(idx_neg), replace=True)
        bi = np.concatenate([bp, bn])
        try:
            vals.append(auroc(y[bi], s[bi]))
        except ValueError:
            continue
    vals = np.array(vals)
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5)), vals


def permutation_p(y, s, obs, n=N_PERM, seed=SEED):
    rng = np.random.default_rng(seed)
    y = np.asarray(y); s = np.asarray(s)
    null = np.empty(n)
    for i in range(n):
        null[i] = auroc(y, rng.permutation(s))
    # p = fraction of permutations reaching the observed AUROC (resampling floor 1/(n+1))
    ge = int((null >= obs).sum())
    p = (ge + 1) / (n + 1)
    return float(p), float(null.mean()), float(np.percentile(null, 95))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--in-dir", required=True,
                    help="Modal extract output dir (rows.jsonl + post safetensors)")
    ap.add_argument("--out", required=True, help="gates verdict JSON path")
    args = ap.parse_args(argv)

    in_dir = Path(args.in_dir).resolve()
    rows = load_jsonl(in_dir / "rows.jsonl")
    answered = [r for r in rows if r.get("answered")]

    # Labels (§3.2): class 1 (halluc) = confab-on-unanswerable OR wrong-answerable;
    # class 0 (good) = correct-answerable. y_trust = 1 - halluc (dial target).
    def is_halluc(r):
        if r.get("confab_on_unanswerable"):
            return True
        if r.get("gold_class") == "answerable" and r.get("correct") is False:
            return True
        return False

    def is_good(r):
        return r.get("gold_class") == "answerable" and r.get("correct") is True

    halluc_rows = [r for r in answered if is_halluc(r)]
    good_rows = [r for r in answered if is_good(r)]
    # residual = gate-miss confabs: confab-on-unanswerable AND score_L24 >= cut
    residual_rows = [r for r in answered
                     if r.get("confab_on_unanswerable")
                     and float(r.get("score_L24", 0.0)) >= GATE_CUT]

    # The fit population is all answered rows with a defined trust label.
    fit_rows = halluc_rows + good_rows
    y_trust = np.array([0] * len(halluc_rows) + [1] * len(good_rows))
    fit_keys = [r["safe_key"] for r in fit_rows]

    # OOF veto (negated dial) on post-L20 over the fit population.
    Xpost, mask = load_post_layer(in_dir, fit_keys, POST_L20)
    if mask.sum() != len(fit_keys):
        # keep only rows whose safetensors are present; realign labels
        fit_rows = [r for r, m in zip(fit_rows, mask) if m]
        y_trust = y_trust[mask]
    dial_oof = oof_scores(Xpost, y_trust, seed=SEED)   # higher = trust
    veto_oof = -dial_oof                                # higher = hallucination

    key_to_veto = {r["safe_key"]: float(v) for r, v in zip(fit_rows, veto_oof)}
    key_to_halluc = {r["safe_key"]: int(y == 0) for r, y in zip(fit_rows, y_trust)}

    # --- AM-G1 / AM-G2: residual (positives) vs good (negatives) --------------
    resid_keys = [r["safe_key"] for r in residual_rows if r["safe_key"] in key_to_veto]
    good_keys = [r["safe_key"] for r in good_rows if r["safe_key"] in key_to_veto]
    y_rg = np.array([1] * len(resid_keys) + [0] * len(good_keys))
    s_rg = np.array([key_to_veto[k] for k in resid_keys]
                    + [key_to_veto[k] for k in good_keys])

    g1_auroc = auroc(y_rg, s_rg)
    ci_lo, ci_hi, _ = bootstrap_auroc_ci(y_rg, s_rg)
    perm_p, perm_mean, perm_p95 = permutation_p(y_rg, s_rg, g1_auroc)

    am_g1 = bool(g1_auroc >= G1_AUROC_FLOOR and ci_lo > G1_CI_LB_FLOOR)
    am_g2 = bool(perm_p <= G2_PERM_P_MAX)

    # --- catch-fraction at the aim-small precision-floor operating point -------
    # Operate over the full answered population (residual+good is not the warn
    # population; PR #205 selects the threshold on the full hallucination-vs-good
    # pool). Here the warn threshold is chosen on (veto, y_halluc) over the fit
    # population, then catch is measured on the residual.
    all_keys = list(key_to_veto.keys())
    veto_all = np.array([key_to_veto[k] for k in all_keys])
    y_hall_all = np.array([key_to_halluc[k] for k in all_keys])

    def warn_precision(yh, wm):
        return float((wm & (yh == 1)).sum() / wm.sum()) if wm.sum() > 0 else np.nan

    def boot_prec_lb(thr, n=N_BOOT, seed=SEED):
        rng = np.random.default_rng(seed)
        vals = []
        for _ in range(n):
            bi = rng.integers(0, len(veto_all), len(veto_all))
            wm = veto_all[bi] >= thr
            p = warn_precision(y_hall_all[bi], wm)
            if not np.isnan(p):
                vals.append(p)
        return float(np.percentile(vals, 2.5)) if vals else np.nan

    thresholds = np.unique(veto_all)
    chosen_thr = None
    for thr in np.sort(thresholds):
        wm = veto_all >= thr
        prec = warn_precision(y_hall_all, wm)
        if np.isnan(prec) or prec < PRECISION_FLOOR:
            continue
        if boot_prec_lb(thr) >= PRECISION_CI_LB_FLOOR:
            chosen_thr = float(thr)
            break  # lowest threshold clearing the floor = max recall (aim-small)

    catch = {"operating_point_precision_floor": PRECISION_FLOOR,
             "precision_ci_lb_floor": PRECISION_CI_LB_FLOOR,
             "chosen_threshold": chosen_thr}
    if chosen_thr is not None:
        resid_veto = np.array([key_to_veto[k] for k in resid_keys])
        warned = resid_veto >= chosen_thr
        n_caught = int(warned.sum())
        p_hat = n_caught / len(resid_keys) if resid_keys else float("nan")
        sd = (p_hat * (1 - p_hat) / len(resid_keys)) ** 0.5 if resid_keys else float("nan")
        catch.update({"n_residual": len(resid_keys), "n_caught": n_caught,
                      "catch_fraction": p_hat, "binomial_sd": sd})
    else:
        catch.update({"n_residual": len(resid_keys), "n_caught": None,
                      "catch_fraction": None,
                      "note": "no threshold cleared the precision floor"})

    # --- flavor breakdown of catches/escapes on the residual ------------------
    flavor = {}
    if chosen_thr is not None:
        for r in residual_rows:
            if r["safe_key"] not in key_to_veto:
                continue
            fl = r.get("category_canon", "") or "(none)"
            warned = key_to_veto[r["safe_key"]] >= chosen_thr
            d = flavor.setdefault(fl, {"total": 0, "caught": 0})
            d["total"] += 1
            d["caught"] += int(warned)

    # --- full-population AUROC (all halluc vs good) ---------------------------
    full_auroc = auroc(y_hall_all, veto_all)

    # --- post-L20 layer sweep on the residual --------------------------------
    layer_sweep = {}
    for L in LAYER_SWEEP:
        Xl, ml = load_post_layer(in_dir, fit_keys, L)
        if ml.sum() != len(fit_keys):
            fr = [r for r, m in zip((halluc_rows + good_rows), ml) if m]
            yl = y_trust  # already aligned to POST_L20 mask; approximate
            if len(fr) != len(yl):
                layer_sweep[f"L{L}"] = None
                continue
        else:
            yl = np.array([0] * len(halluc_rows) + [1] * len(good_rows))
        try:
            d_oof = oof_scores(Xl, yl, seed=SEED)
            v_oof = -d_oof
            k2v = {r["safe_key"]: float(v)
                   for r, v in zip(halluc_rows + good_rows, v_oof)}
            rk = [k for k in resid_keys if k in k2v]
            gk = [k for k in good_keys if k in k2v]
            yy = np.array([1] * len(rk) + [0] * len(gk))
            ss = np.array([k2v[k] for k in rk] + [k2v[k] for k in gk])
            layer_sweep[f"L{L}"] = round(auroc(yy, ss), 4)
        except Exception:  # noqa: BLE001
            layer_sweep[f"L{L}"] = None

    verdict = {
        "amendment": "AM", "seed": SEED, "gate_cut": GATE_CUT,
        "post_layer": POST_L20,
        "counts": {
            "answered": len(answered),
            "hallucination_class": len(halluc_rows),
            "good_class": len(good_rows),
            "residual_deterministic": len(residual_rows),
            "residual_scored": len(resid_keys),
            "residual_flavor": dict(Counter(
                (r.get("category_canon", "") or "(none)") for r in residual_rows)),
            "base_rate_halluc": round(len(halluc_rows) / max(len(answered), 1), 4),
        },
        "AM_G1": {
            "auroc": round(g1_auroc, 4),
            "bootstrap_ci95": [round(ci_lo, 4), round(ci_hi, 4)],
            "floor": G1_AUROC_FLOOR, "ci_lb_floor": G1_CI_LB_FLOOR,
            "pass": am_g1,
        },
        "AM_G2": {
            "permutation_p": round(perm_p, 5), "null_mean": round(perm_mean, 4),
            "null_p95": round(perm_p95, 4), "p_max": G2_PERM_P_MAX,
            "n_perm": N_PERM, "pass": am_g2,
        },
        "catch_fraction": catch,
        "flavor_breakdown": flavor,
        "full_population_auroc": round(full_auroc, 4),
        "post_l20_layer_sweep": layer_sweep,
        "oracle_56": {
            "deterministic_residual": len(residual_rows),
            "oracle_mean": ORACLE_56,
            "note": "43 deterministic gate-miss set vs report's stochastic ~56",
        },
        "overall": ("PASS" if (am_g1 and am_g2)
                    else ("FAIL" if not (am_g1 or am_g2) else "AMBIGUOUS")),
    }

    Path(args.out).write_text(json.dumps(verdict, indent=2), encoding="utf-8")
    print(json.dumps(verdict, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
