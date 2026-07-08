#!/usr/bin/env python3
"""Amendment AF (script 2/4) — base doubt probe fit + per-item certainty labels (CPU).

Pre-registered in
experiments/second-person-doubt-prime/AMENDMENT.md (§3, §4, §7).

Loads the pre-gen anchor tensors from script 1. For EACH layer, fits a logistic
regression known(1) vs unknown(0) and scores held-out AUROC via stratified 5-fold
CV (fixed random_state). Picks the argmax-AUROC layer.

GATE (AE sensor rule, §4): if argmax held-out AUROC < 0.90 -> STOP, write a stop
report, do NOT proceed to generation.

If PASS: refit on all rows at the argmax layer, project every row onto the probe
decision function, threshold at the POPULATION MEDIAN of the projection -> binary
certainty {HIGH, LOW}, with the KNOWN-like (higher-answerability) side mapped to
HIGH (sign verified: mean projection of known rows must exceed unknown rows; flip
if not). Then permute the TRUE label vector with seed 20260703 (preserves the
~50/50 marginals exactly).

Emits af_labels.json {row_key: {certainty_true, certainty_permuted}} plus the
argmax layer, AUROC, the per-layer AUROC table, and label counts.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

PROBE_DIR = Path(__file__).resolve().parent
DEFAULT_PREGEN = PROBE_DIR / "analysis" / "af_base_pregen"

AUROC_GATE = 0.90
PERMUTE_SEED = 20260703
CV_RANDOM_STATE = 0
N_FOLDS = 5


def load_rows(pregen_dir: Path) -> list[dict]:
    rows = []
    with (pregen_dir / "rows.jsonl").open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_layer_matrix(pregen_dir: Path, rows: list[dict], layer_key: str) -> np.ndarray:
    from safetensors.torch import load_file
    vecs = []
    for r in rows:
        t = load_file(str(pregen_dir / f"{r['safe_key']}__pre.safetensors"))
        vecs.append(t[layer_key].numpy().astype(np.float64))
    return np.vstack(vecs)


def run(args) -> int:
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import StratifiedKFold, cross_val_predict
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import roc_auc_score

    pregen_dir = Path(args.pregen_dir).resolve()
    rows = load_rows(pregen_dir)
    manifest = json.loads((pregen_dir / "manifest.json").read_text())
    n_layers = manifest["n_layers"]  # tensors are L0..L{n_layers}
    layer_keys = [f"L{i}" for i in range(n_layers + 1)]

    y = np.array([1 if r["label"] == "known" else 0 for r in rows], dtype=int)
    print(f"[amendment-af/fit] rows={len(rows)} known={int(y.sum())} "
          f"unknown={int((1 - y).sum())} layers={len(layer_keys)}", flush=True)

    skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True,
                          random_state=CV_RANDOM_STATE)

    per_layer = {}
    best_layer = None
    best_auroc = -1.0
    for lk in layer_keys:
        X = load_layer_matrix(pregen_dir, rows, lk)
        clf = make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=2000, C=1.0),
        )
        proba = cross_val_predict(clf, X, y, cv=skf, method="predict_proba")[:, 1]
        auroc = float(roc_auc_score(y, proba))
        per_layer[lk] = auroc
        if auroc > best_auroc:
            best_auroc = auroc
            best_layer = lk
        print(f"[amendment-af/fit] {lk}: heldout AUROC={auroc:.4f}", flush=True)

    print(f"\n[amendment-af/fit] argmax layer={best_layer} AUROC={best_auroc:.4f} "
          f"(gate {AUROC_GATE})", flush=True)

    # ---- AE sensor GATE ----
    if best_auroc < AUROC_GATE:
        stop = {
            "amendment": "AF",
            "stage": "probe_fit",
            "verdict": "STOP-SENSOR-BELOW-FLOOR",
            "reason": (f"argmax held-out AUROC {best_auroc:.4f} < gate "
                       f"{AUROC_GATE}; the base doubt sensor is not real enough "
                       "to render its output to text. Per protocol §4/§7 the run "
                       "does not proceed to generation. No rescue (no layer "
                       "sweep beyond argmax, no threshold search)."),
            "argmax_layer": best_layer,
            "argmax_auroc": best_auroc,
            "auroc_gate": AUROC_GATE,
            "per_layer_auroc": per_layer,
            "n_rows": len(rows),
        }
        (pregen_dir / "af_probe_fit_stop.json").write_text(
            json.dumps(stop, indent=2), encoding="utf-8")
        print(json.dumps(stop, indent=2), flush=True)
        print("\n[amendment-af/fit] SENSOR GATE FAILED -> STOP. No labels, no "
              "generation.", flush=True)
        return 0

    # ---- refit on all rows at argmax; project; median-threshold ----
    X = load_layer_matrix(pregen_dir, rows, best_layer)
    clf = make_pipeline(
        StandardScaler(),
        LogisticRegression(max_iter=2000, C=1.0),
    )
    clf.fit(X, y)
    proj = clf.decision_function(X)  # higher => more known-like (answerability)

    # Verify sign: known rows must project higher than unknown; flip if not.
    mean_known = float(proj[y == 1].mean())
    mean_unknown = float(proj[y == 0].mean())
    flipped = False
    if mean_known < mean_unknown:
        proj = -proj
        flipped = True
        mean_known, mean_unknown = -mean_known, -mean_unknown

    median = float(np.median(proj))
    # HIGH = known-like (higher-answerability) side = at/above median.
    certainty = np.where(proj >= median, "HIGH", "LOW")

    true_labels = {rows[i]["row_key"]: str(certainty[i]) for i in range(len(rows))}

    # Permute the TRUE label vector (preserves marginals exactly).
    rng = np.random.default_rng(PERMUTE_SEED)
    perm = rng.permutation(len(rows))
    permuted_arr = certainty[perm]
    permuted_labels = {rows[i]["row_key"]: str(permuted_arr[i])
                       for i in range(len(rows))}

    n_high = int((certainty == "HIGH").sum())
    n_low = int((certainty == "LOW").sum())

    # Cross-tab: how the TRUE certainty splits by known/unknown (diagnostic only).
    def _split(mask):
        return {
            "HIGH": int(((certainty == "HIGH") & mask).sum()),
            "LOW": int(((certainty == "LOW") & mask).sum()),
        }

    labels_payload = {
        "amendment": "AF",
        "stage": "probe_fit",
        "verdict": "SENSOR-GATE-PASS",
        "argmax_layer": best_layer,
        "argmax_auroc": best_auroc,
        "auroc_gate": AUROC_GATE,
        "per_layer_auroc": per_layer,
        "n_rows": len(rows),
        "sign_flipped": flipped,
        "mean_proj_known": mean_known,
        "mean_proj_unknown": mean_unknown,
        "median_threshold": median,
        "permute_seed": PERMUTE_SEED,
        "cv_random_state": CV_RANDOM_STATE,
        "n_folds": N_FOLDS,
        "label_counts_true": {"HIGH": n_high, "LOW": n_low},
        "certainty_by_label_true": {
            "known": _split(y == 1),
            "unknown": _split(y == 0),
        },
        "labels": {
            rk: {
                "certainty_true": true_labels[rk],
                "certainty_permuted": permuted_labels[rk],
            }
            for rk in true_labels
        },
    }
    out_path = pregen_dir / "af_labels.json"
    out_path.write_text(json.dumps(labels_payload, indent=2), encoding="utf-8")

    print(f"[amendment-af/fit] labels: HIGH={n_high} LOW={n_low} "
          f"(sign_flipped={flipped})", flush=True)
    print(f"[amendment-af/fit] certainty_by_label(true): "
          f"{labels_payload['certainty_by_label_true']}", flush=True)
    print(f"[amendment-af/fit] wrote {out_path}", flush=True)
    print("[amendment-af/fit] SENSOR GATE PASSED -> proceed to generation.",
          flush=True)
    return 0


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pregen-dir", default=str(DEFAULT_PREGEN),
                    help="dir with pre-gen tensors + rows.jsonl (script 1 output)")
    return ap.parse_args(argv)


if __name__ == "__main__":
    sys.exit(run(parse_args()))
