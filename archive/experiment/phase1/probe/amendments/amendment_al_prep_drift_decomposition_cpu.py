#!/usr/bin/env python3
"""Amendment AL prep — decompose the GRPO drift onto named epistemic axes.

Follow-up to amendment_al_prep_true_internals_cpu.py, which showed ~98% of
the training displacement (TRUE-base, PERMUTED-base at L24) is orthogonal to
the answerability readout. This script asks WHAT the displacement is made of,
using the program's named directions at L24:

  answerability  fit here on the base union surface (the sensor axis).
  caution        refuse-vs-answer logistic direction, fit on the cached AH A0
                 surface (1,662 rows, GRPO-v2 activations, behavior labels).
  commitment     mean(confab) - mean(refuse) within unanswerable rows on A0,
                 residualised against the caution axis (radial-sim recipe).

The DOUBT axis exists only as an L35 artifact (caution_direction_L35 /
doubt_gain_map_L35); the arm extracts carry L20/24/28 only, so doubt is NOT
in this bank — noted in the report, to be closed by adding upper layers to
the next extraction cell.

Objects decomposed (per row and as mean drift vectors):
  dh_true = h_true - h_base      dh_perm = h_perm - h_base
  dd      = dh_true - dh_perm    (the sensor-specific displacement)
and optionally dh_grpo_v2 when --grpo-dir is given (deployment-checkpoint
drift on the same pool, for the four-way).

For each: signed projection per axis (split by gold label), fraction of the
mean-drift norm captured by the axis bank (least squares onto its span), and
a PCA characterization of the residual row-level drift (top components:
variance explained, cosine vs each named axis, correlation with label and
with the base answerability logit).

Caveat recorded in output: caution/commitment axes are fit in GRPO-v2
activation space; cross-checkpoint readout transfer measured today is ~1.0
AUROC, so projections are meaningful, but absolute scales are indicative.

CPU only. Usage mirrors amendment_al_prep_true_internals_cpu.py, plus
--a0-rows / --a0-cache and optional --grpo-dir.
"""

import argparse
import json
import time
from pathlib import Path

import numpy as np

L = "L24"


def load_jsonl(p):
    return [json.loads(l) for l in Path(p).open() if l.strip()]


def load_surface_layer(d: Path, layer=L):
    from safetensors import safe_open
    rows = load_jsonl(d / "rows.jsonl")
    X, kept = [], []
    for r in rows:
        fp = d / f"{r['safe_key']}__pre.safetensors"
        if not fp.exists():
            continue
        with safe_open(str(fp), "pt") as st:
            X.append(st.get_tensor(layer).float().numpy())
        kept.append(r)
    return np.asarray(X, dtype=np.float32), kept


def unit(v):
    return v / np.linalg.norm(v)


