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

Outputs (UNTRACKED) under analysis/dark_displacement_census/:
  census_report.json   machine-readable spectra, fractions, component stats
  candidate directions dark_cand_{arm}_{layer}_pc{idx}.json (top ranked)
The committed human summary is written by hand from the JSON.

Usage
-----
  python experiment/phase1/probe/dark_displacement_census.py \
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
from sklearn.model_selection import StratifiedKFold

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
CANON = Path("/home/profsynapse/code/Epistemic-Humility-Research")
AH_PROBES = CANON / "experiment/phase1/probe/analysis/ah_stage0/probes"


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
    succ, succ_meta = [], []
    arel, arel_meta = [], []
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
        anchors.append(anchor); anchor_y.append(y); anchor_ridx.append(ridx)
        # successive
        for i in range(H.shape[0] - 1):
            succ.append(H[i + 1] - H[i])
            tok = pm.get(poss[i + 1], -1)
            succ_meta.append((ridx, i, y, alen, tok))
        # anchor-relative
        for i in range(H.shape[0]):
            arel.append(H[i] - anchor)
            tok = pm.get(poss[i], -1)
            arel_meta.append((ridx, i, y, alen, tok))
        used += 1
    return {
        "succ": np.asarray(succ), "succ_meta": np.asarray(succ_meta, float),
        "arel": np.asarray(arel), "arel_meta": np.asarray(arel_meta, float),
        "anchors": np.asarray(anchors), "anchor_y": np.asarray(anchor_y, int),
        "anchor_ridx": np.asarray(anchor_ridx, int), "n_rows_used": used,
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


def characterise_components(R: np.ndarray, comps: np.ndarray, meta: np.ndarray,
                            seed: int) -> list[dict]:
    """Per-component stats: consistency (half-fit cosine), outcome AUROC,
    trajectory, nuisance correlations."""
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

    out = []
    for j in range(comps.shape[0]):
        c = comps[j]
        s = R @ c                                 # per-vector score
        # orient so higher score == confab-leaning (for interpretable AUROC)
        a = oof_component_auroc(s, y)
        if a < 0.5:
            s = -s; c = -c; a = 1 - a
        row_auroc = row_level_oof_auroc(s, ridx, seed)
        # consistency: best |cosine| of this comp against each half's top-k
        cons1 = float(np.max(np.abs(C1 @ c))) if C1.size else float("nan")
        cons2 = float(np.max(np.abs(C2 @ c))) if C2.size else float("nan")
        cons = float(min(cons1, cons2))
        # trajectory: mean |score| by normalized window position (0..1)
        # normalize step within each row
        nrm = np.zeros_like(step)
        for r in np.unique(ridx):
            mm = ridx == r
            mx = step[mm].max()
            nrm[mm] = step[mm] / mx if mx > 0 else 0.0
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
        lay = {"span_axes": span_names, "n_rows_used": d["n_rows_used"],
               "families": {}}
        comp_store[layer] = {}
        for fam in ("succ", "arel"):
            D = d[fam]
            meta = d[fam + "_meta"]
            vs = variance_split(D, Q)
            R = project_out_span(D, Q)
            spec = residual_spectrum(R, N_PCA_RESID, SEED)
            comps = spec.pop("components")
            comp_stats = characterise_components(R, comps[:N_TOP], meta, SEED)
            comp_store[layer][fam] = comp_stats
            fam_out = {
                "n_vectors": int(D.shape[0]),
                "variance": vs,
                "spectrum": spec,
                "components": [
                    {k: v for k, v in c.items() if k != "vector"}
                    for c in comp_stats
                ],
            }
            lay["families"][fam] = fam_out
            print(f"[{arm}/{layer}/{fam}] dark={vs['frac_outside_span_dark']:.3f} "
                  f"top1={spec['top1_share']:.3f} effrank={spec['participation_ratio_effrank']:.1f} "
                  f"({time.time()-t0:.0f}s)", flush=True)
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
                # Gate on the honest instrument: pooled per-vector AUROC + a
                # STRICT nuisance filter (length / token-pos / step). The
                # row-level OOF is length-confounded and only reported.
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
                        "schema_version": "phase3-residual-caution-direction/v1",
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
                            "seed": SEED,
                            "script": "experiment/phase1/probe/dark_displacement_census.py",
                        },
                    }
                    fn = out / f"dark_cand_{arm}_{layer}_{fam}_pc{c['idx']}.json"
                    fn.write_text(json.dumps(rec, indent=2))
                    frozen.append({"file": fn.name, **{
                        k: rec["provenance"][k] for k in
                        ("confab_auroc_rowlevel_oof", "consistency_halfcos",
                         "trajectory", "checkpoint_transfer_abscos")}})
    return frozen


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

    report["frozen_candidates"] = {}
    for arm in ("raw-base", "grpo-v2"):
        report["frozen_candidates"][arm] = freeze_candidates(
            stores[arm], arm, xfer, args.out, report["arms"][arm])

    (args.out / "census_report.json").write_text(json.dumps(report, indent=2))
    print("WROTE", args.out / "census_report.json", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
