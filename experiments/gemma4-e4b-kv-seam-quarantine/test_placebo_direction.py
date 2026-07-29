"""CPU-only unit tests for placebo_direction.py (cell.yaml
placebo_direction_control). No torch/model import; every test here must be
runnable without a GPU or a checkpoint download.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import placebo_direction as pd  # noqa: E402


HIDDEN_DIM = 2560  # families/gemma4-e4b.yaml hidden_size


def _fixed_c_hat_u_d(hidden_dim: int = HIDDEN_DIM):
    rng = np.random.default_rng(12345)
    c_hat = pd.unit(rng.normal(size=hidden_dim))
    u_d = pd.unit(rng.normal(size=hidden_dim))
    return c_hat, u_d


# ---------------------------------------------------------------------------
# (a) reproducibility from the registered seeds alone
# ---------------------------------------------------------------------------


def test_fresh_random_direction_reproducible():
    d1 = pd.fresh_random_direction(42, HIDDEN_DIM)
    d2 = pd.fresh_random_direction(42, HIDDEN_DIM)
    assert np.array_equal(d1, d2)
    assert abs(np.linalg.norm(d1) - 1.0) < 1e-9


def test_draw_seed_formula():
    # cell.yaml direction_construction.rng: SEED_BASE + hidden_dim + hs_index + K_index
    assert pd.draw_seed(2560, 22, 0) == pd.SEED_BASE + 2560 + 22 + 0
    assert pd.draw_seed(2560, 22, 3) == pd.SEED_BASE + 2560 + 22 + 3
    assert pd.draw_seed(2560, 24, 0) != pd.draw_seed(2560, 22, 0)  # site-scoped


def test_redraw_seed_formula_and_no_collision_with_primary_draws():
    k = 5
    redraw1 = pd.redraw_seed(2560, 22, 1, k=k)
    assert redraw1 == pd.SEED_BASE + 2560 + 22 + k + 1
    primary_seeds = {pd.draw_seed(2560, 22, i) for i in range(k)}
    redraw_seeds = {pd.redraw_seed(2560, 22, a, k=k) for a in range(1, 10)}
    assert primary_seeds.isdisjoint(redraw_seeds)


def test_screen_k_accepted_directions_reproducible_end_to_end():
    c_hat, u_d = _fixed_c_hat_u_d()
    accepted1, ledger1 = pd.screen_k_accepted_directions(HIDDEN_DIM, 22, c_hat, u_d, k=5)
    accepted2, ledger2 = pd.screen_k_accepted_directions(HIDDEN_DIM, 22, c_hat, u_d, k=5)
    assert len(accepted1) == 5
    for a, b in zip(accepted1, accepted2):
        assert np.array_equal(a, b)
    assert ledger1 == ledger2


# ---------------------------------------------------------------------------
# (b) the screen rejects a planted high-cosine draw
# ---------------------------------------------------------------------------


def test_sc1_screen_rejects_high_cosine_to_c_hat():
    c_hat, u_d = _fixed_c_hat_u_d()
    # A direction identical to c_hat has cosine 1.0 >> SC1_BAR against c_hat.
    check = pd.sc1_screen(c_hat, c_hat, u_d)
    assert check["passed"] is False
    assert abs(check["cos_c_hat"] - 1.0) < 1e-9


def test_sc1_screen_rejects_high_cosine_to_u_d():
    c_hat, u_d = _fixed_c_hat_u_d()
    check = pd.sc1_screen(u_d, c_hat, u_d)
    assert check["passed"] is False
    assert abs(check["cos_u_d"] - 1.0) < 1e-9


def test_screen_k_accepted_directions_voids_a_planted_high_cosine_primary_draw():
    """Force the FIRST primary draw at a site to equal c_hat (by constructing
    c_hat as that exact draw), so the ledger must record a void for it and
    then continue drawing until K accept.

    hidden_dim=2560 matches the registered gemma4-e4b hidden_size: at this
    dimension the per-draw SC1 pass rate is ~30-35% (cell.yaml
    randomness_quality_bar.why_a_redraw_ledger_is_mandatory), so k=1 clears
    within max_redraws=300 with overwhelming probability; a small hidden_dim
    would depress the pass rate enough to make exhaustion the flaky case
    instead of the planted void.
    """
    hidden_dim = HIDDEN_DIM
    hs_index = 900001  # a site index that will never collide with a real one
    planted_seed = pd.draw_seed(hidden_dim, hs_index, 0)
    planted_direction = pd.fresh_random_direction(planted_seed, hidden_dim)
    # u_d orthogonal-ish reference, unrelated to the planted draw.
    u_d = pd.unit(np.random.default_rng(7).normal(size=hidden_dim))

    accepted, ledger = pd.screen_k_accepted_directions(
        hidden_dim, hs_index, planted_direction, u_d, k=1, max_redraws=300
    )
    assert len(accepted) == 1
    first_entry = ledger[0]
    assert first_entry["seed"] == planted_seed
    assert first_entry["draw_kind"] == "primary"
    assert first_entry["decision"] == "void"
    assert abs(first_entry["cos_c_hat"] - 1.0) < 1e-9
    # At least one void occurred (the planted one); some later draws may also
    # void by chance, all of which must be recorded too.
    assert any(e["decision"] == "void" for e in ledger)


def test_redraw_exhaustion_raises_not_run():
    """An SC1 bar of 0.0 (nothing but the exact zero vector could ever pass,
    which unit() forbids) forces every draw to void, so max_redraws must be
    exhausted and PlaceboRedrawExhausted raised -- never a relaxed bar."""
    hidden_dim = 32
    hs_index = 900002
    c_hat = pd.unit(np.random.default_rng(1).normal(size=hidden_dim))
    u_d = pd.unit(np.random.default_rng(2).normal(size=hidden_dim))

    def _impossible_screen(direction, c_hat, u_d, bar=0.0):
        return {"cos_c_hat": 1.0, "cos_u_d": 1.0, "bar": bar, "passed": False}

    orig = pd.sc1_screen
    pd.sc1_screen = _impossible_screen
    try:
        with pytest.raises(pd.PlaceboRedrawExhausted):
            pd.screen_k_accepted_directions(
                hidden_dim, hs_index, c_hat, u_d, k=1, max_redraws=5
            )
    finally:
        pd.sc1_screen = orig


# ---------------------------------------------------------------------------
# (c) the ledger records voids (and accepts), and is written to disk
# ---------------------------------------------------------------------------


def test_ledger_records_both_accept_and_void(tmp_path):
    c_hat, u_d = _fixed_c_hat_u_d()
    accepted, ledger = pd.screen_k_accepted_directions(HIDDEN_DIM, 22, c_hat, u_d, k=5)
    decisions = {e["decision"] for e in ledger}
    assert "accept" in decisions
    n_accept = sum(1 for e in ledger if e["decision"] == "accept")
    assert n_accept == 5
    assert len(ledger) >= 5  # >= because at least some draws may void first

    out_path = tmp_path / "placebo_draw_ledger.seam_pair.json"
    pd.write_ledger(out_path, ledger, hs_index=22, hidden_dim=HIDDEN_DIM)
    payload = json.loads(out_path.read_text())
    assert payload["hs_index"] == 22
    assert payload["hidden_dim"] == HIDDEN_DIM
    assert payload["n_accepted"] == 5
    assert payload["n_draws"] == len(ledger)
    assert payload["n_voided"] == len(ledger) - 5
    assert payload["draws"] == ledger


# ---------------------------------------------------------------------------
# sigma/gain magnitude-matching regression guard (known factorial defect:
# gate-contribution-factorial/run_factorial.py:270-284 once realized gain**2
# instead of gain*sigma). Mirrors test_factorial_smoke.py's own pinning.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("dose_target", [28.5068, 50.5311])
def test_placebo_write_params_sigma_is_one_gain_equals_dose(dose_target):
    sigma, gain = pd.placebo_write_params(dose_target)
    assert sigma == 1.0
    assert gain == dose_target
    assert sigma != gain, "sigma and gain must not be conflated (the gain-squared defect)"
    assert abs(sigma * gain - dose_target) < 1e-9
    assert gain ** 2 != dose_target  # squaring would NOT reproduce the registered dose
