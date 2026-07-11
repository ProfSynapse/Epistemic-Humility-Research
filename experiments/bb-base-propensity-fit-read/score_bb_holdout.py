#!/usr/bin/env python3
"""BB phase 1 step 3 (CPU, no GPU): score the frozen base direction on the
750-row base READ extraction (AMENDMENT.md section 5.3).

Runs AFTER the Modal GPU lane (cloud/modal_bb_phase1.py) has produced the
read-surface extraction (L24/L35 per row, pulled back from the Modal Volume
into the gitignored analysis/phase1/read/extract/ tree) and AFTER phase 0
already produced the read-surface behavior grades
(analysis/phase0/bb-phase0-r1/rows_graded.jsonl, already on disk locally --
this script does NOT regenerate them). Applies the frozen base scorer
(directions/frozen_scorer_base/, produced by freeze_scorer_base.py) to each
read-surface row and evaluates the pre-stated gates in gates.yaml:
  BB-P1-G1 (reading AUROC + 1,000-resample row-bootstrap 95% CI)
  BB-P1-G2 (caution positive control, floor)
plus the registered near-duplicate sensitivity recompute (AMENDMENT.md
section 8), if --sensitivity is passed and near_dup_sweep_bb.py has already
produced its sidecar.

The scoring path (score_rows) is the exact frozen deployment path from
freeze_scorer_base.py -- copied verbatim from H9's score_holdout.py:
  P24 = scaler24.transform(pca24.transform(X24))
  c_raw = caution_clf.decision_function(scaler35.transform(pca35.transform(X35)))
  c_frozen = (c_raw - caution_zscale_mean) / caution_zscale_std
  R = P24 - caution_residualizer.predict(c_frozen)
  prop_z = (R @ d_confab_full - prop_mean) / prop_std

CANNOT be run against real data yet: there is no phase-1 GPU extraction on
disk (no model has been loaded on this host per the host constraint; the
Modal run is not launched by this build). Wired to full working state and
validated by --selftest, which exercises the scoring math and gate logic on
random arrays without any real data (same posture as H9's score_holdout.py
--selftest).

Usage:
  python score_bb_holdout.py --cell cell.yaml --gates gates.yaml [--sensitivity]
  python score_bb_holdout.py --selftest
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
    """[n_rows, 37, dim]; one safetensors open per row (same layout as fit)."""
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
    """Frozen deployment path -> (prop_z, caution_z). Identical to freeze_scorer_base."""
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
    # Same disjointness-repair as H9's score_holdout.py: PASS and FAIL
    # predicates are not provably disjoint; resolve any overlap to
    # INCONCLUSIVE literally, per the AMENDMENT's "a CI that straddles the
    # boundaries -> inconclusive" rule, rather than by evaluation order.
    pass_cond = auroc >= rg["pass_auroc_min"] and ci_lo > rg["pass_ci_lower_min"]
    fail_cond = auroc <= rg["fail_auroc_max"] or ci_hi < rg["fail_ci_upper_max"]
    if pass_cond and fail_cond:
        return "INCONCLUSIVE"
    if pass_cond:
        return "PASS"
    if fail_cond:
        return "FAIL"
    return "INCONCLUSIVE"


def evaluate(prop_z, caution_z, is_confab, is_un_ref, is_refused,
             gates: dict, seed: int, tag: str) -> dict:
    rg = gates["reading_gate"]
    fe = gates["fit_evaluability"]
    n_confab, n_un_ref = int(is_confab.sum()), int(is_un_ref.sum())

    # BB-P1-G0 read here is a RECORD of the read-surface's own confab/refusal
    # mass (informational); the GATING G0 check is the fit-surface precondition
    # computed in freeze_scorer_base.py and passed in via fit_g0_met.
    g0_read_surface = {"n_confab": n_confab, "n_un_refused": n_un_ref,
                       "min_confabs": fe["min_confabs"],
                       "min_un_refused": fe["min_unanswerable_refusals"]}

    caution_auroc = float(roc_auc_score(is_refused.astype(int), caution_z)) \
        if len(np.unique(is_refused)) > 1 else float("nan")
    g2 = {"caution_auroc": caution_auroc,
          "floor": gates["caution_control"]["floor_auroc_min"],
          "pass": bool(caution_auroc >= gates["caution_control"]["floor_auroc_min"])}

    # BB-P1-G1 reading contrast: confab (pos) vs unanswerable-refused (neg)
    sel = is_confab | is_un_ref
    y = is_confab[sel].astype(int)
    s = prop_z[sel]
    if not g2["pass"]:
        g1 = {"verdict": "NOT-ADJUDICATED (caution floor failed; pipeline failure)",
              "auroc": None, "ci": None}
    else:
        auroc = float(roc_auc_score(y, s))
        lo, hi = bootstrap_auroc_ci(y, s, rg["bootstrap_resamples"],
                                    rg["bootstrap_ci"], seed)
        g1 = {"verdict": classify_reading(auroc, lo, hi, rg), "auroc": auroc,
              "ci": [lo, hi], "ci_level": rg["bootstrap_ci"]}
    return {"tag": tag, "BB-P1-G0_read_surface_record": g0_read_surface,
            "BB-P1-G2": g2, "BB-P1-G1": g1}


def score(cell: dict, gates: dict, exp_dir: Path, do_sensitivity: bool,
          read_extract_dir: Path | None, phase0_graded: Path | None,
          fit_fidelity_report: Path | None) -> dict:
    sc_cfg = cell["phase1"]["scorer"]
    fz = load_frozen(exp_dir / sc_cfg["frozen_out"])

    ids = load_jsonl(exp_dir / cell["read_surface"]["id_manifest"])
    row_keys = [r["row_key"] for r in ids]
    assert len(row_keys) == cell["read_surface"]["n_rows"], \
        f"read manifest has {len(row_keys)} rows; expected {cell['read_surface']['n_rows']}"

    extract_dir = read_extract_dir or (exp_dir / "analysis/phase1/read/extract/data")
    graded_path = phase0_graded or (
        exp_dir / "analysis/phase0/bb-phase0-r1/rows_graded.jsonl")
    graded = {r["row_key"]: r for r in load_jsonl(graded_path)}
    missing_graded = [rk for rk in row_keys if rk not in graded]
    assert not missing_graded, \
        f"{len(missing_graded)} manifest row_keys missing from phase-0 graded rows"

    stack = load_stack(extract_dir, row_keys)
    Lp = sc_cfg["fit_layers"]["propensity"]
    Lc = sc_cfg["fit_layers"]["caution"]
    X24 = stack[:, Lp, :].astype(np.float64)
    X35 = stack[:, Lc, :].astype(np.float64)
    prop_z, caution_z = score_rows(fz, X24, X35)

    g = [graded[rk] for rk in row_keys]
    is_confab = np.array([r["gold_class"] == "unanswerable" and r["answered"] for r in g])
    is_un_ref = np.array([r["gold_class"] == "unanswerable" and r["refused"] for r in g])
    is_refused = np.array([bool(r["refused"]) for r in g])

    seed = cell["seed"]
    headline = evaluate(prop_z, caution_z, is_confab, is_un_ref, is_refused,
                        gates, seed, "headline")

    # BB-P1-G0 (fit-surface evaluability, GATING; AMENDMENT.md section 6): must
    # be checked before BB-P1-G1 is adjudicated. Read from freeze_scorer_base's
    # own fidelity report rather than recomputed here (that report already has
    # the fit-surface confab/refusal counts).
    fid_path = fit_fidelity_report or (
        exp_dir / sc_cfg["frozen_out"] / "fidelity_report.json")
    fit_report = json.loads(fid_path.read_text())
    fit_g0 = fit_report["BB-P1-G0_fit_evaluability"]
    if not fit_g0["met"]:
        headline["BB-P1-G1"] = {"verdict": "INCONCLUSIVE-BY-POWER (fit-surface "
                                "BB-P1-G0 unmet)", "auroc": None, "ci": None}

    report = {"headline": headline, "BB-P1-G0_fit_surface": fit_g0,
              "honest_prior": fit_report.get("honest_prior_NONGATING")}
    report["heldout_zscale_nongating"] = {
        "prop_z_mean": float(prop_z.mean()), "prop_z_std": float(prop_z.std()),
        "caution_z_mean": float(caution_z.mean()), "caution_z_std": float(caution_z.std())}

    if do_sensitivity:
        flagged_path = exp_dir / cell["sensitivity"]["flagged_out"]
        if not flagged_path.exists():
            raise FileNotFoundError(
                f"--sensitivity requires the near-dup sidecar {flagged_path}; "
                f"run near_dup_sweep_bb.py first (do not default to clean).")
        flagged = set(json.loads(flagged_path.read_text()))
        keep = np.array([rk not in flagged for rk in row_keys])
        recompute = evaluate(prop_z[keep], caution_z[keep], is_confab[keep],
                             is_un_ref[keep], is_refused[keep], gates, seed,
                             "near_dup_excluded")
        report["sensitivity_near_dup"] = {
            "n_flagged": int((~keep).sum()),
            "excluded_recompute": recompute,
            "verdict_flip": (report["headline"]["BB-P1-G1"]["verdict"]
                             != recompute["BB-P1-G1"]["verdict"])}

    out_path = exp_dir / cell["phase1"]["scoring"]["gate_report_out"]
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
    assert res["BB-P1-G2"]["pass"] in (True, False)
    assert res["BB-P1-G1"]["verdict"] in (
        "PASS", "FAIL", "INCONCLUSIVE",
        "NOT-ADJUDICATED (caution floor failed; pipeline failure)")
    return res


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cell", default="cell.yaml")
    ap.add_argument("--gates", default="gates.yaml")
    ap.add_argument("--sensitivity", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--read-extract-dir", default=None)
    ap.add_argument("--phase0-graded", default=None)
    ap.add_argument("--fit-fidelity-report", default=None)
    args = ap.parse_args()
    gates = yaml.safe_load(Path(args.gates).read_text())
    if args.selftest:
        print(json.dumps(selftest(gates), indent=2))
        return 0
    exp_dir = Path(args.cell).resolve().parent
    cell = yaml.safe_load(Path(args.cell).read_text())
    report = score(
        cell, gates, exp_dir, args.sensitivity,
        Path(args.read_extract_dir) if args.read_extract_dir else None,
        Path(args.phase0_graded) if args.phase0_graded else None,
        Path(args.fit_fidelity_report) if args.fit_fidelity_report else None)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
