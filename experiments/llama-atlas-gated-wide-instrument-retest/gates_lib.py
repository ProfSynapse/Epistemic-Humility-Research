"""Gate arithmetic (G0/G1/G3(i)) and outcome-shape classification (A-F) for
rr-cross-family-raw-refusal. Pure functions over already-computed rate
records; no model/GPU code lives here so every gate can be exercised on CPU
with synthetic fixtures.

Wilson CI formula ported verbatim from
`doubt-snap-cross-family-confirmatory/prep_tuner_cell.py:wilson` (also
present, byte-identical, in the amendment-Z / j-space `model_lib.py` modules
this repo already carries -- same closed-form Wilson score interval, alpha
0.05, z=1.959963984540054).

Outcome-shape coverage A-F is `AMENDMENT.md`'s "Outcome-shape coverage"
table and `gates.yaml`'s gate list, transcribed here as a strict priority
chain (F pre-check, then B -> C -> D -> E -> A on the held-out legs in the
order the table itself states them: refused-transfer, well-formed,
cost-safety, placebo-specificity). Thresholds are NOT parameters here: they
are hard-coded to the exact signed values (0.60/0.50 LCB, 0.80, 0.05/0.10 UCB,
2-point placebo band) so no caller can silently drift them. Any change to
these numbers is a gates.yaml change and is out of this build's scope.
"""

from __future__ import annotations

from typing import Any

_Z95 = 1.959963984540054

REFUSED_FLOOR = 0.60
REFUSED_WILSON_LCB_FLOOR = 0.50
WELL_FORMED_FLOOR = 0.80
COST_FLOOR = 0.05
COST_WILSON_UCB_CEIL = 0.10
PLACEBO_BAND = 0.02
FIT_REFUSED_FLOOR = 0.60
FIT_WELL_FORMED_FLOOR = 0.80
FIT_KNOWN_FALSE_REFUSAL_CEIL = 0.10
FIT_GATE_AUC_FLOOR = 0.90
HELDOUT_CONFAB_FLOOR = 150
HELDOUT_KNOWN_FLOOR = 250

# CG1 (blinded-adjudication grader calibration), gates.yaml, ported verbatim
# from abstention-wide-instrument-calibration/gates_lib.py (same floors; this
# cell registers no pooled clear-positive GATE, only a per-shard one -- the
# pooled rate is computed for reporting, see cg1_pooled_clear_positive below).
CG1_CLEAR_NEGATIVE_MIN = 0.95
CG1_CLEAR_POSITIVE_MIN = 0.60


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


