"""SC1 (magnitude-matching and randomness) checks for
gate-contribution-factorial (gates.yaml `sc1_magnitude_matching`).

Two independent checks per random seed (applies to the K=5
`true_gate__random`/`permuted_gate__random` seeds; the `c_hat` write has no
randomness check, only a readback check):

  1. Randomness bar (CPU-only, pure vector math): |cos(r_hat, c_hat)| <= 0.015
     AND |cos(r_hat, u_d)| <= 0.015 (RR3 red-team bar, cell.yaml
     `write.randomness_bar_cos`).
  2. Readback tolerance (requires a real GPU erase-write pass):
     |readback_measured - target| / target <= 0.005 (cell.yaml
     `write.readback_tolerance_rel`), target = the family's
     `setpoint_dose_abs` for BOTH the c_hat write and every random-seed write
     (gates.yaml sc1: "every dosed write (c_hat and every random seed) is an
     erase-write to the family setpoint").

Void-and-redraw ledger: a seed failing EITHER check is voided before grading
and redrawn from the next pre-registered seed (gates.yaml
`sc1_magnitude_matching.on_fail`); the void is recorded. Build-time
interpretation, mirroring census's own convention: the "next pre-registered
seed" on a void is `family_seed_floor + K_SEEDS_PER_FAMILY + attempt`
(qwen's first redraw is 44000006), staying inside that family's own disjoint
1,000,000-wide seed block (config.RANDOM_SEED_BLOCKS) and never colliding
with the other family's seeds, the permuted-gate seeds (20260713/20260715),
or the subsample seed (46260714).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import config  # noqa: E402
import common  # noqa: E402
from direction_draw import fresh_random_direction  # noqa: E402

RANDOMNESS_BAR_COS = config.RANDOMNESS_BAR_COS
READBACK_TOLERANCE_REL = config.READBACK_TOLERANCE_REL


def redraw_seed(family: str, attempt: int) -> int:
    """attempt=1 is the FIRST redraw after the K=5 primary seeds void."""
    floor = min(config.RANDOM_SEED_BLOCKS[family])
    return floor + config.K_SEEDS_PER_FAMILY + attempt


def check_randomness_bar(seed: int, hidden_dim: int, c_hat: np.ndarray, u_d: np.ndarray) -> dict[str, Any]:
    direction = fresh_random_direction(seed, hidden_dim)
    cos_c_hat = common.cos_sim(direction, c_hat)
    cos_u_d = common.cos_sim(direction, u_d)
    passed = abs(cos_c_hat) <= RANDOMNESS_BAR_COS and abs(cos_u_d) <= RANDOMNESS_BAR_COS
    return {
        "seed": seed, "abs_cos_to_c_hat": abs(cos_c_hat), "abs_cos_to_u_d": abs(cos_u_d),
        "bar": RANDOMNESS_BAR_COS, "passed": passed,
    }


def check_readback(seed: int, family: str, readback_measured: float | None, target: float) -> dict[str, Any]:
    if readback_measured is None:
        return {"seed": seed, "family": family, "readback_measured": None, "target": target, "passed": False, "reason": "no_readback_recorded"}
    delta = abs(readback_measured - target)
    rel_delta = delta / abs(target)
    return {
        "seed": seed, "family": family, "readback_measured": readback_measured, "target": target,
        "abs_delta": delta, "rel_delta": rel_delta, "tolerance_rel": READBACK_TOLERANCE_REL,
        "passed": rel_delta <= READBACK_TOLERANCE_REL,
    }


def resolve_seed_ledger(
    family: str, primary_seeds: list[int], hidden_dim: int, c_hat: np.ndarray, u_d: np.ndarray,
    readback_by_seed: dict[int, float] | None = None, target: float | None = None,
    max_redraws: int = 300,
) -> dict[str, Any]:
    """Walks the primary K=5 seeds in order; any seed failing the randomness
    bar (and, if readback is supplied, the readback tolerance) is voided and
    replaced by `redraw_seed`. Ported (logic) from census's own
    `sc1_checks.resolve_seed_ledger`."""
    accepted: list[int] = []
    voids: list[dict[str, Any]] = []
    attempt = 0
    candidates = list(primary_seeds)
    i = 0
    while len(accepted) < len(primary_seeds):
        if i >= len(candidates):
            attempt += 1
            if attempt > max_redraws:
                raise SystemExit(f"SC1 FAIL ({family}): exceeded {max_redraws} redraws; check the direction/setpoint wiring, this is not expected from seed noise alone.")
            candidates.append(redraw_seed(family, attempt))
        seed = candidates[i]
        rand_check = check_randomness_bar(seed, hidden_dim, c_hat, u_d)
        rb_check = None
        seed_passed = rand_check["passed"]
        if seed_passed and readback_by_seed is not None and target is not None:
            rb_check = check_readback(seed, family, readback_by_seed.get(seed), target)
            seed_passed = seed_passed and rb_check["passed"]
        if seed_passed:
            accepted.append(seed)
        else:
            voids.append({"seed": seed, "randomness_bar": rand_check, "readback": rb_check})
        i += 1
    return {
        "family": family, "accepted_seeds": accepted, "n_accepted": len(accepted),
        "voids": voids, "n_voids": len(voids),
    }
