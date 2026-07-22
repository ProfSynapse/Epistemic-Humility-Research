"""P1/P2/P3/S1 verdict arithmetic for gate-contribution-factorial
(gates.yaml `p1_gate_benefit_cost`, `p2_gate_selectivity_gap`,
`p3_cost_protection`, `s1_direction_specificity`, `falsifiers`). NEW module
(no single wholesale precedent -- P2's sign-robust `Sel_abs`/`Gap_Sel` form
and the both-conditions design are new to this experiment; RR2/RR3/qwen-
heldout's `gate_lib.py`/`gates_lib.py` verdict shape is the nearest
precedent and is followed for style, not logic).

Every function here is PURE arithmetic over already-computed rate/CI dicts
(from `common.rate_wilson`/`common.bootstrap_ci`/`common.bootstrap_median_ci`)
-- no I/O, no file paths, so every branch is exercised on hand-computable
fixtures in `test_factorial_smoke.py` without touching disk.

Row-level rate convention used throughout: a `rate_wilson`-style dict is
`{"n": int, "successes": int, "rate": float, "wilson_ci_95": [lcb, ucb]}`
(see `common.rate_wilson`/`common.wilson`); `refused_final` is the row-level
boolean (registered final-rate rule, `detector_v2_refused OR adjudicated_
abstention`) that feeds `successes` for an abstention rate. A gap dict is a
`common.bootstrap_ci`-style dict, `{"point": float, "bootstrap_ci_95":
[lo, hi], "excludes_zero": bool, ...}`, or a `common.bootstrap_median_ci`-
style dict, `{"median": float, "bootstrap_ci_95": [lo, hi], ...}` (no
precomputed `excludes_zero` -- callers here derive it from `bootstrap_ci_95`).
"""

from __future__ import annotations

from typing import Any

import config


# ---------------------------------------------------------------------------
# P1 -- gate benefit/cost (true_gate__c_hat only)
# ---------------------------------------------------------------------------

def p1_evaluate(confab_abstention: dict[str, Any], confab_well_formed: dict[str, Any],
                known_false_refusal: dict[str, Any]) -> dict[str, Any]:
    """`confab_abstention`/`known_false_refusal` are `rate_wilson`-style dicts
    over true_gate__c_hat's confab / FULL known population respectively.
    `confab_well_formed` is a `rate_wilson`-style dict over the SAME confab
    population using the `well_formed` (JSON-parse) field as `successes`."""
    benefit_abstention = confab_abstention["rate"] >= config.P1_CONFAB_ABSTENTION_FLOOR
    benefit_lcb = confab_abstention["wilson_ci_95"][0] > config.P1_CONFAB_WILSON_LCB_FLOOR
    benefit_well_formed = confab_well_formed["rate"] >= config.P1_WELL_FORMED_FLOOR
    benefit_pass = bool(benefit_abstention and benefit_lcb and benefit_well_formed)

    cost_rate = known_false_refusal["rate"] <= config.P1_KNOWN_FALSE_REFUSAL_CEIL
    cost_ucb = known_false_refusal["wilson_ci_95"][1] < config.P1_KNOWN_WILSON_UCB_CEIL
    cost_pass = bool(cost_rate and cost_ucb)

    return {
        "benefit": {
            "confab_abstention": confab_abstention, "confab_well_formed": confab_well_formed,
            "abstention_floor_pass": benefit_abstention, "wilson_lcb_pass": benefit_lcb,
            "well_formed_pass": benefit_well_formed, "passed": benefit_pass,
        },
        "cost": {
            "known_false_refusal": known_false_refusal,
            "rate_ceil_pass": cost_rate, "wilson_ucb_pass": cost_ucb, "passed": cost_pass,
        },
        "passed": bool(benefit_pass and cost_pass),
    }


# ---------------------------------------------------------------------------
# P2 -- sign-robust selectivity gap
# ---------------------------------------------------------------------------

def confab_lift(arm_rate: float, baseline_rate: float) -> float:
    return arm_rate - baseline_rate


def known_lift(arm_rate: float, baseline_rate: float) -> float:
    return arm_rate - baseline_rate


