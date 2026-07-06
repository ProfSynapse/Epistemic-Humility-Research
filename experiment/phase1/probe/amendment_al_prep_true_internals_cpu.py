#!/usr/bin/env python3
"""Amendment AL prep — CPU internals characterization of the AI-TRUE checkpoint.

Three-way comparison on the IDENTICAL 18.5k-row union pool (pre-generation
states, final prompt token): clean-SFT base (all-layer sensor-refit surface)
vs AI-TRUE vs AI-PERMUTED (L20/L24/L28 verdict extracts). All CPU; no new
GPU passes. PERMUTED is the training-drift control throughout: any geometry
change it shares with TRUE is generic GRPO drift, anything TRUE-only is the
sensor reward's doing.

Questions:
  1. Axis geometry  — per (checkpoint, layer): answerability probe OOF AUROC
     + raw-space direction; cross-checkpoint direction cosines. Did the
     sensor reward ROTATE the readout axis, or leave it (readout unmoved =
     consistent with the AI verdict's "learned correlates, not consultation")?
  2. Readout transfer — 3x3 matrix at the sensor layer: probe fit on
     checkpoint A scored on checkpoint B's states (AUROC). Does the base
     sensor still read the trained arms cold?
  3. State displacement — dh = h_arm − h_base per row at the sensor layer:
     magnitude, fraction along the base readout axis vs orthogonal, split by
     gold label; cosine between TRUE's and PERMUTED's mean drift directions.

Usage (conda unsloth_env python, from the repo probe dir):
  python amendment_al_prep_true_internals_cpu.py \
      --base-dir  <analysis>/par_sensor_refit/union_pregen_4bit \
      --true-dir  <analysis>/amendment_ai/verdict/true_extract_union/data \
      --perm-dir  <analysis>/amendment_ai/verdict/permuted_extract_union/data \
      --out <analysis>/amendment_al_prep/true_internals_report.json

Analysis output stays untracked; this script is the committed provenance.
"""

import argparse
import json
import time
from pathlib import Path

import numpy as np

LAYERS = ("L20", "L24", "L28")
SENSOR_LAYER = "L24"          # sensor v2 layer (PAR prereg 1.1)
N_FOLDS = 5
CV_RANDOM_STATE = 0


def load_jsonl(p):
    return [json.loads(l) for l in Path(p).open() if l.strip()]


def load_surface(d: Path, layers=LAYERS):
    """Return (dict layer -> [n,h] float32, kept rows) following the
    amendment_ai_verdict_score.py loader conventions."""
    from safetensors import safe_open
    rows = load_jsonl(d / "rows.jsonl")
    X = {l: [] for l in layers}
    kept = []
    for r in rows:
        fp = d / f"{r['safe_key']}__pre.safetensors"
        if not fp.exists():
            continue
        with safe_open(str(fp), "pt") as st:
            for l in layers:
                X[l].append(st.get_tensor(l).float().numpy())
        kept.append(r)
    return {l: np.asarray(v, dtype=np.float32) for l, v in X.items()}, kept


