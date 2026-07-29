"""CPU-only unit tests for pipeline.summarize_layer_records -- the pure
aggregation function the fired-only G2 companion (g2_companion.py) plugs
into (AMENDMENT.md ~1028-1068, gates.yaml g2_selectivity_cap). No GPU, no
model load: this exercises the aggregation logic against synthetic per-row
records shaped exactly like `run_one_row`'s return value.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import pipeline as pl  # noqa: E402


def _row(role: str, fire: bool, *, clean_tighten: bool = False,
         not_well_formed_correct: bool = False, readback=None,
         degenerate: bool = False) -> dict:
    return {
        "role": role, "fire": fire, "readback_measured": readback,
        "clean_tighten": clean_tighten, "not_well_formed_correct": not_well_formed_correct,
        "grade": {"degenerate": degenerate, "clean_tighten": clean_tighten},
    }


def test_summarize_layer_records_basic_shape_and_g1_g2():
    dose_target = 30.0
    records = (
        [_row("confab", fire=True, clean_tighten=True, readback=30.0) for _ in range(6)]
        + [_row("confab", fire=False, clean_tighten=False) for _ in range(2)]
        + [_row("known_correct_answered", fire=False, not_well_formed_correct=False)
           for _ in range(10)]
    )
    out = pl.summarize_layer_records(records, dose_target, hs_index=22, kv_sharing="on")
    assert out["hs_index"] == 22
    assert out["kv_sharing"] == "on"
    assert out["n_rows"] == 18
    assert out["n_fired"] == 6
    assert out["frac_readback_within_tol"] == 1.0
    assert out["collapse_rate_on_dosed"] == 0.0
    assert out["confab_tighten"]["n"] == 8
    assert out["confab_tighten"]["successes"] == 6
    # Full-population G2 is transcribed verbatim: rate over ALL known rows,
    # unfiltered by fire (gates.yaml g2_selectivity_cap.population_note).
    assert out["known_correct_cost_control"]["n"] == 10
    assert out["known_correct_cost_control"]["successes"] == 0


def test_summarize_layer_records_carries_fired_only_companion():
    dose_target = 30.0
    known_fired = [
        _row("known_correct_answered", fire=True, not_well_formed_correct=(i < 2), readback=30.0)
        for i in range(40)
    ]
    known_not_fired = [
        _row("known_correct_answered", fire=False, not_well_formed_correct=False)
        for _ in range(20)
    ]
    records = known_fired + known_not_fired
    out = pl.summarize_layer_records(records, dose_target, hs_index=38, kv_sharing="on")
    fired_only = out["known_correct_cost_control_fired_only"]
    assert fired_only["n_fired_known"] == 40
    assert fired_only["adjudicable"] is True  # >= 35, gates.yaml floor
    assert fired_only["successes"] == 2
    block = out["known_correct_cost_control_g2_block"]
    assert block["fired_only"] == fired_only
    assert block["undosed_floor"]["n"] == 20


def test_summarize_layer_records_readback_out_of_tolerance():
    dose_target = 30.0
    records = [
        _row("confab", fire=True, clean_tighten=True, readback=50.0),  # far outside 5%+0.5
        _row("known_correct_answered", fire=False),
    ]
    out = pl.summarize_layer_records(records, dose_target, hs_index=22, kv_sharing="off")
    assert out["frac_readback_within_tol"] == 0.0


def test_summarize_layer_records_no_fired_rows_is_none_not_zero():
    """An undosed pass (every row fire=False) must report frac_readback_
    within_tol / collapse_rate as None, not 0.0 -- there is nothing to
    measure, which is a different fact from measuring zero tolerance."""
    records = [_row("confab", fire=False), _row("known_correct_answered", fire=False)]
    out = pl.summarize_layer_records(records, 30.0, hs_index=22, kv_sharing="on")
    assert out["frac_readback_within_tol"] is None
    assert out["collapse_rate_on_dosed"] is None
    assert out["n_fired"] == 0
