"""Direction-specificity control (P1/P2): random-direction construction, the
SC1 randomness-quality bar, and the void-and-redraw ledger.

Registered in `cell.yaml placebo_direction_control` (`direction_construction`,
`randomness_quality_bar` id SC1, `k_number_of_draws`, `magnitude_matching`) and
`AMENDMENT.md` "Pre-sign record: the direction-specificity control (P1, P2,
G3)". Pure numpy, no torch/model import anywhere in this module, so the draw
and screen logic is exercisable on CPU in isolation from any generation code
(run_contrast.py is the caller that wires the accepted directions into an
actual dosed pass).

Every seed used here is reproducible from (hidden_dim, hs_index, seed_base)
alone -- no seed is chosen after a result is seen (cell.yaml
`direction_construction.seeds_are_registered_here`).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

#: cell.yaml direction_construction.seed_base
SEED_BASE = 20260725
#: cell.yaml k_number_of_draws.K, CLOSED by the lead on 2026-07-25.
K = 5
#: cell.yaml randomness_quality_bar.rule
SC1_BAR = 0.015
#: cell.yaml randomness_quality_bar.max_redraws
MAX_REDRAWS = 300


class PlaceboRedrawExhausted(RuntimeError):
    """Raised when `max_redraws` is exhausted before K directions clear SC1.

    Per cell.yaml `randomness_quality_bar.ledger`: exhausting max_redraws
    without K accepted directions is a NOT-RUN for that arm, never a
    relaxation of the bar. Callers catch this and record NOT-RUN; they must
    not loosen SC1_BAR or MAX_REDRAWS to make it stop firing.
    """


def unit(v: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(v))
    if n == 0.0:
        raise ValueError("cannot normalize a zero vector")
    return v / n


def fresh_random_direction(seed: int, hidden_dim: int) -> np.ndarray:
    """r_hat = unit(rng.normal(size=hidden_dim)).

    cell.yaml direction_construction.unit_vectors: "r_hat =
    unit(rng.normal(size=hidden_dim))"; .rng: "np.random.default_rng(...)".
    """
    rng = np.random.default_rng(seed)
    return unit(rng.normal(size=hidden_dim))


def cos_sim(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def draw_seed(hidden_dim: int, hs_index: int, k_index: int,
              seed_base: int = SEED_BASE) -> int:
    """Seed for the `k_index`-th (0-based) PRIMARY draw at this site.

    cell.yaml direction_construction.rng: "SEED_BASE + hidden_dim + hs_index
    + K_index".
    """
    if k_index < 0:
        raise ValueError("k_index is 0-based; first primary draw is k_index=0")
    return seed_base + hidden_dim + hs_index + k_index


def redraw_seed(hidden_dim: int, hs_index: int, attempt: int, k: int = K,
                seed_base: int = SEED_BASE) -> int:
    """Seed for the `attempt`-th (1-based) redraw at this site.

    cell.yaml randomness_quality_bar.redraw_rule: "redraw_seed(attempt) =
    seed_base + hidden_dim + hs_index + K + attempt". Offsetting by `k`
    (the fixed K, not a running k_index) keeps every redraw seed clear of the
    K primary-draw seeds (which occupy k_index in [0, K)), mirroring
    placebo-seed-distribution-census/sc1_checks.py's own redraw_seed pattern.
    """
    if attempt < 1:
        raise ValueError("attempt is 1-based; the first redraw is attempt=1")
    return seed_base + hidden_dim + hs_index + k + attempt


def sc1_screen(direction: np.ndarray, c_hat: np.ndarray, u_d: np.ndarray,
               bar: float = SC1_BAR) -> dict:
    """cell.yaml randomness_quality_bar.rule: "|cos(r_hat, c_hat)| <= bar AND
    |cos(r_hat, u_d)| <= bar"."""
    cos_c_hat = cos_sim(direction, c_hat)
    cos_u_d = cos_sim(direction, u_d)
    passed = abs(cos_c_hat) <= bar and abs(cos_u_d) <= bar
    return {"cos_c_hat": cos_c_hat, "cos_u_d": cos_u_d, "bar": bar, "passed": passed}


