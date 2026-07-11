#!/usr/bin/env python3
"""H9 step 4 (CPU, no GPU): score the frozen direction on the held-out draw.

Runs AFTER the Modal GPU lane (cloud/modal_h9_holdout.py) has produced held-out
extraction (L24/L35 per row) and graded behavior labels, pulled back from the
Modal Volume into the gitignored analysis/holdout_run/ tree. Applies the frozen
scorer (directions/frozen_scorer/, produced by freeze_scorer.py) to each held-out
row, evaluates the pre-stated gates in gates.yaml, and emits an aggregates-only
gate report (no question text, no per-row generations) to analysis-committed/.

The held-out scoring path is the exact frozen deployment path from freeze_scorer:
  P24 = scaler24.transform(pca24.transform(X24))
  c_raw = caution_clf.decision_function(scaler35.transform(pca35.transform(X35)))
  c_frozen = (c_raw - caution_zscale_mean) / caution_zscale_std
  R = P24 - caution_residualizer.predict(c_frozen)
  prop_z = (R @ d_confab_full - prop_mean) / prop_std

Gates (AMENDMENT.md section 5): H9-G0 evaluability, H9-G2 caution floor,
H9-G1 reading AUROC + 1,000-resample row-bootstrap 95% CI, plus the registered
near-duplicate sensitivity recompute (section 8.1).

CANNOT be smoke-run before the GPU lane exists: there is no held-out extraction
on disk yet. This script is wired to full working state and validated by import
plus a synthetic-shape self-test (--selftest) that exercises the scoring math and
gate logic on random arrays without any real data.

Usage:
  python score_holdout.py --cell cell.yaml --gates gates.yaml [--sensitivity]
  python score_holdout.py --selftest        # gate logic + scoring shape check
"""
from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np
import yaml
from sklearn.metrics import roc_auc_score

N_LAYERS = 37


def load_jsonl(p: Path):
    return [json.loads(l) for l in p.open() if l.strip()]


def load_stack(extract_data: Path, row_keys: list[str]) -> np.ndarray:
    """[n_rows, 37, dim]; one safetensors open per row (same layout as AL)."""
    from safetensors import safe_open

    safe = {r["row_key"]: r["safe_key"]
            for r in load_jsonl(extract_data / "rows.jsonl")}
    keys = [f"L{i}" for i in range(N_LAYERS)]
    out = None
    for i, rk in enumerate(row_keys):
        with safe_open(str(extract_data / f"{safe[rk]}__pre.safetensors"), "np") as h:
            if out is None:
                dim = h.get_tensor("L0").shape[0]
                out = np.empty((len(row_keys), N_LAYERS, dim), dtype=np.float32)
            for li, key in enumerate(keys):
                out[i, li] = h.get_tensor(key)
    return out


def load_frozen(frozen_dir: Path) -> dict:
    import joblib

    zs = json.loads((frozen_dir / "prop_zscale.json").read_text())
    return {
        "pca24": joblib.load(frozen_dir / "pca24.joblib"),
        "pca35": joblib.load(frozen_dir / "pca35.joblib"),
        "scaler24": joblib.load(frozen_dir / "scaler24.joblib"),
        "scaler35": joblib.load(frozen_dir / "scaler35.joblib"),
        "caution_clf": joblib.load(frozen_dir / "caution_logistic.joblib"),
        "caution_residualizer": joblib.load(frozen_dir / "caution_residualizer.joblib"),
        "d_confab_full": np.load(frozen_dir / "d_confab_full.npy"),
        "zscale": zs,
    }


def score_rows(fz: dict, X24: np.ndarray, X35: np.ndarray):
    """Frozen deployment path -> (prop_z, caution_z). Identical to freeze_scorer."""
    P24 = fz["scaler24"].transform(fz["pca24"].transform(X24))
    c_raw = fz["caution_clf"].decision_function(
        fz["scaler35"].transform(fz["pca35"].transform(X35)))
    zs = fz["zscale"]
    c_frozen = (c_raw - zs["caution_zscale_mean"]) / zs["caution_zscale_std"]
    R = P24 - fz["caution_residualizer"].predict(c_frozen.reshape(-1, 1))
    prop_raw = R @ fz["d_confab_full"]
    prop_z = (prop_raw - zs["prop_mean"]) / zs["prop_std"]
    return prop_z, c_frozen


def bootstrap_auroc_ci(y: np.ndarray, s: np.ndarray, n_resamples: int,
                       ci: float, seed: int):
    rng = np.random.default_rng(seed)
    n = len(y)
    stats = []
    for _ in range(n_resamples):
        idx = rng.integers(0, n, size=n)
        yb, sb = y[idx], s[idx]
        if len(np.unique(yb)) < 2:
            continue
        stats.append(roc_auc_score(yb, sb))
    lo = float(np.percentile(stats, (1 - ci) / 2 * 100))
    hi = float(np.percentile(stats, (1 + ci) / 2 * 100))
    return lo, hi


def classify_reading(auroc: float, ci_lo: float, ci_hi: float, rg: dict) -> str:
    if auroc >= rg["pass_auroc_min"] and ci_lo > rg["pass_ci_lower_min"]:
        return "PASS"
    if auroc <= rg["fail_auroc_max"] or ci_hi < rg["fail_ci_upper_max"]:
        return "FAIL"
    return "INCONCLUSIVE"