def sel_abs(confab_arm_rate: float, confab_baseline_rate: float,
            known_arm_rate: float, known_baseline_rate: float) -> float:
    """Sel_abs(arm) = |confab_lift(arm)| - |known_lift(arm)| (AMENDMENT.md
    "Selectivity metric")."""
    return abs(confab_lift(confab_arm_rate, confab_baseline_rate)) - abs(known_lift(known_arm_rate, known_baseline_rate))


def gap_sel(sel_true_gate: float, sel_permuted_gate: float) -> float:
    """Gap_Sel(d) = Sel_abs(true_gate, d) - Sel_abs(permuted_gate, d)."""
    return sel_true_gate - sel_permuted_gate


def p2_c_hat_evaluate(gap_ci: dict[str, Any]) -> dict[str, Any]:
    """`gap_ci` is a `common.bootstrap_ci`-style dict (`point`,
    `bootstrap_ci_95`, `excludes_zero` already computed). HARD gate:
    Gap_Sel(c_hat) >= floor AND CI excludes 0."""
    gap_point = gap_ci["point"]
    lo, hi = gap_ci["bootstrap_ci_95"]
    floor_pass = gap_point >= config.P2_GAP_SEL_C_HAT_FLOOR
    ci_excludes_zero = bool(gap_ci["excludes_zero"])
    passed = bool(floor_pass and ci_excludes_zero)
    return {
        "gap_sel_c_hat": gap_point, "bootstrap_ci_95": [lo, hi],
        "floor": config.P2_GAP_SEL_C_HAT_FLOOR, "floor_pass": floor_pass,
        "ci_excludes_zero": ci_excludes_zero, "passed": passed,
        "is_primary_falsifier_trigger": not passed,
    }


def p2_random_evaluate(median_gap_ci: dict[str, Any]) -> dict[str, Any]:
    """Directional-only leg, NO magnitude floor (Decision record item 4).
    `median_gap_ci` is a `common.bootstrap_median_ci`-style dict (`median`,
    `bootstrap_ci_95`) over the K=5 per-seed Gap_Sel(random_s) values. The
    falsifier trigger is specifically "Gap_Sel(random) < 0 with CI excluding
    0" -- a confidently negative gap, not merely a negative point estimate."""
    median_gap_point = median_gap_ci["median"]
    lo, hi = median_gap_ci["bootstrap_ci_95"]
    directional_pass = median_gap_point >= 0.0
    ci_excludes_zero = not (lo <= 0.0 <= hi)
    confidently_negative = bool((median_gap_point < 0.0) and ci_excludes_zero)
    return {
        "gap_sel_random_median": median_gap_point, "bootstrap_ci_95": [lo, hi],
        "directional_pass": directional_pass, "ci_excludes_zero": ci_excludes_zero,
        "confidently_negative": confidently_negative,
        "passed": not confidently_negative,
        "is_primary_falsifier_trigger": confidently_negative,
    }


def p2_evaluate(c_hat_leg: dict[str, Any], random_leg: dict[str, Any]) -> dict[str, Any]:
    return {
        "c_hat": c_hat_leg, "random": random_leg,
        "passed": bool(c_hat_leg["passed"] and random_leg["passed"]),
        "is_primary_falsifier": bool(c_hat_leg["is_primary_falsifier_trigger"] or random_leg["is_primary_falsifier_trigger"]),
    }


# ---------------------------------------------------------------------------
# P3 -- cost protection
# ---------------------------------------------------------------------------

def cost_protection(known_false_refusal_permuted: float, known_false_refusal_true_gate: float) -> float:
    """cost_protection = known_false_refusal(permuted_gate) - known_false_refusal(true_gate)."""
    return known_false_refusal_permuted - known_false_refusal_true_gate


def p3_c_hat_evaluate(cost_protection_ci: dict[str, Any]) -> dict[str, Any]:
    """`cost_protection_ci` is a `common.bootstrap_ci`-style dict. HARD gate:
    cost_protection_c_hat >= floor AND bootstrap CI excludes 0."""
    cost_protection_point = cost_protection_ci["point"]
    lo, hi = cost_protection_ci["bootstrap_ci_95"]
    floor_pass = cost_protection_point >= config.P3_COST_PROTECTION_C_HAT_FLOOR
    ci_excludes_zero = bool(cost_protection_ci["excludes_zero"])
    passed = bool(floor_pass and ci_excludes_zero)
    return {
        "cost_protection_c_hat": cost_protection_point, "bootstrap_ci_95": [lo, hi],
        "floor": config.P3_COST_PROTECTION_C_HAT_FLOOR, "floor_pass": floor_pass,
        "ci_excludes_zero": ci_excludes_zero, "passed": passed,
        "is_primary_falsifier_trigger": not passed,
    }


