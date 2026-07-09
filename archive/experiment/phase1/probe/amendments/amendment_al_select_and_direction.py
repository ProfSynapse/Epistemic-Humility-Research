#!/usr/bin/env python3
"""Amendment AL step 1: frozen readouts, arm selection, steering direction+alpha.

CPU-only. Consumes ONLY the existing AL-prep TRUE A0 extracts (no GPU): the
pre-generation L24/L35 states over the 1,662-row surface and the byte-pinned
graded rows. Produces the selection manifest the steering run consumes.

Readouts (identical construction to the ungated ceiling sim
amendment_al_prep_radial_ceiling_ungated.py, which set the pre-registered
primary threshold z >= 1.5484):
  c    caution z : logistic refused-vs-answered on PCA-128 of L35, 5-fold OOF
       decision function, z-scored. Used only for the secondary arm's gate.
  prop propensity z : d_confab from the scope check. Features are
       StandardScaler(PCA-128) of L24, caution-residualized (each PCA column
       regressed on c, residuals kept); direction = mean(confab) minus
       mean(unanswerable-refused) on those residuals, OOF over the two defining
       cells and full-fit for every other row; z-scored on the full population.

SELECTION uses the OOF prop z-score at z >= 1.5484 (PRIMARY) so it reproduces
the ceiling-sim operating point exactly (sanity target: 98 rows = 30 confab /
64 refused / 1 correct / 3 wrong). STOP if the count differs by more than
rounding.

STEERING DIRECTION d_raw (amendment section 3.2, FULL-SAMPLE frozen fit):
  d_confab_full = unit(mean_R(confab) - mean_R(un_refused))  in the residual
  PCA-128 space. Map back to raw 2560-dim by undoing the StandardScaler and the
  PCA rotation:  d_raw_unnorm = (d_confab_full / scaler_scale) @ pca_components ;
  d_raw = unit(d_raw_unnorm) in raw space.
ALPHA (single pre-registered value): raw-space projection gap between the confab
  mean and the unanswerable-refused mean along d_raw (raw L24 states):
  alpha = mean_raw(confab) @ d_raw - mean_raw(un_refused) @ d_raw.

SECONDARY (gated-logistic balanced) uses the gated findings thresholds
(gate_cut -2.742 on the caution score c, m_cut -0.009 on the gated commitment
readout). The gated readout differs from the ungated prop only in the
residualization set (caution + flavor); we recompute it here from the same
extracts, matching the gated sim construction, so the secondary pushed set is
reproducible. Reported separately, never pooled with the primary claim.

CONTROL (permuted assignment): 98 rows drawn uniformly at random from all 1,662
(seed recorded), same alpha and direction, disjoint from nothing (pure random).

Outputs (UNTRACKED) under analysis/amendment_al_prep/amendment_al_run/:
  selection_manifest.json  arms, thresholds, pushed row_keys, sanity census
  d_raw.npy                raw-space unit steering direction (2560,)
Usage:
  python amendment_al_select_and_direction.py
"""

import warnings
warnings.filterwarnings("ignore")
import os
os.environ.setdefault("OMP_NUM_THREADS", "8")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "8")
os.environ.setdefault("MKL_NUM_THREADS", "8")

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from sklearn.decomposition import PCA
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler

ARCHIVE_AMENDMENTS_DIR = Path(__file__).resolve().parent
if str(ARCHIVE_AMENDMENTS_DIR) not in sys.path:
    sys.path.insert(0, str(ARCHIVE_AMENDMENTS_DIR))

from path_compat import repo_root  # noqa: E402

from amendment_al_prep_doubt_axis_check import load_a0_stack, load_jsonl  # noqa: E402
from amendment_al_prep_familiarity_vs_knowing import oof_meandiff_proj, unit  # noqa: E402

CANONICAL = repo_root()
DEFAULT_AL_PREP = CANONICAL / "experiment/phase1/probe/analysis/amendment_al_prep"
SEED = 20260705
L_PROP = 24
L_CAUTION = 35
N_PCA = 128
N_SPLITS = 5

# pre-registered operating points (LOCKED in the amendment / findings)
PRIMARY_Z = 1.5484                 # ungated balanced threshold, prop z-score
SECONDARY_GATE_CUT = -2.742        # gated balanced gate_cut on caution score c
SECONDARY_M_CUT = -0.009           # gated balanced m_cut on gated commitment readout
CONTROL_SEED = SEED + 1000         # recorded seed for the permuted draw

# sanity targets for the primary pushed set (amendment section 3.3)
SANITY = {"n": 98, "confab": 30, "refused": 64, "correct": 1, "wrong": 3}


