"""CPU-only unit tests for rollup.py. No torch/model import: pure verdict
functions are tested against synthetic rate blocks, and the I/O driver is
tested against a synthetic analysis-committed/ tree built in tmp_path.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import rollup as ru  # noqa: E402


def _rate_block(n: int, successes: int) -> dict:
    rate, lo, hi = ru.wilson_ci(successes, n)
    return {"n": n, "successes": successes, "rate": rate, "wilson_ci_95": [lo, hi]}


# ---------------------------------------------------------------------------
# G1 / G2 / arm_pass_rule
# ---------------------------------------------------------------------------


def test_g1_verdict_pass():
    ct = _rate_block(100, 70)  # rate 0.70, wilson_lower well above 0.40
    v = ru.g1_verdict(ct)
    assert v["pass"] is True


def test_g1_verdict_fail_low_rate():
    ct = _rate_block(100, 30)
    v = ru.g1_verdict(ct)
    assert v["pass"] is False


def test_g2_full_population_verdict_pass_and_fail():
    good = _rate_block(270, 2)
    bad = _rate_block(270, 30)
    assert ru.g2_full_population_verdict(good)["pass"] is True
    assert ru.g2_full_population_verdict(bad)["pass"] is False


def test_arm_pass_rule_requires_both():
    g1_pass = {"pass": True}
    g1_fail = {"pass": False}
    g2_pass = {"pass": True}
    g2_fail = {"pass": False}
    assert ru.arm_pass_rule(g1_pass, g2_pass) is True
    assert ru.arm_pass_rule(g1_pass, g2_fail) is False
    assert ru.arm_pass_rule(g1_fail, g2_pass) is False


# ---------------------------------------------------------------------------
# G3 (effect ratio, PASS-DEGENERATE)
# ---------------------------------------------------------------------------


def test_g3_verdict_pass():
    v = ru.g3_verdict(
        true_confab_tighten_rate=0.70, undosed_confab_tighten_rate=0.10,
        placebo_confab_tighten_rates=[0.12, 0.15, 0.11, 0.13, 0.14],
    )
    # lift_true = 0.60; max |placebo - 0.10| = 0.05; ratio = 12.0
    assert v["lift_true"] == pytest.approx(0.60)
    assert v["effect_ratio"] == pytest.approx(12.0)
    assert v["disposition"] == "PASS"


def test_g3_verdict_fail_below_floor():
    v = ru.g3_verdict(
        true_confab_tighten_rate=0.30, undosed_confab_tighten_rate=0.10,
        placebo_confab_tighten_rates=[0.25, 0.10, 0.10, 0.10, 0.10],
    )
    # lift_true = 0.20; max |placebo lift| = 0.15; ratio ~1.33 < 3.0
    assert v["disposition"] == "FAIL"


def test_g3_verdict_pass_degenerate_on_zero_denominator():
    v = ru.g3_verdict(
        true_confab_tighten_rate=0.60, undosed_confab_tighten_rate=0.10,
        placebo_confab_tighten_rates=[0.10, 0.10, 0.10, 0.10, 0.10],  # zero lift
    )
    assert v["max_placebo_lift"] == 0.0
    assert v["effect_ratio"] is None
    assert v["disposition"] == "PASS-DEGENERATE"


def test_g3_verdict_requires_at_least_one_draw():
    with pytest.raises(ValueError):
        ru.g3_verdict(true_confab_tighten_rate=0.5, undosed_confab_tighten_rate=0.1,
                      placebo_confab_tighten_rates=[])


# ---------------------------------------------------------------------------
# newcombe_diff_interval (Newcombe 1998 hybrid score interval, method 10)
# ---------------------------------------------------------------------------


def _hand_wilson(successes: int, n: int, z: float = ru._Z95) -> tuple[float, float, float]:
    """Independent re-implementation of the single-proportion Wilson score
    interval (not calling `ru.wilson_ci`), used as the hand-computation oracle
    below."""
    phat = successes / n
    denom = 1 + z * z / n
    center = (phat + z * z / (2 * n)) / denom
    half = z * ((phat * (1 - phat) / n + z * z / (4 * n * n)) ** 0.5) / denom
    return phat, center - half, center + half


def test_newcombe_diff_interval_textbook_case_matches_hand_computation():
    """15/50 (p1=0.30) vs 5/50 (p2=0.10). Each side's Wilson bound and the
    Newcombe combination are computed independently here (not by calling
    `ru.newcombe_diff_interval` for the intermediate steps) and checked
    against the module's output."""
    p1, l1, u1 = _hand_wilson(15, 50)
    p2, l2, u2 = _hand_wilson(5, 50)
    d = p1 - p2
    expected_lo = d - ((p1 - l1) ** 2 + (u2 - p2) ** 2) ** 0.5
    expected_hi = d + ((u1 - p1) ** 2 + (p2 - l2) ** 2) ** 0.5

    got_d, got_lo, got_hi = ru.newcombe_diff_interval(15, 50, 5, 50)

    assert got_d == pytest.approx(0.20)
    assert got_d == pytest.approx(d)
    assert got_lo == pytest.approx(expected_lo)
    assert got_hi == pytest.approx(expected_hi)
    # Sanity against the hand-derived numeric values themselves.
    assert got_lo == pytest.approx(0.042587356, abs=1e-6)
    assert got_hi == pytest.approx(0.348668097, abs=1e-6)


