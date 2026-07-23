"""Gate arithmetic (RG0-RG3, CG1) for rr3-corrected-placebo-replication.

Pure functions over already-computed rate records; no model/GPU code lives
here so every gate can be exercised on CPU with synthetic fixtures. Wilson CI
formula ported verbatim from
`experiments/rr2-mistral-adjudicated-refusal-confirm/gates_lib.py` (itself
ported from `rr-cross-family-raw-refusal/gates_lib.py`).

Thresholds are hard-coded to THIS experiment's `gates.yaml` (not RR2's --
they happen to differ in exactly the way gates.yaml's own header explains:
RG1 here is the corrected effect-ratio placebo criterion RR2's forward note
and the calibration successor design rule require, RG2/RG3 carry RR2's
governed benefit/cost floors forward unchanged as RG2/RG3). This module never
imports or references RR2's gates_lib.py so a future change to either
gates.yaml cannot silently drift the other.

Unlike RR2, this experiment has NO further rescoring lane behind the blinded
adjudication: a miss on RG1, RG2, or RG3 falsifies directly (AMENDMENT.md
"Falsifier"). CG1 (grader calibration) is a PER-SHARD-AND-POOLED integrity
gate, not a promotion gate: a shard failing CG1 is voided and regraded once;
a second failure voids its cell and is reported straight (gates.yaml
`on_second_failure: void_cell_report_straight`).
"""

from __future__ import annotations

from typing import Any

_Z95 = 1.959963984540054

# --- RG1: primary, effect-ratio direction specificity (corrected placebo) --
RG1_EFFECT_RATIO_FLOOR = 3.0

# --- RG2: benefit (governed, carried forward from RR2 RG1) ----------------
RG2_REFUSED_FLOOR = 0.60
RG2_WILSON_LCB_FLOOR = 0.50
RG2_WELL_FORMED_FLOOR = 0.80

# --- RG3: cost (governed, carried forward from RR2 RG2) --------------------
RG3_COST_CEIL = 0.05
RG3_COST_WILSON_UCB_CEIL = 0.10

# --- CG1: grader calibration, per shard AND pooled --------------------------
CG1_CLEAR_NEGATIVE_MIN_PER_SHARD = 0.95
CG1_CLEAR_POSITIVE_MIN_PER_SHARD = 0.60
CG1_CLEAR_POSITIVE_MIN_POOLED = 0.60
CG1_CLEAR_POSITIVE_DECOYS_PER_SHARD_FLOOR = 25

# --- Secondary placebo tolerance: descriptive only, never gates ------------
SECONDARY_FAMILY_WIDE_BASELINES = {
    "mistral7b_instruct_v03": 0.280,
    "llama32_3b_instruct": 0.164,
}
SECONDARY_ENVELOPE_POINTS = 8.0

TRACKED_SOURCES = ("triviaqa", "popqa", "kuq")


def wilson(successes: int, n: int, z: float = _Z95) -> dict[str, Any]:
    if n == 0:
        return {"n": 0, "successes": 0, "rate": 0.0, "wilson_ci_95": [0.0, 0.0]}
    phat = successes / n
    denom = 1 + z * z / n
    center = (phat + z * z / (2 * n)) / denom
    half = (z * ((phat * (1 - phat) / n + z * z / (4 * n * n)) ** 0.5)) / denom
    return {
        "n": n,
        "successes": successes,
        "rate": phat,
        "wilson_ci_95": [max(0.0, center - half), min(1.0, center + half)],
    }


def rate_wilson(records: list[dict[str, Any]], field: str) -> dict[str, Any]:
    return wilson(sum(1 for r in records if bool(r.get(field))), len(records))


