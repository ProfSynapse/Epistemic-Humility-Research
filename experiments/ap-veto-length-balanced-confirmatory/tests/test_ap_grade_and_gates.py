"""Amendment AP - CPU smoke tests for ap_grade_and_gates.py (no GPU, no Modal).

Covers, per the task's smoke requirement:
  * caliper_match actually equalizes length distributions on synthetic data
    (structural correctness: pairs within caliper, 1:1, deterministic).
  * evaluate_gates exercises the pass branch AND every fail/void branch:
      - AP-G0 void (length not neutralized)
      - AP-G1 fail (veto below floor)
      - AP-G2 fail, two ways (CI includes zero; point below floor)
      - all-PASS
  * a full synthetic-data integration run (caliper match -> OOF veto ->
    length-only baseline -> paired bootstrap margin -> gates) lands PASS on a
    constructed separable-but-length-matched population, exercising the whole
    pipeline together rather than only its unit pieces.

Run with an explicit file path (the rtk pytest directory-glob false negative):
  pytest experiments/ap-veto-length-balanced-confirmatory/tests/test_ap_grade_and_gates.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

EXP_DIR = Path(__file__).resolve().parents[1]
if str(EXP_DIR) not in sys.path:
    sys.path.insert(0, str(EXP_DIR))

import ap_grade_and_gates as m  # noqa: E402


# ---------------------------------------------------------------------------
# caliper_match: structural correctness on synthetic rows.
# ---------------------------------------------------------------------------
def _row(safe_key, length):
    return {"safe_key": safe_key, "answer_tok_len": length}


def test_caliper_match_respects_caliper_and_is_1to1():
    rng = np.random.default_rng(0)
    # Deliberately length-disjoint-ish populations with a narrow overlap band,
    # mirroring AM's own finding (confabs long, good short) so the test proves
    # matching only accepts pairs inside the overlap.
    halluc_lens = rng.integers(20, 150, size=60)
    good_lens = rng.integers(10, 60, size=60)
    halluc_rows = [_row(f"h{i}", int(l)) for i, l in enumerate(halluc_lens)]
    good_rows = [_row(f"g{i}", int(l)) for i, l in enumerate(good_lens)]

    matched_h, matched_g = m.caliper_match(halluc_rows, good_rows, caliper=3)

    assert len(matched_h) == len(matched_g)
    assert len(matched_h) > 0
    for h, g in zip(matched_h, matched_g):
        assert abs(h["answer_tok_len"] - g["answer_tok_len"]) <= 3
    # No row matched twice.
    assert len(set(h["safe_key"] for h in matched_h)) == len(matched_h)
    assert len(set(g["safe_key"] for g in matched_g)) == len(matched_g)


def test_caliper_match_equalizes_length_distributions():
    rng = np.random.default_rng(1)
    halluc_lens = rng.integers(20, 150, size=200)
    good_lens = rng.integers(10, 60, size=200)
    halluc_rows = [_row(f"h{i}", int(l)) for i, l in enumerate(halluc_lens)]
    good_rows = [_row(f"g{i}", int(l)) for i, l in enumerate(good_lens)]

    pre_gap = abs(halluc_lens.mean() - good_lens.mean())
    matched_h, matched_g = m.caliper_match(halluc_rows, good_rows, caliper=3)
    matched_h_lens = np.array([r["answer_tok_len"] for r in matched_h])
    matched_g_lens = np.array([r["answer_tok_len"] for r in matched_g])
    post_gap = abs(matched_h_lens.mean() - matched_g_lens.mean())

    assert post_gap < pre_gap
    assert post_gap <= 3.0  # paired means cannot drift beyond the caliper


def test_caliper_match_is_order_independent():
    rng = np.random.default_rng(2)
    halluc_rows = [_row(f"h{i}", int(l))
                   for i, l in enumerate(rng.integers(20, 150, size=40))]
    good_rows = [_row(f"g{i}", int(l))
                for i, l in enumerate(rng.integers(10, 60, size=40))]

    mh1, mg1 = m.caliper_match(halluc_rows, good_rows, caliper=3)
    mh2, mg2 = m.caliper_match(list(reversed(halluc_rows)), list(reversed(good_rows)),
                               caliper=3)

    pairs1 = sorted((h["safe_key"], g["safe_key"]) for h, g in zip(mh1, mg1))
    pairs2 = sorted((h["safe_key"], g["safe_key"]) for h, g in zip(mh2, mg2))
    assert pairs1 == pairs2


def test_caliper_match_zero_overlap_drops_everything():
    halluc_rows = [_row("h0", 100), _row("h1", 120)]
    good_rows = [_row("g0", 10), _row("g1", 12)]
    matched_h, matched_g = m.caliper_match(halluc_rows, good_rows, caliper=3)
    assert matched_h == []
    assert matched_g == []


# ---------------------------------------------------------------------------
# evaluate_gates: pass branch + every fail/void branch, hand-picked numbers.
# ---------------------------------------------------------------------------
def test_gate_g0_void_when_length_not_neutralized():
    v = m.evaluate_gates(length_only_auroc=0.65, veto_auroc=0.90, veto_ci_lo=0.80,
                         margin_point=0.30, margin_ci_lo=0.20, margin_ci_hi=0.40)
    assert v["void"] is True
    assert v["overall"] == "VOID"
    assert v["AP_G0"]["pass"] is False
    assert v["AP_G1"] is None
    assert v["AP_G2"] is None


def test_gate_g1_fail_when_veto_below_floor():
    v = m.evaluate_gates(length_only_auroc=0.55, veto_auroc=0.60, veto_ci_lo=0.55,
                         margin_point=0.20, margin_ci_lo=0.10, margin_ci_hi=0.30)
    assert v["void"] is False
    assert v["AP_G0"]["pass"] is True
    assert v["AP_G1"]["pass"] is False
    assert v["overall"] == "FAIL"


def test_gate_g1_fail_when_ci_lb_at_or_below_floor():
    # AUROC clears 0.68 but the bootstrap CI lower bound does not clear 0.60.
    v = m.evaluate_gates(length_only_auroc=0.55, veto_auroc=0.70, veto_ci_lo=0.58,
                         margin_point=0.20, margin_ci_lo=0.10, margin_ci_hi=0.30)
    assert v["AP_G1"]["pass"] is False
    assert v["overall"] == "FAIL"


def test_gate_g2_fail_when_margin_ci_includes_zero():
    v = m.evaluate_gates(length_only_auroc=0.55, veto_auroc=0.75, veto_ci_lo=0.65,
                         margin_point=0.20, margin_ci_lo=-0.02, margin_ci_hi=0.35)
    assert v["AP_G1"]["pass"] is True
    assert v["AP_G2"]["ci_excludes_zero"] is False
    assert v["AP_G2"]["pass"] is False
    assert v["overall"] == "FAIL"


def test_gate_g2_fail_when_point_below_floor_despite_ci_excluding_zero():
    v = m.evaluate_gates(length_only_auroc=0.55, veto_auroc=0.70, veto_ci_lo=0.62,
                         margin_point=0.05, margin_ci_lo=0.02, margin_ci_hi=0.09)
    assert v["AP_G1"]["pass"] is True
    assert v["AP_G2"]["ci_excludes_zero"] is True
    assert v["AP_G2"]["pass"] is False
    assert v["overall"] == "FAIL"


def test_gate_all_pass():
    v = m.evaluate_gates(length_only_auroc=0.55, veto_auroc=0.75, veto_ci_lo=0.65,
                         margin_point=0.20, margin_ci_lo=0.10, margin_ci_hi=0.30)
    assert v["AP_G0"]["pass"] is True
    assert v["AP_G1"]["pass"] is True
    assert v["AP_G2"]["pass"] is True
    assert v["void"] is False
    assert v["overall"] == "PASS"


# ---------------------------------------------------------------------------
# Full synthetic-data integration: caliper match -> OOF veto -> length-only
# -> paired bootstrap margin -> gates, all on synthetic feature vectors.
# ---------------------------------------------------------------------------
def _make_population(rng, n, length_lo, length_hi, feat_dim, feat_mean, feat_sd=1.0):
    lengths = rng.integers(length_lo, length_hi, size=n)
    feats = rng.normal(loc=feat_mean, scale=feat_sd, size=(n, feat_dim))
    rows = [{"safe_key": f"k{i}", "answer_tok_len": int(lengths[i])}
            for i in range(n)]
    return rows, feats


def test_full_pipeline_pass_on_separable_length_matched_synthetic_data():
    rng = np.random.default_rng(42)
    feat_dim = 12
    # Overlapping length ranges so caliper matching has plenty of candidates
    # (unlike AM's all-long residual, this mirrors AP's length-balanced design).
    halluc_rows, halluc_X = _make_population(
        rng, n=150, length_lo=15, length_hi=60, feat_dim=feat_dim,
        feat_mean=np.concatenate([[1.6], np.zeros(feat_dim - 1)]))
    good_rows, good_X = _make_population(
        rng, n=150, length_lo=15, length_hi=60, feat_dim=feat_dim,
        feat_mean=np.concatenate([[-1.6], np.zeros(feat_dim - 1)]))

    # caliper_match operates on row dicts only; carry features alongside via
    # a safe_key -> feature lookup so matching and feature order stay aligned.
    h_feat = {r["safe_key"]: x for r, x in zip(halluc_rows, halluc_X)}
    g_feat = {r["safe_key"]: x for r, x in zip(good_rows, good_X)}

    matched_h, matched_g = m.caliper_match(halluc_rows, good_rows, caliper=3)
    assert len(matched_h) >= 30  # enough pairs for a stable OOF fit

    fit_rows = matched_h + matched_g
    y_halluc = np.array([1] * len(matched_h) + [0] * len(matched_g))
    length_all = np.array([r["answer_tok_len"] for r in fit_rows], dtype=float)
    X = np.vstack([h_feat[r["safe_key"]] for r in matched_h]
                  + [g_feat[r["safe_key"]] for r in matched_g])

    length_only_auroc = m.auroc(y_halluc, length_all)
    assert length_only_auroc <= m.G0_LENGTH_ONLY_MAX, (
        "caliper matching should neutralize length on this constructed "
        "overlapping-range population; if this fails the synthetic setup, "
        "not the matcher, is miscalibrated")

    dial_oof = m.oof_scores(X, 1 - y_halluc, seed=m.SEED)
    veto_oof = -dial_oof
    veto_auroc = m.auroc(y_halluc, veto_oof)
    veto_ci_lo, veto_ci_hi, _ = m.bootstrap_auroc_ci(y_halluc, veto_oof, n=200)
    margin_point = veto_auroc - length_only_auroc
    margin_ci_lo, margin_ci_hi, _ = m.paired_bootstrap_margin_ci(
        y_halluc, veto_oof, length_all, n=200)

    verdict = m.evaluate_gates(length_only_auroc, veto_auroc, veto_ci_lo,
                               margin_point, margin_ci_lo, margin_ci_hi)

    assert verdict["AP_G0"]["pass"] is True
    assert verdict["AP_G1"]["pass"] is True, verdict["AP_G1"]
    assert verdict["AP_G2"]["pass"] is True, verdict["AP_G2"]
    assert verdict["overall"] == "PASS"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