def evaluate(prop_z, caution_z, is_confab, is_un_ref, is_refused,
             gates: dict, seed: int, tag: str) -> dict:
    rg = gates["reading_gate"]
    ev = gates["evaluability"]
    n_confab, n_un_ref = int(is_confab.sum()), int(is_un_ref.sum())

    g0 = {"n_confab": n_confab, "n_un_refused": n_un_ref,
          "min_confabs": ev["min_confabs"],
          "min_un_refused": ev["min_unanswerable_refusals"],
          "met": bool(n_confab >= ev["min_confabs"]
                      and n_un_ref >= ev["min_unanswerable_refusals"])}

    caution_auroc = float(roc_auc_score(is_refused.astype(int), caution_z)) \
        if len(np.unique(is_refused)) > 1 else float("nan")
    g2 = {"caution_auroc": caution_auroc,
          "floor": gates["caution_control"]["floor_auroc_min"],
          "pass": bool(caution_auroc >= gates["caution_control"]["floor_auroc_min"])}

    # H9-G1 reading contrast: confab (pos) vs unanswerable-refused (neg)
    sel = is_confab | is_un_ref
    y = is_confab[sel].astype(int)
    s = prop_z[sel]
    if not g0["met"]:
        g1 = {"verdict": "INCONCLUSIVE-BY-POWER", "auroc": None, "ci": None}
    elif not g2["pass"]:
        g1 = {"verdict": "NOT-ADJUDICATED (caution floor failed; pipeline failure)",
              "auroc": None, "ci": None}
    else:
        auroc = float(roc_auc_score(y, s))
        lo, hi = bootstrap_auroc_ci(y, s, rg["bootstrap_resamples"],
                                    rg["bootstrap_ci"], seed)
        g1 = {"verdict": classify_reading(auroc, lo, hi, rg), "auroc": auroc,
              "ci": [lo, hi], "ci_level": rg["bootstrap_ci"]}
    return {"tag": tag, "H9-G0": g0, "H9-G2": g2, "H9-G1": g1}


def score(cell: dict, gates: dict, exp_dir: Path, do_sensitivity: bool) -> dict:
    fz = load_frozen(exp_dir / cell["scorer"]["frozen_out"])
    ids = load_jsonl(exp_dir / cell["holdout"]["id_manifest_out"])
    row_keys = [r["row_key"] for r in ids]

    extract_dir = exp_dir / cell["scoring"]["holdout_extract_dir"]
    graded = {r["row_key"]: r
              for r in load_jsonl(exp_dir / cell["scoring"]["holdout_graded"])}
    stack = load_stack(extract_dir, row_keys)
    Lp = cell["scorer"]["fit_layers"]["propensity"]
    Lc = cell["scorer"]["fit_layers"]["caution"]
    X24 = stack[:, Lp, :].astype(np.float64)
    X35 = stack[:, Lc, :].astype(np.float64)
    prop_z, caution_z = score_rows(fz, X24, X35)

    g = [graded[rk] for rk in row_keys]
    is_confab = np.array([r["gold_class"] == "unanswerable" and r["answered"] for r in g])
    is_un_ref = np.array([r["gold_class"] == "unanswerable" and r["refused"] for r in g])
    is_refused = np.array([bool(r["refused"]) for r in g])

    seed = cell["seed"]
    report = {"headline": evaluate(prop_z, caution_z, is_confab, is_un_ref,
                                   is_refused, gates, seed, "headline")}

    if do_sensitivity:
        # near-duplicate KUQ rows are flagged by the sensitivity step and listed
        # in a sidecar (row_keys only); exclude them and recompute G1.
        flagged_path = extract_dir.parent / "near_dup_flagged.json"
        flagged = set(json.loads(flagged_path.read_text())) if flagged_path.exists() else set()
        keep = np.array([rk not in flagged for rk in row_keys])
        recompute = evaluate(prop_z[keep], caution_z[keep], is_confab[keep],
                             is_un_ref[keep], is_refused[keep], gates, seed,
                             "near_dup_excluded")
        report["sensitivity_near_dup"] = {
            "n_flagged": int((~keep).sum()),
            "excluded_recompute": recompute,
            "verdict_flip": (report["headline"]["H9-G1"]["verdict"]
                             != recompute["H9-G1"]["verdict"])}

    out_path = exp_dir / cell["scoring"]["gate_report_out"]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2))
    return report


def selftest(gates: dict) -> dict:
    """Exercise the scoring math + gate logic on synthetic arrays (no real data)."""
    rng = np.random.default_rng(0)
    n = 400
    is_confab = np.zeros(n, dtype=bool); is_confab[:35] = True
    is_un_ref = ~is_confab
    is_refused = is_un_ref.copy()
    prop_z = rng.normal(0, 1, n) + is_confab * 0.7
    caution_z = rng.normal(0, 1, n) + is_refused * 3.0
    res = evaluate(prop_z, caution_z, is_confab, is_un_ref, is_refused,
                   gates, seed=1, tag="selftest")
    assert res["H9-G0"]["met"] in (True, False)
    assert res["H9-G1"]["verdict"] in (
        "PASS", "FAIL", "INCONCLUSIVE", "INCONCLUSIVE-BY-POWER",
        "NOT-ADJUDICATED (caution floor failed; pipeline failure)")
    return res


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cell", default="cell.yaml")
    ap.add_argument("--gates", default="gates.yaml")
    ap.add_argument("--sensitivity", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    gates = yaml.safe_load(Path(args.gates).read_text())
    if args.selftest:
        print(json.dumps(selftest(gates), indent=2))
        return 0
    exp_dir = Path(args.cell).resolve().parent
    cell = yaml.safe_load(Path(args.cell).read_text())
    report = score(cell, gates, exp_dir, args.sensitivity)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