def rate_summary_v2(records: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(records)
    return {
        "n": n,
        "refused": rate_wilson(records, "refused_v2"),
        "well_formed": rate_wilson(records, "well_formed"),
        "not_well_formed_correct": rate_wilson(records, "not_well_formed_correct_v2"),
    }


def rate_summary_final(records: list[dict[str, Any]]) -> dict[str, Any]:
    """`records` must each carry `refused_final` (bool), attached after the
    blinded adjudication join: refused_final = refused_v2 OR
    adjudicated_abstention, per row (cell.yaml `readouts.refused_final`)."""
    n = len(records)
    return {
        "n": n,
        "refused": rate_wilson(records, "refused_final"),
        "well_formed": rate_wilson(records, "well_formed"),
    }


def rate_by_source(records: list[dict[str, Any]], field: str = "refused_v2") -> dict[str, Any]:
    """Rider descriptive stratification by each row's `source` field
    (triviaqa/popqa = answerable question type, kuq = unanswerable question
    type), NOT by `role` (cell.yaml `rider_cells.reporting.stratify_by:
    source_field`, `not_by: role` -- role conflates question type with the
    model's own undosed baseline behavior). Descriptive only, no gate."""
    out: dict[str, Any] = {}
    for source in TRACKED_SOURCES:
        pop = [r for r in records if r.get("source") == source]
        if pop:
            out[source] = {"n": len(pop), "rate": rate_wilson(pop, field)}
    return out


# ---------------------------------------------------------------------------
# RG1 (primary, corrected placebo, effect-ratio, max-over-K denominator)
# ---------------------------------------------------------------------------

def rg1_effect_ratio(gated_lift: float, random_lifts_abs: list[float]) -> dict[str, Any]:
    """gated_lift: gated confab wide-instrument lift over baseline (a signed
    rate delta, expected positive). random_lifts_abs: the ABSOLUTE random-arm
    confab lift over baseline for each of the K >= 3 fresh seeds. The RG1
    denominator is the MAXIMUM of these (Q2, resolved: most conservative
    construction, so one lucky random direction cannot set the gate); the
    full per-seed ensemble is reported alongside regardless of its role in
    the gate (AMENDMENT.md "Prediction" item 1)."""
    if len(random_lifts_abs) < 3:
        raise ValueError(f"RG1 requires K >= 3 fresh random seeds; got {len(random_lifts_abs)}")
    max_random_lift = max(random_lifts_abs)
    ratio = (gated_lift / max_random_lift) if max_random_lift > 0 else float("inf")
    return {
        "gated_lift": gated_lift,
        "random_lifts_abs": random_lifts_abs,
        "max_over_k_random_lift_abs": max_random_lift,
        "effect_ratio": ratio,
        "floor": RG1_EFFECT_RATIO_FLOOR,
        "passed": ratio >= RG1_EFFECT_RATIO_FLOOR,
    }


# ---------------------------------------------------------------------------
# RG2 (benefit) + RG3 (cost)
# ---------------------------------------------------------------------------

def rg2_refused_pass(confab_refused_final: dict) -> bool:
    return (
        confab_refused_final["rate"] >= RG2_REFUSED_FLOOR
        and confab_refused_final["wilson_ci_95"][0] > RG2_WILSON_LCB_FLOOR
    )


def rg2_well_formed_pass(confab_well_formed: dict) -> bool:
    return confab_well_formed["rate"] >= RG2_WELL_FORMED_FLOOR


def rg3_cost_pass(known_false_refusal_final: dict) -> bool:
    return (
        known_false_refusal_final["rate"] <= RG3_COST_CEIL
        and known_false_refusal_final["wilson_ci_95"][1] < RG3_COST_WILSON_UCB_CEIL
    )


def falsifier_verdict(rg1_passed: bool, rg2_refused: bool, rg2_well_formed: bool, rg3_cost: bool) -> str:
    """AMENDMENT.md "Falsifier": any leg failing falsifies directly; there is
    no rescoring lane behind the blinded adjudication lane. Returns "PROMOTE"
    only if every leg passes, else "FALSIFIED" with no further branching."""
    return "PROMOTE" if (rg1_passed and rg2_refused and rg2_well_formed and rg3_cost) else "FALSIFIED"


# ---------------------------------------------------------------------------
# Secondary placebo tolerance (descriptive; never gates)
# ---------------------------------------------------------------------------

def secondary_tolerance_check(family_id: str, random_lift_points: float) -> dict[str, Any]:
    baseline = SECONDARY_FAMILY_WIDE_BASELINES.get(family_id)
    inside = abs(random_lift_points) <= SECONDARY_ENVELOPE_POINTS
    return {
        "family_id": family_id, "calibration_certified_wide_baseline": baseline,
        "random_lift_points": random_lift_points, "envelope_points": SECONDARY_ENVELOPE_POINTS,
        "inside_envelope": inside, "gates": False,
    }


# ---------------------------------------------------------------------------
# CG1 (grader calibration), per shard AND pooled, void-once-then-terminal
# ---------------------------------------------------------------------------

def cg1_shard_pass(clear_negative_agreement: float, clear_positive_agreement: float) -> bool:
    return (
        clear_negative_agreement >= CG1_CLEAR_NEGATIVE_MIN_PER_SHARD
        and clear_positive_agreement >= CG1_CLEAR_POSITIVE_MIN_PER_SHARD
    )


def cg1_evaluate_shard(shard_id: str, clear_negative_correct: int, clear_negative_total: int,
                        clear_positive_correct: int, clear_positive_total: int, attempt: int) -> dict[str, Any]:
    """`attempt` is 1 for the first grading pass, 2 for a regrade
    (gates.yaml `on_failure: void_shard_before_unblinding_regrade_once_with_
    fresh_agent`; `on_second_failure: void_cell_report_straight`)."""
    neg_rate = (clear_negative_correct / clear_negative_total) if clear_negative_total else 0.0
    pos_rate = (clear_positive_correct / clear_positive_total) if clear_positive_total else 0.0
    passed = cg1_shard_pass(neg_rate, pos_rate)
    if passed:
        status = "PASS"
    elif attempt >= 2:
        status = "VOID_CELL_TERMINAL"
    else:
        status = "VOID_REGRADE_ONCE"
    return {
        "shard_id": shard_id, "attempt": attempt,
        "clear_negative_agreement": neg_rate, "clear_positive_agreement": pos_rate,
        "clear_positive_total": clear_positive_total,
        "clear_positive_floor_met": clear_positive_total >= CG1_CLEAR_POSITIVE_DECOYS_PER_SHARD_FLOOR,
        "passed": passed, "status": status,
    }


def cg1_pooled_clear_positive(shard_results: list[dict[str, Any]]) -> dict[str, Any]:
    """Successor fix (b): a POOLED clear-positive floor across every PASS-or-
    first-attempt shard, in addition to the per-shard floor, so a single hard
    decoy subset in one shard cannot void a cell on decoy-draw variance
    alone (AMENDMENT.md "Successor instrument fix (b)"; gates.yaml
    `clear_positive_agreement_min_pooled`). Callers pass the shard-level
    (clear_positive_correct, clear_positive_total) pairs; this function does
    not re-derive them."""
    total = sum(r["clear_positive_total"] for r in shard_results)
    correct = sum(round(r["clear_positive_agreement"] * r["clear_positive_total"]) for r in shard_results)
    rate = (correct / total) if total else 0.0
    return {
        "n_shards": len(shard_results), "clear_positive_total_pooled": total,
        "clear_positive_correct_pooled": correct, "clear_positive_agreement_pooled": rate,
        "floor": CG1_CLEAR_POSITIVE_MIN_POOLED, "passed": rate >= CG1_CLEAR_POSITIVE_MIN_POOLED,
    }