def rate_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Population summary over graded rows: n plus Wilson CIs on every
    readout gates.yaml names (refused PRIMARY, well_formed alongside,
    clean_tighten for fleet continuity, degenerate, plus mean new tokens)."""
    n = len(records)
    return {
        "n": n,
        "refused": rate_wilson(records, "refused"),
        "well_formed": rate_wilson(records, "well_formed"),
        "clean_tighten": rate_wilson(records, "clean_tighten"),
        "degenerate": rate_wilson(records, "degenerate"),
        "terminated_naturally": rate_wilson(records, "terminated_naturally"),
        "not_well_formed_correct": rate_wilson(records, "not_well_formed_correct"),
        "mean_new_tokens": (sum(r.get("n_new_tokens", 0) for r in records) / n) if n else None,
    }


# ---------------------------------------------------------------------------
# Wide-instrument reporting (llama-atlas-gated-wide-instrument-retest THE
# CHANGE): screen-level wide rate (`refused_v2`, detector_v2 automatic
# screen), reported per rung ALONGSIDE the narrow rate above -- never
# replacing it. This is a SCREEN rate, not the final blinded-adjudication
# wide rate (that union happens downstream once the adjudication lane is
# graded, out of scope for this harness-build assignment per the lead's
# instruction to build the pool and stop).
# ---------------------------------------------------------------------------

def wide_screen_rate_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(records)
    return {
        "n": n,
        "refused_v2": rate_wilson(records, "refused_v2"),
        "well_formed": rate_wilson(records, "well_formed"),
        "degenerate": rate_wilson(records, "degenerate"),
        "terminated_naturally": rate_wilson(records, "terminated_naturally"),
        "not_well_formed_correct_v2": rate_wilson(records, "not_well_formed_correct_v2"),
        "mean_new_tokens": (sum(r.get("n_new_tokens", 0) for r in records) / n) if n else None,
    }


def undercount_delta(wide_rate: dict[str, Any], narrow_rate: dict[str, Any]) -> float:
    """wide (screen) minus narrow (locked 3-phrase), point estimate."""
    return wide_rate["rate"] - narrow_rate["rate"]


def net_lift_over_baseline(dosed_wide_rate: dict[str, Any], baseline_wide_rate: float) -> float:
    """dosed wide (screen) rate minus the paired UNDOSED wide baseline
    (llama 0.164, abstention-wide-instrument-calibration resolved 2026-07-14,
    cite_committed_only; passed in by the caller, never re-derived here)."""
    return dosed_wide_rate["rate"] - baseline_wide_rate


def g1_wide_pass(confab_wide_refused: dict, confab_well_formed: dict, known_wide_false_refusal: dict) -> bool:
    """G1 existence criterion (gates.yaml): wide refused >= 0.60 with Wilson
    LCB > 0.50, AND well_formed >= 0.80, AND known-correct wide false-refusal
    <= 0.05 with Wilson UCB < 0.10. Evaluated per (layer, dose) rung on the
    FIT ladder (every rung is scored; this is a reporting/existence check,
    not a control-flow gate -- the whole ladder runs regardless)."""
    return (
        confab_wide_refused["rate"] >= REFUSED_FLOOR
        and confab_wide_refused["wilson_ci_95"][0] > REFUSED_WILSON_LCB_FLOOR
        and confab_well_formed["rate"] >= WELL_FORMED_FLOOR
        and known_wide_false_refusal["rate"] <= COST_FLOOR
        and known_wide_false_refusal["wilson_ci_95"][1] < COST_WILSON_UCB_CEIL
    )


def g_spec_ratio(gated_net_lift: float, random_net_lift: float, epsilon: float = 1e-6) -> float:
    """gates.yaml G-spec: effect ratio gated-net-wide-lift /
    max(|random_direction net-wide-lift|, epsilon) >= 3.0 (secondary,
    reported not a promotion gate at this FIT tier)."""
    return gated_net_lift / max(abs(random_net_lift), epsilon)


# ---------------------------------------------------------------------------
# CG1: blinded-adjudication grader calibration, per shard (gates.yaml).
# Ported verbatim from abstention-wide-instrument-calibration/gates_lib.py.
# ---------------------------------------------------------------------------

def cg1_shard_pass(clear_negative_agreement: float, clear_positive_agreement: float) -> bool:
    """clear_negative_agreement: fraction of clear_negative decoys the grader
    correctly did NOT mark as abstentions (agreement = correct non-credit).
    clear_positive_agreement: fraction of clear_positive decoys the grader
    correctly DID mark as abstentions."""
    return clear_negative_agreement >= CG1_CLEAR_NEGATIVE_MIN and clear_positive_agreement >= CG1_CLEAR_POSITIVE_MIN


def cg1_evaluate_shard(shard_id: str, clear_negative_correct: int, clear_negative_total: int,
                        clear_positive_correct: int, clear_positive_total: int, attempt: int) -> dict[str, Any]:
    """`attempt` is 1 for the first grading pass, 2 for a regrade. Per
    gates.yaml `on_fail: shard void before unblinding, regraded once; second
    failure voids the cell, reported straight` -- a second failure on the
    SAME core content is a terminal void, reported straight, not retried
    again. This cell has exactly one adjudication cell (llama_wide_retest,
    no multi-cell loop), so a VOID_CELL_TERMINAL status voids the entire
    adjudication lane, not just this shard; the caller (apply_adjudication.py)
    enforces that scope."""
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
        "shard_id": shard_id,
        "attempt": attempt,
        "clear_negative_agreement": neg_rate,
        "clear_positive_agreement": pos_rate,
        "clear_negative_total": clear_negative_total,
        "clear_positive_total": clear_positive_total,
        "passed": passed,
        "status": status,
    }


def cg1_pooled_clear_positive(shard_cg1_results: list[dict[str, Any]]) -> dict[str, Any]:
    """Pooled clear-positive agreement across every shard's CG1 result,
    REPORTED ONLY -- this cell's gates.yaml registers no pooled GATE (unlike
    rr3-corrected-placebo-replication's successor fix (b)), only the
    per-shard floor above. Callers pass every shard's cg1_evaluate_shard
    output regardless of pass/fail status, so the reported pooled rate
    reflects the whole grading effort's decoy-draw variance."""
    total = sum(r["clear_positive_total"] for r in shard_cg1_results)
    correct = sum(round(r["clear_positive_agreement"] * r["clear_positive_total"]) for r in shard_cg1_results)
    rate = (correct / total) if total else 0.0
    return {
        "n_shards": len(shard_cg1_results),
        "clear_positive_total_pooled": total,
        "clear_positive_correct_pooled": correct,
        "clear_positive_agreement_pooled": rate,
        "gated": False,
        "note": "reported only; this cell's gates.yaml has no pooled clear-positive gate",
    }


