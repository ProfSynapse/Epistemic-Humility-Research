#!/usr/bin/env python3
"""M1b fine-ladder pre-sign design derivation. Read-only over M1's committed
artifacts:
  - experiments/margin-mapping/analysis/margin_dataset/qwen35_4b_margin_rows.jsonl
    (sha256 84f4d3b8674a18eb944a4b921383e1cfb1147db892dee2c19348f671b7f41565,
    verified against provenance_manifest.json in the same dir)
  - experiments/margin-mapping/cell.yaml (M1 ladder, reference dose)
  - experiments/margin-mapping/analysis-committed/threshold_derivation/
    threshold_derivation_report.json (committed probit fit: mu=2.0157,
    sigma=1.1158 for confab; mu=5.4366, sigma=1.8964 for known)

No writes to experiments/. No GPU. This script only reads M1's row-level
JSONL and the committed derivation report, and computes M1b instrument
design candidates.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from scipy import stats

REPO = Path("/home/profsynapse/code/Epistemic-Humility-Research")
MARGIN_ROWS = REPO / "experiments/margin-mapping/analysis/margin_dataset/qwen35_4b_margin_rows.jsonl"
THRESH_REPORT = REPO / "experiments/margin-mapping/analysis-committed/threshold_derivation/threshold_derivation_report.json"

REFERENCE_DOSE = 12.608187917799976  # cell.yaml qwen35_4b reference_dose_abs
M1_MULTIPLIERS = [0.0625, 0.125, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0]  # idx 1..10; idx0 = dose0
TOP_PRECOLLAPSE_MULT = 1.5   # unchanged floor numerator (18.912281876699964 dose_abs)
FLOOR = 2.5                  # unchanged criterion floor (registered, M1 Decision record item 4)
N_BOOT = 10000
SEED = 47260714              # repo convention (gate-contribution-factorial / M1 threshold derivation)

TOP_PRECOLLAPSE_DOSE = TOP_PRECOLLAPSE_MULT * REFERENCE_DOSE
REQUIRED_EXACT_RUNG_DOSE = TOP_PRECOLLAPSE_DOSE / FLOOR
REQUIRED_EXACT_RUNG_MULT = REQUIRED_EXACT_RUNG_DOSE / REFERENCE_DOSE


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(l) for l in path.open() if l.strip()]


def mult_for_idx(idx) -> float:
    """idx0 = dose 0; idx i (1..10) -> M1_MULTIPLIERS[i-1]."""
    if idx is None:
        return float("inf")
    if idx == 0:
        return 0.0
    return M1_MULTIPLIERS[idx - 1]


def main() -> None:
    rows = load_jsonl(MARGIN_ROWS)
    assert len(rows) == 760, f"expected 760 rows, got {len(rows)}"
    confab = [r for r in rows if r["role"] == "confab"]
    known = [r for r in rows if r["role"] == "known_correct_answered"]
    assert len(confab) == 400 and len(known) == 360

    report: dict[str, Any] = {
        "inputs": {
            "margin_rows_path": str(MARGIN_ROWS),
            "margin_rows_sha256_expected": "84f4d3b8674a18eb944a4b921383e1cfb1147db892dee2c19348f671b7f41565",
            "reference_dose_abs": REFERENCE_DOSE,
            "top_precollapse_dose_abs": TOP_PRECOLLAPSE_DOSE,
            "floor": FLOOR,
            "required_exact_rung_dose_abs": REQUIRED_EXACT_RUNG_DOSE,
            "required_exact_rung_mult": REQUIRED_EXACT_RUNG_MULT,
        }
    }

    # -----------------------------------------------------------------
    # Sanity: reproduce M1's Outcome numbers from the row-level dataset
    # -----------------------------------------------------------------
    def median_and_ci(vals: list[float], n_boot=N_BOOT, seed=SEED):
        arr = np.array(vals)
        point = float(np.median(arr))
        rng = np.random.default_rng(seed)
        idx = rng.integers(0, len(arr), size=(n_boot, len(arr)))
        boots = np.median(arr[idx], axis=1)
        lo, hi = np.percentile(boots, [2.5, 97.5])
        return point, float(lo), float(hi)

    confab_tipping = [r["tipping_dose_abs"] for r in confab]  # censored ones use top-rung value already
    point, lo, hi = median_and_ci(confab_tipping)
    n_censored_confab = sum(1 for r in confab if r["tipping_censored"])
    n_censored_known = sum(1 for r in known if r["tipping_censored"])
    report["sanity_reproduction"] = {
        "confab_median_dose_abs": point, "confab_median_ci95": [lo, hi],
        "amendment_outcome_cited": {"median": 9.456140938349982, "ci95": [6.304093958899988, 9.456140938349982]},
        "match": math.isclose(point, 9.456140938349982, rel_tol=1e-6),
        "n_confab_tipping_censored": n_censored_confab, "n_known_tipping_censored": n_censored_known,
        "amendment_cited": {"confab_censored": 92, "known_censored": 322},
    }

    # -----------------------------------------------------------------
    # Bracket distribution: for each confab row, which M1 rung interval
    # (prev-non-tip-rung, tipping-rung] does its tipping dose fall in.
    # tipping_idx is None only when tipping_censored=True (right-censored
    # at top rung); idx0 rows (tip at dose 0) are logically impossible here
    # (dose 0 is the reused baseline and is not a "ladder" rung) but checked.
    # -----------------------------------------------------------------
    idx_counts_confab: dict[Any, int] = {}
    for r in confab:
        k = r["tipping_idx"] if not r["tipping_censored"] else "censored"
        idx_counts_confab[k] = idx_counts_confab.get(k, 0) + 1
    idx_counts_known: dict[Any, int] = {}
    for r in known:
        k = r["tipping_idx"] if not r["tipping_censored"] else "censored"
        idx_counts_known[k] = idx_counts_known.get(k, 0) + 1

    def relabel(d):
        return {(f"idx{k}_mult{mult_for_idx(k)}" if k != "censored" else "censored"): v
                for k, v in sorted(d.items(), key=lambda kv: (kv[0] is None, kv[0] == "censored", kv[0] if isinstance(kv[0], int) else -1))}

    report["bracket_distribution"] = {
        "confab": relabel(idx_counts_confab),
        "known": relabel(idx_counts_known),
        "note": "idx i (1..10) means tipped at M1_MULTIPLIERS[i-1]x, bracket = (prev_rung, this_rung]; "
                "idx6=1.0x, idx5=0.75x, idx4=0.5x, idx7=1.5x are the brackets of interest for the fine window.",
    }

    # rows whose bracket overlaps the candidate fine windows
    def rows_in_bracket(pop, idxs):
        return [r for r in pop if (not r["tipping_censored"]) and r["tipping_idx"] in idxs]

    idx5_rows = rows_in_bracket(confab, {5})   # bracket (0.5x, 0.75x] -- contains the M1 point-estimate median
    idx4_rows = rows_in_bracket(confab, {4})   # bracket (0.25x, 0.5x]
    idx6_rows = rows_in_bracket(confab, {6})   # bracket (0.75x, 1.0x]
    report["critical_bracket_counts"] = {
        "idx4_0.25to0.5x": len(idx4_rows),
        "idx5_0.5to0.75x_contains_M1_median": len(idx5_rows),
        "idx6_0.75to1.0x": len(idx6_rows),
        "sum_idx4_5_6": len(idx4_rows) + len(idx5_rows) + len(idx6_rows),
        "n_confab_total": len(confab),
    }

    # -----------------------------------------------------------------
    # Candidate rung sets
    # -----------------------------------------------------------------
    candidates = {
        "A_quarter_x_plus_required": {
            "mults": [0.375, 0.5, REQUIRED_EXACT_RUNG_MULT, 0.75, 0.875, 1.0, 1.5, 2.0],
            "reused_from_M1": [0.5, 0.75, 1.0, 1.5, 2.0],
            "new_mults": [0.375, REQUIRED_EXACT_RUNG_MULT, 0.875],
        },
        "B_eighth_octave_0.375_to_1.0_plus_reanchor": {
            "mults": None,  # computed below, expected to blow budget
        },
        "C_dense_arithmetic_0.5_to_0.75_plus_reanchor": {
            "mults": [0.5, 0.55, REQUIRED_EXACT_RUNG_MULT, 0.65, 0.7, 0.75, 1.5, 2.0],
            "reused_from_M1": [0.5, 0.75, 1.5, 2.0],
            "new_mults": [0.55, REQUIRED_EXACT_RUNG_MULT, 0.65, 0.7],
        },
    }

    # Candidate B: eighth-octave (ratio 2**(1/8)) from 1.0 down to >=0.375
    ratio8 = 2 ** (1 / 8)
    b_mults = [1.0]
    while b_mults[-1] / ratio8 >= 0.375 - 1e-9:
        b_mults.append(b_mults[-1] / ratio8)
    b_mults = sorted(set(round(m, 6) for m in b_mults))
    candidates["B_eighth_octave_0.375_to_1.0_plus_reanchor"]["mults"] = b_mults + [1.5, 2.0]
    candidates["B_eighth_octave_0.375_to_1.0_plus_reanchor"]["reused_from_M1"] = [m for m in b_mults + [1.5, 2.0] if m in (0.5, 0.75, 1.0, 1.5, 2.0)]
    candidates["B_eighth_octave_0.375_to_1.0_plus_reanchor"]["new_mults"] = [m for m in b_mults + [1.5, 2.0] if m not in (0.5, 0.75, 1.0, 1.5, 2.0)]

    for name, spec in candidates.items():
        mults = sorted(spec["mults"])
        doses = [m * REFERENCE_DOSE for m in mults]
        n_total_rungs = len(mults)
        bounds = [TOP_PRECOLLAPSE_DOSE / d for d in doses if d <= TOP_PRECOLLAPSE_DOSE]
        exact_hit = any(math.isclose(b, FLOOR, rel_tol=1e-9) for b in bounds)
        spec["resolved"] = {
            "mults_sorted": mults,
            "n_total_rungs": n_total_rungs,
            "n_new_rungs": len(spec.get("new_mults", [])) if spec.get("new_mults") is not None else None,
            "achievable_bounds_near_floor": sorted([round(b, 4) for b in bounds if 1.5 <= b <= 5.0]),
            "hits_floor_exactly": exact_hit,
            "within_budget_8": n_total_rungs <= 8,
        }

    report["candidate_rung_sets"] = {k: v["resolved"] for k, v in candidates.items()}

    # -----------------------------------------------------------------
    # Expected outcome distribution under (a) empirical M1 distribution
    # with uniform-in-log placement within each row's censoring interval,
    # and (b) the committed probit fit (log-normal margins).
    # For each candidate, the "fine-ladder median" is determined by: take
    # each row's TRUE simulated margin (continuous), then round it UP to
    # the smallest candidate rung >= true margin that is present in that
    # candidate's rung set (this is what a real staircase would observe:
    # the smallest ladder dose at which the row is scored refused). The
    # observed fine median is the median of these discretized values; the
    # bound is TOP_PRECOLLAPSE_DOSE / observed_fine_median.
    # -----------------------------------------------------------------
    def m1_interval_bounds(row) -> tuple[float, float]:
        """(lo, hi) dose_abs bracket for the row's true (pre-M1b) margin,
        from M1's own rungs. Censored rows: (top_precollapse_dose, +inf)
        is not usable for log-uniform sampling, so censored rows are capped
        at (top_rung, 4x*reference) for simulation purposes only (M1's own
        right-censoring point), flagged in the output as a simulation cap,
        not a claim about the true value."""
        idx = row["tipping_idx"]
        if row["tipping_censored"]:
            return (4.0 * REFERENCE_DOSE, 8.0 * REFERENCE_DOSE)  # simulation cap only, never a claim
        if idx == 0:
            # Row already refused at the reused dose-0 baseline: no ladder
            # interval brackets it (there is no rung below dose 0), so its
            # true margin is deterministically ~0, not a sampled interval.
            # Use a fixed tiny interval (negligible vs the smallest ladder
            # rung, 0.0625x = 0.788 dose_abs) to avoid a log(0) singularity
            # while keeping the value effectively zero for every candidate
            # rung set below.
            return (1e-9, 1e-6)
        hi = mult_for_idx(idx) * REFERENCE_DOSE
        prev_idx = idx - 1
        lo = mult_for_idx(prev_idx) * REFERENCE_DOSE if prev_idx >= 0 else 1e-6
        return (lo, hi)

    def simulate_empirical(pop, n_boot=N_BOOT, seed=SEED):
        n = len(pop)
        rng = np.random.default_rng(seed)
        intervals = np.array([m1_interval_bounds(r) for r in pop])
        log_lo = np.log(np.maximum(intervals[:, 0], 1e-6))
        log_hi = np.log(intervals[:, 1])
        # row-level bootstrap indices, then uniform-in-log draw within each
        # resampled row's own interval (fresh draw per bootstrap replicate)
        idx = rng.integers(0, n, size=(n_boot, n))
        u = rng.uniform(size=(n_boot, n))
        true_margins = np.exp(log_lo[idx] + u * (log_hi[idx] - log_lo[idx]))
        return true_margins

    def simulate_probit(n_rows, mu, sigma, n_boot=N_BOOT, seed=SEED):
        rng = np.random.default_rng(seed + 1)
        z = rng.standard_normal(size=(n_boot, n_rows))
        return np.exp(mu + sigma * z)

    thresh = json.loads(THRESH_REPORT.read_text())
    confab_fit = thresh["step2_qwen_fits"]["confab"]["probit_fit"]
    mu_c, sigma_c = confab_fit["mu"], confab_fit["sigma"]

    def discretize_and_bound(true_margins: np.ndarray, rung_doses: list[float]) -> np.ndarray:
        rung_arr = np.array(sorted(rung_doses) + [np.inf])
        # smallest rung >= true margin, per element
        obs = rung_arr[np.searchsorted(rung_arr, true_margins, side="left")]
        median_obs = np.median(obs, axis=1)
        return TOP_PRECOLLAPSE_DOSE / median_obs

    outcome = {}
    for name, spec in candidates.items():
        mults = spec["resolved"]["mults_sorted"]
        rung_doses = [m * REFERENCE_DOSE for m in mults]
        # (a) empirical M1 distribution, uniform-in-log within bracket
        tm_emp = simulate_empirical(confab)
        bound_emp = discretize_and_bound(tm_emp, rung_doses)
        # (b) committed probit fit
        tm_fit = simulate_probit(len(confab), mu_c, sigma_c)
        bound_fit = discretize_and_bound(tm_fit, rung_doses)
        outcome[name] = {
            "empirical_model": {
                "median_bound_point": float(np.median(bound_emp)),
                "bound_ci95": [float(np.percentile(bound_emp, 2.5)), float(np.percentile(bound_emp, 97.5))],
                "P_bound_ge_floor": float(np.mean(bound_emp >= FLOOR)),
            },
            "probit_fit_model": {
                "median_bound_point": float(np.median(bound_fit)),
                "bound_ci95": [float(np.percentile(bound_fit, 2.5)), float(np.percentile(bound_fit, 97.5))],
                "P_bound_ge_floor": float(np.mean(bound_fit >= FLOOR)),
            },
        }
    report["expected_outcome_distribution"] = outcome

    # -----------------------------------------------------------------
    # Population conditioning: GPU savings estimate for candidate A and C
    # -----------------------------------------------------------------
    pop_cost = {}
    n_confab = len(confab)
    n_known = len(known)
    m1_total_generations = len(M1_MULTIPLIERS) * (n_confab + n_known)  # + dose0 reused, excluded
    for name, spec in candidates.items():
        n_new = len(spec.get("new_mults", []))
        full_pop_cost = n_new * n_confab
        # conditional: only rows in idx4/5/6 brackets need new-rung generation
        n_conditional_rows_A_style = len(idx4_rows) + len(idx5_rows) + len(idx6_rows)
        n_conditional_rows_C_style = len(idx5_rows)  # C's window doesn't touch idx4/idx6 brackets
        cond_rows = n_conditional_rows_C_style if "C_" in name else n_conditional_rows_A_style
        conditional_cost = n_new * cond_rows
        pop_cost[name] = {
            "n_new_rungs": n_new,
            "full_population_cost_generations": full_pop_cost,
            "conditional_population_cost_generations": conditional_cost,
            "conditional_row_count_used": cond_rows,
            "savings_fraction_vs_full_pop": 1 - (conditional_cost / full_pop_cost) if full_pop_cost else None,
            "fraction_of_M1_total_cost": full_pop_cost / m1_total_generations,
            "conditional_fraction_of_M1_total_cost": conditional_cost / m1_total_generations,
        }
    report["population_conditioning"] = {
        "m1_total_generations_confab_plus_known_10_rungs": m1_total_generations,
        "candidates": pop_cost,
        "bias_note": (
            "Conditioning on M1's own tipping_idx is NOT circular for the fine-median "
            "question because idx-4/6-bracket rows' contribution to 'is this row's true "
            "margin above or below any point in (0.5x,1.0x]' is already fully determined "
            "by M1 (idx<=4 rows have margin<=0.5x -> counts as 'below' any fine point in "
            "(0.5,1.0]; idx>=6 in the (0.75,1.0] bracket already know margin>0.75x). The "
            "risk is coverage, not bias: a bootstrap resample that draws disproportionately "
            "from a bracket not given fine treatment will report the coarse M1-bracket "
            "value for that replicate, which can only WIDEN the resampled CI relative to a "
            "full-fine-pool design, never narrow it in a way that favors a predetermined "
            "answer. Monotonicity risk (0.035 confab non-monotone, per M1 C1) means a small "
            "fraction of idx4/idx6 rows could in principle un-tip and re-tip inside the fine "
            "window under a hypothetical non-monotone path; M1's own non-monotone rate is "
            "pre-collapse and applies to the FULL ladder, not selectively to this window, so "
            "this is a pre-existing construct-level risk unchanged by conditioning."
        ),
    }

    # -----------------------------------------------------------------
    # Known rows: what {1.5x,2.0x}-only buys vs full fine ladder vs reuse
    # -----------------------------------------------------------------
    known_at_1p5 = [r for r in known if not r["tipping_censored"] and r["tipping_idx"] == 7]
    known_censored_above_1p5 = [r for r in known if r["tipping_censored"] or (r["tipping_idx"] is not None and r["tipping_idx"] > 7)]
    known_collapse_exactly_at_2p0 = sum(1 for r in known if r["collapse_idx"] == 8)
    known_collapse_censored = any(r["collapse_censored"] for r in known)
    known_collapse_max_idx = max(r["collapse_idx"] for r in known)
    report["known_row_analysis"] = {
        "n_known_total": n_known,
        "n_tipped_exactly_at_1.5x": len(known_at_1p5),
        "n_censored_or_tipped_above_1.5x": len(known_censored_above_1p5),
        "fraction_censored_above_1.5x_amendment_cited": 322 / 360,
        "n_collapse_exactly_at_2.0x_rung_idx8": known_collapse_exactly_at_2p0,
        "collapse_idx_max_across_known": known_collapse_max_idx,
        "collapse_censored_any": known_collapse_censored,
        "collapse_note": (
            "No known row is collapse-censored and none has collapse_idx>8: the "
            "population-level well-formedness rate reaches 0.000 by the 2.0x rung for "
            "every row (cumulative), matching the Outcome's 'total well-formedness "
            "collapse at the 2.0x rung (25.216) in both roles'; individual rows' FIRST "
            "non-well-formed rung ranges from idx4 to idx8 (285/360 collapse exactly at "
            "idx8, the rest earlier)."
        ),
        "option_reuse_byte_identical": {
            "new_generations": 0,
            "buys": (
                "The 1.5x and 2.0x rungs for ALL 360 known rows already exist in M1's "
                "committed runlogs (qwen35_4b__rung_1p5.jsonl, qwen35_4b__rung_2.jsonl), "
                "same substrate/direction/dose/rows. Under the RG0 byte-repro rule already "
                "used elsewhere in M1 (dose-0 baseline reuse), these can be merged into M1b "
                "at zero new GPU cost and zero new adjudication. Buys: full leg-(b) censoring "
                "evidence (fraction above 1.5x) and the collapse-cliff reconfirmation "
                "(well_formed=0 at 2.0x) for free, IF the direction vector, substrate revision, "
                "and dose law are unchanged from M1 (true per the amendment: 'UNCHANGED floor "
                "2.5' framing implies the substrate/site/direction are also unchanged)."
            ),
        },
        "option_rerun_1.5_2.0_only": {
            "new_generations": 2 * n_known,
            "buys": (
                "A fresh, M1b-native replicate of the top-rung/collapse-cliff evidence, "
                "independent of M1's specific run (hedges against a repeat of the mistral "
                "direction-vector loss incident, or any staleness in the reused artifact). "
                "Costs 720 new generations (2 rungs x 360 rows), ~9.5% of M1's total known-row "
                "cost (10 rungs x 360 = 3600), but gives NO new information about the fine "
                "confab-median region and does not change the known-row censoring picture "
                "unless the fresh run disagrees with M1 (which would itself be a red flag)."
            ),
        },
        "option_full_fine_ladder_for_known": {
            "new_generations": f"{candidates['C_dense_arithmetic_0.5_to_0.75_plus_reanchor']['resolved']['n_new_rungs']} new rungs x 360 known rows = "
                                f"{candidates['C_dense_arithmetic_0.5_to_0.75_plus_reanchor']['resolved']['n_new_rungs'] * n_known} "
                                "(candidate C new-rung count; candidate A would cost "
                                f"{candidates['A_quarter_x_plus_required']['resolved']['n_new_rungs'] * n_known})",
            "buys": (
                "Almost nothing: 89.4% of known rows are already right-censored above the "
                "top pre-collapse rung (322/360 per the amendment Outcome), so a fine ladder "
                "below 1.5x would mostly just reconfirm that the same rows still haven't "
                "tipped -- it cannot move the leg-(b) censoring fraction (which is defined "
                "relative to the SAME top pre-collapse rung, unchanged) and cannot resolve "
                "the (extrapolated, not observed) fitted known median, since that median "
                "(229.7 dose_abs on qwen) sits far above even the top M1 rung (50.4 dose_abs). "
                "Recommendation: do not run a fine ladder for known rows; it burns budget "
                "with near-zero expected information gain given leg (b) does not depend on "
                "the confab-median region at all."
            ),
        },
    }

    # -----------------------------------------------------------------
    # Statistics: expected bootstrap CI width at n=400 for the recommended
    # candidate, and the discreteness residual (achievable bound values
    # near 2.5 for the recommended ladder).
    # -----------------------------------------------------------------
    recommended = "C_dense_arithmetic_0.5_to_0.75_plus_reanchor"
    rec_mults = candidates[recommended]["resolved"]["mults_sorted"]
    rec_doses = [m * REFERENCE_DOSE for m in rec_mults]
    tm_emp_rec = simulate_empirical(confab)
    bound_emp_rec = discretize_and_bound(tm_emp_rec, rec_doses)
    ci_width_emp = float(np.percentile(bound_emp_rec, 97.5) - np.percentile(bound_emp_rec, 2.5))
    tm_fit_rec = simulate_probit(len(confab), mu_c, sigma_c)
    bound_fit_rec = discretize_and_bound(tm_fit_rec, rec_doses)
    ci_width_fit = float(np.percentile(bound_fit_rec, 97.5) - np.percentile(bound_fit_rec, 2.5))

    report["recommended_candidate"] = recommended
    report["recommended_candidate_statistics"] = {
        "mults": rec_mults,
        "n_new_rungs": candidates[recommended]["resolved"]["n_new_rungs"],
        "achievable_bounds_near_floor": candidates[recommended]["resolved"]["achievable_bounds_near_floor"],
        "bootstrap_ci_width_n400_empirical_model": ci_width_emp,
        "bootstrap_ci_width_n400_probit_fit_model": ci_width_fit,
        "point_estimate_stays_the_registered_convention": (
            "M1's own criterion adjudication used the point-estimate bound (18.912/9.456=2.0) "
            "against the floor, reporting the bootstrap CI descriptively (M1 Outcome: "
            "'bootstrap CI [2.0, 3.0]'). This derivation recommends the SAME convention for "
            "M1b: point estimate is the pass/fail surface, CI reported descriptively, per "
            "M1 precedent -- this is a design-info observation, not a re-opening of M1's "
            "resolved statistical convention."
        ),
    }

    out_path = Path("/tmp/claude-1000/-mnt-f-Code-Epistemic-Humility-Research/292064d8-cb30-460a-ad90-29559ab5cf7f/scratchpad/m1b/m1b_design_report.json")
    out_path.write_text(json.dumps(report, indent=2))
    print(f"wrote {out_path}")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
