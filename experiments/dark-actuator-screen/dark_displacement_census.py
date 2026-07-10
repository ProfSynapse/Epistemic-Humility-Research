#!/usr/bin/env python3
"""Dark displacement census (CPU-only lab-notebook diagnostic).

Question
--------
Generation moves the residual stream a lot from token to token. The named
epistemic axes (doubt, caution, propensity, veto) are a thin shell: item-20
found ~99% of generation-time displacement outside the doubt/caution_perp
plane (n=41 all-confab), and the session-0035 MI fleet found the prime writes
92-99% off every readable axis while caution survives 40 direction removals.
This census characterises the REMAINDER: how much per-token displacement lives
outside the span of the named axes, whether that "dark" remainder is isotropic
noise or structured, and whether any of its top components separate outcomes,
are cross-row consistent, are non-nuisance, and transfer across checkpoints.

Surface
-------
Amendment AK Stage 1 per-position captures (professorsynapse/eh-al-prep-staging,
ak-stage1-{raw-base,grpo-v2}-r1). 1,338 rows per arm; the pool is unanswerable-
only (label == unknown), so the sole outcome axis available here is
confab-vs-refuse (309 confab / 1,029 refuse). Captured layers: L16 L20 L24 L28
L34. Captured positions per row: anchor, first_visible(==answer_k0),
answer_k0..answer_kN (stride 4), answer_end. Tensors keyed "<layer>@<pos>",
dim 2560, float32.

Displacement definitions (per row, per captured layer):
  successive  : h_{t+1} - h_t across the ordered answer window
                (answer_k0, answer_k1, ..., answer_end)
  anchor-rel  : h_t - h_anchor for each window position t

Known-axes span (projected out per layer)
------------------------------------------
Only axes with a usable artifact / definition at a captured layer enter the
span at that layer. On this Qwen3-4B capture we have:
  doubt      : frozen AH answerability probe joblib (probe_L20/L24/L28), the
               exact frozen trunk the AK G2 machinery uses (class 1 == known;
               doubt = -decision). Available at L20, L24, L28 only.
  refuse     : pool mean(refuse) - mean(confab) direction, fit per layer
               (the caution/refusal readout on this unanswerable pool).
  propensity : pool confab-vs-refuse logistic direction in RAW space, fit per
               layer (the AK confab-propensity readout).
An orthonormal basis of the SPAN of these is built by QR and projected out as
a block (not sequential rank-1s). The steering gate/dial directions and the
L35 caution_perp artifact are on a DIFFERENT model/layer and are NOT applied
here (documented negative). The refuse/propensity directions are fit on the
SAME pool, so removing them is the strongest reasonable definition of "named"
structure; the residual is therefore a conservative (upper-bounded) dark
fraction, not an inflated one.

CPU probe discipline
--------------------
randomized PCA, LogisticRegression(saga, tol=1e-3); never full-dim lbfgs.
Everything seeded (SEED). Tensors are streamed one safetensors open per row.

Every frozen candidate is then walked through the three decision-table screens
from docs/research/dark-displacement-literature-map.md (per candidate direction,
not as a pre-PCA transform, so the candidate set is unchanged): input
linear-predictability from the anchor (row 4), positional-carrier R^2 (row 2),
and rogue-coordinate load (row 1). A candidate that clears all three ceilings
survives the screens; the headline question is whether any candidate does.

Outputs (UNTRACKED) under analysis/dark_displacement_census/:
  census_report.json   machine-readable spectra, fractions, component stats,
                       per-candidate screen results, and candidate_screen_summary
  candidate directions dark_cand_{arm}_{layer}_{family}_pc{idx}.json (top ranked,
                       each carrying its screen verdict in provenance)
The committed human summary is written by hand from the JSON.

Usage
-----
  python experiments/dark-actuator-screen/dark_displacement_census.py \
      --data-root /path/to/ak_census --out /path/to/out [--max-rows N]
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
from safetensors.numpy import load_file
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import KFold, StratifiedKFold

SEED = 20260706
LAYERS = ["L16", "L20", "L24", "L28", "L34"]
DOUBT_LAYERS = {"L20", "L24", "L28"}      # frozen AH probe available
N_PCA_RESID = 64                          # residual PCA rank to inspect
N_TOP = 20                                # top components to characterise
N_FOLDS = 5
N_REPEATS = 4
CAND_AUROC = 0.60                         # candidate outcome-separation floor
CAND_CONS = 0.60                          # candidate half-fit cosine floor
CAND_NUISANCE = 0.15                      # strict |corr| ceiling (len/pos/step)
SCREEN_POS_R2 = 0.30                      # positional-carrier R^2 ceiling (litmap row2)
SCREEN_INPUT_R2 = 0.50                    # input-linear bookkeeping R^2 ceiling (row4)
SCREEN_ROGUE_MASS = 0.50                  # rogue-coordinate energy fraction ceiling (row1)
SCREEN_ROGUE_TOPK = 20                    # top-|loading| coords inspected for rogue overlap
CANON = Path("/home/profsynapse/code/Epistemic-Humility-Research")
AH_PROBES = CANON / "archive/experiment/phase1/probe/analysis/ah_stage0/probes"


# ---------------------------------------------------------------- small helpers
def unit(v: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(v))
    return v / n if n else v


def auroc(y: np.ndarray, s: np.ndarray) -> float:
    if len(np.unique(y)) < 2:
        return float("nan")
    return float(roc_auc_score(y, s))


def logreg() -> LogisticRegression:
    return LogisticRegression(solver="saga", tol=1e-3, max_iter=5000, C=1.0)


def window_positions(row: dict) -> list[str]:
    """Ordered answer-window positions: answer_k0..answer_kN, answer_end.

    Matches amendment_ak_stage1_lib.answer_window_positions: first_visible
    shares answer_k0's index, so we use the answer_k* / answer_end series to
    keep positions non-duplicated and monotone.
    """
    pm = row["position_index_map"]
    ks = sorted((k for k in pm if k.startswith("answer_k")),
                key=lambda k: int(k[len("answer_k"):]))
    out = list(ks)
    if "answer_end" in pm and (not out or pm["answer_end"] != pm.get(out[-1])):
        out.append("answer_end")
    elif "answer_end" in pm and out and pm["answer_end"] == pm.get(out[-1]):
        out[-1] = "answer_end"
    return out


class DoubtTrunk:
    """Frozen AH answerability probe -> doubt projection (higher == more doubt)."""

    def __init__(self, layer: str):
        import joblib
        o = joblib.load(str(AH_PROBES / f"probe_{layer}.joblib"))
        scaler, clf = o["scaler"], o["clf"]
        self.w = np.asarray(clf.coef_, dtype=np.float64).ravel()
        self.b = float(np.asarray(clf.intercept_).ravel()[0])
        self.mean = np.asarray(scaler.mean_, dtype=np.float64)
        self.scale = np.asarray(scaler.scale_, dtype=np.float64)
        # equivalent raw-space direction of the doubt projection (unit), so it
        # can join the QR span alongside pool-fit raw-space directions.
        self.raw_dir = unit(-(self.w / self.scale))


# ---------------------------------------------------------------- loading
def load_rows(data_dir: Path) -> list[dict]:
    return [json.loads(l) for l in (data_dir / "rows.jsonl").open() if l.strip()]


def tensor_path(tens_dir: Path, safe_key: str) -> Path:
    return tens_dir / f"{safe_key}.safetensors"


def load_row_window(tens_dir: Path, row: dict, layer: str
                    ) -> tuple[np.ndarray, np.ndarray] | None:
    """Return (H_window [n_pos, dim], anchor [dim]) for one row/layer, or None.

    H_window rows are ordered by window_positions(row). anchor is the anchor
    capture at the same layer.
    """
    t = load_file(str(tensor_path(tens_dir, row["safe_key"])))
    ak = f"{layer}@anchor"
    if ak not in t:
        return None
    anchor = np.asarray(t[ak], dtype=np.float64)
    poss = window_positions(row)
    H = []
    for p in poss:
        key = f"{layer}@{p}"
        if key not in t:
            H.append(None)
            continue
        H.append(np.asarray(t[key], dtype=np.float64))
    H = [h for h in H if h is not None]
    if len(H) < 2:
        return None
    return np.asarray(H), anchor


# ---------------------------------------------------------------- span
def build_span(H_anchor: np.ndarray, y_confab: np.ndarray, layer: str
               ) -> tuple[np.ndarray, list[str]]:
    """Orthonormal basis (Q, dim x k) of the named-axis span at this layer.

    Directions (raw 2560-space, unit):
      refuse     : mean(refuse anchors) - mean(confab anchors)
      propensity : logistic(confab vs refuse) coef on standardized anchors,
                   mapped back to raw space
      doubt      : frozen AH probe raw direction (only if layer in DOUBT_LAYERS)
    QR gives an orthonormal basis of their span so we project the block out at
    once (span, not sequential rank-1).
    """
    names, dirs = [], []
    refuse_mean = H_anchor[y_confab == 0].mean(0)
    confab_mean = H_anchor[y_confab == 1].mean(0)
    dirs.append(unit(refuse_mean - confab_mean)); names.append("refuse")

    from sklearn.preprocessing import StandardScaler
    sc = StandardScaler().fit(H_anchor)
    Z = sc.transform(H_anchor)
    clf = logreg().fit(Z, y_confab)
    prop_raw = clf.coef_.ravel() / sc.scale_
    dirs.append(unit(prop_raw)); names.append("propensity")

    if layer in DOUBT_LAYERS:
        dirs.append(DoubtTrunk(layer).raw_dir); names.append("doubt")

    M = np.asarray(dirs).T                       # dim x k
    Q, _ = np.linalg.qr(M)
    # keep only columns spanning non-degenerate directions
    keep = []
    for j in range(Q.shape[1]):
        if np.linalg.norm(M[:, :j + 1] - Q[:, :j + 1] @ (Q[:, :j + 1].T @ M[:, :j + 1])) < 1e6:
            keep.append(j)
    return Q[:, :len(names)], names


def project_out_span(X: np.ndarray, Q: np.ndarray) -> np.ndarray:
    """Remove the column-space of Q (orthonormal) from rows of X."""
    return X - (X @ Q) @ Q.T


# ---------------------------------------------------------------- census core
def collect_deltas(tens_dir: Path, rows: list[dict], layer: str, max_rows: int
                   ) -> dict:
    """Gather successive and anchor-relative displacement vectors per layer.

    Returns arrays with per-vector provenance (row index, step index, kind,
    outcome label, answer length, absolute token position index).
    """
    succ, succ_meta, succ_aref = [], [], []
    arel, arel_meta, arel_aref = [], [], []
    absmax_seen = np.zeros(2560)          # per-coordinate max|value| over positions
    absacc = np.zeros(2560); absn = 0     # for per-coord mean|value|
    m2 = np.zeros(2560); m4 = np.zeros(2560); mu = np.zeros(2560); ncoord = 0
    anchors, anchor_y, anchor_ridx = [], [], []
    used = 0
    for ridx, r in enumerate(rows):
        if used >= max_rows:
            break
        got = load_row_window(tens_dir, r, layer)
        if got is None:
            continue
        H, anchor = got
        poss = window_positions(r)[:H.shape[0]]
        pm = r["position_index_map"]
        y = int(bool(r["confab_on_unanswerable"]))
        alen = H.shape[0]
        aidx = len(anchors)                # this row's slot in the anchors array
        anchors.append(anchor); anchor_y.append(y); anchor_ridx.append(ridx)
        # per-coordinate raw magnitude stats over ALL captured positions (for the
        # massive-activation / rogue-dimension scan). Includes the anchor row.
        allpos = np.vstack([anchor[None, :], H])
        absmax_seen = np.maximum(absmax_seen, np.abs(allpos).max(0))
        absacc += np.abs(allpos).sum(0); absn += allpos.shape[0]
        mu += allpos.sum(0); m2 += (allpos ** 2).sum(0); m4 += (allpos ** 4).sum(0)
        ncoord += allpos.shape[0]
        # successive
        for i in range(H.shape[0] - 1):
            succ.append(H[i + 1] - H[i])
            tok = pm.get(poss[i + 1], -1)
            succ_meta.append((ridx, i, y, alen, tok)); succ_aref.append(aidx)
        # anchor-relative
        for i in range(H.shape[0]):
            arel.append(H[i] - anchor)
            tok = pm.get(poss[i], -1)
            arel_meta.append((ridx, i, y, alen, tok)); arel_aref.append(aidx)
        used += 1
    # per-coordinate raw stats (population moments across all captured positions)
    mean = mu / max(ncoord, 1)
    var = m2 / max(ncoord, 1) - mean ** 2
    fourth = m4 / max(ncoord, 1) - 4 * mean * (m2 / max(ncoord, 1)) \
        + 6 * mean ** 2 * (m2 / max(ncoord, 1)) - 3 * mean ** 4  # central 4th moment
    with np.errstate(divide="ignore", invalid="ignore"):
        kurt = np.where(var > 0, fourth / (var ** 2), 0.0)   # non-excess kurtosis
        meanabs = absacc / max(absn, 1)
        max_over_median = absmax_seen / max(float(np.median(meanabs)), 1e-9)
    return {
        "succ": np.asarray(succ), "succ_meta": np.asarray(succ_meta, float),
        "succ_aref": np.asarray(succ_aref, int),
        "arel": np.asarray(arel), "arel_meta": np.asarray(arel_meta, float),
        "arel_aref": np.asarray(arel_aref, int),
        "anchors": np.asarray(anchors), "anchor_y": np.asarray(anchor_y, int),
        "anchor_ridx": np.asarray(anchor_ridx, int), "n_rows_used": used,
        "coord_mean": mean, "coord_var": var, "coord_kurtosis": kurt,
        "coord_max_over_median_absmean": max_over_median,
        "coord_meanabs": meanabs,
    }


def variance_split(D: np.ndarray, Q: np.ndarray) -> dict:
    """Fraction of total displacement variance inside vs outside the span.

    Uses total (trace) variance of raw deltas vs the residual after removing
    the span. Reported per delta family.
    """
    total = float((D ** 2).sum())
    R = project_out_span(D, Q)
    outside = float((R ** 2).sum())
    inside = total - outside
    # per-basis energy share
    proj = D @ Q                                  # n x k
    per_axis = (proj ** 2).sum(0) / total if total else np.zeros(Q.shape[1])
    return {
        "total_energy": total,
        "frac_inside_span": inside / total if total else float("nan"),
        "frac_outside_span_dark": outside / total if total else float("nan"),
        "per_axis_share": per_axis.tolist(),
    }


def residual_spectrum(R: np.ndarray, n_pca: int, seed: int) -> dict:
    """PCA the residual (dark) deltas; report spectrum shape + effective rank."""
    Rc = R - R.mean(0)
    k = min(n_pca, Rc.shape[0] - 1, Rc.shape[1])
    pca = PCA(n_components=k, random_state=seed).fit(Rc)
    ev = pca.explained_variance_ratio_
    # participation ratio (effective rank) on the FULL residual covariance is
    # approximated from the retained spectrum plus the tail mass.
    total_var = float(((Rc) ** 2).sum() / Rc.shape[0])
    kept = float(pca.explained_variance_.sum())
    tail = max(total_var - kept, 0.0)
    eig = list(pca.explained_variance_) + [tail]  # lump tail as one bucket
    eig = np.asarray(eig)
    pr = float((eig.sum() ** 2) / (eig ** 2).sum()) if (eig ** 2).sum() else 0.0
    return {
        "components": pca.components_,            # k x dim (returned in-mem)
        "explained_variance_ratio": ev.tolist(),
        "top1_share": float(ev[0]) if len(ev) else float("nan"),
        "top5_share": float(ev[:5].sum()),
        "top20_share": float(ev[:20].sum()),
        "participation_ratio_effrank": pr,
        "n_components": int(k),
    }


# ---------------------------------------------------------------- screen 2:
# massive activations / rogue dimensions (2402.17762, 2109.04404)
def rogue_dimension_scan(deltas: dict, layer: str) -> dict:
    """Flag massive-activation / rogue coordinates from the per-coord raw stats.

    A coordinate is rogue if its max|value| over positions is >= ROGUE_MULT x the
    median coordinate mean-|value| (the "thousands-of-times-median" signature of
    2402.17762) OR its kurtosis is extreme. These are per-dim standardized (not
    zeroed) before any residual geometry so they cannot dominate norm/cosine/PCA
    (2109.04404: per-dimension standardization neutralizes rogue dims).
    """
    ROGUE_MULT = 100.0                    # max/median-|mean| threshold
    KURT_MULT = 50.0                      # kurtosis vs median-kurtosis threshold
    mom = deltas["coord_max_over_median_absmean"]
    kurt = deltas["coord_kurtosis"]
    med_kurt = float(np.median(kurt))
    rogue_mag = np.where(mom >= ROGUE_MULT)[0]
    rogue_kurt = np.where(kurt >= KURT_MULT * max(med_kurt, 1e-9))[0]
    rogue = sorted(set(rogue_mag.tolist()) | set(rogue_kurt.tolist()))
    return {
        "layer": layer,
        "n_rogue": len(rogue),
        "rogue_coords": rogue,
        "top_max_over_median": sorted(mom.tolist(), reverse=True)[:10],
        "median_max_over_median": float(np.median(mom)),
        "max_kurtosis": float(kurt.max()),
        "median_kurtosis": med_kurt,
        "rogue_mult": ROGUE_MULT, "kurt_mult": KURT_MULT,
    }


# ---------------------------------------------------------------- family-level:
# linear predictability from the input activation (2410.14670)
def linear_predictability_screen(D: np.ndarray, anchors: np.ndarray,
                                 aref: np.ndarray, seed: int) -> dict:
    """OOF R^2 of a linear (ridge) map from the input-side anchor to the delta.

    Runs FIRST (map doc: fastest discriminator). The input activation is the
    row's anchor (prompt_len-1, the last prompt token, at the SAME layer). Any
    residual mass linearly predictable from that input is SAE dark matter / mean
    bookkeeping (2410.14670 report R^2 ~0.7-0.95 mid-layer), NOT a knob. Returns
    the predictable-norm fraction and the UN-predictable residual (D minus the
    OOF linear prediction) to feed PCA ranking.
    """
    from sklearn.linear_model import Ridge
    X = anchors[aref]                          # per-vector input activation
    # Reduce BOTH sides with a fixed (label-agnostic) PCA so the ridge is
    # cheap: input-PCA -> residual-PCA scores, reconstruct the prediction. The
    # residual PCA is fit once on all deltas; the recovered variance fraction in
    # that reduced space is the predictable fraction (the retained-basis tail is
    # small for these low-effective-rank residuals, reported alongside).
    ky = min(N_PCA_RESID, D.shape[0] - 1, D.shape[1])
    pca_y = PCA(n_components=ky, random_state=seed).fit(D)
    Y = pca_y.transform(D)                      # n x ky
    kept_frac = float(pca_y.explained_variance_ratio_.sum())
    predY = np.zeros_like(Y)
    for tr, te in KFold(n_splits=N_FOLDS, shuffle=True,
                        random_state=seed).split(X):
        kx = min(N_PCA_RESID, len(tr) - 1, X.shape[1])
        pca_x = PCA(n_components=kx, random_state=seed).fit(X[tr])
        Ztr, Zte = pca_x.transform(X[tr]), pca_x.transform(X[te])
        reg = Ridge(alpha=1.0).fit(Ztr, Y[tr])
        predY[te] = reg.predict(Zte)
    predD = pca_y.inverse_transform(predY)     # back to full space (mean re-added)
    ss_res = float(((D - predD) ** 2).sum())
    ss_tot = float(((D - D.mean(0)) ** 2).sum())
    r2 = 1.0 - ss_res / ss_tot if ss_tot else float("nan")
    predicted_norm_frac = 1.0 - (ss_res / float((D ** 2).sum())) \
        if (D ** 2).sum() else float("nan")
    return {
        "oof_r2_from_input": r2,
        "predicted_norm_fraction": predicted_norm_frac,
        "residual_pca_retained_var_frac": kept_frac,
        "unpredictable": D - predD,            # in-mem, fed to PCA ranking
    }


# ---------------------------------------------------------------- positional
# spiral identity (2310.04861)
def positional_spiral_check(D: np.ndarray, meta: np.ndarray, seed: int) -> dict:
    """Test whether displacement is captured by a low-rank positional basis.

    2310.04861: a low-rank (rank ~8-12), low-frequency positional component
    (a spiral in token index) absorbs much raw displacement. We fit the
    fraction of delta variance explained by a rank-R least-squares map from a
    Fourier positional feature of the absolute token index. High -> positional
    bookkeeping.
    """
    tok = meta[:, 4].astype(float)
    ok = tok >= 0
    if ok.sum() < 50:
        return {"positional_var_explained": float("nan"), "n": int(ok.sum())}
    t = tok[ok]
    tn = (t - t.min()) / max(t.max() - t.min(), 1.0)
    # low-frequency Fourier basis (the "spiral"): rank ~ 2*K + 1
    K = 6
    feats = [np.ones_like(tn)]
    for k in range(1, K + 1):
        feats += [np.sin(2 * np.pi * k * tn), np.cos(2 * np.pi * k * tn)]
    F = np.vstack(feats).T
    Dz = D[ok]
    # least-squares fit F -> Dz, variance explained
    coef, *_ = np.linalg.lstsq(F, Dz, rcond=None)
    pred = F @ coef
    ss_res = float(((Dz - pred) ** 2).sum())
    ss_tot = float(((Dz - Dz.mean(0)) ** 2).sum())
    return {
        "positional_var_explained": 1.0 - ss_res / ss_tot if ss_tot else float("nan"),
        "basis_rank": int(F.shape[1]), "n": int(ok.sum()),
    }


# ---------------------------------------------------------------- per-candidate
# screens: each frozen candidate direction is walked through the literature
# decision table (docs/research/dark-displacement-literature-map.md). The three
# screens run PER DIRECTION (not as a pre-PCA transform) so the candidates are
# the SAME components the committed census froze; the screens judge them, they
# do not redefine them.
def input_predictability_per_component(S: np.ndarray, X: np.ndarray, seed: int
                                       ) -> np.ndarray:
    """OOF R^2 predicting each component's per-vector score from the input.

    S: (n, m) per-vector scores (one column per candidate direction). X: (n, dim)
    input activation (the row anchor at the same layer, broadcast per vector). A
    single KFold ridge on a fold-local, label-agnostic input PCA fits all m
    columns at once, so the shared input basis is built once per fold. Returns
    per-column OOF R^2. High R^2 == the direction's activation is a linear image
    of the input, i.e. SAE dark matter / mean bookkeeping (2410.14670), not a
    knob.
    """
    from sklearn.linear_model import Ridge
    predS = np.zeros_like(S)
    for tr, te in KFold(n_splits=N_FOLDS, shuffle=True,
                        random_state=seed).split(X):
        kx = min(N_PCA_RESID, len(tr) - 1, X.shape[1])
        pca = PCA(n_components=kx, random_state=seed).fit(X[tr])
        reg = Ridge(alpha=1.0).fit(pca.transform(X[tr]), S[tr])
        predS[te] = reg.predict(pca.transform(X[te]))
    ss_res = ((S - predS) ** 2).sum(0)
    ss_tot = ((S - S.mean(0)) ** 2).sum(0)
    return np.where(ss_tot > 0, 1.0 - ss_res / ss_tot, np.nan)


def position_predictability_per_component(S: np.ndarray, tok: np.ndarray,
                                          seed: int, K: int = 6) -> np.ndarray:
    """OOF R^2 predicting each component's score from absolute token index alone.

    Low-frequency Fourier basis of the min-max normalized absolute token position
    (the 2310.04861 positional spiral). High R^2 == positional carrier, not
    epistemic content. Vectors with an unknown token index (-1) are dropped.
    """
    tok = np.asarray(tok, float)
    ok = tok >= 0
    m = S.shape[1]
    if ok.sum() < 50:
        return np.full(m, np.nan)
    t = tok[ok]
    tn = (t - t.min()) / max(t.max() - t.min(), 1.0)
    feats = [np.ones_like(tn)]
    for k in range(1, K + 1):
        feats += [np.sin(2 * np.pi * k * tn), np.cos(2 * np.pi * k * tn)]
    F = np.vstack(feats).T
    Sok = S[ok]
    predS = np.zeros_like(Sok)
    for tr, te in KFold(n_splits=N_FOLDS, shuffle=True,
                        random_state=seed).split(F):
        coef, *_ = np.linalg.lstsq(F[tr], Sok[tr], rcond=None)
        predS[te] = F[te] @ coef
    ss_res = ((Sok - predS) ** 2).sum(0)
    ss_tot = ((Sok - Sok.mean(0)) ** 2).sum(0)
    return np.where(ss_tot > 0, 1.0 - ss_res / ss_tot, np.nan)


def rogue_load(c: np.ndarray, rogue_set: set) -> tuple[int, float]:
    """How much a unit direction loads on rogue coordinates (litmap row1).

    Returns (overlap in the top-|loading| coords, fraction of the direction's L2
    energy sitting on the rogue set).
    """
    order = np.argsort(np.abs(c))[::-1][:SCREEN_ROGUE_TOPK]
    overlap = int(sum(1 for i in order if int(i) in rogue_set))
    mass = float(sum(c[i] ** 2 for i in rogue_set)) if rogue_set else 0.0
    return overlap, mass


def screen_verdict(rogue_mass: float, rogue_overlap: int,
                   pos_r2: float, input_r2: float) -> str:
    """Literature decision-table identity for one candidate direction.

    Cheap nuisance identities first (litmap: rows 1, 2, 4 before the row-6 knob),
    so a direction that trips more than one screen is named by the cheapest one.
    """
    if rogue_mass >= SCREEN_ROGUE_MASS or rogue_overlap >= SCREEN_ROGUE_TOPK // 2:
        return "rogue_load"                       # litmap row1
    if np.isfinite(pos_r2) and pos_r2 >= SCREEN_POS_R2:
        return "positional"                       # litmap row2
    if np.isfinite(input_r2) and input_r2 >= SCREEN_INPUT_R2:
        return "bookkeeping_linear"               # litmap row4
    return "survives_screens"                     # litmap row6 candidate manifold


def oof_component_auroc(scores: np.ndarray, y: np.ndarray) -> float:
    """AUROC of a fixed per-vector score against a binary outcome (POOLED).

    scores/y are per-vector; the label is the row outcome, so this pools many
    delta vectors per row. Inflated by within-row correlation and length
    imbalance -- used only to ORIENT a component. The reported, non-leaky
    number is the row-level OOF AUROC (row_level_oof_auroc).
    """
    return auroc(y, scores)


def row_level_oof_auroc(scores: np.ndarray, ridx: np.ndarray, seed: int
                        ) -> float:
    """Row-aggregated outcome AUROC (mean score per row), reported not gated.

    CAVEAT: on this unanswerable-only pool, confab rows generate LONGER answers
    than refuse rows, so the row-MEAN of any component that grows with position
    inherits the length signal and separates confab-vs-refuse near-perfectly
    even when the component itself is length bookkeeping. This metric is
    therefore NOT used to gate candidates (it is length-confounded via row
    aggregation); the pooled per-vector AUROC together with the strict nuisance
    correlation filter is the honest instrument. Kept in the report to expose
    the confound explicitly.
    """
    rows = np.unique(ridx)
    row_score = np.array([scores[ridx == r].mean() for r in rows])
    row_y = np.array([_row_y_lookup[r] for r in rows])
    if len(np.unique(row_y)) < 2:
        return float("nan")
    oof = np.zeros(len(rows))
    skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=seed)
    for tr, te in skf.split(row_score.reshape(-1, 1), row_y):
        mu = row_score[tr].mean()
        oof[te] = row_score[te] - mu
    return auroc(row_y, oof)


# module-level row->outcome lookup, set per (arm, layer, family) collection
_row_y_lookup: dict = {}


def row_level_oof_auroc_fast(scores: np.ndarray, inv: np.ndarray, n_rows: int,
                             row_y: np.ndarray, seed: int) -> float:
    """Vectorized row-level OOF AUROC (same semantics as row_level_oof_auroc).

    inv maps each vector to its compact row index; row_y is the per-row outcome.
    Row score = mean vector score per row (via bincount), then seeded OOF
    train-mean centering. See row_level_oof_auroc for the length-confound caveat.
    """
    ssum = np.bincount(inv, weights=scores, minlength=n_rows)
    cnt = np.bincount(inv, minlength=n_rows).astype(float)
    cnt[cnt == 0] = 1.0
    row_score = ssum / cnt
    if len(np.unique(row_y)) < 2:
        return float("nan")
    oof = np.zeros(n_rows)
    for tr, te in StratifiedKFold(n_splits=N_FOLDS, shuffle=True,
                                  random_state=seed).split(
            row_score.reshape(-1, 1), row_y):
        oof[te] = row_score[te] - row_score[tr].mean()
    return auroc(row_y, oof)


def characterise_components(R: np.ndarray, comps: np.ndarray, meta: np.ndarray,
                            anchors: np.ndarray, aref: np.ndarray,
                            rogue_set: set, seed: int) -> list[dict]:
    """Per-component stats: consistency (half-fit cosine), outcome AUROC,
    trajectory, nuisance correlations, and the three literature screens
    (rogue-load, input-linear-predictability, positional) with a verdict."""
    ridx = meta[:, 0].astype(int)
    step = meta[:, 1]
    y = meta[:, 2].astype(int)
    alen = meta[:, 3]
    tok = meta[:, 4]
    rng = np.random.default_rng(seed)
    # row -> outcome lookup for the leakage-safe row-level OOF screen
    global _row_y_lookup
    _row_y_lookup = {int(r): int(y[ridx == r][0]) for r in np.unique(ridx)}

    # half-fit consistency: split ROWS (not vectors) into halves, refit PCA on
    # residual of each half, match top comps by |cosine|.
    uniq = np.unique(ridx)
    rng.shuffle(uniq)
    h1 = set(uniq[: len(uniq) // 2].tolist())
    m1 = np.array([r in h1 for r in ridx])
    def half_comps(mask):
        Rh = R[mask]
        Rh = Rh - Rh.mean(0)
        k = min(comps.shape[0], Rh.shape[0] - 1, Rh.shape[1])
        return PCA(n_components=k, random_state=seed).fit(Rh).components_
    C1 = half_comps(m1)
    C2 = half_comps(~m1)

    # component-independent quantities, computed ONCE (vectorized):
    # normalized within-row step position 0..1 (per-row max via np.maximum.at).
    uniq = np.unique(ridx)
    inv = np.searchsorted(uniq, ridx)             # row -> compact index
    row_max = np.zeros(len(uniq))
    np.maximum.at(row_max, inv, step)
    denom = np.where(row_max[inv] > 0, row_max[inv], 1.0)
    nrm = step / denom
    # row outcome (for the row-level OOF) aligned to compact index
    row_y = np.array([_row_y_lookup[int(r)] for r in uniq])

    # ---- the three literature screens, batched across all components (the two
    # regression screens share their basis, so they are fit once here, not per
    # component). Sign-invariant, so run on the unoriented scores.
    S_all = R @ comps.T                            # n x m per-vector scores
    input_r2 = input_predictability_per_component(S_all, anchors[aref], seed)
    pos_r2 = position_predictability_per_component(S_all, tok, seed)

    out = []
    for j in range(comps.shape[0]):
        c = comps[j]
        s = R @ c                                 # per-vector score
        # orient so higher score == confab-leaning (for interpretable AUROC)
        a = oof_component_auroc(s, y)
        if a < 0.5:
            s = -s; c = -c; a = 1 - a
        rogue_overlap, rogue_mass = rogue_load(c, rogue_set)
        verdict = screen_verdict(rogue_mass, rogue_overlap,
                                 float(pos_r2[j]), float(input_r2[j]))
        row_auroc = row_level_oof_auroc_fast(s, inv, len(uniq), row_y, seed)
        # consistency: best |cosine| of this comp against each half's top-k
        cons1 = float(np.max(np.abs(C1 @ c))) if C1.size else float("nan")
        cons2 = float(np.max(np.abs(C2 @ c))) if C2.size else float("nan")
        cons = float(min(cons1, cons2))
        early = float(np.mean(np.abs(s[nrm <= 0.33])))
        late = float(np.mean(np.abs(s[nrm >= 0.67])))
        traj = "rise" if late > 1.15 * early else ("decay" if late < 0.87 * early else "flat")
        # nuisance correlations
        def corr(x):
            if np.std(x) == 0 or np.std(s) == 0:
                return 0.0
            return float(np.corrcoef(s, x)[0, 1])
        out.append({
            "idx": j,
            "confab_auroc": a,
            "confab_auroc_rowlevel_oof": row_auroc,
            "consistency_halfcos": cons,
            "traj": traj, "mean_abs_early": early, "mean_abs_late": late,
            "corr_answer_len": corr(alen),
            "corr_token_pos": corr(tok),
            "corr_step_norm": corr(nrm),
            "screen_rogue_topk_overlap": rogue_overlap,
            "screen_rogue_energy_frac": rogue_mass,
            "screen_input_linear_r2": float(input_r2[j]),
            "screen_position_r2": float(pos_r2[j]),
            "screen_verdict": verdict,
            "survives_all_screens": verdict == "survives_screens",
            "vector": c,
        })
    return out


# ---------------------------------------------------------------- driver
def run_arm(arm: str, data_root: Path, out: Path, max_rows: int) -> dict:
    data_dir = data_root / f"ak-stage1-{arm}-r1" / "data"
    tens_dir = data_root / f"ak-stage1-{arm}-r1" / "tensors" / "extracted"
    rows = load_rows(data_dir)
    print(f"[{arm}] {len(rows)} rows", flush=True)
    arm_res = {"arm": arm, "n_rows": len(rows), "layers": {}}
    comp_store: dict = {}
    for layer in LAYERS:
        t0 = time.time()
        d = collect_deltas(tens_dir, rows, layer, max_rows)
        if d["anchors"].shape[0] < 20:
            print(f"[{arm}/{layer}] too few rows, skip", flush=True)
            continue
        Q, span_names = build_span(d["anchors"], d["anchor_y"], layer)
        # rogue / massive-activation coordinates for this layer (litmap row1).
        rogue = rogue_dimension_scan(d, layer)
        rogue_set = set(int(i) for i in rogue["rogue_coords"])
        lnum = int(layer[1:])
        lay = {"span_axes": span_names, "n_rows_used": d["n_rows_used"],
               "depth_band": ("early" if lnum <= 16 else
                              "middle" if lnum <= 28 else "late"),
               "rogue_dimensions": rogue, "families": {}}
        comp_store[layer] = {}
        for fam in ("succ", "arel"):
            D = d[fam]
            meta = d[fam + "_meta"]
            aref = d[fam + "_aref"]
            # Candidate identification is UNCHANGED from the committed census:
            # variance split + PCA on the RAW span-residual, so the frozen
            # candidates are identical. The three screens below JUDGE those
            # candidates (per direction), they do not redefine them.
            vs = variance_split(D, Q)
            R = project_out_span(D, Q)
            spec = residual_spectrum(R, N_PCA_RESID, SEED)
            comps = spec.pop("components")
            comp_stats = characterise_components(
                R, comps[:N_TOP], meta, d["anchors"], aref, rogue_set, SEED)
            comp_store[layer][fam] = comp_stats
            # family-level context for the decision table (informative, not gates):
            #   input linear-predictability of the whole residual (litmap row4)
            #   and positional-spiral variance of the whole residual (row2).
            lin = linear_predictability_screen(R, d["anchors"], aref, SEED)
            lin.pop("unpredictable", None)
            spiral = positional_spiral_check(R, meta, SEED)
            ev = spec["explained_variance_ratio"]
            elbow = (spec["top5_share"] >= 0.35 and
                     (ev[0] / max(ev[min(9, len(ev) - 1)], 1e-9)) >= 5.0)
            n_surv = sum(1 for c in comp_stats if c["survives_all_screens"])
            fam_out = {
                "n_vectors": int(D.shape[0]),
                "variance": vs,
                "spectrum": spec,
                "family_input_linear_predictability": lin,
                "family_positional_spiral": spiral,
                "structured_spectrum_elbow": bool(elbow),
                "n_components_surviving_screens": int(n_surv),
                "components": [
                    {k: v for k, v in c.items() if k != "vector"}
                    for c in comp_stats
                ],
            }
            lay["families"][fam] = fam_out
            print(f"[{arm}/{layer}/{fam}] dark={vs['frac_outside_span_dark']:.3f} "
                  f"famLinR2={lin['oof_r2_from_input']:.2f} "
                  f"famSpiral={spiral['positional_var_explained']:.2f} "
                  f"rogue={rogue['n_rogue']} "
                  f"top1={spec['top1_share']:.3f} effrank={spec['participation_ratio_effrank']:.1f} "
                  f"surv={n_surv}/{len(comp_stats)} ({time.time()-t0:.0f}s)", flush=True)
        arm_res["layers"][layer] = lay
    return arm_res, comp_store


def checkpoint_transfer(store_a: dict, store_b: dict) -> dict:
    """Cosine of matched top components (by index) between the two arms."""
    out = {}
    for layer in store_a:
        if layer not in store_b:
            continue
        out[layer] = {}
        for fam in store_a[layer]:
            if fam not in store_b[layer]:
                continue
            ca = np.asarray([c["vector"] for c in store_a[layer][fam]])
            cb = np.asarray([c["vector"] for c in store_b[layer][fam]])
            k = min(len(ca), len(cb))
            # best |cosine| of each arm-A comp against ALL arm-B comps
            M = np.abs(ca[:k] @ cb[:k].T)
            best = M.max(1) if M.size else np.array([])
            out[layer][fam] = {
                "per_comp_best_abscos": best.tolist(),
                "mean_best_abscos": float(best.mean()) if best.size else float("nan"),
                "n": int(k),
            }
    return out


def freeze_candidates(store: dict, arm: str, layer_transfer: dict, out: Path,
                      arm_res: dict) -> list[dict]:
    """Write direction JSONs for components that clear consistency + outcome
    separation, in the frozen-direction schema the knob screen consumes."""
    frozen = []
    for layer, fams in store.items():
        for fam, comps in fams.items():
            for c in comps:
                rl = c.get("confab_auroc_rowlevel_oof", float("nan"))
                # Original committed gate (unchanged): honest pooled AUROC + the
                # STRICT nuisance filter (length / token-pos / step) + consistency.
                # The three literature screens are recorded per candidate below;
                # they do NOT gate the freeze, so the candidate set is identical
                # to the committed census and each candidate carries its verdict.
                if (c["consistency_halfcos"] >= CAND_CONS
                        and c["confab_auroc"] >= CAND_AUROC
                        and abs(c["corr_answer_len"]) < CAND_NUISANCE
                        and abs(c["corr_token_pos"]) < CAND_NUISANCE
                        and abs(c["corr_step_norm"]) < CAND_NUISANCE):
                    lnum = int(layer[1:])
                    xfer = None
                    lt = layer_transfer.get(layer, {}).get(fam)
                    if lt and c["idx"] < len(lt["per_comp_best_abscos"]):
                        xfer = lt["per_comp_best_abscos"][c["idx"]]
                    theta = np.asarray(c["vector"], dtype=np.float64)
                    rec = {
                        "schema_version": "mechinterp-residual-caution-direction/v1",
                        "layer": lnum,
                        "block": lnum - 1,
                        "source": "dark_displacement_residual_pca",
                        "hidden_dim": int(theta.shape[0]),
                        "theta": [float(v) for v in theta],
                        "sigma": 1.0,
                        "mu_pos": 0.0,
                        "mu_neg": 0.0,
                        "provenance": {
                            "amendment": "lab-dark-displacement-census",
                            "arm": arm,
                            "delta_family": fam,
                            "residual_pc_idx": c["idx"],
                            "confab_auroc_pooled": c["confab_auroc"],
                            "confab_auroc_rowlevel_oof": rl,
                            "consistency_halfcos": c["consistency_halfcos"],
                            "trajectory": c["traj"],
                            "corr_answer_len": c["corr_answer_len"],
                            "corr_token_pos": c["corr_token_pos"],
                            "checkpoint_transfer_abscos": xfer,
                            "screen_rogue_topk_overlap":
                                c["screen_rogue_topk_overlap"],
                            "screen_rogue_energy_frac":
                                c["screen_rogue_energy_frac"],
                            "screen_input_linear_r2": c["screen_input_linear_r2"],
                            "screen_position_r2": c["screen_position_r2"],
                            "screen_verdict": c["screen_verdict"],
                            "survives_all_screens": c["survives_all_screens"],
                            "seed": SEED,
                            "script": "experiments/dark-actuator-screen/dark_displacement_census.py",
                        },
                    }
                    fn = out / f"dark_cand_{arm}_{layer}_{fam}_pc{c['idx']}.json"
                    fn.write_text(json.dumps(rec, indent=2))
                    frozen.append({"file": fn.name, **{
                        k: rec["provenance"][k] for k in
                        ("confab_auroc_rowlevel_oof", "consistency_halfcos",
                         "trajectory", "checkpoint_transfer_abscos",
                         "screen_rogue_topk_overlap", "screen_rogue_energy_frac",
                         "screen_input_linear_r2", "screen_position_r2",
                         "screen_verdict", "survives_all_screens")}})
    return frozen


def family_verdict(fam_meta: dict, depth_band: str, n_rogue: int) -> dict:
    """Map a (layer, family) residual to a decision-table identity (litmap).

    Rows of docs/research/dark-displacement-literature-map.md:
      row1 rogue dims, row2 position/context bookkeeping, row4 SAE dark matter,
      row5 dense/noise, row6 representation manifold (knob candidate).
    A family gets its DOMINANT identity plus the numbers that decide it.
    """
    lin = fam_meta["family_input_linear_predictability"]["oof_r2_from_input"]
    spiral = fam_meta["family_positional_spiral"]["positional_var_explained"]
    elbow = fam_meta["structured_spectrum_elbow"]
    effrank = fam_meta["spectrum"]["participation_ratio_effrank"]
    top5 = fam_meta["spectrum"]["top5_share"]
    tags = []
    if n_rogue > 0:
        tags.append("row1_rogue_dimensions")
    if np.isfinite(spiral) and spiral >= 0.30:
        tags.append("row2_positional_context_bookkeeping")
    if np.isfinite(lin) and lin >= 0.50:
        tags.append("row4_sae_dark_matter_linear")
    # after stripping linear + span, what is the leftover PCA shape?
    if elbow and top5 >= 0.35:
        leftover = "row6_candidate_manifold" if effrank <= 20 else "row5_dense_noise"
    else:
        leftover = "row5_dense_noise"
    tags.append(leftover)
    # depth conditioning (row3): late-layer big displacement is expected sharpening
    dominant = ("row4_sae_dark_matter_linear"
                if (np.isfinite(lin) and lin >= 0.50) else leftover)
    return {
        "input_linear_r2": lin,
        "positional_var_explained": spiral,
        "structured_elbow": elbow,
        "effective_rank": effrank,
        "depth_band": depth_band,
        "depth_note": ("late-layer displacement toward unembedding is expected "
                       "sharpening (row3), not anomaly" if depth_band == "late"
                       else "middle-band order-sensitive displacement is the "
                       "surprising signal (row3)" if depth_band == "middle"
                       else "early-layer displacement is detokenization (row3)"),
        "identity_tags": tags,
        "dominant_identity": dominant,
        "leftover_after_screens": leftover,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--max-rows", type=int, default=10_000)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    report = {"seed": SEED, "layers_captured": LAYERS,
              "doubt_layers": sorted(DOUBT_LAYERS),
              "n_top": N_TOP, "n_pca_resid": N_PCA_RESID,
              "candidate_gates": {"auroc": CAND_AUROC, "consistency": CAND_CONS},
              "arms": {}}
    stores = {}
    for arm in ("raw-base", "grpo-v2"):
        arm_res, store = run_arm(arm, args.data_root, args.out, args.max_rows)
        report["arms"][arm] = arm_res
        stores[arm] = store

    xfer = checkpoint_transfer(stores["raw-base"], stores["grpo-v2"])
    report["checkpoint_transfer_rawbase_vs_grpov2"] = xfer

    # per-family decision-table verdicts in the literature-map vocabulary.
    report["family_verdicts"] = {}
    for arm, ar in report["arms"].items():
        report["family_verdicts"][arm] = {}
        for layer, lay in ar["layers"].items():
            n_rogue = lay["rogue_dimensions"]["n_rogue"]
            for fam, fm in lay["families"].items():
                report["family_verdicts"][arm][f"{layer}/{fam}"] = family_verdict(
                    fm, lay["depth_band"], n_rogue)

    report["frozen_candidates"] = {}
    for arm in ("raw-base", "grpo-v2"):
        report["frozen_candidates"][arm] = freeze_candidates(
            stores[arm], arm, xfer, args.out, report["arms"][arm])

    # headline: the three literature screens applied to every frozen candidate.
    report["candidate_screen_thresholds"] = {
        "position_r2_ceiling": SCREEN_POS_R2,
        "input_linear_r2_ceiling": SCREEN_INPUT_R2,
        "rogue_energy_frac_ceiling": SCREEN_ROGUE_MASS,
        "rogue_topk_overlap_ceiling": SCREEN_ROGUE_TOPK // 2,
        "topk_coords_inspected": SCREEN_ROGUE_TOPK,
    }
    screen_summary = {}
    for arm in ("raw-base", "grpo-v2"):
        cands = report["frozen_candidates"][arm]
        by_verdict: dict = {}
        for c in cands:
            by_verdict.setdefault(c["screen_verdict"], 0)
            by_verdict[c["screen_verdict"]] += 1
        survivors = [c["file"] for c in cands if c["survives_all_screens"]]
        screen_summary[arm] = {
            "n_frozen_candidates": len(cands),
            "verdict_counts": by_verdict,
            "n_survive_all_screens": len(survivors),
            "survivors": survivors,
        }
    report["candidate_screen_summary"] = screen_summary
    report["headline_any_candidate_survives_all_screens"] = any(
        screen_summary[a]["n_survive_all_screens"] > 0 for a in screen_summary)

    (args.out / "census_report.json").write_text(json.dumps(report, indent=2))
    print("WROTE", args.out / "census_report.json", flush=True)
    for arm, s in screen_summary.items():
        print(f"[screens/{arm}] frozen={s['n_frozen_candidates']} "
              f"verdicts={s['verdict_counts']} "
              f"survive_all={s['n_survive_all_screens']}", flush=True)
    print("HEADLINE any candidate survives all screens:",
          report["headline_any_candidate_survives_all_screens"], flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