def fit_probe(X, y, cv=True):
    """Scaler+LR probe per the verdict-scorer recipe; returns
    (pipeline, oof_auroc, raw-space unit direction)."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import StratifiedKFold
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    auroc = None
    if cv:
        oof = np.zeros(len(y))
        skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True,
                              random_state=CV_RANDOM_STATE)
        for tr, te in skf.split(X, y):
            m = make_pipeline(StandardScaler(),
                              LogisticRegression(C=1.0, max_iter=5000))
            m.fit(X[tr], y[tr])
            oof[te] = m.decision_function(X[te])
        auroc = float(roc_auc_score(y, oof))

    full = make_pipeline(StandardScaler(),
                         LogisticRegression(C=1.0, max_iter=5000))
    full.fit(X, y)
    scaler, lr = full.named_steps["standardscaler"], \
        full.named_steps["logisticregression"]
    w_raw = (lr.coef_[0] / scaler.scale_).astype(np.float64)
    w_raw /= np.linalg.norm(w_raw)
    return full, auroc, w_raw


def cos(a, b):
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-dir", required=True)
    ap.add_argument("--true-dir", required=True)
    ap.add_argument("--perm-dir", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    from sklearn.metrics import roc_auc_score

    t0 = time.time()
    surfaces, rows_by = {}, {}
    for name, d in (("base", a.base_dir), ("true", a.true_dir),
                    ("permuted", a.perm_dir)):
        surfaces[name], rows_by[name] = load_surface(Path(d))
        print(f"[al-prep] loaded {name}: {len(rows_by[name])} rows "
              f"({time.time()-t0:.0f}s)", flush=True)

    # Align on common row_keys, identical order everywhere.
    key_sets = [set(r["row_key"] for r in rows_by[n]) for n in surfaces]
    common = sorted(set.intersection(*key_sets))
    idx = {}
    for n in surfaces:
        pos = {r["row_key"]: i for i, r in enumerate(rows_by[n])}
        idx[n] = np.array([pos[k] for k in common])
    rows = [rows_by["base"][i] for i in idx["base"]]
    y = np.array([1 if r["label"] == "known" else 0 for r in rows])
    X = {n: {l: surfaces[n][l][idx[n]] for l in LAYERS} for n in surfaces}
    del surfaces
    report = {"n_common": len(common),
              "label_counts": {"known": int(y.sum()),
                               "unknown": int((1 - y).sum())}}
    print(f"[al-prep] aligned {len(common)} common rows "
          f"({int(y.sum())} known / {int((1-y).sum())} unknown)", flush=True)

    # 1. Axis geometry: probe per (checkpoint, layer) + direction cosines.
    probes, geometry = {}, {}
    for l in LAYERS:
        geometry[l] = {}
        for n in X:
            _, auroc, w = fit_probe(X[n][l], y)
            probes[(n, l)] = (_, w)
            geometry[l][n] = {"oof_auroc": round(auroc, 4)}
            print(f"[al-prep] probe {n}/{l}: OOF AUROC {auroc:.4f} "
                  f"({time.time()-t0:.0f}s)", flush=True)
        for pair in (("base", "true"), ("base", "permuted"),
                     ("true", "permuted")):
            c = cos(probes[(pair[0], l)][1], probes[(pair[1], l)][1])
            geometry[l][f"cos_{pair[0]}_{pair[1]}"] = round(c, 4)
    report["axis_geometry"] = geometry

    # 2. Readout transfer at the sensor layer: fit on A, score B.
    L = SENSOR_LAYER
    transfer = {}
    for src in X:
        transfer[src] = {}
        for dst in X:
            s = probes[(src, L)][0].decision_function(X[dst][L])
            transfer[src][dst] = round(float(roc_auc_score(y, s)), 4)
    report["readout_transfer_auroc"] = {
        "layer": L, "note": "row = probe-fit checkpoint, col = states scored",
        "matrix": transfer}

    # 3. State displacement at the sensor layer.
    w_base = probes[("base", L)][1]
    disp = {}
    for arm in ("true", "permuted"):
        dh = (X[arm][L] - X["base"][L]).astype(np.float64)
        proj = dh @ w_base
        norms = np.linalg.norm(dh, axis=1)
        base_norms = np.linalg.norm(X["base"][L].astype(np.float64), axis=1)
        mean_drift = dh.mean(axis=0)
        d = {
            "mean_disp_norm": round(float(norms.mean()), 3),
            "mean_disp_over_state_norm":
                round(float((norms / base_norms).mean()), 4),
            "mean_proj_on_base_axis": round(float(proj.mean()), 3),
            "axis_fraction_of_disp":
                round(float((np.abs(proj) / norms).mean()), 4),
            "mean_drift_vector_norm":
                round(float(np.linalg.norm(mean_drift)), 3),
            "cos_mean_drift_vs_base_axis":
                round(cos(mean_drift, w_base), 4),
        }
        for lbl, mask in (("known", y == 1), ("unknown", y == 0)):
            d[f"{lbl}_mean_proj_on_base_axis"] = \
                round(float(proj[mask].mean()), 3)
            d[f"{lbl}_mean_disp_norm"] = round(float(norms[mask].mean()), 3)
        disp[arm] = d
        disp[f"_mean_drift_{arm}"] = mean_drift
    disp["cos_mean_drift_true_vs_permuted"] = round(
        cos(disp.pop("_mean_drift_true"), disp.pop("_mean_drift_permuted")), 4)
    report["state_displacement"] = {"layer": L, "vs": "clean-SFT base",
                                    "sign_note": "base axis: + = known/answerable",
                                    **disp}

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=1))
    print(f"[al-prep] report -> {out} ({time.time()-t0:.0f}s)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
