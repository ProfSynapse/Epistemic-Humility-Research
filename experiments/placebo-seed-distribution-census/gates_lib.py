"""CG1 (grader calibration) gate arithmetic for
placebo-seed-distribution-census (gates.yaml `sc2_grading_integrity.
grader_calibration`). Ported from `rr3-corrected-placebo-replication/
gates_lib.py`'s CG1 section (this experiment has no RG1/RG2/RG3 promotion
gates -- AMENDMENT.md "Gates": "no promotion gate"). Wilson CI lives in
`common.py` (shared with subsample/criterion arithmetic).
"""

from __future__ import annotations

from typing import Any

CG1_CLEAR_NEGATIVE_MIN_PER_SHARD = 0.95   # gates.yaml sc2_grading_integrity.clear_negative_agreement_min_per_shard
CG1_CLEAR_POSITIVE_MIN_PER_SHARD = 0.60   # gates.yaml sc2_grading_integrity.clear_positive_agreement_min_per_shard
CG1_CLEAR_POSITIVE_MIN_POOLED = 0.60      # gates.yaml sc2_grading_integrity.clear_positive_agreement_min_pooled
CG1_CLEAR_POSITIVE_DECOYS_PER_SHARD_FLOOR = 25  # gates.yaml sc2_grading_integrity.clear_positive_decoys_per_shard_floor


def cg1_shard_pass(clear_negative_agreement: float, clear_positive_agreement: float) -> bool:
    return (
        clear_negative_agreement >= CG1_CLEAR_NEGATIVE_MIN_PER_SHARD
        and clear_positive_agreement >= CG1_CLEAR_POSITIVE_MIN_PER_SHARD
    )


def cg1_evaluate_shard(shard_id: str, clear_negative_correct: int, clear_negative_total: int,
                        clear_positive_correct: int, clear_positive_total: int, attempt: int) -> dict[str, Any]:
    """`attempt` is 1 for the first grading pass, 2 for a regrade
    (gates.yaml `on_failure: void_shard_before_unblinding_regrade_once_with_
    fresh_agent`; `on_second_failure: void_shard_rows_report_straight`)."""
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
    first-attempt shard, in addition to the per-shard floor."""
    total = sum(r["clear_positive_total"] for r in shard_results)
    correct = sum(round(r["clear_positive_agreement"] * r["clear_positive_total"]) for r in shard_results)
    rate = (correct / total) if total else 0.0
    return {
        "n_shards": len(shard_results), "clear_positive_total_pooled": total,
        "clear_positive_correct_pooled": correct, "clear_positive_agreement_pooled": rate,
        "floor": CG1_CLEAR_POSITIVE_MIN_POOLED, "passed": rate >= CG1_CLEAR_POSITIVE_MIN_POOLED,
    }