def cos(a, b):
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def fit_direction_logistic(X, y):
    """Scaler+LR raw-space unit direction (verdict-scorer recipe)."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    m = make_pipeline(StandardScaler(),
                      LogisticRegression(C=1.0, max_iter=5000))
    m.fit(X, y)
    sc, lr = m.named_steps["standardscaler"], \
        m.named_steps["logisticregression"]
    return m, unit((lr.coef_[0] / sc.scale_).astype(np.float64))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-dir", required=True)
    ap.add_argument("--true-dir", required=True)
    ap.add_argument("--perm-dir", required=True)
    ap.add_argument("--grpo-dir", default=None,
                    help="optional GRPO-v2 union extraction for the four-way")
    ap.add_argument("--a0-rows", required=True)
    ap.add_argument("--a0-cache", required=True,
                    help="mi_category_geometry cache dir with L24.npy + manifest.jsonl")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    t0 = time.time()

    # ---------------- union surfaces, aligned rows -----------------------
    dirs = {"base": a.base_dir, "true": a.true_dir, "permuted": a.perm_dir}
    if a.grpo_dir:
        dirs["grpo_v2"] = a.grpo_dir
    Xs, rows_by = {}, {}
    for n, d in dirs.items():
        Xs[n], rows_by[n] = load_surface_layer(Path(d))
        print(f"[al-drift] loaded {n}: {len(rows_by[n])} rows "
              f"({time.time()-t0:.0f}s)", flush=True)
    common = sorted(set.intersection(
        *[set(r["row_key"] for r in rows_by[n]) for n in Xs]))
    for n in Xs:
        pos = {r["row_key"]: i for i, r in enumerate(rows_by[n])}
        Xs[n] = Xs[n][np.array([pos[k] for k in common])]
    rows = [r for r in rows_by["base"]
            if r["row_key"] in set(common)]
    rows.sort(key=lambda r: r["row_key"])
    y = np.array([1 if r["label"] == "known" else 0 for r in rows])

    # ---------------- axis bank at L24 -----------------------------------
    probe, w_ans = fit_direction_logistic(Xs["base"], y)
    base_logit = probe.decision_function(Xs["base"])

    a0 = load_jsonl(a.a0_rows)
    man = load_jsonl(Path(a.a0_cache) / "manifest.jsonl")
    man_idx = {m["row_key"]: i for i, m in enumerate(man)}
    X24 = np.load(str(Path(a.a0_cache) / "L24.npy")).astype(np.float32)
    graded = [r for r in a0 if r["row_key"] in man_idx
              and not r.get("degenerate") and not r.get("ungradeable")]
    Xa0 = X24[np.array([man_idx[r["row_key"]] for r in graded])]
    y_refuse = np.array([1 if r["refused"] else 0 for r in graded])
    _, w_caution = fit_direction_logistic(Xa0, y_refuse)

    un = [(i, r) for i, r in enumerate(graded)
          if r["gold_class"] == "unanswerable"]
    Xun = Xa0[np.array([i for i, _ in un])].astype(np.float64)
    y_confab = np.array([1 if r["confab_on_unanswerable"] else 0
                         for _, r in un])
    md = Xun[y_confab == 1].mean(0) - Xun[y_confab == 0].mean(0)
    md = md - np.dot(md, w_caution) * w_caution   # residualise vs caution
    w_commit = unit(md)

    bank = {"answerability": w_ans, "caution": w_caution,
            "commitment": w_commit}
    axis_cos = {f"{p}~{q}": round(cos(bank[p], bank[q]), 4)
                for p in bank for q in bank if p < q}
    print(f"[al-drift] axis bank ready {axis_cos} ({time.time()-t0:.0f}s)",
          flush=True)

    # ---------------- decomposition --------------------------------------
    objects = {
        "dh_true": (Xs["true"] - Xs["base"]).astype(np.float64),
        "dh_permuted": (Xs["permuted"] - Xs["base"]).astype(np.float64),
    }
    objects["dd_sensor_specific"] = objects["dh_true"] - objects["dh_permuted"]
    if "grpo_v2" in Xs:
        objects["dh_grpo_v2"] = (Xs["grpo_v2"] - Xs["base"]).astype(np.float64)

    B = np.stack([bank[k] for k in bank])          # [3, h]
    report = {"n_rows": len(rows), "layer": L, "axis_cosines": axis_cos,
              "doubt_axis_note": "doubt/caution_perp exist only at L35; arm "
              "extracts carry L20/24/28 - add upper layers to the next "
              "extraction cell to close this",
              "axis_source_caveat": "caution/commitment fit on the AH A0 "
              "GRPO-v2 surface; answerability fit on the base union surface",
              "objects": {}}
    for name, D in objects.items():
        mean_d = D.mean(axis=0)
        proj = D @ B.T                              # [n, 3] signed
        coef, *_ = np.linalg.lstsq(B.T, mean_d, rcond=None)
        in_span = B.T @ coef
        o = {
            "mean_drift_norm": round(float(np.linalg.norm(mean_d)), 3),
            "mean_row_disp_norm":
                round(float(np.linalg.norm(D, axis=1).mean()), 3),
            "bank_fraction_of_mean_drift":
                round(float(np.linalg.norm(in_span) /
                            np.linalg.norm(mean_d)), 4),
            "axes": {},
        }
        for j, k in enumerate(bank):
            o["axes"][k] = {
                "mean_proj": round(float(proj[:, j].mean()), 3),
                "cos_mean_drift": round(cos(mean_d, bank[k]), 4),
                "known_mean_proj": round(float(proj[y == 1, j].mean()), 3),
                "unknown_mean_proj": round(float(proj[y == 0, j].mean()), 3),
            }
        # PCA characterization of the row-level object
        Dc = (D - mean_d).astype(np.float32)
        from sklearn.decomposition import PCA
        pca = PCA(n_components=6, random_state=0)
        S = pca.fit_transform(Dc)
        pcs = []
        for j in range(6):
            c = pca.components_[j].astype(np.float64)
            pcs.append({
                "var_frac": round(float(pca.explained_variance_ratio_[j]), 4),
                "cos_axes": {k: round(cos(c, bank[k]), 3) for k in bank},
                "corr_label": round(float(np.corrcoef(S[:, j], y)[0, 1]), 3),
                "corr_base_logit":
                    round(float(np.corrcoef(S[:, j], base_logit)[0, 1]), 3),
            })
        o["pca_top6"] = pcs
        report["objects"][name] = o
        print(f"[al-drift] {name}: bank captures "
              f"{o['bank_fraction_of_mean_drift']:.1%} of mean drift "
              f"({time.time()-t0:.0f}s)", flush=True)

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=1))
    print(f"[al-drift] report -> {out} ({time.time()-t0:.0f}s)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
