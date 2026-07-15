"""Fresh per-seed random-direction draw for placebo-seed-distribution-census.

One build-time interpretation, recorded here (cell.yaml registers the K seed
INTEGERS directly per family, `census.seed_blocks`, but not an RNG formula):
each seed draws one fresh unit-norm direction via
`unit(np.random.default_rng(seed).normal(size=hidden_dim))` -- the SAME
normal-then-unit construction `direction_fit.fit_directions` uses for its own
embedded random_direction and `rr3-corrected-placebo-replication/
heldout_scorer.py:fresh_random_direction` uses for its core K-seed arm,
WITHOUT any offset (RR3's own core arm applies no offset either, only its
per-dose RIDER seeds do, to keep them disjoint from a shared base seed -- this
census's seeds are already distinct, pre-registered, per-family top-level
values, so no offset is needed or would be reproducible from cell.yaml
alone).
"""

from __future__ import annotations

import numpy as np

from common import unit


def fresh_random_direction(seed: int, hidden_dim: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return unit(rng.normal(size=hidden_dim))