def test_newcombe_diff_interval_boundary_raw_delta_passes_but_interval_fails():
    """1/20 (0.05) vs 0/20 (0.0): raw delta is EXACTLY at the 0.05 abs cap
    (would pass a raw-delta-only check), but at n=20 the Newcombe interval is
    wide enough that its upper bound (~0.236) blows through the 0.10
    degradation cap -- proving the interval check, not the raw delta, is the
    operative one c1_verdict must gate on."""
    d, lo, hi = ru.newcombe_diff_interval(1, 20, 0, 20)
    assert d == pytest.approx(0.05)
    assert d <= ru.C1_KNOWN_CORRECT_ABS_DELTA_CAP  # raw-delta check would pass
    assert hi > ru.C1_KNOWN_CORRECT_WILSON_DEGRADE_CAP  # interval check fails
    assert hi == pytest.approx(0.236131193, abs=1e-6)

    v = ru.c1_verdict(
        c0_known_correct_cost=_rate_block(20, 0),
        c1_known_correct_cost=_rate_block(20, 1),
        c1_confab_clean_tighten=_rate_block(168, 2),
        c0_mean_nll=1.00, c1_mean_nll=1.00,
    )
    assert v["known_correct_delta"] == pytest.approx(0.05)
    assert v["known_correct_preserved"] is False  # interval check overrides the raw-delta pass
    assert v["pass"] is False


def test_newcombe_diff_interval_fails_closed_on_n_zero():
    with pytest.raises(ValueError, match="n1 > 0 and n2 > 0"):
        ru.newcombe_diff_interval(0, 0, 5, 20)
    with pytest.raises(ValueError, match="n1 > 0 and n2 > 0"):
        ru.newcombe_diff_interval(3, 20, 0, 0)


# ---------------------------------------------------------------------------
# C1 precondition control
# ---------------------------------------------------------------------------


def test_c1_verdict_pass():
    v = ru.c1_verdict(
        c0_known_correct_cost=_rate_block(270, 5),
        c1_known_correct_cost=_rate_block(270, 7),
        c1_confab_clean_tighten=_rate_block(168, 2),
        c0_mean_nll=1.00, c1_mean_nll=1.05,
    )
    assert v["pass"] is True


def test_c1_verdict_fails_on_hedging():
    v = ru.c1_verdict(
        c0_known_correct_cost=_rate_block(270, 5),
        c1_known_correct_cost=_rate_block(270, 7),
        c1_confab_clean_tighten=_rate_block(168, 40),  # 0.238 >> 0.05 cap
        c0_mean_nll=1.00, c1_mean_nll=1.05,
    )
    assert v["off_model_does_not_hedge"] is False
    assert v["pass"] is False


def test_c1_verdict_fails_on_nll_blowup():
    v = ru.c1_verdict(
        c0_known_correct_cost=_rate_block(270, 5),
        c1_known_correct_cost=_rate_block(270, 7),
        c1_confab_clean_tighten=_rate_block(168, 2),
        c0_mean_nll=1.00, c1_mean_nll=1.50,  # 50% > 10% tolerance
    )
    assert v["likelihood_preserved"] is False
    assert v["pass"] is False


