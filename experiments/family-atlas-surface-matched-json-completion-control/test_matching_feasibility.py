from __future__ import annotations

import numpy as np

from diagnose_matching_feasibility import (
    optimize_extension,
    optimize_partition,
    optimize_subset,
)


def _values() -> np.ndarray:
    rng = np.random.default_rng(11)
    return rng.normal(size=(24, 3, 5))


def test_optimize_subset_is_deterministic_and_unique() -> None:
    first, first_score = optimize_subset(_values(), 8, seed=19, iterations=300)
    second, second_score = optimize_subset(_values(), 8, seed=19, iterations=300)

    assert first == second
    assert first_score == second_score
    assert len(first) == len(set(first)) == 8


def test_optimize_partition_returns_disjoint_fixed_size_sets() -> None:
    left, right, score = optimize_partition(
        _values(), n_per_partition=7, seed=23, iterations=300
    )

    assert len(left) == len(set(left)) == 7
    assert len(right) == len(set(right)) == 7
    assert set(left).isdisjoint(right)
    assert np.isfinite(score)


def test_optimize_extension_retains_fixed_subset() -> None:
    fixed = [1, 5, 9, 13]
    selected, score = optimize_extension(
        _values(), fixed=fixed, n_additional=6, seed=29, iterations=300
    )

    assert len(selected) == len(set(selected)) == 10
    assert set(fixed).issubset(selected)
    assert np.isfinite(score)