def screen_k_accepted_directions(
    hidden_dim: int, hs_index: int, c_hat: np.ndarray, u_d: np.ndarray, *,
    k: int = K, seed_base: int = SEED_BASE, max_redraws: int = MAX_REDRAWS,
) -> tuple[list[np.ndarray], list[dict]]:
    """Draw and SC1-screen directions until `k` are accepted or
    `max_redraws` is exhausted.

    Returns `(accepted_directions, ledger)`. `ledger` holds one entry per
    draw, accepted AND voided, in draw order -- the void-and-redraw ledger
    cell.yaml requires be written for every arm (`randomness_quality_bar.
    ledger`). Raises `PlaceboRedrawExhausted` rather than accepting a draw
    that fails SC1 (see that exception's docstring).
    """
    if k < 1:
        raise ValueError("k must be >= 1")
    accepted: list[np.ndarray] = []
    ledger: list[dict] = []
    k_index = 0
    attempt = 0
    while len(accepted) < k:
        if k_index < k:
            seed = draw_seed(hidden_dim, hs_index, k_index, seed_base)
            draw_kind = "primary"
            this_k_index = k_index
            k_index += 1
            this_attempt = None
        else:
            attempt += 1
            if attempt > max_redraws:
                raise PlaceboRedrawExhausted(
                    f"hs{hs_index}: exceeded max_redraws={max_redraws} before "
                    f"{k} directions cleared SC1 ({len(accepted)} accepted so "
                    "far). This is a NOT-RUN for this arm's placebo control, "
                    "not a relaxation of the SC1 bar."
                )
            seed = redraw_seed(hidden_dim, hs_index, attempt, k, seed_base)
            draw_kind = "redraw"
            this_k_index = None
            this_attempt = attempt

        direction = fresh_random_direction(seed, hidden_dim)
        check = sc1_screen(direction, c_hat, u_d)
        entry = {
            "seed": seed, "draw_kind": draw_kind, "k_index": this_k_index,
            "attempt": this_attempt, "cos_c_hat": check["cos_c_hat"],
            "cos_u_d": check["cos_u_d"], "bar": check["bar"],
            "decision": "accept" if check["passed"] else "void",
        }
        ledger.append(entry)
        if check["passed"]:
            accepted.append(direction)
    return accepted, ledger


def write_ledger(path: str | Path, ledger: list[dict], *, hs_index: int,
                 hidden_dim: int, k: int = K, max_redraws: int = MAX_REDRAWS) -> None:
    """Write the void-and-redraw ledger to
    `analysis-committed/gemma4-e4b/placebo_draw_ledger.<site_set>.json`
    (cell.yaml randomness_quality_bar.ledger). The caller resolves the
    site-set-scoped filename via `family_config.site_set_artifact`; this
    function only writes the payload."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "hs_index": hs_index, "hidden_dim": hidden_dim, "sc1_bar": SC1_BAR,
        "k": k, "max_redraws": max_redraws, "n_draws": len(ledger),
        "n_accepted": sum(1 for e in ledger if e["decision"] == "accept"),
        "n_voided": sum(1 for e in ledger if e["decision"] == "void"),
        "draws": ledger,
    }
    p.write_text(json.dumps(payload, indent=2))


def placebo_write_params(dose_target: float) -> tuple[float, float]:
    """cell.yaml magnitude_matching.convention: "sigma = 1.0, so the
    realized gain equals the arm's calibrated absolute dose".

    Mirrors `gate-contribution-factorial/run_factorial.py`'s
    `random_write_params` exactly (sigma=1.0, gain=setpoint). This
    deliberately does NOT reproduce that file's known defect
    (`run_factorial.py:270-284`, once passing gain as the sigma argument
    too and realizing gain**2 instead of gain*sigma); see
    `test_placebo_direction.py` for the pinned regression guard.
    """
    sigma = 1.0
    gain = float(dose_target)
    return sigma, gain
