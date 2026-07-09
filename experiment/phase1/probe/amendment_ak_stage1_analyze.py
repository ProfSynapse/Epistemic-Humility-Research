#!/usr/bin/env python3
"""Amendment AK Stage 1 - full gate analysis (CPU, deterministic, seeded).

Runs AFTER the AK-G2 pilot floor is locked and committed
(experiments/commitment-point/artifacts/stage1/ak_stage1_pilot_floor.json). Evaluates, per
AMENDMENT-AK-commitment-point.md §4:

  AK-G1 (crystallization, GATED on grpo-v2):
    veto AUROC at answer-end  -  veto AUROC at first-visible  >=  +0.10.
    The veto/correctness axis is REFIT PER POSITION out-of-fold (item 31: frozen
    correctness axes do not transport across positions). Label = confab (the
    veto reads a confabulation on an unanswerable question as low-trust). Fit
    is PCA-128 randomized + LogisticRegression(saga, tol=1e-3) per the project
    probe convention. The AJ equal-rank random-direction control is carried as
    the artifact guard (a random rank-1-through-PCA direction should read ~0.5).

  AK-G2 (doubt-trajectory discriminability, three-way fork, GATED):
    on the NON-PILOT rows, PASS requires
      (a) |full-run slope contrast| >= COMMITTED_FLOOR   AND
      (b) permutation p < 0.01.
    Which path wins (H-rise / H-flat(-then-rise) / H-drop) is the finding and is
    reported, not adjudicated here.

Raw-base is DESCRIPTIVE (doc §3.1: "AK-G1 gates on grpo-v2; the raw-base curve
is reported descriptively alongside it"). Both arms are reported for G1 and G2.

Outputs under experiments/commitment-point/artifacts/stage1/ by default:
  ak_stage1_gate_report.json   machine-readable verdicts + curves + CIs
  human summary printed to stdout; pass --report-md to persist it
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler

import amendment_ak_stage1_lib as ak

WORKTREE = Path(__file__).resolve().parents[3]
_CANON = Path("/home/profsynapse/code/Epistemic-Humility-Research")
_PROBES_REL = "experiment/phase1/probe/analysis/ah_stage0/probes"
PROBES_DIR = (_CANON / _PROBES_REL if (_CANON / _PROBES_REL).is_dir()
              else WORKTREE / _PROBES_REL)
STAGE1_ARTIFACT_DIR = WORKTREE / "experiments/commitment-point/artifacts/stage1"
FLOOR_JSON = STAGE1_ARTIFACT_DIR / "ak_stage1_pilot_floor.json"
OUT_DIR = STAGE1_ARTIFACT_DIR

SEED = 20260705
N_PCA = 128
N_SPLITS = 5
N_REPEATS = 4
G1_LAYER = "L24"          # veto/correctness read layer within captured band
AK_G1_MARGIN = 0.10       # doc §4


# ----------------------------------------------------------------------------
# AUROC + per-position OOF veto probe
# ----------------------------------------------------------------------------

def _auroc(y: np.ndarray, s: np.ndarray) -> float:
    from sklearn.metrics import roc_auc_score
    if len(np.unique(y)) < 2:
        return float("nan")
    return float(roc_auc_score(y, s))


def _load_position_matrix(arm_dir: Path, rows: list[dict], layer: str,
                          pos: str) -> tuple[np.ndarray, np.ndarray, list[int]]:
    """X (rows-with-that-position, dim), y=confab, and the surviving row indices."""
    X, y, keep = [], [], []
    for i, r in enumerate(rows):
        if pos not in r["position_index_map"]:
            continue
        v = ak.load_vec(arm_dir, r["safe_key"], layer, pos)
        if v is None:
            continue
        X.append(v)
        y.append(int(bool(r["confab_on_unanswerable"])))
        keep.append(i)
    return np.asarray(X, dtype=np.float64), np.asarray(y, dtype=np.int64), keep


def _oof_scores(X: np.ndarray, y: np.ndarray, seed: int,
                random_dir: bool = False) -> np.ndarray:
    """Repeated stratified K-fold OOF decision scores.

    PCA-128 (fit on train) -> StandardScaler -> LogisticRegression(saga).
    If random_dir: replace the fitted probe with a fixed random direction in the
    PCA-reduced space (the AJ equal-rank guard) -- same rank as the real probe,
    no label information.
    """
    n = len(y)
    acc = np.zeros(n, dtype=np.float64)
    cnt = np.zeros(n, dtype=np.float64)
    for rep in range(N_REPEATS):
        skf = StratifiedKFold(n_splits=N_SPLITS, shuffle=True,
                              random_state=seed + rep)
        for tr, te in skf.split(X, y):
            k = min(N_PCA, X[tr].shape[0] - 1, X[tr].shape[1])
            pca = PCA(n_components=k, random_state=seed + rep).fit(X[tr])
            Ztr, Zte = pca.transform(X[tr]), pca.transform(X[te])
            sc = StandardScaler().fit(Ztr)
            Ztr, Zte = sc.transform(Ztr), sc.transform(Zte)
            if random_dir:
                rng = np.random.default_rng(seed + rep + 977)
                w = rng.standard_normal(Ztr.shape[1])
                w /= np.linalg.norm(w)
                s = Zte @ w
            else:
                clf = LogisticRegression(solver="saga", tol=1e-3,
                                         max_iter=5000, C=1.0)
                clf.fit(Ztr, y[tr])
                s = clf.decision_function(Zte)
            acc[te] += s
            cnt[te] += 1.0
    cnt[cnt == 0] = 1.0
    return acc / cnt


def _boot_auroc_ci(y: np.ndarray, s: np.ndarray, seed: int,
                   n_boot: int = 2000) -> tuple[float, float, float]:
    rng = np.random.default_rng(seed)
    base = _auroc(y, s)
    vals = []
    n = len(y)
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        if len(np.unique(y[idx])) < 2:
            continue
        vals.append(_auroc(y[idx], s[idx]))
    lo, hi = (float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))) \
        if vals else (float("nan"), float("nan"))
    return base, lo, hi


def veto_crystallization(arm_dir: Path, rows: list[dict], layer: str,
                         seed: int) -> dict:
    """AK-G1 curve: OOF veto AUROC at first-visible and answer-end (+ guard)."""
    res = {"layer": layer, "positions": {}}
    for pos_name, pos in (("first_visible", "answer_k0"),
                          ("answer_end", "answer_end")):
        X, y, keep = _load_position_matrix(arm_dir, rows, layer, pos)
        s = _oof_scores(X, y, seed)
        auroc, lo, hi = _boot_auroc_ci(y, s, seed)
        s_rand = _oof_scores(X, y, seed, random_dir=True)
        rand_auroc = _auroc(y, s_rand)
        res["positions"][pos_name] = {
            "capture_pos": pos, "n": int(len(y)),
            "n_confab": int(y.sum()), "n_refuse": int((1 - y).sum()),
            "veto_auroc": auroc, "ci95": [lo, hi],
            "random_dir_guard_auroc": rand_auroc,
        }
    fv = res["positions"]["first_visible"]["veto_auroc"]
    ae = res["positions"]["answer_end"]["veto_auroc"]
    res["delta_answerend_minus_firstvisible"] = ae - fv
    return res


# ----------------------------------------------------------------------------
# AK-G2 full-run slope contrast on non-pilot rows
# ----------------------------------------------------------------------------

def g2_full(arm_dir: Path, nonpilot_rows: list[dict], trunk: ak.DoubtTrunk,
            floor: float, seed: int) -> dict:
    sc = ak.slope_contrast(arm_dir, nonpilot_rows, trunk)
    p = ak.permutation_p(sc.confab_slopes, sc.refuse_slopes, n_perm=10000,
                         seed=seed)
    # bootstrap CI on the contrast
    rng = np.random.default_rng(seed + 13)
    cs = np.asarray(sc.confab_slopes)
    rs = np.asarray(sc.refuse_slopes)
    boots = []
    for _ in range(5000):
        bc = rng.choice(cs, len(cs), replace=True).mean()
        br = rng.choice(rs, len(rs), replace=True).mean()
        boots.append(bc - br)
    lo, hi = float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))
    clears = abs(sc.contrast) >= floor
    passes = bool(clears and p < 0.01)
    # path label from the sign / magnitude of confab-row mean slope
    if sc.mean_confab > 0 and sc.mean_confab >= abs(sc.mean_refuse) * 0.5:
        confab_traj = "rise"
    elif sc.mean_confab <= 0:
        confab_traj = "drop"
    else:
        confab_traj = "flat-or-weak-rise"
    return {
        "n_confab": sc.n_confab, "n_refuse": sc.n_refuse,
        "mean_slope_confab": sc.mean_confab,
        "mean_slope_refuse": sc.mean_refuse,
        "slope_contrast": sc.contrast, "slope_contrast_se": sc.se,
        "contrast_ci95": [lo, hi],
        "permutation_p": p, "committed_floor": floor,
        "clears_floor": bool(clears), "p_below_0.01": bool(p < 0.01),
        "AK_G2_pass": passes,
        "confab_doubt_trajectory_sign": confab_traj,
        "note": ("path is descriptive; a G2 PASS means the fork is "
                 "adjudicable at this n, a MISS means it is not"),
    }


# ----------------------------------------------------------------------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--grpo-dir", required=True)
    ap.add_argument("--raw-dir", required=True)
    ap.add_argument("--trunk-layer", default=None,
                    help="override; default = the layer in the committed floor")
    ap.add_argument("--g1-layer", default=G1_LAYER)
    ap.add_argument("--out-dir", default=str(OUT_DIR))
    ap.add_argument("--report-md", default=None,
                    help="optional path for the generated Markdown summary")
    args = ap.parse_args(argv)

    floor_doc = json.loads(FLOOR_JSON.read_text())
    floor = floor_doc["COMMITTED_FLOOR"]
    trunk_layer = args.trunk_layer or floor_doc["trunk"]["layer"]
    pilot_keys = set(floor_doc["pilot_row_keys"])

    grpo_dir = Path(args.grpo_dir).resolve()
    raw_dir = Path(args.raw_dir).resolve()
    trunk = ak.DoubtTrunk.load(PROBES_DIR, trunk_layer)

    grpo_rows = ak.load_rows(grpo_dir)
    raw_rows = ak.load_rows(raw_dir)
    grpo_nonpilot = [r for r in grpo_rows if r["row_key"] not in pilot_keys]
    raw_nonpilot = [r for r in raw_rows if r["row_key"] not in pilot_keys]

    report = {
        "amendment": "AK", "stage": "stage1_gate_analysis",
        "seed": SEED, "trunk_layer": trunk_layer, "g1_layer": args.g1_layer,
        "committed_floor": floor,
        "committed_floor_sha_note": "floor from experiments/commitment-point/artifacts/stage1/ak_stage1_pilot_floor.json",
        "n_pilot_excluded": len(pilot_keys),
        "config_sha": {"grpo_v2": grpo_rows[0]["config_sha"],
                       "raw_base": raw_rows[0]["config_sha"]},
        # ---- AK-G1 (gated on grpo-v2) ----
        "AK_G1": {
            "gated_arm": "grpo-v2",
            "grpo_v2": veto_crystallization(grpo_dir, grpo_rows, args.g1_layer, SEED),
            "raw_base_descriptive": veto_crystallization(raw_dir, raw_rows, args.g1_layer, SEED),
        },
        # ---- AK-G2 (gated, non-pilot) ----
        "AK_G2": {
            "gated_arm": "grpo-v2",
            "grpo_v2": g2_full(grpo_dir, grpo_nonpilot, trunk, floor, SEED),
            "raw_base_descriptive": g2_full(raw_dir, raw_nonpilot, trunk, floor, SEED),
        },
    }
    g1 = report["AK_G1"]["grpo_v2"]["delta_answerend_minus_firstvisible"]
    report["AK_G1"]["verdict"] = ("PASS" if g1 >= AK_G1_MARGIN else "MISS")
    report["AK_G1"]["delta"] = g1
    report["AK_G1"]["margin"] = AK_G1_MARGIN
    report["AK_G2"]["verdict"] = ("PASS" if report["AK_G2"]["grpo_v2"]["AK_G2_pass"]
                                  else "MISS")
    # falsifier: G1 miss AND (G3 is stage-2; here we can only note G1)
    report["falsifier_note"] = (
        "Full AK falsifier needs G3 (Stage 2). Stage 1 reports G1 (grpo-v2) "
        "and G2; a G1 MISS is one of the two falsifier conditions.")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "ak_stage1_gate_report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")

    g1g = report["AK_G1"]["grpo_v2"]
    g2g = report["AK_G2"]["grpo_v2"]
    md = [
        "# Amendment AK Stage 1 - gate report", "",
        f"Trunk layer (G2): {trunk_layer}. G1 veto layer: {args.g1_layer}. "
        f"Seed {SEED}. Committed floor {floor:.6g} "
        f"(pilot excluded, n={len(pilot_keys)}).", "",
        "## AK-G1 crystallization (GATED on grpo-v2)",
        f"- first-visible veto AUROC: {g1g['positions']['first_visible']['veto_auroc']:.4f} "
        f"CI {g1g['positions']['first_visible']['ci95']} "
        f"(rand-dir guard {g1g['positions']['first_visible']['random_dir_guard_auroc']:.3f})",
        f"- answer-end veto AUROC:    {g1g['positions']['answer_end']['veto_auroc']:.4f} "
        f"CI {g1g['positions']['answer_end']['ci95']} "
        f"(rand-dir guard {g1g['positions']['answer_end']['random_dir_guard_auroc']:.3f})",
        f"- delta (end - first) = {g1g['delta_answerend_minus_firstvisible']:+.4f} "
        f"(need >= +{AK_G1_MARGIN}) -> **{report['AK_G1']['verdict']}**",
        f"- raw-base (descriptive) delta = "
        f"{report['AK_G1']['raw_base_descriptive']['delta_answerend_minus_firstvisible']:+.4f}",
        "",
        "## AK-G2 doubt-trajectory discriminability (GATED, non-pilot)",
        f"- grpo-v2 slope contrast = {g2g['slope_contrast']:+.4f} "
        f"CI {['%.3f' % v for v in g2g['contrast_ci95']]}, SE {g2g['slope_contrast_se']:.4f}",
        f"- |contrast| vs floor {floor:.4f}: clears={g2g['clears_floor']}; "
        f"perm p={g2g['permutation_p']:.4g} (<0.01? {g2g['p_below_0.01']})",
        f"- confab mean slope {g2g['mean_slope_confab']:+.3f} / "
        f"refuse mean slope {g2g['mean_slope_refuse']:+.3f} "
        f"-> confab trajectory: {g2g['confab_doubt_trajectory_sign']}",
        f"- **{report['AK_G2']['verdict']}**",
        f"- raw-base (descriptive) contrast = "
        f"{report['AK_G2']['raw_base_descriptive']['slope_contrast']:+.4f}, "
        f"perm p={report['AK_G2']['raw_base_descriptive']['permutation_p']:.4g}",
    ]
    if args.report_md:
        report_md = Path(args.report_md)
        report_md.parent.mkdir(parents=True, exist_ok=True)
        report_md.write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