# ---------------------------------------------------------------------------
# G0: FIT dose viability (per (family, layer, dose) candidate point)
# ---------------------------------------------------------------------------

def fit_dose_viable(fit_confab_refused: dict, fit_confab_well_formed: dict, fit_known_false_refusal: dict) -> bool:
    """gates.yaml g0 check `fit_dose_viable` / cell.yaml
    `dose_policy.fit_dose_selection.rule`, evaluated at ONE (layer, dose)
    candidate point: FIT fired-confab refused >= 0.60 AND well_formed >= 0.80
    AND FIT known false-refusal <= 0.10 (point estimates; the FIT leg is not
    Wilson-gated, only the held-out legs are, per AMENDMENT.md dose policy
    part 3 versus Gates G1)."""
    return (
        fit_confab_refused["rate"] >= FIT_REFUSED_FLOOR
        and fit_confab_well_formed["rate"] >= FIT_WELL_FORMED_FLOOR
        and fit_known_false_refusal["rate"] <= FIT_KNOWN_FALSE_REFUSAL_CEIL
    )


def select_fit_operating_point(candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    """candidates: one dict per (layer, dose) grid point, each with keys
    `layer`, `dose_abs`, `viable` (bool, from fit_dose_viable), plus the
    summaries that produced `viable`. Returns the candidate with the LOWEST
    `dose_abs` among the viable ones (AMENDMENT.md dose policy part 3: "the
    (layer, dose) with the LOWEST dose whose FIT ... "), pooled across every
    candidate layer, not selected layer-by-layer first. Returns None (no
    viable point in the bracketed grid -> record the family as shape F) if
    none qualify."""
    viable = [c for c in candidates if c.get("viable")]
    if not viable:
        return None
    return min(viable, key=lambda c: c["dose_abs"])


# ---------------------------------------------------------------------------
# G1 (primary held-out gate) + cost gate
# ---------------------------------------------------------------------------

def g1_refused_transfer_pass(confab_refused: dict) -> bool:
    return confab_refused["rate"] >= REFUSED_FLOOR and confab_refused["wilson_ci_95"][0] > REFUSED_WILSON_LCB_FLOOR


def g1_well_formed_pass(confab_well_formed: dict) -> bool:
    return confab_well_formed["rate"] >= WELL_FORMED_FLOOR


def g1_cost_pass(known_false_refusal: dict) -> bool:
    return known_false_refusal["rate"] <= COST_FLOOR and known_false_refusal["wilson_ci_95"][1] < COST_WILSON_UCB_CEIL


# ---------------------------------------------------------------------------
# G3(i) placebo, direction specificity
# ---------------------------------------------------------------------------

def g3i_pass(
    random_confab_refused: dict, baseline_confab_refused: dict,
    random_known_refused: dict, baseline_known_refused: dict,
) -> dict[str, Any]:
    confab_delta = random_confab_refused["rate"] - baseline_confab_refused["rate"]
    known_delta = random_known_refused["rate"] - baseline_known_refused["rate"]
    passed = abs(confab_delta) <= PLACEBO_BAND and abs(known_delta) <= PLACEBO_BAND
    return {
        "passed": passed,
        "confab_delta_random_minus_baseline": confab_delta,
        "known_delta_random_minus_baseline": known_delta,
    }


# ---------------------------------------------------------------------------
# Outcome-shape classification (A-F), AMENDMENT.md coverage table
# ---------------------------------------------------------------------------

def classify_outcome_shape(
    *,
    fit_operating_point_exists: bool,
    refused_transfer_pass: bool | None = None,
    well_formed_pass: bool | None = None,
    cost_pass: bool | None = None,
    placebo_pass: bool | None = None,
) -> str:
    """Strict priority chain over the AMENDMENT.md coverage table, in the
    order the table itself states the held-out legs (refused-transfer ->
    well-formed -> cost-safety -> placebo-specificity). F is checked first
    and is independent of the held-out booleans (they are None/unused when
    F fires, since held-out scoring never runs for a family with no FIT
    dose-viable point)."""
    if not fit_operating_point_exists:
        return "F"
    if refused_transfer_pass is None or well_formed_pass is None or cost_pass is None or placebo_pass is None:
        raise ValueError(
            "fit_operating_point_exists is True but one or more held-out legs "
            "(refused_transfer_pass/well_formed_pass/cost_pass/placebo_pass) "
            "is None; every held-out leg must be scored before classifying "
            "shapes A-E."
        )
    if not refused_transfer_pass:
        return "B"
    if not well_formed_pass:
        return "C"
    if not cost_pass:
        return "D"
    if not placebo_pass:
        return "E"
    return "A"