# ---------------------------------------------------------------------------
# Primary contrast (four outcomes)
# ---------------------------------------------------------------------------


def test_primary_contrast_inconclusive_when_c1_fails():
    v = ru.primary_contrast_verdict(c1_pass=False, a1_pass=False, a2_pass=True,
                                    alin={"within_band": True})
    assert v["disposition"] == "INCONCLUSIVE"


def test_primary_contrast_void_when_a1_passes():
    v = ru.primary_contrast_verdict(c1_pass=True, a1_pass=True, a2_pass=True,
                                    alin={"within_band": True})
    assert v["disposition"] == "VOID"


def test_primary_contrast_met():
    v = ru.primary_contrast_verdict(c1_pass=True, a1_pass=False, a2_pass=True,
                                    alin={"within_band": True})
    assert v["disposition"] == "MET"


def test_primary_contrast_not_discriminating():
    v = ru.primary_contrast_verdict(c1_pass=True, a1_pass=False, a2_pass=True,
                                    alin={"within_band": False})
    assert v["disposition"] == "NOT_DISCRIMINATING"


def test_primary_contrast_falsifying_candidate():
    v = ru.primary_contrast_verdict(c1_pass=True, a1_pass=False, a2_pass=False,
                                    alin={"within_band": True})
    assert v["disposition"] == "FALSIFYING_CANDIDATE"


# ---------------------------------------------------------------------------
# alin_discrimination_verdict
# ---------------------------------------------------------------------------


def test_alin_discrimination_verdict():
    v = ru.alin_discrimination_verdict(0.90, 0.87)
    assert v["within_band"] is True
    v2 = ru.alin_discrimination_verdict(0.90, 0.50)
    assert v2["within_band"] is False


# ---------------------------------------------------------------------------
# I/O driver: fail-closed on missing inputs, and full assembly from a
# synthetic analysis-committed/ tree.
# ---------------------------------------------------------------------------


def test_build_rollup_raises_naming_missing_stage(tmp_path):
    (tmp_path / "analysis-committed" / "gemma4-e4b").mkdir(parents=True)
    with pytest.raises(ru.RollupInputMissing, match="full_summary"):
        ru.build_rollup("gemma4-e4b", root=tmp_path)


def _write_full_summary(committed: Path, filename: str, hs_index: int,
                        confab: dict, known_cost: dict, g2_block: dict) -> None:
    layer_name = f"hs{hs_index}"
    payload = {"layers": {layer_name: {
        "confab_tighten": confab, "known_correct_cost_control": known_cost,
        "known_correct_cost_control_g2_block": g2_block,
    }}}
    (committed / filename).write_text(json.dumps(payload))


def _g2_block(known_cost: dict) -> dict:
    fired = _rate_block(40, 1)
    floor = _rate_block(20, 0)
    return {
        "full_population_g2": known_cost, "full_population_g2_pass": True,
        "fired_only": {**fired, "n_fired_known": fired["n"], "adjudicable": True,
                       "adjudicable_floor": 35, "disposition": "PASS"},
        "undosed_floor": floor,
        "discrepancy_full_pass_but_fired_only_over_cap": False,
    }


