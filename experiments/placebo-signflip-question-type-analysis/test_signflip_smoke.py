"""Smoke tests for placebo-signflip-question-type-analysis, synthetic
fixtures only (no real staged data, no model, no GPU).

Run: python3 -m pytest test_signflip_smoke.py
(never bare `python3 test_signflip_smoke.py`; and never a bare directory
glob under rtk -- see this repo's documented rtk pytest false-negative
gotcha -- always pass this explicit file path.)

The BG1 real-data checks (frame_port.check_qwen_frame /
check_mistral_frame_via_fit_reuse_report / opt-in realdata variants) are
marked `realdata` and SKIPPED by default; they read the real staged
provenance tree under analysis/staged_inputs/ (run staging.py first) and are
meant for the lead to run explicitly:

    python3 -m pytest test_signflip_smoke.py -m realdata -v
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import behavioral_leg as bl  # noqa: E402
import common  # noqa: E402
import frame_port as fp  # noqa: E402
import mechanism_leg as ml  # noqa: E402

REALDATA = pytest.mark.skipif(
    os.environ.get("SIGNFLIP_RUN_REALDATA") != "1",
    reason="opt-in real-data check; set SIGNFLIP_RUN_REALDATA=1 to run (requires staging.py to have been run)",
)


# ---------------------------------------------------------------------------
# common.py
# ---------------------------------------------------------------------------

def test_wilson_known_values():
    w = common.wilson(50, 100)
    assert w["n"] == 100 and w["successes"] == 50
    assert w["rate"] == pytest.approx(0.5)
    lo, hi = w["wilson_ci_95"]
    assert lo < 0.5 < hi
    assert w["wilson_ci_95"] == pytest.approx([0.40383, 0.59617], abs=1e-4)


def test_wilson_zero_n():
    w = common.wilson(0, 0)
    assert w == {"n": 0, "successes": 0, "rate": 0.0, "wilson_ci_95": [0.0, 0.0]}


def test_rate_wilson_field_lookup():
    records = [{"refused_final": True}, {"refused_final": False}, {"refused_final": True}]
    w = common.rate_wilson(records, "refused_final")
    assert w["n"] == 3 and w["successes"] == 2


def test_delta_pts():
    a = {"rate": 0.30}
    b = {"rate": 0.10}
    assert common.delta_pts(a, b) == pytest.approx(20.0)


@pytest.mark.parametrize(
    "row_key,expected",
    [
        ("kuq_unknowns_all:1001", "unanswerable"),
        ("kuq_unknowns_all:0", "unanswerable"),
        ("popqa:42", "answerable"),
        ("triviaqa:7", "answerable"),
    ],
)
def test_question_type_of(row_key, expected):
    assert common.question_type_of(row_key) == expected


def test_question_type_of_rejects_unknown_prefix():
    with pytest.raises(ValueError):
        common.question_type_of("mystery_source:0")


def test_paired_rows_only_keeps_intersection():
    active = {"a": {"row_key": "a", "role": "confab"}, "b": {"row_key": "b", "role": "confab"}}
    baseline = {"a": {"row_key": "a"}, "c": {"row_key": "c"}}
    pairs = common.paired_rows(active, baseline)
    assert len(pairs) == 1
    assert pairs[0][0]["row_key"] == "a"


def test_paired_rows_role_filter_excludes_wrong_role():
    active = {"a": {"row_key": "a", "role": "confab"}, "b": {"row_key": "b", "role": "known_correct_answered"}}
    baseline = {"a": {"row_key": "a"}, "b": {"row_key": "b"}}
    pairs = common.paired_rows(active, baseline, role="confab")
    assert len(pairs) == 1 and pairs[0][0]["row_key"] == "a"


def test_combine_active_and_baseline_fills_unfired_from_baseline():
    """The 9-row baseline-fill logic (AMENDMENT.md Cell B): row_keys absent
    from the active (fired) arm inherit their baseline row verbatim."""
    active = {"a": {"row_key": "a", "text": "active"}}
    baseline = {"a": {"row_key": "a", "text": "baseline"}, "b": {"row_key": "b", "text": "baseline"}}
    combined = common.combine_active_and_baseline(["a", "b"], active, baseline)
    by_key = {r["row_key"]: r for r in combined}
    assert by_key["a"]["text"] == "active"
    assert by_key["b"]["text"] == "baseline"  # unfired -> baseline fill


def test_combine_active_and_baseline_raises_on_missing_row():
    active = {}
    baseline = {"a": {"row_key": "a"}}
    with pytest.raises(KeyError):
        common.combine_active_and_baseline(["a", "missing"], active, baseline)


def test_bootstrap_smd_deterministic_with_fixed_seed():
    a = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    b = np.array([0.5, 1.5, 2.5, 3.5])
    r1 = common.bootstrap_smd(a, b, n_boot=200, seed=42)
    r2 = common.bootstrap_smd(a, b, n_boot=200, seed=42)
    assert r1 == r2  # exact reproducibility for a fixed seed


def test_bootstrap_smd_different_seed_differs_but_same_point_estimate():
    a = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    b = np.array([0.5, 1.5, 2.5, 3.5, 2.0])
    r1 = common.bootstrap_smd(a, b, n_boot=500, seed=1)
    r2 = common.bootstrap_smd(a, b, n_boot=500, seed=2)
    assert r1["smd"] == r2["smd"]  # point estimate is seed-independent
    assert r1["bootstrap_ci_95"] != r2["bootstrap_ci_95"]  # CI resample differs


def test_bootstrap_smd_identical_groups_gives_zero():
    a = np.array([1.0, 1.0, 1.0, 1.0])
    b = np.array([1.0, 1.0, 1.0, 1.0])
    r = common.bootstrap_smd(a, b, n_boot=50, seed=0)
    assert r["smd"] == 0.0


def test_mann_whitney_u_separated_groups_significant():
    a = np.array([10.0, 11.0, 12.0, 13.0])
    b = np.array([1.0, 2.0, 3.0, 4.0])
    result = common.mann_whitney_u(a, b)
    assert result["p_value"] < 0.05


# ---------------------------------------------------------------------------
# frame_port.py (gate arithmetic, synthetic)
# ---------------------------------------------------------------------------

def test_gate_decision_fires_above_tau():
    # proj_d=5, mu_d=0, sigma_d=1 -> z_d=5 clipped to 2 -> score=-2 -> below any reasonable tau
    d = fp.gate_decision(proj_d=5.0, mu_d=0.0, sigma_d=1.0, tau=-1.0)
    assert d["z_d"] == 2.0  # clipped
    assert d["score_neg_z_d"] == -2.0
    assert d["fire"] is False  # -2.0 >= -1.0 is False


def test_gate_decision_fires_when_score_high():
    # proj_d very negative -> z_d very negative -> score positive -> fires
    d = fp.gate_decision(proj_d=-5.0, mu_d=0.0, sigma_d=1.0, tau=1.0)
    assert d["z_d"] == -2.0  # clipped
    assert d["score_neg_z_d"] == 2.0
    assert d["fire"] is True


def test_gate_decision_matches_naive_unclipped_when_within_bounds():
    d = fp.gate_decision(proj_d=1.0, mu_d=0.0, sigma_d=2.0, tau=-0.4)
    assert d["z_d"] == pytest.approx(0.5)
    assert d["score_neg_z_d"] == pytest.approx(-0.5)
    assert d["fire"] is False  # -0.5 >= -0.4 is False


def test_standardized_score_clip_vs_unclip():
    clipped = fp.standardized_score(10.0, mu=0.0, sigma=1.0, clip=True)
    unclipped = fp.standardized_score(10.0, mu=0.0, sigma=1.0, clip=False)
    assert clipped == 2.0
    assert unclipped == 10.0


def test_raw_projection_is_dot_product():
    h = np.array([1.0, 2.0, 3.0])
    v = np.array([1.0, 0.0, 0.0])
    assert fp.raw_projection(h, v) == pytest.approx(1.0)


def test_load_direction_vector_rejects_nontrivial_mu(tmp_path):
    import json

    bad = tmp_path / "bad_direction.json"
    bad.write_text(json.dumps({"vector": [1.0, 0.0], "mu": [0.1, 0.0]}))
    with pytest.raises(SystemExit):
        fp.load_direction_vector(bad)


def test_load_direction_vector_accepts_trivial_mu(tmp_path):
    import json

    good = tmp_path / "good_direction.json"
    good.write_text(json.dumps({"vector": [1.0, 0.0], "mu": [0.0, 0.0]}))
    v = fp.load_direction_vector(good)
    assert np.array_equal(v, np.array([1.0, 0.0]))


# ---------------------------------------------------------------------------
# behavioral_leg.py subtype binning (synthetic)
# ---------------------------------------------------------------------------

def test_subtype_delta_table_bins_correctly():
    pairs = [
        ({"row_key": "kuq_unknowns_all:1", "refused": True}, {"row_key": "kuq_unknowns_all:1", "category_canon": "future unknown", "refused": False}),
        ({"row_key": "kuq_unknowns_all:2", "refused": False}, {"row_key": "kuq_unknowns_all:2", "category_canon": "future unknown", "refused": False}),
        ({"row_key": "kuq_unknowns_all:3", "refused": True}, {"row_key": "kuq_unknowns_all:3", "category_canon": "underspecified question", "refused": True}),
    ]
    table = bl.subtype_delta_table(
        pairs, active_grade=lambda a: a["refused"], baseline_grade=lambda b: b["refused"],
    )
    assert table["future unknown"]["n_paired"] == 2
    assert table["future unknown"]["random_refused_final"]["successes"] == 1
    assert table["underspecified question"]["n_paired"] == 1
    assert table["controversial/debatable question"]["n_paired"] == 0
    assert "3/3" in table["_coverage_note"]


def test_subtype_rate_table_bins_correctly():
    rows = [
        {"category_canon": "counterfactual questions", "g": True},
        {"category_canon": "counterfactual questions", "g": False},
        {"category_canon": "unrecognized_subtype", "g": True},
    ]
    table = bl.subtype_rate_table(rows, grade=lambda r: r["g"])
    assert table["counterfactual questions"]["n"] == 2
    assert table["counterfactual questions"]["successes"] == 1
    assert "2/3" in table["_coverage_note"]  # the unrecognized-subtype row does not match any KUQ_SUBTYPES bin


# ---------------------------------------------------------------------------
# mechanism_leg.py M1/M3 math (synthetic)
# ---------------------------------------------------------------------------

def test_m3_row_displacement_matches_manual_erase_write():
    h = np.array([1.0, 0.0, 0.0])
    r_hat = np.array([0.0, 1.0, 0.0])
    c_hat = np.array([0.0, 0.7071067811865476, 0.7071067811865476])
    dose_abs = 4.0
    # h has zero projection onto r_hat -> displacement = dot_r_chat * dose_abs
    disp = ml.m3_row_displacement(h, r_hat, c_hat, dose_abs)
    dot_r_chat = float(r_hat @ c_hat)
    assert disp == pytest.approx(dot_r_chat * dose_abs)
    # manual erase-write reconstruction agrees
    h_new = h - float(h @ r_hat) * r_hat + dose_abs * r_hat
    manual_disp = float(h_new @ c_hat) - float(h @ c_hat)
    assert disp == pytest.approx(manual_disp)


def test_m3_row_displacement_nonzero_prior_projection():
    h = np.array([0.5, 0.5, 0.0])
    r_hat = np.array([0.0, 1.0, 0.0])
    c_hat = np.array([1.0, 0.0, 0.0])
    dose_abs = 3.0
    disp = ml.m3_row_displacement(h, r_hat, c_hat, dose_abs)
    h_new = h - float(h @ r_hat) * r_hat + dose_abs * r_hat
    manual_disp = float(h_new @ c_hat) - float(h @ c_hat)
    assert disp == pytest.approx(manual_disp)
    assert disp == pytest.approx(0.0)  # r_hat and c_hat orthogonal here, so no displacement onto c_hat


def test_project_population_assigns_question_type():
    anchors = {"kuq_unknowns_all:0": np.array([1.0, 0.0]), "popqa:1": np.array([0.0, 1.0])}
    u_d = np.array([1.0, 0.0])
    c_hat = np.array([0.0, 1.0])
    projected = ml.project_population(anchors, u_d, c_hat, mu_d=0.0, sigma_d=1.0, mu_c=0.0, sigma_c=1.0)
    by_key = {r["row_key"]: r for r in projected}
    assert by_key["kuq_unknowns_all:0"]["question_type"] == "unanswerable"
    assert by_key["popqa:1"]["question_type"] == "answerable"


def test_m1_contrast_detects_separated_groups():
    projected = (
        [{"question_type": "unanswerable", "z_d": v} for v in [5.0, 5.2, 4.8, 5.1, 4.9]]
        + [{"question_type": "answerable", "z_d": v} for v in [-1.0, -1.2, -0.8, -1.1, -0.9]]
    )
    result = ml.m1_contrast(projected, "z_d", seed=7)
    assert result["prediction_consistent"] is True
    assert result["mann_whitney"]["p_value"] < 0.05
    assert result["bootstrap_smd"]["bootstrap_ci_95"][0] > 0  # CI does not span 0


def test_m2_summary_is_descriptive_and_flags_underpowered():
    stats = {
        "qwen35-4b": {"mean_z_d": -0.2, "std_z_d": 1.0, "mean_z_c": -0.1, "std_z_c": 1.0},
        "mistral7b-v03": {"mean_z_d": 0.3, "std_z_d": 1.1, "mean_z_c": 0.2, "std_z_c": 1.1},
    }
    summary = ml.m2_summary(stats)
    assert summary["underpowered"] is True
    assert summary["families"]["qwen35-4b"]["direction"] == "suppress"
    assert summary["families"]["mistral7b-v03"]["direction"] == "recruit"


# ---------------------------------------------------------------------------
# BG1 real-data checks (opt-in)
# ---------------------------------------------------------------------------

@REALDATA
def test_bg1_qwen_realdata_reproduces_firing_set():
    result = fp.check_qwen_frame()
    assert result["pass"] is True
    assert result["n_mismatches"] == 0


@REALDATA
def test_bg1_mistral_fit_reuse_crosscheck_realdata():
    result = fp.check_mistral_frame_via_fit_reuse_report()
    assert result["pass"] is True


@REALDATA
def test_bg1_mistral_realdata_fire_set():
    """Loads the 251MB mistral anchors JSON; only run explicitly."""
    result = fp.check_mistral_frame_realdata()
    assert result["pass"] is True


@REALDATA
def test_bg1_llama_realdata_reconstruction():
    """Loads the 493MB llama anchors JSON three times (once per candidate
    layer); only run explicitly, and expect a longer runtime."""
    result = fp.check_llama_frame_realdata()
    assert result["pass"] is True
