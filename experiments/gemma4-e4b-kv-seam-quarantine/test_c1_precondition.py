"""CPU-only unit tests for c1_precondition.py (gates.yaml
g0_c1_precondition_control producer). No torch/model import except where
explicitly noted: this exercises the structural/aggregation logic against
synthetic rows and rate blocks, plus a real (no-model) row-loading check
against the private FIT-split data, the same way test_pipeline_summarize.py
and test_rollup.py test their own modules.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import c1_precondition as c1p  # noqa: E402
import pipeline as pl  # noqa: E402
import rollup as ru  # noqa: E402


def _rate_block(n: int, successes: int) -> dict:
    rate, lo, hi = ru.wilson_ci(successes, n)
    return {"n": n, "successes": successes, "rate": rate, "wilson_ci_95": [lo, hi]}


def _condition_block(*, known_n: int, known_successes: int, confab_n: int,
                     confab_successes: int, mean_nll: float) -> dict:
    """Shaped exactly like `run_condition`'s return value -- the two keys
    `verdict_from_summary` reads plus `mean_nll`."""
    return {
        "known_correct_cost_control": _rate_block(known_n, known_successes),
        "confab_tighten": _rate_block(confab_n, confab_successes),
        "mean_nll": mean_nll,
    }


# ---------------------------------------------------------------------------
# _force_off -- the arm's entire scope (no injection in either condition)
# ---------------------------------------------------------------------------


def test_force_off_sets_every_row_fire_false():
    rows = [{"row_key": "a", "fire": True}, {"row_key": "b"}, {"row_key": "c", "fire": False}]
    out = c1p._force_off(rows)
    assert all(r["fire"] is False for r in out)
    assert [r["row_key"] for r in out] == ["a", "b", "c"]
    # original rows untouched (copy, not mutate-in-place)
    assert rows[0]["fire"] is True


# ---------------------------------------------------------------------------
# _inert_direction_vector -- the mechanical hook vehicle, provably inert
# because fire is always False (module docstring "NO SITE")
# ---------------------------------------------------------------------------


def test_inert_direction_vector_shape_and_unit_norm():
    v = c1p._inert_direction_vector(2560)
    assert v.shape == (2560,)
    assert v.dtype == np.float32
    assert abs(float(np.linalg.norm(v)) - 1.0) < 1e-5


def test_inert_direction_vector_reproducible():
    v1 = c1p._inert_direction_vector(128)
    v2 = c1p._inert_direction_vector(128)
    assert np.array_equal(v1, v2)  # fixed seed -> same artifact across re-runs


# ---------------------------------------------------------------------------
# _validate_reference_completions -- the guard for the C1 NLL interpretation
# ruling (lead, 2026-07-30): C0 generates its own reference and must not be
# handed one; C1 cannot compute the paired/gating NLL without C0's per-row
# completion tokens. Pure-python guard, no model needed to test it.
# ---------------------------------------------------------------------------


def test_validate_reference_completions_on_accepts_none():
    c1p._validate_reference_completions("on", None)  # must not raise


def test_validate_reference_completions_on_rejects_provided_map():
    with pytest.raises(ValueError, match="kv_sharing='on'"):
        c1p._validate_reference_completions("on", {"row1": object()})


def test_validate_reference_completions_off_requires_nonempty_map():
    with pytest.raises(ValueError, match="kv_sharing='off'"):
        c1p._validate_reference_completions("off", None)
    with pytest.raises(ValueError, match="kv_sharing='off'"):
        c1p._validate_reference_completions("off", {})


def test_validate_reference_completions_off_accepts_nonempty_map():
    c1p._validate_reference_completions("off", {"row1": object()})  # must not raise


def test_validate_reference_completions_rejects_unknown_kv_sharing():
    with pytest.raises(ValueError, match="unknown kv_sharing"):
        c1p._validate_reference_completions("bogus", {"row1": object()})


# ---------------------------------------------------------------------------
# verdict_from_summary -- transcribes gates.yaml g0_c1_precondition_control.
# pass_if_all via rollup.c1_verdict (imported, not reimplemented). These
# three cases mirror test_rollup.py's own test_c1_verdict_pass /
# test_c1_verdict_fails_on_hedging / test_c1_verdict_fails_on_nll_blowup,
# but exercised through THIS module's summary-dict shape (the shape
# c1_precondition.py actually produces and rollup.py actually reads), not
# rollup.c1_verdict's raw kwargs directly.
# ---------------------------------------------------------------------------


def test_verdict_from_summary_pass():
    summary = {
        "c0": _condition_block(known_n=270, known_successes=5, confab_n=168,
                               confab_successes=2, mean_nll=1.00),
        "c1": _condition_block(known_n=270, known_successes=7, confab_n=168,
                               confab_successes=2, mean_nll=1.05),
    }
    v = c1p.verdict_from_summary(summary)
    assert v["pass"] is True
    assert v["known_correct_preserved"] is True
    assert v["off_model_does_not_hedge"] is True
    assert v["likelihood_preserved"] is True


def test_verdict_from_summary_fails_on_hedging():
    summary = {
        "c0": _condition_block(known_n=270, known_successes=5, confab_n=168,
                               confab_successes=2, mean_nll=1.00),
        "c1": _condition_block(known_n=270, known_successes=7, confab_n=168,
                               confab_successes=40, mean_nll=1.05),  # 0.238 >> 0.05 cap
    }
    v = c1p.verdict_from_summary(summary)
    assert v["off_model_does_not_hedge"] is False
    assert v["pass"] is False


def test_verdict_from_summary_fails_on_nll_blowup():
    summary = {
        "c0": _condition_block(known_n=270, known_successes=5, confab_n=168,
                               confab_successes=2, mean_nll=1.00),
        "c1": _condition_block(known_n=270, known_successes=7, confab_n=168,
                               confab_successes=2, mean_nll=1.50),  # 50% > 10% tolerance
    }
    v = c1p.verdict_from_summary(summary)
    assert v["likelihood_preserved"] is False
    assert v["pass"] is False


def test_verdict_from_summary_fails_on_known_correct_degradation():
    summary = {
        "c0": _condition_block(known_n=270, known_successes=5, confab_n=168,
                               confab_successes=2, mean_nll=1.00),
        "c1": _condition_block(known_n=270, known_successes=40, confab_n=168,
                               confab_successes=2, mean_nll=1.00),  # big cost jump
    }
    v = c1p.verdict_from_summary(summary)
    assert v["known_correct_preserved"] is False
    assert v["pass"] is False


# ---------------------------------------------------------------------------
# write_summary -- round-trips to the exact path rollup.build_rollup() reads
# (rollup.py: committed / "c1_precondition_summary.json")
# ---------------------------------------------------------------------------


def test_write_summary_round_trips_at_rollup_read_path(tmp_path, monkeypatch):
    monkeypatch.setattr(c1p, "HERE", tmp_path)
    summary = {
        "family": "gemma4-e4b", "split": "fit",
        "c0": _condition_block(known_n=10, known_successes=1, confab_n=10,
                               confab_successes=0, mean_nll=1.0),
        "c1": _condition_block(known_n=10, known_successes=1, confab_n=10,
                               confab_successes=0, mean_nll=1.0),
    }
    out_path = c1p.write_summary("gemma4-e4b", summary)
    assert out_path == tmp_path / "analysis-committed" / "gemma4-e4b" / "c1_precondition_summary.json"
    assert out_path.is_file()
    round_tripped = json.loads(out_path.read_text())
    assert round_tripped == summary
    # This is exactly the path rollup.build_rollup() reads (rollup.py
    # build_rollup: `committed / "c1_precondition_summary.json"`).
    assert out_path.name == "c1_precondition_summary.json"


# ---------------------------------------------------------------------------
# Integration (no model, no GPU): real FIT-split row loading. This is a
# regression guard for the exact bug this test run caught -- a fresh
# `git worktree add` checkout of this repo materializes
# analysis-committed/gemma4-e4b/{split_manifest,eval_pool_manifest}.json as
# plain-text symlink-content placeholders instead of real symlinks
# (core.symlinks=false), which makes pl.load_rows raise a JSONDecodeError.
# If this test fails with that error, repair the two symlinks by hand
# (read each placeholder's own text content as the relative target and
# `ln -s` it) before trusting any other row-loading stage in this worktree.
# ---------------------------------------------------------------------------


def test_load_rows_fit_split_both_roles_nonempty():
    confab = pl.load_rows("gemma4-e4b", "confab", "fit")
    known = pl.load_rows("gemma4-e4b", "known_correct_answered", "fit")
    assert len(confab) > 0
    assert len(known) > 0
    assert all(r["role"] == "confab" for r in confab)
    assert all(r["role"] == "known_correct_answered" for r in known)


def test_run_dry_run_reports_correct_row_counts(capsys):
    rc = c1p.run("gemma4-e4b", smoke_n=None, dry_run=True)
    assert rc == 0
    plan = json.loads(capsys.readouterr().out)
    confab = pl.load_rows("gemma4-e4b", "confab", "fit")
    known = pl.load_rows("gemma4-e4b", "known_correct_answered", "fit")
    assert plan["n_confab_fit"] == len(confab)
    assert plan["n_known_correct_answered_fit"] == len(known)
    assert plan["caps"]["known_correct_abs_delta_cap"] == ru.C1_KNOWN_CORRECT_ABS_DELTA_CAP
    assert plan["caps"]["hedge_rate_cap"] == ru.C1_HEDGE_RATE_CAP
    assert plan["caps"]["nll_rel_tolerance"] == ru.C1_NLL_REL_TOLERANCE
