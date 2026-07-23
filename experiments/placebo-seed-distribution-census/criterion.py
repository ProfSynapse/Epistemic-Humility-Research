"""Survive/Retire/Indeterminate criterion arithmetic for
placebo-seed-distribution-census (gates.yaml `sc_criterion`, FIXED before the
run, no-goalpost rule -- AMENDMENT.md "Falsifier").

Pure functions over already-computed per-seed deltas; no model/GPU code here
so every branch is exercised on CPU with synthetic fixtures
(test_census_smoke.py).
"""

from __future__ import annotations

from typing import Any

from common import bootstrap_fraction_ci, median_iqr_span

MAGNITUDE_FLOOR_PTS = 3.0
F_S_SURVIVE_FLOOR = 0.80
F_S_SURVIVE_BOOTSTRAP_LCB_FLOOR = 0.50
F_S_RETIRE_CEIL = 0.60


def sign_of(delta_pts: float) -> int:
    if delta_pts > 0:
        return 1
    if delta_pts < 0:
        return -1
    return 0


def committed_sign_int(committed_sign: str) -> int:
    return {"positive": 1, "negative": -1, "none": 0}[committed_sign]


def evaluate_family_with_committed_sign(
    family: str, committed_sign: str, deltas_pts: list[float],
) -> dict[str, Any]:
    """SURVIVES iff f_s >= 0.80 AND bootstrap_95_lower_bound(f_s) > 0.50 AND
    |m| >= 3.0 with m in the committed direction.
    RETIRED iff f_s <= 0.60 OR the IQR spans zero.
    INDETERMINATE otherwise. (gates.yaml sc_criterion.survives/retired_falsified/indeterminate)"""
    target_sign = committed_sign_int(committed_sign)
    if target_sign == 0:
        raise ValueError(f"family {family!r} has no committed sign; use evaluate_family_null_control")

    signs = [sign_of(d) for d in deltas_pts]
    frac = bootstrap_fraction_ci(signs, target_sign)
    f_s = frac["fraction"]
    f_s_lcb = frac["bootstrap_ci_95"][0]
    spread = median_iqr_span(deltas_pts)
    m = spread["median"]
    m_in_direction = (m is not None) and (sign_of(m) == target_sign or m == 0)
    m_abs_clears_floor = (m is not None) and abs(m) >= MAGNITUDE_FLOOR_PTS

    survives = (
        f_s >= F_S_SURVIVE_FLOOR
        and f_s_lcb > F_S_SURVIVE_BOOTSTRAP_LCB_FLOOR
        and m_abs_clears_floor
        and m_in_direction
    )
    retired = (f_s <= F_S_RETIRE_CEIL) or bool(spread["iqr_spans_zero"])

    if survives:
        verdict = "SURVIVES"
    elif retired:
        verdict = "RETIRED"
    else:
        verdict = "INDETERMINATE"

    return {
        "family": family, "committed_sign": committed_sign, "verdict": verdict,
        "f_s": f_s, "f_s_bootstrap_ci_95": frac["bootstrap_ci_95"],
        "median_signed_delta_pts": m, "magnitude_floor_pts": MAGNITUDE_FLOOR_PTS,
        "iqr": [spread["q25"], spread["q75"]], "iqr_spans_zero": spread["iqr_spans_zero"],
        "full_span": [spread["min"], spread["max"]],
        "n_seeds": len(deltas_pts),
    }


def evaluate_family_null_control(family: str, deltas_pts: list[float]) -> dict[str, Any]:
    """llama (gates.yaml sc_criterion.llama_null_control): expectation is a
    distribution centered near zero (|median| < 3.0) with no dominant sign.
    A distribution concentrated on one sign with |median| >= 3.0 is a NEWLY
    DISCOVERED placebo sign for that family, reported straight, not a
    falsification of anything (there is nothing to falsify -- no committed
    sign)."""
    signs = [sign_of(d) for d in deltas_pts]
    frac_pos = bootstrap_fraction_ci(signs, 1)
    frac_neg = bootstrap_fraction_ci(signs, -1)
    spread = median_iqr_span(deltas_pts)
    m = spread["median"]

    dominant_sign = None
    dominant_frac = None
    if frac_pos["fraction"] >= F_S_SURVIVE_FLOOR:
        dominant_sign, dominant_frac = "positive", frac_pos
    elif frac_neg["fraction"] >= F_S_SURVIVE_FLOOR:
        dominant_sign, dominant_frac = "negative", frac_neg

    m_abs_clears_floor = (m is not None) and abs(m) >= MAGNITUDE_FLOOR_PTS
    newly_discovered_sign = bool(dominant_sign) and m_abs_clears_floor
    near_zero_null_holds = (m is not None) and abs(m) < MAGNITUDE_FLOOR_PTS and not dominant_sign

    if newly_discovered_sign:
        verdict = f"NEWLY_DISCOVERED_{dominant_sign.upper()}_SIGN"
    elif near_zero_null_holds:
        verdict = "NEAR_ZERO_NULL_HOLDS"
    else:
        verdict = "INDETERMINATE_NULL_CONTROL"

    return {
        "family": family, "committed_sign": "none", "verdict": verdict,
        "fraction_positive": frac_pos["fraction"], "fraction_positive_bootstrap_ci_95": frac_pos["bootstrap_ci_95"],
        "fraction_negative": frac_neg["fraction"], "fraction_negative_bootstrap_ci_95": frac_neg["bootstrap_ci_95"],
        "median_signed_delta_pts": m, "magnitude_floor_pts": MAGNITUDE_FLOOR_PTS,
        "iqr": [spread["q25"], spread["q75"]], "iqr_spans_zero": spread["iqr_spans_zero"],
        "full_span": [spread["min"], spread["max"]],
        "n_seeds": len(deltas_pts),
    }
