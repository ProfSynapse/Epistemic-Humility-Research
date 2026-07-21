#!/usr/bin/env python3
"""G_val planted-signal validation + prediction bands (correctness-geometry
scale-ladder cell), v3. SYNTHETIC DATA ONLY -- never loads or touches the
real Amendment X activation caches, row_key labels, or correct/wrong
outcomes. This is the module authorized to run before `bin/exp sign`.

Pre-registered in experiments/correctness-geometry-scale-ladder/AMENDMENT.md,
design packet sections 13-23 (v2 rebuild + v3 disposition) + LEAD
ADJUDICATION v2 (section 21) and v3 (teammate message, 2026-07-20). v1's run
(mean-shift generator) FAILED all four estimators at all three scales; v2's
run (correlated-redundant flat-Rashomon) built the right generator but its
OWN construction-validity criterion (a) turned out to be unsatisfiable by
ANY mean-shift-type construction (LDA argument: the Bayes-optimal linear
boundary is always rank-1) -- both records are in NOTEBOOK.md and
analysis-committed/, retained for provenance. v3 RETIRES criterion (a) and
replaces it with (a-new) monotone E1 degradation across the r-ladder and
(b-new) a derived index-resolution criterion (sigma_c <= R_max), designates
E1 PRIMARY, demotes E2/E3-k1/E4 to descriptive companions, and fixes the
E1 estimator itself (averaged over R_SH split-half draws, not one noisy
draw) plus the diffuse-calibration search precision.

Pipeline, in order:
  1. Per-scale DIFFUSE (r, rho) calibration (lib.diffuse_grid_point over
     lib.diffuse_grid_points(), dispatched through lib.parallel_map),
     anchored to CD's 0.174 split-half reliability (priority) and SO's
     ~0.04 random-slice margin (tiebreak) -- lead ruling 21.1. v3 fix (ii):
     more reps/finer calib_iters than v2's search, to remove the
     calibration-procedure drift documented in NOTEBOOK.md (14B's official
     R_SIM=30 mean landed at 0.266 against a 0.165 calibration estimate).
  2. Resolve the five per-scale conditions: compact (r=1), r-ladder
     {r=2,4,8} at the fixed RHO_LADDER, and the calibrated diffuse.
  3. R_SIM=30 reps per (scale, condition): generate a FULL-N (imbalanced,
     matching each scale's real class counts) synthetic dataset, calibrated
     by bisection to that scale's already-committed X-G2 dial AUROC; run
     E1 at full-n (PRIMARY, v3 fix (i): averaged over R_SH split-half
     draws); draw a matched-n (N*=377/377) stratified subsample from the
     SAME full-n draw for E1 (secondary) / E2 / E3-k1 / E4 (all matched-n,
     unchanged sampling rule, descriptive companions per v3) and the
     k-sweep (still computed, descriptive -- it no longer feeds a gate
     criterion since (a-old) is retired).
  4. Aggregate over reps; evaluate construction-validity v3 (a-new)-(c) --
     HARD BLOCKING STOP if (a-new), (c), or (b-new) at the 8B/14B "powered
     pair" fails; 1.7B's own (b-new) result is recorded as a BRANCH
     (full pass, or stated limitation) rather than a blocking failure,
     per the lead's pre-stated 1.7B disposition (item 6).
  5. Evaluate G_val v2-band-based criteria per estimator per scale (section
     16, unchanged structure) and the primary-designation fallback order
     (section 21.5: E3-k1, then E1, then E2; E4 never primary) -- this now
     resolves mechanically to E1 (E3-k1 still fails separation; E1's old
     hand-picked absolute-0.70 reach floor is replaced by the SAME (b-new)
     band-based test construction-validity uses, so E1's own gate criteria
     and its construction-validity criteria are one source of truth).
  6. Two-anchor (compact + diffuse) prediction bands per scale per
     estimator (section 17, un-clipped per 22.6.1) and the pre-registered
     trend test (section 22.6.3: monotonicity of c + Delta_c vs propagated
     sigma) -- both implemented as pure functions, NOT evaluated here since
     this module never reads a real observed value.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
TUNER_DIR = REPO_ROOT / "synaptic-tuner"
if str(TUNER_DIR) not in sys.path:
    sys.path.insert(0, str(TUNER_DIR))
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from shared.utilities.run_log import RunLog  # noqa: E402
import scale_ladder_lib as lib  # noqa: E402

MODULE_VERSION = 3

# Already-committed X-G2 dial AUROC per scale (Amendment X Outcome table,
# experiments/cross-model-size-sweep/AMENDMENT.md lines 175/195/214). Public,
# already-signed numbers; using them to calibrate synthetic signal strength
# is not a read of any real per-row label. Unchanged from v1.
OBSERVED_FULL_PCA_AUROC = {"1.7b": 0.8152, "8b": 0.8621, "14b": 0.8399}

SEED_PLANTED = 20260720
SEED_DIFFUSE_CALIB = 20260722

R_LADDER_CONDITIONS = ("r2", "r4", "r8")   # r-ladder members with r>1
CONDITION_ORDER = ("compact", "r2", "r4", "r8", "diffuse")
CONDITION_R = {"compact": 1, "r2": 2, "r4": 4, "r8": 8}   # "diffuse" resolved per scale
R_LADDER_ALL = ("compact", "r2", "r4", "r8")   # v3 (a-new): full r-ladder including compact

# v3 construction-validity thresholds (design packet section 22.3, teammate
# message item 1 "v3 build"). RETIRES v2's criterion (a) (k=1 decodability-
# insufficiency -- proven mathematically unsatisfiable by any mean-shift-type
# construction, LDA argument, section 13/22.1) and its hand-picked absolute
# CV_B_COMPACT_E1_FLOOR=0.70. Fixed BEFORE the official v3 run is read.
CV_A_MONOTONE_TOL_MULT = 1.0   # (a-new): r-ladder E1 full-n means must be non-increasing
                                # compact->r2->r4->r8, within this multiple of the mean
                                # per-condition half-width (the reps' own spread), not a
                                # hand-picked absolute tolerance.
CV_C_SEPARATION_MARGIN = 0.0   # (c): separation must exceed the pooled half-width by >0 (strict)

# v3 (b-new): derived index-resolution ceiling (section 22.3/22.7). R_max is
# DERIVED from a pre-stated minimum detectable per-scale-step
# crystallization effect (Delta_min) and a confidence multiple (z), never
# reverse-engineered from a result: R_max = Delta_min / (z * sqrt(2)).
# Delta_min=0.5 ("half the full diffuse->compact range per scale-step -- a
# crystallization-scale effect, appropriate for an exploratory Tier-2 looking
# for a big effect"), z=1.5 -- both the design packet's own recommended
# values (section 22.3), adopted by the lead ("LOCKED as adopted"). Neither
# moves after seeing the run, in either direction (teammate message item 1).
CV_B_DELTA_MIN = 0.5
CV_B_Z = 1.5
CV_B_R_MAX = CV_B_DELTA_MIN / (CV_B_Z * float(np.sqrt(2.0)))   # ~= 0.2357

# v3 pre-stated 1.7B disposition (teammate message item 6): (b-new) is a hard
# requirement at the "powered pair" (8B, 14B); 1.7B's own (b-new) result is
# recorded as a BRANCH (full pass vs stated limitation), never allowed to
# block the overall gate or be reverse-engineered by moving CV_B_DELTA_MIN /
# CV_B_Z to force a pass.
CV_B_POWERED_SCALES = ("8b", "14b")


def resolve_diffuse_params(workers: int, smoke: bool = False) -> dict:
    """Per-scale diffuse (r, rho) calibration, parallelized across the full
    grid (independent work units, keyed by explicit scale/r/rho strings).

    Smoke mode uses a MUCH smaller grid/quick_reps/calib_iters purely to
    keep the smoke drill fast (this search has no reported/gated numbers of
    its own -- it just picks (r, rho) -- so shrinking it in smoke mode does
    not touch anything the smoke drill needs to validate: RunLog
    persistence, --workers equivalence, kill-resume, and the full
    downstream aggregation/gate code path all still run against whatever
    (r, rho) the smoke-scale search picks).

    v3 fix (ii) (design packet section 22.7 / teammate message item 3(ii)):
    the official (non-smoke) search's quick_reps/quick_calib_iters are
    raised from v2's 2/25 to 5/35 -- v2's 14B diffuse point drifted from a
    0.165 calibration estimate to a 0.266 official R_SIM=30 mean, a
    calibration-PROCEDURE artifact (too few reps, too loose an AUROC
    calibration tolerance in the search), not a reason to hand-pick a
    different point. This is a search-precision fix, not a retune of any
    gate threshold the search's own numbers are judged against (it has
    none)."""
    out = {}
    grid = [(8, 0.7), (32, 0.85)] if smoke else lib.diffuse_grid_points()
    quick_reps = 1 if smoke else 5
    quick_calib_iters = 12 if smoke else 35
    quick_r_sh = 1 if smoke else 3
    for scale in lib.SCALES:
        n_pos_full, n_neg_full = lib.EXPECTED_CLASS_COUNTS[scale]
        base_seed = lib.sub_seed(SEED_DIFFUSE_CALIB, scale)
        args_list = [
            (scale, r, rho, OBSERVED_FULL_PCA_AUROC[scale], n_pos_full, n_neg_full,
             lib.N_STAR, base_seed, quick_reps, 5, quick_calib_iters, quick_r_sh)
            for (r, rho) in grid
        ]
        candidates = lib.parallel_map(lib.diffuse_grid_point, args_list, workers)
        best = lib.pick_best_diffuse_candidate(candidates)
        out[scale] = best
        print(f"[planted-sim] diffuse calibration scale={scale}: r={best['r']} rho={best['rho']} "
              f"achieved E1_full_n={best['e1_full_n_mean']:.3f} (target {lib.DIFFUSE_FINGERPRINT_TARGET['e1_full_n']}) "
              f"E3_k1_margin={best['e3_k1_margin_mean']:.3f} (target {lib.DIFFUSE_FINGERPRINT_TARGET['e3_k1_margin']})",
              flush=True)
    return out


def resolve_conditions(diffuse_params: dict) -> dict:
    conditions = {}
    for scale in lib.SCALES:
        dp = diffuse_params[scale]
        conditions[scale] = {
            "compact": (1, 0.0),
            "r2": (2, lib.RHO_LADDER),
            "r4": (4, lib.RHO_LADDER),
            "r8": (8, lib.RHO_LADDER),
            "diffuse": (dp["r"], dp["rho"]),
        }
    return conditions


def run_one_rep(scale: str, condition: str, r: int, rho: float, rep: int) -> dict:
    target_auroc = OBSERVED_FULL_PCA_AUROC[scale]
    n_pos_full, n_neg_full = lib.EXPECTED_CLASS_COUNTS[scale]
    gen_seed = lib.sub_seed(SEED_PLANTED, scale, condition, f"rep{rep}", "gen_full")
    X_full, y_full = lib.synthetic_redundant_features(
        n_pos_full, n_neg_full, lib.PCA_DIM, r, rho, target_auroc, gen_seed, calib_iters=40,
    )
    fit_seed = lib.sub_seed(SEED_PLANTED, scale, condition, f"rep{rep}", "fit")
    # v3 fix (i): E1 averaged over lib.R_SH independent split-half draws
    # (was a single draw in v2) -- applied identically to full-n (primary)
    # and matched-n (secondary).
    e1_full_n = lib.e1_split_half_reliability_avg(X_full, y_full, fit_seed)

    sub_idx = lib.stratified_subsample_indices(
        y_full, lib.N_STAR, lib.sub_seed(SEED_PLANTED, scale, condition, f"rep{rep}", "sub"),
    )
    Xm, ym = X_full[sub_idx], y_full[sub_idx]
    e1_matched_n = lib.e1_split_half_reliability_avg(Xm, ym, fit_seed)
    e2 = lib.e2_concentration_ratio(Xm, ym, fit_seed)
    e3_k1 = lib.e3_random_slice_margin(Xm, ym, 1, fit_seed)
    e4 = lib.e4_participation_ratio(Xm, ym, fit_seed, p_perm=100)
    k_sweep = {str(k): lib.restricted_cv_auroc(Xm, ym, k, fit_seed) for k in (1, 2, 4, 8)}

    return {
        "e1_full_n": e1_full_n, "e1_matched_n": e1_matched_n,
        "e2_ratio": e2["ratio"], "e2_auroc_full": e2["auroc_full"], "e2_auroc_top1": e2["auroc_top1"],
        "e3_k1_margin": e3_k1["margin"], "e3_k1_disc_auroc": e3_k1["discriminative_auroc"],
        "e3_k1_rand_mean": e3_k1["random_slice_mean_auroc"],
        "e4_pr": e4["pr"], "e4_pr_raw_unadjusted": e4["pr_raw_unadjusted"],
        "k_sweep": k_sweep,
    }


def _rep_worker(scale, condition, r, rho, rep):
    return scale, condition, rep, run_one_rep(scale, condition, r, rho, rep)


def key_for(scale, condition, rep) -> str:
    return f"{scale}|{condition}|{rep}"


def central_90(values: list[float]) -> tuple[float, float]:
    arr = np.asarray([v for v in values if np.isfinite(v)], dtype=float)
    if len(arr) == 0:
        return float("nan"), float("nan")
    return float(np.percentile(arr, 5)), float(np.percentile(arr, 95))


SCALAR_KEYS = ("e1_full_n", "e1_matched_n", "e2_ratio", "e3_k1_margin", "e4_pr")


def aggregate(records: dict, conditions: dict, r_sim: int) -> dict:
    agg = {}
    for scale in lib.SCALES:
        agg[scale] = {}
        for condition in CONDITION_ORDER:
            vals = {k: [] for k in SCALAR_KEYS}
            k_sweep_vals = {str(k): [] for k in (1, 2, 4, 8)}
            for rep in range(r_sim):
                rec = records.get(key_for(scale, condition, rep))
                if rec is None:
                    continue
                for k in vals:
                    vals[k].append(rec[k])
                for kk in k_sweep_vals:
                    k_sweep_vals[kk].append(rec["k_sweep"][kk])
            entry = {}
            for k, vs in vals.items():
                lo, hi = central_90(vs)
                arr = np.asarray([v for v in vs if np.isfinite(v)], dtype=float)
                entry[k] = {"mean": float(np.mean(arr)) if len(arr) else float("nan"),
                            "median": float(np.median(arr)) if len(arr) else float("nan"),
                            "p5": lo, "p95": hi, "n": len(arr)}
            entry["k_sweep"] = {kk: float(np.mean(vs)) if vs else float("nan")
                                for kk, vs in k_sweep_vals.items()}
            agg[scale][condition] = entry
    return agg


def _pooled_hw(scale: str, condition: str, key: str, agg: dict) -> float:
    d = agg[scale][condition][key]
    return float((d["p95"] - d["p5"]) / 2.0)


def check_construction_validity(agg: dict) -> dict:
    """v3 construction-validity (design packet section 22.3, teammate
    message item 1). RETIRES v2's criterion (a) (k=1 decodability-
    insufficiency, section 14/21.4) -- proven mathematically unsatisfiable
    by any mean-shift-type construction (LDA argument; verified empirically
    at every (scale, r) cell in the v2 run, -0.0005 to +0.0030 rise against
    a >0.02 requirement) and replaced with two criteria that test the axis
    the cell actually measures:

    (a-new) monotone E1 full-n degradation across the r-ladder {compact,
    r2, r4, r8} at fixed rho=RHO_LADDER, at all three scales -- the v2 run
    already demonstrated this cleanly (section 22.3); this criterion turns
    that demonstration into a governed, re-checked-every-run assertion.
    (b-new) derived index-resolution ceiling sigma_c(s) <=
    CV_B_R_MAX per scale, where sigma_c(s) = (diffuse_hw_s / 1.645) /
    gap_s and gap_s = compact_mean_s - diffuse_mean_s (E1 full-n).
    HARD requirement at the "powered pair" (8B, 14B); 1.7B's own result is
    recorded as a BRANCH (pre-stated lead disposition, teammate message
    item 6) and does NOT block overall_pass.
    (c) unchanged: compact-vs-diffuse separated on the primary estimator
    (E1 full-n, since only E1 is designated PRIMARY under v3 -- section
    22.3: "compact/diffuse separated on the primary estimator"). The
    multi-estimator separation table (E1/E2/E3-k1) is still computed and
    reported for transparency, but the (c) pass/fail is E1-specific.
    """
    detail = {"a_monotone_r_ladder": {}, "b_index_resolution": {}, "c_separation": {}}
    a_pass_all, c_pass_all = True, True

    for scale in lib.SCALES:
        # --- (a-new): monotone E1 full-n degradation, compact -> r8 -------
        r_vals = [agg[scale][c]["e1_full_n"]["mean"] for c in R_LADDER_ALL]
        tol = float(np.nanmean([_pooled_hw(scale, c, "e1_full_n", agg) for c in R_LADDER_ALL])) \
            * CV_A_MONOTONE_TOL_MULT
        monotone = bool(all(r_vals[i] >= r_vals[i + 1] - tol for i in range(len(r_vals) - 1)))
        a_pass_all = a_pass_all and monotone
        detail["a_monotone_r_ladder"][scale] = {
            "e1_full_n_means": dict(zip(R_LADDER_ALL, r_vals)), "tolerance": tol, "pass": monotone,
        }

        # --- (b-new): derived index-resolution ceiling --------------------
        compact_mean = agg[scale]["compact"]["e1_full_n"]["mean"]
        diffuse_mean = agg[scale]["diffuse"]["e1_full_n"]["mean"]
        diffuse_hw = _pooled_hw(scale, "diffuse", "e1_full_n", agg)
        gap = compact_mean - diffuse_mean
        sigma_c = float((diffuse_hw / 1.645) / gap) if gap > 1e-9 else float("inf")
        b_ok = bool(np.isfinite(sigma_c) and sigma_c <= CV_B_R_MAX)
        detail["b_index_resolution"][scale] = {
            "compact_mean": compact_mean, "diffuse_mean": diffuse_mean, "gap": gap,
            "diffuse_half_width": diffuse_hw, "sigma_c": sigma_c, "r_max": CV_B_R_MAX, "pass": b_ok,
        }

        # --- (c): separation, E1-specific pass/fail, full table reported --
        sep = {}
        for key, higher_is_compact in (("e1_full_n", True), ("e2_ratio", True), ("e3_k1_margin", True)):
            cm = agg[scale]["compact"][key]["mean"]
            dm = agg[scale]["diffuse"][key]["mean"]
            pooled_hw = float(np.nanmean([_pooled_hw(scale, "compact", key, agg),
                                           _pooled_hw(scale, "diffuse", key, agg)]))
            diff = (cm - dm) if higher_is_compact else (dm - cm)
            separated = bool(np.isfinite(diff) and diff > pooled_hw + CV_C_SEPARATION_MARGIN)
            sep[key] = {"compact_mean": cm, "diffuse_mean": dm,
                        "pooled_half_width": pooled_hw, "diff": diff, "separated": separated}
        c_ok = bool(sep["e1_full_n"]["separated"])
        c_pass_all = c_pass_all and c_ok
        detail["c_separation"][scale] = {"per_estimator": sep, "pass": c_ok, "primary_estimator": "e1_full_n"}

    b_pass_powered = all(detail["b_index_resolution"][s]["pass"] for s in CV_B_POWERED_SCALES)
    b_1p7b_pass = detail["b_index_resolution"]["1.7b"]["pass"]
    b_1p7b_branch = "full_pass" if b_1p7b_pass else "stated_limitation"

    overall = bool(a_pass_all and b_pass_powered and c_pass_all)
    return {
        "a_pass": a_pass_all, "b_pass_powered": b_pass_powered, "b_1p7b_pass": b_1p7b_pass,
        "b_1p7b_branch": b_1p7b_branch, "c_pass": c_pass_all, "overall_pass": overall,
        "r_max": CV_B_R_MAX, "delta_min": CV_B_DELTA_MIN, "z": CV_B_Z, "detail": detail,
    }


def _mono_ok(vals: list[float], increasing: bool, tol: float) -> bool:
    if increasing:
        return all(vals[i] <= vals[i + 1] + tol for i in range(len(vals) - 1))
    return all(vals[i] >= vals[i + 1] - tol for i in range(len(vals) - 1))


def g_val_v2(agg: dict, cv: dict) -> dict:
    """Section 16: separation / monotonicity / compact-reachability, band-
    based, per estimator per scale. Computed and reported for ALL FOUR
    estimators for transparency, but only E1 is PRIMARY under v3 (teammate
    message item 2); E2/E3_k1/E4 are descriptive companions and keep the
    UNCHANGED all-three-scales rule (teammate message: "the all-three-scales
    rule is not relaxed" for them).

    E1's own "reachable" criterion is v3's REPLACEMENT for v2's hand-picked
    absolute CV_B_COMPACT_E1_FLOOR=0.70: it is the SAME (b-new)
    sigma_c<=R_max result construction-validity computes (`cv` is passed in
    so there is one source of truth, not two independently-tuned band
    checks). E1's overall "pass" (the boolean `designate_primary` reads)
    uses the "powered pair" (8B, 14B) per the pre-stated 1.7B disposition
    (teammate message item 6); 1.7B's own per-scale result is still reported
    honestly (it may show `pass: false` there) but does not block E1 from
    being usable as primary."""
    out = {}
    estimator_specs = {
        "E1": ("e1_full_n", True),
        "E2": ("e2_ratio", True),
        "E3_k1": ("e3_k1_margin", True),
        "E4": ("e4_pr", False),
    }
    for est, (key, higher_is_compact) in estimator_specs.items():
        per_scale = {}
        for scale in lib.SCALES:
            compact_mean = agg[scale]["compact"][key]["mean"]
            diffuse_mean = agg[scale]["diffuse"][key]["mean"]
            compact_hw = (agg[scale]["compact"][key]["p95"] - agg[scale]["compact"][key]["p5"]) / 2.0
            diffuse_hw = (agg[scale]["diffuse"][key]["p95"] - agg[scale]["diffuse"][key]["p5"]) / 2.0
            pooled_hw = float(np.nanmean([compact_hw, diffuse_hw]))
            diff = (compact_mean - diffuse_mean) if higher_is_compact else (diffuse_mean - compact_mean)
            separated = bool(np.isfinite(diff) and diff > pooled_hw)

            r_vals = [agg[scale][c][key]["mean"] for c in ("compact", "r2", "r4", "r8")]
            tol = float(np.nanmean([
                (agg[scale][c][key]["p95"] - agg[scale][c][key]["p5"]) / 2.0
                for c in ("compact", "r2", "r4", "r8")
            ]))
            monotone = bool(_mono_ok(r_vals, increasing=not higher_is_compact, tol=tol) if not higher_is_compact
                             else _mono_ok(r_vals, increasing=False, tol=tol))

            if est == "E1":
                reachable = bool(cv["detail"]["b_index_resolution"][scale]["pass"])
                reach_desc = "band-based: same (b-new) sigma_c<=R_max as construction-validity (v3, replaces v2's absolute-0.70 floor)"
            else:
                reachable = True
                reach_desc = "no separate reachability limb (descriptive companion, v3); separation+monotonicity only"

            scale_pass = bool(separated and monotone and reachable)
            per_scale[scale] = {
                "compact_mean": compact_mean, "diffuse_mean": diffuse_mean,
                "pooled_half_width": pooled_hw, "diff": diff, "separated": separated,
                "r_ladder_means": dict(zip(("compact", "r2", "r4", "r8"), r_vals)),
                "monotone": monotone, "reachable": reachable, "reachability_note": reach_desc,
                "pass": scale_pass,
            }
        overall_pass_all_three = all(per_scale[s]["pass"] for s in lib.SCALES)
        if est == "E1":
            overall_pass_powered = all(per_scale[s]["pass"] for s in CV_B_POWERED_SCALES)
            out[est] = {
                "per_scale": per_scale, "pass": overall_pass_powered,
                "pass_all_three_scales": overall_pass_all_three,
                "pass_powered_pair_8b_14b": overall_pass_powered,
                "note": "PRIMARY (v3). 'pass' uses the powered-pair (8B/14B) carve-out per the "
                        "pre-stated 1.7B disposition; 1.7B's own per-scale result is reported "
                        "honestly above and does not block this designation.",
            }
        else:
            out[est] = {"per_scale": per_scale, "pass": overall_pass_all_three,
                         "note": "descriptive companion (v3); all-three-scales rule NOT relaxed."}
    return out


def designate_primary(g_val: dict) -> dict:
    """Section 21.5 fallback order: E3-k1, then E1, then E2; E4 never
    primary. M4-prime fires if none of E1/E2/E3 pass (section 18).

    v3: this mechanism is UNCHANGED -- it is the pre-registered fallback
    ORDER, not a hand-picked outcome. It resolves to E1 mechanically because
    E3_k1 still fails separation (its construction is unaffected by the v3
    changes) and E1's own G_val criteria were fixed (v3 item 2/22.4) so it
    can now pass at the powered pair. The teammate message's "E1 PRIMARY"
    ruling is the predicted RESULT of applying this unchanged order to the
    v3 numbers, not an override of it."""
    order = ("E3_k1", "E1", "E2")
    for est in order:
        if g_val[est]["pass"]:
            return {"primary": est, "fallback_order": order, "m4_prime": False}
    return {"primary": None, "fallback_order": order, "m4_prime": True}


def two_anchor_bands(agg: dict) -> dict:
    """Section 17: compact + diffuse bands per scale per estimator."""
    bands = {}
    for scale in lib.SCALES:
        bands[scale] = {}
        for key in SCALAR_KEYS:
            entry = {}
            for anchor in ("compact", "diffuse"):
                d = agg[scale][anchor][key]
                entry[anchor] = {"mean": d["mean"], "p5": d["p5"], "p95": d["p95"],
                                  "half_width": float((d["p95"] - d["p5"]) / 2.0) if np.isfinite(d["p95"]) else float("nan")}
            bands[scale][key] = entry
    return bands


def crystallization_index(observed: float, compact_mean: float, diffuse_mean: float) -> float:
    """Section 17: c = (observed - diffuse_mean) / (compact_mean - diffuse_mean).
    ~0 if the scale's correctness object looks CD/SO-diffuse, ~1 if
    crystallized. Pure function -- this module never has a REAL `observed`
    value to pass in (it never reads real labels); ready for use once
    scale_ladder_real.py's real-label run exists, post-sign.

    v3 (section 22.6.1, teammate message item 5): c is deliberately NOT
    clipped to [0, 1] -- out-of-range values are informative (c<0 = more
    diffuse than the real 4B direction; c>1 = more identifiable than a
    clean rank-1 signal at this n). This was already the case in v2 (no
    clip was ever implemented here); this docstring makes it explicit per
    the design packet's own correction to its earlier "clipped" wording.
    Per-scale-anchor normalization (each scale's OWN compact_mean/
    diffuse_mean) is what makes cross-scale comparison coherent under
    full-n-primary (21.2/22.4/22.6.2) -- it absorbs the differing n and
    hidden_dim per scale, superseding matched-n comparability for E1."""
    denom = compact_mean - diffuse_mean
    if not np.isfinite(denom) or abs(denom) < 1e-12:
        return float("nan")
    return float((observed - diffuse_mean) / denom)


def trend_test(c_by_scale: dict, sigma_c_by_scale: dict, z: float) -> dict:
    """Section 22.6.3 pre-registered trend test, implemented but NOT
    EVALUATED here (this module never reads a real observed value, so
    `c_by_scale` has no real content to pass in pre-sign). Ready for the
    real-label run post-sign.

    Headline read = (i) monotonicity of (c_1.7b, c_8b, c_14b) and (ii) the
    endpoint contrast Delta_c = c_14b - c_1.7b against the propagated
    standard error sigma = sqrt(sigma_c(1.7b)^2 + sigma_c(14b)^2);
    "materially sharpening" = Delta_c > z*sigma, with z LOCKED AT SIGN (per
    the design packet -- this function accepts z as a parameter rather than
    hard-coding one, so the lead's sign-time choice is the only place it is
    fixed)."""
    order = ("1.7b", "8b", "14b")
    vals = [c_by_scale.get(s) for s in order]
    monotone = None
    if all(v is not None and np.isfinite(v) for v in vals):
        monotone = bool(vals[0] <= vals[1] <= vals[2])
    delta_c, sigma_prop, materially_sharpening = None, None, None
    c_lo, c_hi = c_by_scale.get("1.7b"), c_by_scale.get("14b")
    s_lo, s_hi = sigma_c_by_scale.get("1.7b"), sigma_c_by_scale.get("14b")
    if c_lo is not None and c_hi is not None and np.isfinite(c_lo) and np.isfinite(c_hi):
        delta_c = float(c_hi - c_lo)
        if s_lo is not None and s_hi is not None and np.isfinite(s_lo) and np.isfinite(s_hi):
            sigma_prop = float(np.sqrt(s_lo ** 2 + s_hi ** 2))
            materially_sharpening = bool(delta_c > z * sigma_prop)
    return {"monotone": monotone, "delta_c": delta_c, "sigma_prop": sigma_prop, "z": z,
            "materially_sharpening": materially_sharpening,
            "evaluated": False, "note": "implemented, not evaluated -- no real observed value pre-sign"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out-dir", default=str(HERE / "analysis-committed"))
    ap.add_argument("--work-dir", default=str(HERE / "analysis"))
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--workers", type=int, default=lib.default_workers())
    ap.add_argument("--fresh", action="store_true", help="discard any existing checkpoint")
    args = ap.parse_args()

    t0 = time.time()
    out_dir = Path(args.out_dir)
    work_dir = Path(args.work_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)
    n_workers = max(1, args.workers)

    r_sim = 3 if args.smoke else lib.R_SIM

    print(f"[planted-sim v2] diffuse calibration (smoke={args.smoke}, workers={n_workers})...", flush=True)
    diffuse_params = resolve_diffuse_params(n_workers, smoke=args.smoke)
    conditions = resolve_conditions(diffuse_params)

    run_config = {
        "module": "scale_ladder_planted_sim", "version": MODULE_VERSION,
        "smoke": args.smoke, "conditions": list(CONDITION_ORDER), "r_sim": r_sim,
        "seed_planted": SEED_PLANTED, "seed_diffuse_calib": SEED_DIFFUSE_CALIB,
        "n_star": lib.N_STAR, "pca_dim": lib.PCA_DIM, "rho_ladder": lib.RHO_LADDER,
        "observed_full_pca_auroc": OBSERVED_FULL_PCA_AUROC,
        "diffuse_params": diffuse_params,
        "diffuse_fingerprint_target": lib.DIFFUSE_FINGERPRINT_TARGET,
    }
    log_path = work_dir / "runlog" / ("planted_sim_smoke.jsonl" if args.smoke else "planted_sim.jsonl")
    run_log = RunLog(log_path, run_config=run_config, fresh=args.fresh)

    all_tasks = []
    for scale in lib.SCALES:
        for condition in CONDITION_ORDER:
            r, rho = conditions[scale][condition]
            for rep in range(r_sim):
                all_tasks.append((scale, condition, r, rho, rep))
    pending = list(run_log.iter_pending(all_tasks, key_fn=lambda t: key_for(t[0], t[1], t[4])))
    print(f"[planted-sim v2] {len(all_tasks)} total reps, {len(pending)} pending, "
          f"workers={n_workers}, smoke={args.smoke}", flush=True)

    by_batch: dict[tuple, list] = {}
    for t in pending:
        by_batch.setdefault((t[0], t[1]), []).append(t)

    for (scale, condition), batch_tasks in by_batch.items():
        results = lib.parallel_map(_rep_worker, batch_tasks, n_workers)
        for s, c, rep, payload in results:
            run_log.record(key_for(s, c, rep), payload)
        print(f"[planted-sim v2] scale={scale} condition={condition} batch done "
              f"({len(batch_tasks)} reps)", flush=True)

    records = {k: {kk: vv for kk, vv in v.items() if kk != run_log.key_field}
               for k, v in run_log._records.items()}
    agg = aggregate(records, conditions, r_sim)
    cv = check_construction_validity(agg)
    g_val = g_val_v2(agg, cv)
    primary = designate_primary(g_val)
    bands = two_anchor_bands(agg)

    wall_s = time.time() - t0
    summary = {
        "config": run_config, "wall_clock_s": wall_s, "n_reps_total": len(all_tasks),
        "n_reps_computed_this_run": len(pending),
        "construction_validity_overall_pass": cv["overall_pass"],
        "construction_validity_1p7b_branch": cv["b_1p7b_branch"],
        "g_val": {k: v["pass"] for k, v in g_val.items()},
        "primary": primary,
    }
    run_log.finalize(summary)
    run_log.close()

    out = {
        "config": run_config, "wall_clock_s": wall_s, "conditions_resolved": conditions,
        "aggregate": agg, "construction_validity": cv, "g_val": g_val,
        "primary_designation": primary, "prediction_bands": bands,
    }
    (out_dir / "planted_sim_g_val.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    _write_md(out, out_dir / "planted_sim_g_val.md")
    print(f"[planted-sim v3] wrote {out_dir}/planted_sim_g_val.{{json,md}} in {wall_s:.1f}s", flush=True)
    print(f"[planted-sim v3] construction_validity.overall_pass = {cv['overall_pass']} "
          f"(a={cv['a_pass']}, b_powered={cv['b_pass_powered']}, "
          f"b_1.7b_branch={cv['b_1p7b_branch']}, c={cv['c_pass']})", flush=True)
    if not cv["overall_pass"]:
        print("[planted-sim v3] HARD BLOCKING STOP: construction-validity failed at the "
              "powered pair (8B/14B) or on (a)/(c); G_val numbers below are computed for "
              "transparency only and are NOT actionable -- no threshold may be locked on "
              "this construction.", flush=True)
    print(f"[planted-sim v3] G_val pass/fail: " + ", ".join(f"{k}={v['pass']}" for k, v in g_val.items()),
          flush=True)
    print(f"[planted-sim v3] primary designation: {primary}", flush=True)
    return 0


def _fmt(v, nd=4):
    if v is None or (isinstance(v, float) and not np.isfinite(v)):
        return "-"
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, float):
        return f"{v:.{nd}f}"
    return str(v)


def _write_md(out: dict, path: Path) -> None:
    lines = ["# Planted-signal validation (G_val) v3 + construction-validity + prediction bands",
              "", "SYNTHETIC DATA ONLY. Correlated-redundant flat-Rashomon generator "
              "(lib.synthetic_redundant_features); conditions = compact (r=1), r-ladder "
              f"{{r2,r4,r8}} at rho={out['config']['rho_ladder']}, diffuse (calibrated per scale). "
              f"R_SIM={out['config']['r_sim']} replicates per (scale, condition), calibrated per "
              f"scale to that scale's committed full-PCA dial AUROC "
              f"({out['config']['observed_full_pca_auroc']}). E1 averaged over R_SH={lib.R_SH} "
              "independent split-half draws (v3 fix i). v3 RETIRES v2's criterion (a) "
              "(decodability-insufficiency, unsatisfiable by any mean-shift construction) and "
              "designates E1 PRIMARY; E2/E3_k1/E4 are descriptive companions.", ""]

    lines.append("## Diffuse calibration (lead ruling 21.1)")
    lines.append("")
    lines.append("| scale | r | rho | achieved E1 full-n (target 0.174) | achieved E3-k1 margin (target 0.04) |")
    lines.append("|---|---|---|---|---|")
    for scale, dp in out["config"]["diffuse_params"].items():
        lines.append(f"| {scale} | {dp['r']} | {dp['rho']} | {_fmt(dp['e1_full_n_mean'])} | {_fmt(dp['e3_k1_margin_mean'])} |")
    lines.append("")

    cv = out["construction_validity"]
    lines.append(f"## Construction-validity gate v3 (section 22.3; HARD BLOCKING STOP if fail): "
                 f"overall_pass = **{cv['overall_pass']}** (a={cv['a_pass']}, "
                 f"b_powered_8b_14b={cv['b_pass_powered']}, b_1.7b_branch={cv['b_1p7b_branch']}, "
                 f"c={cv['c_pass']}); R_max={_fmt(cv['r_max'])} (Delta_min={cv['delta_min']}, z={cv['z']})")
    lines.append("")
    lines.append("### (a-new) monotone E1 full-n degradation, r-ladder {compact,r2,r4,r8}")
    lines.append("")
    lines.append("| scale | compact | r2 | r4 | r8 | tolerance | pass |")
    lines.append("|---|---|---|---|---|---|---|")
    for scale, d in cv["detail"]["a_monotone_r_ladder"].items():
        m = d["e1_full_n_means"]
        lines.append(f"| {scale} | {_fmt(m['compact'])} | {_fmt(m['r2'])} | {_fmt(m['r4'])} | {_fmt(m['r8'])} "
                     f"| {_fmt(d['tolerance'])} | {d['pass']} |")
    lines.append("")
    lines.append("### (b-new) derived index-resolution ceiling: sigma_c(s) <= R_max "
                 f"(R_max = Delta_min/(z*sqrt(2)) = {_fmt(cv['r_max'])}); HARD at {CV_B_POWERED_SCALES}, "
                 "1.7B recorded as a branch (pre-stated 1.7B disposition)")
    lines.append("")
    lines.append("| scale | compact mean | diffuse mean | gap | diffuse half-width | sigma_c | pass |")
    lines.append("|---|---|---|---|---|---|---|")
    for scale, d in cv["detail"]["b_index_resolution"].items():
        lines.append(f"| {scale} | {_fmt(d['compact_mean'])} | {_fmt(d['diffuse_mean'])} | {_fmt(d['gap'])} "
                     f"| {_fmt(d['diffuse_half_width'])} | {_fmt(d['sigma_c'])} | {d['pass']} |")
    lines.append("")
    lines.append("### (c) compact-vs-diffuse separation on the primary estimator (E1 full-n); "
                 "E2/E3-k1 reported alongside for transparency")
    lines.append("")
    for scale, d in cv["detail"]["c_separation"].items():
        lines.append(f"- **{scale}** (pass={d['pass']}, primary_estimator={d['primary_estimator']}): " + ", ".join(
            f"{k}: diff={_fmt(v['diff'])} vs half-width={_fmt(v['pooled_half_width'])} sep={v['separated']}"
            for k, v in d["per_estimator"].items()))
    lines.append("")

    lines.append("## G_val v2-band-based pass/fail (ACTIONABLE per estimator: E1 uses the powered-pair "
                 "carve-out per the pre-stated 1.7B disposition; E2/E3_k1/E4 keep the unchanged "
                 "all-three-scales rule and remain descriptive companions)")
    lines.append("")
    lines.append("| estimator | pass |")
    lines.append("|---|---|")
    for est, v in out["g_val"].items():
        lines.append(f"| {est} | {v['pass']} |")
    lines.append("")
    for est, v in out["g_val"].items():
        lines.append(f"### {est} per-scale detail")
        lines.append("")
        for scale, d in v["per_scale"].items():
            lines.append(f"- **{scale}**: compact={_fmt(d['compact_mean'])} diffuse={_fmt(d['diffuse_mean'])} "
                         f"diff={_fmt(d['diff'])} pooled_hw={_fmt(d['pooled_half_width'])} sep={d['separated']} "
                         f"mono={d['monotone']} reach={d['reachable']} pass={d['pass']} "
                         f"r_ladder={{ {', '.join(f'{k}:{_fmt(vv)}' for k, vv in d['r_ladder_means'].items())} }}")
        lines.append("")

    lines.append(f"## Primary designation (section 21.5): {out['primary_designation']}")
    lines.append("")

    lines.append("## Aggregate estimator values by scale x condition (mean [p5,p95], n reps)")
    lines.append("")
    for scale in out["aggregate"]:
        lines.append(f"### {scale}")
        lines.append("")
        lines.append("| condition | E1 full-n | E1 matched-n | E2 ratio | E3 k=1 margin | E4 PR |")
        lines.append("|---|---|---|---|---|---|")
        for condition, entry in out["aggregate"][scale].items():
            e1f, e1m, e2, e3, e4 = (entry["e1_full_n"], entry["e1_matched_n"], entry["e2_ratio"],
                                     entry["e3_k1_margin"], entry["e4_pr"])
            lines.append(
                f"| {condition} | {_fmt(e1f['mean'])} [{_fmt(e1f['p5'])},{_fmt(e1f['p95'])}] "
                f"| {_fmt(e1m['mean'])} [{_fmt(e1m['p5'])},{_fmt(e1m['p95'])}] "
                f"| {_fmt(e2['mean'])} [{_fmt(e2['p5'])},{_fmt(e2['p95'])}] "
                f"| {_fmt(e3['mean'])} [{_fmt(e3['p5'])},{_fmt(e3['p95'])}] "
                f"| {_fmt(e4['mean'])} [{_fmt(e4['p5'])},{_fmt(e4['p95'])}] |")
        lines.append("")

    lines.append("## Two-anchor prediction bands (compact + diffuse, per scale per estimator)")
    lines.append("")
    for scale, b in out["prediction_bands"].items():
        lines.append(f"### {scale}")
        lines.append("")
        for key, anchors in b.items():
            lines.append(f"- **{key}**: compact mean={_fmt(anchors['compact']['mean'])} "
                         f"hw={_fmt(anchors['compact']['half_width'])}; "
                         f"diffuse mean={_fmt(anchors['diffuse']['mean'])} hw={_fmt(anchors['diffuse']['half_width'])}")
        lines.append("")
    lines.append("Crystallization index c = (observed - diffuse_mean) / (compact_mean - diffuse_mean), "
                 "NOT clipped to [0,1] (v3 section 22.6.1 -- out-of-range values are informative), and "
                 "the pre-registered trend test (monotonicity + endpoint contrast Delta_c vs propagated "
                 "sigma_c, section 22.6.3) are both implemented (`crystallization_index`, `trend_test`) "
                 "but NOT evaluated here -- this module never reads a real observed value. Per-scale "
                 "sigma_c (the trend test's propagated-error input) is already computed above under "
                 "the (b-new) construction-validity detail.")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
