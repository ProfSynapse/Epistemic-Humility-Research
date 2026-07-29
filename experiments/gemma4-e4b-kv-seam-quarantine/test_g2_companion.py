"""CPU-only unit tests for g2_companion.py (gates.yaml g2_selectivity_cap
companion metrics). No torch/model import."""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import g2_companion as g2c  # noqa: E402


def _records(n: int, n_bad: int, metric: str = "not_well_formed_correct") -> list[dict]:
    return [{metric: (i < n_bad)} for i in range(n)]


# ---------------------------------------------------------------------------
# The 35-row ADJUDICABLE boundary (34 -> NOT-ADJUDICABLE, 35 -> ADJUDICABLE)
# ---------------------------------------------------------------------------


def test_boundary_34_rows_is_not_adjudicable():
    result = g2c.fired_only_companion(_records(34, 0))
    assert result["n_fired_known"] == 34
    assert result["adjudicable"] is False
    assert result["disposition"] == "NOT-ADJUDICABLE"
    # wilson_upper(0,34) = 0.1015 >= 0.10: even a flawless 0/34 cannot clear the cap.
    assert result["wilson_ci_95"][1] >= g2c.CAP_WILSON_UPPER


def test_boundary_35_rows_is_adjudicable_and_passes_on_zero_failures():
    result = g2c.fired_only_companion(_records(35, 0))
    assert result["n_fired_known"] == 35
    assert result["adjudicable"] is True
    assert result["disposition"] == "PASS"
    assert result["wilson_ci_95"][1] < g2c.CAP_WILSON_UPPER


def test_adjudicable_fails_over_cap():
    # 35 fired-known rows, 3 not-well-formed-correct: rate ~0.086 > 0.05 cap.
    result = g2c.fired_only_companion(_records(35, 3))
    assert result["adjudicable"] is True
    assert result["rate"] > g2c.CAP_RATE
    assert result["disposition"] == "FAIL"


def test_not_adjudicable_is_never_pass_or_fail_regardless_of_rate():
    # A 2/2 failure: not gradeable at this n, but must not silently read PASS.
    result = g2c.fired_only_companion(_records(2, 2))
    assert result["adjudicable"] is False
    assert result["disposition"] == "NOT-ADJUDICABLE"
    assert result["rate"] == 1.0


# ---------------------------------------------------------------------------
# Discrepancy-surfacing rule (c): fired-only rate over cap while full-
# population G2 passes must be flagged even when NOT-ADJUDICABLE.
# ---------------------------------------------------------------------------


def test_discrepancy_flagged_when_full_population_passes_but_fired_only_over_cap():
    full_population = {"n": 270, "successes": 2, "rate": 2 / 270, "wilson_ci_95": [0.0, 0.03]}
    block = g2c.g2_three_number_block(
        full_population=full_population,
        full_population_pass=True,
        fired_known_records=_records(2, 2),  # 2/2 failures: NOT-ADJUDICABLE but alarming
        undosed_known_records=_records(50, 0),
    )
    assert block["fired_only"]["disposition"] == "NOT-ADJUDICABLE"
    assert block["discrepancy_full_pass_but_fired_only_over_cap"] is True


def test_no_discrepancy_when_full_population_fails():
    full_population = {"n": 270, "successes": 30, "rate": 30 / 270, "wilson_ci_95": [0.08, 0.15]}
    block = g2c.g2_three_number_block(
        full_population=full_population,
        full_population_pass=False,
        fired_known_records=_records(2, 2),
        undosed_known_records=_records(50, 0),
    )
    # The rule only fires when full-population G2 PASSES while the fired-only
    # companion is alarming -- a full-population fail is not a "discrepancy".
    assert block["discrepancy_full_pass_but_fired_only_over_cap"] is False


def test_no_discrepancy_when_fired_only_under_cap():
    full_population = {"n": 270, "successes": 2, "rate": 2 / 270, "wilson_ci_95": [0.0, 0.03]}
    block = g2c.g2_three_number_block(
        full_population=full_population,
        full_population_pass=True,
        fired_known_records=_records(40, 0),
        undosed_known_records=_records(50, 0),
    )
    assert block["fired_only"]["disposition"] == "PASS"
    assert block["discrepancy_full_pass_but_fired_only_over_cap"] is False


def test_undosed_floor_has_no_disposition_vocabulary():
    floor = g2c.undosed_floor(_records(50, 1))
    assert set(floor) == {"n", "successes", "rate", "wilson_ci_95"}
    assert "disposition" not in floor