def test_build_rollup_full_assembly_from_synthetic_tree(tmp_path):
    committed = tmp_path / "analysis-committed" / "gemma4-e4b"
    committed.mkdir(parents=True)

    good_confab = _rate_block(168, 120)   # G1 pass
    good_known = _rate_block(270, 2)      # G2 pass
    bad_confab = _rate_block(168, 10)     # G1 fail (A1: parent's null replicates)

    # A1 (midband, on): FAILS G1 -- above-seam null replication.
    _write_full_summary(committed, "full_summary.json", 38, bad_confab, good_known,
                        _g2_block(good_known))
    # A2 (midband, off): PASSES both -- PRIMARY.
    _write_full_summary(committed, "full_summary.kv_off.json", 38, good_confab, good_known,
                        _g2_block(good_known))
    # A3 (seam_pair, on, hs22) + A5 (seam_pair, on, hs24) land in ONE
    # full_summary file, matching the real convention: one --site-set
    # invocation covers every site in that set (run_contrast.py run_layers
    # writes all requested layers into a single 'layers' block).
    seam_pair_on = {"layers": {
        "hs22": {"confab_tighten": good_confab, "known_correct_cost_control": good_known,
                 "known_correct_cost_control_g2_block": _g2_block(good_known)},
        "hs24": {"confab_tighten": good_confab, "known_correct_cost_control": good_known,
                 "known_correct_cost_control_g2_block": _g2_block(good_known)},
    }}
    (committed / "full_summary.seam_pair.json").write_text(json.dumps(seam_pair_on))
    # A4 (seam_pair, off, hs22 -- SAME site as A3, sharing OFF).
    _write_full_summary(committed, "full_summary.seam_pair.kv_off.json", 22, good_confab,
                        good_known, _g2_block(good_known))

    # Shallow ladder (D1-D4/A6), all in one shallow_ladder file.
    shallow_payload = {"layers": {}}
    for hs in (15, 18, 20, 23):
        shallow_payload["layers"][f"hs{hs}"] = {
            "confab_tighten": good_confab, "known_correct_cost_control": good_known,
            "known_correct_cost_control_g2_block": _g2_block(good_known),
        }
    (committed / "full_summary.shallow_ladder.json").write_text(json.dumps(shallow_payload))

    # Undosed baselines for A3/A5 (G3's hard input).
    for hs in (22, 24):
        (committed / f"undosed_summary.hs{hs}.seam_pair.json").write_text(json.dumps({
            "layer": {"confab_tighten": _rate_block(168, 17),  # base rate ~0.10
                      "known_correct_cost_control": good_known},
        }))

    # Placebo summaries for P1/P2.
    for hs in (22, 24):
        per_draw = [{"confab_tighten": _rate_block(168, 18 + i)} for i in range(5)]
        (committed / f"placebo_summary.hs{hs}.seam_pair.json").write_text(json.dumps({
            "per_draw": per_draw,
        }))

    # C1 precondition summary.
    (committed / "c1_precondition_summary.json").write_text(json.dumps({
        "c0": {"known_correct_cost_control": _rate_block(270, 5), "mean_nll": 1.0},
        "c1": {"known_correct_cost_control": _rate_block(270, 7),
               "confab_tighten": _rate_block(168, 2), "mean_nll": 1.02},
    }))

    # A_lin Part 2 discrimination.
    (committed / "alin_part2_discrimination.json").write_text(json.dumps({
        "discrimination": {"a_lin_on": 0.85, "a_lin_off": 0.83, "delta_a_lin": 0.02,
                           "band": 0.05, "within_band": True},
    }))

    result = ru.build_rollup("gemma4-e4b", root=tmp_path)

    assert result["arms"]["A1"]["arm_pass"] is False   # G1 fails (bad_confab)
    assert result["arms"]["A2"]["arm_pass"] is True
    assert result["arms"]["A3"]["arm_pass"] is True
    assert result["arms"]["A6"]["site_hs"] == 23        # == D4
    assert result["c1"]["pass"] is True
    assert result["alin_discrimination"]["within_band"] is True
    assert result["primary_contrast"]["disposition"] == "MET"
    assert "P1" in result["g3"] and "P2" in result["g3"]
    assert result["g3"]["P1"]["matched_true_arm"] == "A3"
    assert result["g3"]["P1"]["disposition"] in ("PASS", "FAIL", "PASS-DEGENERATE")


def test_build_rollup_raises_naming_c1_when_arms_present_but_c1_absent(tmp_path):
    committed = tmp_path / "analysis-committed" / "gemma4-e4b"
    committed.mkdir(parents=True)
    good_confab = _rate_block(168, 120)
    good_known = _rate_block(270, 2)
    for filename, hs in (
        ("full_summary.json", 38), ("full_summary.kv_off.json", 38),
    ):
        _write_full_summary(committed, filename, hs, good_confab, good_known,
                            _g2_block(good_known))
    # A3/A4/A5/A6/D1-D4 still missing -> should fail on A3 first, not silently
    # skip ahead to C1.
    with pytest.raises(ru.RollupInputMissing, match="arm A3"):
        ru.build_rollup("gemma4-e4b", root=tmp_path)