def oof_caution(P35, y_ref, seed):
    """5-fold OOF caution log-odds, z-scored (same as the ceiling sim)."""
    out = np.zeros(len(y_ref))
    skf = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=seed)
    for tr, te in skf.split(P35, y_ref):
        sc = StandardScaler().fit(P35[tr])
        clf = LogisticRegression(solver="saga", tol=1e-3, max_iter=2000,
                                 random_state=seed).fit(sc.transform(P35[tr]),
                                                        y_ref[tr])
        out[te] = clf.decision_function(sc.transform(P35[te]))
    return (out - out.mean()) / out.std()


def flavor_of(r):
    """Refusal-flavor bucket for the gated readout residualization (matches the
    gated sim: category_canon on unanswerable rows, '(none)' otherwise)."""
    return r.get("category_canon") or "(none)"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--al-prep-dir", default=str(DEFAULT_AL_PREP))
    ap.add_argument("--out-subdir", default="amendment_al_run")
    args = ap.parse_args()
    al_prep = Path(args.al_prep_dir)
    out_dir = al_prep / args.out_subdir
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = load_jsonl(al_prep / "true_a0" / "gen/data/rows_graded.jsonl")
    n = len(rows)
    assert n == 1662, f"expected 1662 rows, got {n}"
    row_keys = [r["row_key"] for r in rows]

    print("[load] TRUE A0 L24/L35 stack ...", flush=True)
    stack = load_a0_stack(al_prep / "true_a0" / "extract/data", row_keys)
    X24 = stack[:, L_PROP, :].astype(np.float64)
    X35 = stack[:, L_CAUTION, :].astype(np.float64)
    del stack

    # ---- PCA + standardize (identical to the sim; capture the transforms so
    #      the direction can be mapped back to raw space) ----
    pca24 = PCA(N_PCA, svd_solver="randomized", random_state=SEED).fit(X24)
    Z24 = pca24.transform(X24)
    scaler24 = StandardScaler().fit(Z24)
    P24 = scaler24.transform(Z24)
    P35 = PCA(N_PCA, svd_solver="randomized", random_state=SEED).fit_transform(X35)

    # ---- caution score c (OOF logistic on refused) ----
    y_ref = np.array([1 if r["refused"] else 0 for r in rows])
    c = oof_caution(P35, y_ref, SEED + 1)

    # ---- ungated propensity readout (SELECTION score) ----
    R = P24 - LinearRegression().fit(c.reshape(-1, 1), P24).predict(c.reshape(-1, 1))
    confab_idx = np.array([i for i, r in enumerate(rows)
                           if r["gold_class"] == "unanswerable" and r["answered"]])
    un_ref_idx = np.array([i for i, r in enumerate(rows)
                           if r["gold_class"] == "unanswerable" and r["refused"]])
    prop_raw = oof_meandiff_proj(R, confab_idx, un_ref_idx, SEED + 2)
    prop = (prop_raw - prop_raw.mean()) / prop_raw.std()

    prop_incell_auroc = float(roc_auc_score(
        np.r_[np.ones(len(confab_idx)), np.zeros(len(un_ref_idx))],
        np.r_[prop[confab_idx], prop[un_ref_idx]]))
    c_auroc = float(roc_auc_score(y_ref, c))
    print(f"[readout] c AUROC={c_auroc:.4f} (sim 0.9561)  "
          f"prop in-cell AUROC={prop_incell_auroc:.4f} (sim 0.6802)", flush=True)

    # ---- behavior labels ----
    def lab(pred):
        return np.array([bool(pred(r)) for r in rows])
    is_confab = lab(lambda r: r["gold_class"] == "unanswerable" and r["answered"])
    is_un_refused = lab(lambda r: r["gold_class"] == "unanswerable" and r["refused"])
    is_ans_refused = lab(lambda r: r["gold_class"] == "answerable" and r["refused"])
    is_correct = lab(lambda r: r["gold_class"] == "answerable" and r["answered"]
                     and r["correct"] is True)
    is_wrong = lab(lambda r: r["gold_class"] == "answerable" and r["answered"]
                   and r["correct"] is False)

    def census(mask):
        return {
            "n": int(mask.sum()),
            "confab": int((mask & is_confab).sum()),
            "refused": int((mask & (is_un_refused | is_ans_refused)).sum()),
            "correct": int((mask & is_correct).sum()),
            "wrong": int((mask & is_wrong).sum()),
        }

    # ---- PRIMARY: prop z >= 1.5484 ----
    primary_mask = prop >= PRIMARY_Z
    prim_census = census(primary_mask)
    print(f"[PRIMARY] z>={PRIMARY_Z} -> census {prim_census} (target {SANITY})",
          flush=True)
    ok = all(abs(prim_census[k] - SANITY[k]) <= 1 for k in SANITY) \
        and prim_census["n"] == SANITY["n"]
    if not ok:
        print("[STOP] primary selection census does not match the amendment "
              "sanity target within rounding.", flush=True)
        (out_dir / "selection_STOP.json").write_text(json.dumps(
            {"primary_census": prim_census, "target": SANITY}, indent=2))
        return 2

    # ---- steering direction d_raw (FULL-SAMPLE frozen fit) ----
    d_confab_full = unit(R[confab_idx].mean(0) - R[un_ref_idx].mean(0))
    # map residual-PCA-space direction back to raw 2560-dim:
    #   P = (Z - Z_mean)/scale ,  Z = X @ components.T  (Z is mean-removed by PCA)
    # a direction v in P-space corresponds to (v / scale) in Z-space, and to
    # (v / scale) @ components in raw X-space.
    d_raw_unnorm = (d_confab_full / scaler24.scale_) @ pca24.components_
    d_raw = unit(d_raw_unnorm)

    # alpha = raw-space projection gap (confab mean - un_refused mean) along d_raw
    raw_proj = X24 @ d_raw
    alpha = float(raw_proj[is_confab].mean() - raw_proj[is_un_refused].mean())
    print(f"[direction] d_raw dim={d_raw.shape[0]} |d_raw|={np.linalg.norm(d_raw):.6f} "
          f"alpha={alpha:.4f}  raw_proj(confab)={raw_proj[is_confab].mean():.3f} "
          f"raw_proj(un_ref)={raw_proj[is_un_refused].mean():.3f}", flush=True)
    if alpha <= 0:
        print("[STOP] alpha non-positive; direction sign wrong.", flush=True)
        return 3

    # ---- SECONDARY: gated-logistic balanced law (reproduce radial_ceiling_true) --
    # The gated sim's balanced operating point is gate_cut=-2.742 on the
    # answerability gate score g (OOF logistic answerable-vs-unanswerable on
    # PCA-128(L24), UNstandardized decision function) and m_cut=-0.009 on the
    # within-unanswerable commitment readout m (4x5-repeat OOF, caution+flavor
    # residualised per fold). Reached = Region2 (g<gate_cut & flavor-shortfall>0)
    # OR Region3 (g<gate_cut & m>=m_cut), restricted to non-degenerate
    # unanswerable rows. The secondary applies the IDENTICAL anti-propensity push
    # (d_raw, alpha) to that reached set; it is exploratory, reported separately,
    # never pooled with the primary claim.
    P24_raw = PCA(N_PCA, svd_solver="randomized", random_state=SEED).fit_transform(X24)
    from sklearn.model_selection import StratifiedKFold as _SKF
    y_ans = np.array([1 if r["gold_class"] == "answerable" else 0 for r in rows])
    g_all = np.zeros(n)
    skf = _SKF(n_splits=N_SPLITS, shuffle=True, random_state=SEED)
    for tr, te in skf.split(P24_raw, y_ans):
        sc = StandardScaler().fit(P24_raw[tr])
        clf = LogisticRegression(solver="saga", tol=1e-3, max_iter=2000,
                                 random_state=SEED).fit(sc.transform(P24_raw[tr]),
                                                        y_ans[tr])
        g_all[te] = clf.decision_function(sc.transform(P24_raw[te]))

    # within-unanswerable commitment m (matches radial_ceiling_true exactly)
    un_pidx = np.array([i for i, r in enumerate(rows)
                        if r["gold_class"] == "unanswerable" and not r["degenerate"]])
    Pun = P24_raw[un_pidx]
    un_rows = [rows[i] for i in un_pidx]
    y_confab_un = np.array([1 if r["confab_on_unanswerable"] else 0 for r in un_rows])
    c_un = c[un_pidx]
    flav_un = np.array([flavor_of(r) for r in un_rows])
    FLAVORS = sorted(set(flav_un))
    FREF = FLAVORS[1:]

    def onehot(catv, ref):
        return np.hstack([(catv == cc).astype(float).reshape(-1, 1) for cc in ref]) \
            if ref else np.zeros((len(catv), 0))

    def confounds(idx):
        return np.hstack([c_un[idx].reshape(-1, 1), onehot(flav_un[idx], FREF)])

    N_REPEAT = 4
    m_oof = np.zeros(len(un_rows))
    n_seen = np.zeros(len(un_rows))
    for rep in range(N_REPEAT):
        skf_m = _SKF(n_splits=N_SPLITS, shuffle=True, random_state=SEED + rep)
        for tr, te in skf_m.split(np.arange(len(un_rows)), y_confab_un):
            lr = LinearRegression().fit(confounds(tr), Pun[tr])
            Rtr = Pun[tr] - lr.predict(confounds(tr))
            Rte = Pun[te] - lr.predict(confounds(te))
            scm = StandardScaler().fit(Rtr)
            Rtr = scm.transform(Rtr)
            Rte = scm.transform(Rte)
            ytr = y_confab_un[tr]
            d = Rtr[ytr == 1].mean(0) - Rtr[ytr == 0].mean(0)
            d = d / (np.linalg.norm(d) + 1e-12)
            m_oof[te] += Rte @ d
            n_seen[te] += 1
    m_oof = m_oof / n_seen

    # per-flavor caution refusal threshold -> shortfall (Region 2)
    flavor_thresh = {}
    for fl in FLAVORS:
        sel = flav_un == fl
        cc = c_un[sel]
        yy = np.array([r["refused"] for r in un_rows])[sel].astype(int)
        if len(set(yy)) < 2:
            flavor_thresh[fl] = float(cc.mean())
            continue
        lr = LogisticRegression(max_iter=2000).fit(cc.reshape(-1, 1), yy)
        b0, b1 = lr.intercept_[0], lr.coef_[0][0]
        flavor_thresh[fl] = float(-b0 / b1) if abs(b1) > 1e-9 else float(cc.mean())
    shortfall = np.array([flavor_thresh[fl] for fl in flav_un]) - c_un

    un_g = g_all[un_pidx]
    un_unans_side = un_g < SECONDARY_GATE_CUT
    r2 = un_unans_side & (shortfall > 0.0)
    r3 = un_unans_side & (m_oof >= SECONDARY_M_CUT)
    reached = r2 | r3
    secondary_mask = np.zeros(n, dtype=bool)
    secondary_mask[un_pidx[reached]] = True
    sec_census = census(secondary_mask)
    sec_census["r2_n"] = int(r2.sum())
    sec_census["r3_n"] = int(r3.sum())
    print(f"[SECONDARY] gate_cut={SECONDARY_GATE_CUT} m_cut={SECONDARY_M_CUT} "
          f"r2={int(r2.sum())} r3={int(r3.sum())} reached={int(reached.sum())} "
          f"-> census {sec_census}", flush=True)

    # ---- CONTROL: permuted assignment, 98 uniformly-random rows (seeded) ----
    rng = np.random.default_rng(CONTROL_SEED)
    control_idx = np.sort(rng.choice(n, size=SANITY["n"], replace=False))
    control_mask = np.zeros(n, dtype=bool)
    control_mask[control_idx] = True
    ctrl_census = census(control_mask)
    print(f"[CONTROL] seed={CONTROL_SEED} -> census {ctrl_census}", flush=True)

    # ---- write direction + manifest ----
    np.save(out_dir / "d_raw.npy", d_raw.astype(np.float32))
    np.save(out_dir / "prop_z.npy", prop.astype(np.float32))
    np.save(out_dir / "caution_z.npy", c.astype(np.float32))

    def keys_of(mask):
        return [row_keys[i] for i in np.nonzero(mask)[0]]

    manifest = {
        "seed": SEED, "control_seed": CONTROL_SEED,
        "layers": {"propensity": L_PROP, "caution": L_CAUTION},
        "config": {"pca": N_PCA, "n_splits": N_SPLITS},
        "readout_quality": {
            "c_oof_auroc_refused": round(c_auroc, 4),
            "prop_incell_oof_auroc": round(prop_incell_auroc, 4)},
        "thresholds": {
            "primary_prop_z": PRIMARY_Z,
            "secondary_gate_cut": SECONDARY_GATE_CUT,
            "secondary_m_cut": SECONDARY_M_CUT},
        "steering": {
            "layer": L_PROP,
            "d_raw_file": "d_raw.npy",
            "d_raw_norm": float(np.linalg.norm(d_raw)),
            "alpha": alpha,
            "alpha_construction": "raw-space proj gap confab_mean - un_refused_mean along d_raw",
            "dose_ladder": [0.5, 2.0]},
        "arms": {
            "primary": {"law": "ungated prop z >= 1.5484",
                        "census": prim_census, "row_keys": keys_of(primary_mask)},
            "control": {"law": "permuted assignment, 98 uniform-random rows",
                        "census": ctrl_census, "row_keys": keys_of(control_mask)},
            "secondary": {"law": "gated-logistic balanced (c<=gate_cut & m>=m_cut)",
                          "census": sec_census, "row_keys": keys_of(secondary_mask)},
        },
        "sanity_target_primary": SANITY,
        "sanity_pass": bool(ok),
    }
    (out_dir / "selection_manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"[select] manifest -> {out_dir / 'selection_manifest.json'}", flush=True)
    print(f"[select] d_raw -> {out_dir / 'd_raw.npy'}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