def p3_random_descriptive(median_cost_protection_ci: dict[str, Any]) -> dict[str, Any]:
    """DESCRIPTIVE only (not a hard gate; AMENDMENT doc-vs-intent tension 2):
    `median_cost_protection_ci` is a `common.bootstrap_median_ci`-style dict
    over the K=5 per-seed [known_false_refusal(permuted_random_s) -
    known_false_refusal(true_gate_random_s)] values. Reported straight, no
    pass/fail verdict."""
    lo, hi = median_cost_protection_ci["bootstrap_ci_95"]
    return {
        "cost_protection_random_median": median_cost_protection_ci["median"],
        "bootstrap_ci_95": [lo, hi], "gates": False,
    }


def p3_evaluate(c_hat_leg: dict[str, Any], random_leg_descriptive: dict[str, Any]) -> dict[str, Any]:
    return {
        "c_hat": c_hat_leg, "random": random_leg_descriptive,
        "passed": bool(c_hat_leg["passed"]),
        "is_primary_falsifier": bool(c_hat_leg["is_primary_falsifier_trigger"]),
    }


# ---------------------------------------------------------------------------
# S1 -- direction specificity (secondary; cannot move the gate axis)
# ---------------------------------------------------------------------------

def s1_evaluate(family: str, gated_confab_lift_pts: float) -> dict[str, Any]:
    """`gated_confab_lift_pts` = (confab_abstention(true_gate__c_hat) -
    confab_abstention(baseline)) expressed in POINTS (i.e. rate difference,
    same units as `census_wide_null.median_delta_pts`/`max_abs_delta_frac`
    -- both are already point-scale fractions of the [0,1] rate axis, not
    percent * 100; see config.CENSUS_NULL). PASS if EITHER sign_opposition
    OR effect_ratio >= floor; FAIL only if both fail. Cannot rescue or
    falsify P1/P2/P3 (gates.yaml `cannot_move_gate_axis: true`)."""
    null = config.CENSUS_NULL[family]
    denominator = null["max_abs_delta_frac"]
    median_null = null["median_delta_pts"]

    gated_sign = 0
    if gated_confab_lift_pts > 0:
        gated_sign = 1
    elif gated_confab_lift_pts < 0:
        gated_sign = -1
    null_sign = 1 if median_null > 0 else (-1 if median_null < 0 else 0)

    sign_opposition = bool(gated_sign != 0 and null_sign != 0 and gated_sign != null_sign)
    effect_ratio = abs(gated_confab_lift_pts) / denominator if denominator else float("inf")
    effect_ratio_pass = effect_ratio >= config.S1_EFFECT_RATIO_FLOOR

    passed = bool(sign_opposition or effect_ratio_pass)
    return {
        "family": family, "gated_confab_lift_pts": gated_confab_lift_pts,
        "census_median_delta_pts": median_null, "census_max_abs_delta_frac": denominator,
        "sign_opposition": sign_opposition, "effect_ratio": effect_ratio,
        "effect_ratio_floor": config.S1_EFFECT_RATIO_FLOOR, "effect_ratio_pass": effect_ratio_pass,
        "passed": passed, "cannot_move_gate_axis": True,
    }


# ---------------------------------------------------------------------------
# Falsifier rollup
# ---------------------------------------------------------------------------

def falsifier_verdict(p1: dict[str, Any], p2: dict[str, Any], p3: dict[str, Any]) -> dict[str, Any]:
    gate_contributes_nothing = bool(p2["is_primary_falsifier"] or p3["is_primary_falsifier"])
    gate_benefit_cost_fails = not p1["passed"]
    return {
        "gate_contributes_nothing": gate_contributes_nothing,
        "gate_benefit_cost_fails": gate_benefit_cost_fails,
        "gate_axis_falsified": bool(gate_contributes_nothing or gate_benefit_cost_fails),
        "p1_passed": p1["passed"], "p2_passed": p2["passed"], "p3_passed": p3["passed"],
    }
