#!/usr/bin/env python3
"""Lab diagnostic for stricter subset selection on existing matched triads."""

from __future__ import annotations

import argparse
import collections
import itertools
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
import sklearn

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from instrument_common import atomic_json, atomic_jsonl, load_jsonl  # noqa: E402
from match_and_gate import (  # noqa: E402
    _full_classifier_features,
    grouped_pairwise_classifier,
    scalar_balance,
)

ROLES = ("known_correct_answered", "confab", "unknown_refused")
MODEL_IDS = ("gemma4_e4b_it", "qwen3_4b_raw_base")
EXPECTED_SKLEARN = "1.7.2"


def _objective(sums: np.ndarray, sums_sq: np.ndarray, n: int) -> float:
    means = sums / n
    variances = np.maximum((sums_sq - sums * sums / n) / (n - 1), 0.0)
    maximum = 0.0
    for a, b in itertools.combinations(range(len(ROLES)), 2):
        denom = np.sqrt((variances[a] + variances[b]) / 2.0)
        values = np.divide(
            np.abs(means[a] - means[b]),
            denom,
            out=(means[a] != means[b]).astype(np.float64),
            where=denom > 0,
        )
        maximum = max(maximum, float(values.max()))
    return maximum


def optimize_subset(
    values: np.ndarray,
    n_select: int,
    seed: int,
    iterations: int,
) -> tuple[list[int], float]:
    rng = np.random.default_rng(seed)
    selected = np.zeros(values.shape[0], dtype=bool)
    selected[rng.choice(values.shape[0], size=n_select, replace=False)] = True
    sums = values[selected].sum(axis=0)
    sums_sq = np.square(values[selected]).sum(axis=0)
    current = _objective(sums, sums_sq, n_select)
    best = current
    best_selected = selected.copy()
    temperature = 0.03
    for _ in range(iterations):
        remove = int(rng.choice(np.flatnonzero(selected)))
        add = int(rng.choice(np.flatnonzero(~selected)))
        candidate_sums = sums - values[remove] + values[add]
        candidate_sums_sq = sums_sq - np.square(values[remove]) + np.square(values[add])
        candidate = _objective(candidate_sums, candidate_sums_sq, n_select)
        if candidate < current or rng.random() < math.exp(
            (current - candidate) / max(temperature, 1e-9)
        ):
            selected[remove] = False
            selected[add] = True
            sums = candidate_sums
            sums_sq = candidate_sums_sq
            current = candidate
            if current < best:
                best = current
                best_selected = selected.copy()
        temperature = max(0.00005, temperature * 0.99994)
    return np.flatnonzero(best_selected).tolist(), best


def optimize_partition(
    values: np.ndarray,
    n_per_partition: int,
    seed: int,
    iterations: int,
) -> tuple[list[int], list[int], float]:
    rng = np.random.default_rng(seed)
    state = np.zeros(values.shape[0], dtype=np.int8)
    order = rng.permutation(values.shape[0])
    state[order[:n_per_partition]] = 1
    state[order[n_per_partition : 2 * n_per_partition]] = 2
    sums = np.asarray([values[state == value].sum(axis=0) for value in (1, 2)])
    sums_sq = np.asarray(
        [np.square(values[state == value]).sum(axis=0) for value in (1, 2)]
    )

    def partition_objective(a: np.ndarray, b: np.ndarray) -> float:
        return max(
            _objective(a[index], b[index], n_per_partition)
            for index in range(2)
        )

    current = partition_objective(sums, sums_sq)
    best = current
    best_state = state.copy()
    temperature = 0.03
    for _ in range(iterations):
        left = int(rng.integers(values.shape[0]))
        candidates = np.flatnonzero(state != state[left])
        right = int(rng.choice(candidates))
        left_state, right_state = int(state[left]), int(state[right])
        candidate_sums = sums.copy()
        candidate_sums_sq = sums_sq.copy()
        if left_state:
            candidate_sums[left_state - 1] -= values[left]
            candidate_sums_sq[left_state - 1] -= np.square(values[left])
        if right_state:
            candidate_sums[right_state - 1] -= values[right]
            candidate_sums_sq[right_state - 1] -= np.square(values[right])
        if left_state:
            candidate_sums[left_state - 1] += values[right]
            candidate_sums_sq[left_state - 1] += np.square(values[right])
        if right_state:
            candidate_sums[right_state - 1] += values[left]
            candidate_sums_sq[right_state - 1] += np.square(values[left])
        candidate = partition_objective(candidate_sums, candidate_sums_sq)
        if candidate < current or rng.random() < math.exp(
            (current - candidate) / max(temperature, 1e-9)
        ):
            state[left], state[right] = right_state, left_state
            sums = candidate_sums
            sums_sq = candidate_sums_sq
            current = candidate
            if current < best:
                best = current
                best_state = state.copy()
        temperature = max(0.00005, temperature * 0.99994)
    return (
        np.flatnonzero(best_state == 1).tolist(),
        np.flatnonzero(best_state == 2).tolist(),
        best,
    )


def optimize_extension(
    values: np.ndarray,
    fixed: list[int],
    n_additional: int,
    seed: int,
    iterations: int,
) -> tuple[list[int], float]:
    rng = np.random.default_rng(seed)
    fixed_mask = np.zeros(values.shape[0], dtype=bool)
    fixed_mask[fixed] = True
    selected = fixed_mask.copy()
    available = np.flatnonzero(~fixed_mask)
    selected[rng.choice(available, size=n_additional, replace=False)] = True
    total = len(fixed) + n_additional
    sums = values[selected].sum(axis=0)
    sums_sq = np.square(values[selected]).sum(axis=0)
    current = _objective(sums, sums_sq, total)
    best = current
    best_selected = selected.copy()
    temperature = 0.03
    for _ in range(iterations):
        remove = int(rng.choice(np.flatnonzero(selected & ~fixed_mask)))
        add = int(rng.choice(np.flatnonzero(~selected)))
        candidate_sums = sums - values[remove] + values[add]
        candidate_sums_sq = sums_sq - np.square(values[remove]) + np.square(values[add])
        candidate = _objective(candidate_sums, candidate_sums_sq, total)
        if candidate < current or rng.random() < math.exp(
            (current - candidate) / max(temperature, 1e-9)
        ):
            selected[remove] = False
            selected[add] = True
            sums = candidate_sums
            sums_sq = candidate_sums_sq
            current = candidate
            if current < best:
                best = current
                best_selected = selected.copy()
        temperature = max(0.00005, temperature * 0.99994)
    return np.flatnonzero(best_selected).tolist(), best


def _role_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts = collections.Counter(str(row.get("role")) for row in rows)
    return dict(sorted(counts.items()))


def diagnose_model(
    model_id: str, n_select: int, seeds: list[int], iterations: int
) -> dict[str, Any]:
    private_root = HERE / "analysis" / model_id
    matched_rows = load_jsonl(private_root / "matched_rows_private.jsonl")
    generation_rows = load_jsonl(private_root / "generation_rows.jsonl")
    source_rows = load_jsonl(HERE / "analysis" / "source" / "rows.jsonl")
    by_triad: dict[str, dict[str, dict[str, Any]]] = {}
    row_index: dict[str, int] = {}
    for index, row in enumerate(matched_rows):
        by_triad.setdefault(row["triad_id"], {})[row["role"]] = row
        row_index[row["row_key"]] = index
    triad_ids = sorted(by_triad)
    triads = [by_triad[triad_id] for triad_id in triad_ids]
    if any(set(triad) != set(ROLES) for triad in triads):
        raise ValueError(f"{model_id}: malformed triad membership")
    if len(triads) < n_select:
        raise ValueError(f"{model_id}: only {len(triads)} triads for floor {n_select}")

    scalar_names = sorted(matched_rows[0]["scalars"])
    scalar_values = np.asarray(
        [
            [
                [triad[role]["scalars"][name] for name in scalar_names]
                for role in ROLES
            ]
            for triad in triads
        ],
        dtype=np.float64,
    )
    scalar_flat = scalar_values.reshape(-1, scalar_values.shape[-1])
    scalar_scale = np.where(scalar_flat.std(axis=0) > 0, scalar_flat.std(axis=0), 1.0)
    scalar_standardized = (
        scalar_values - scalar_flat.mean(axis=0)[None, None, :]
    ) / scalar_scale[None, None, :]
    lexical_values = np.asarray(
        [
            [triad[role]["matching_vector"] for role in ROLES]
            for triad in triads
        ],
        dtype=np.float64,
    )
    lexical_flat = lexical_values.reshape(-1, lexical_values.shape[-1])
    lexical_scale = np.where(
        lexical_flat.std(axis=0) > 0, lexical_flat.std(axis=0), 1.0
    )
    lexical_standardized = (
        lexical_values - lexical_flat.mean(axis=0)[None, None, :]
    ) / lexical_scale[None, None, :]
    balance_values = np.concatenate(
        [scalar_standardized, lexical_standardized], axis=2
    )
    features = _full_classifier_features(
        source_rows, matched_rows, private_root / "surface" / "basis.joblib"
    )

    useful = [row for row in generation_rows if row.get("role") in set(ROLES)]
    known_pairs = {
        row["original_pair_id"]
        for row in useful
        if row["role"] == "known_correct_answered"
    }
    exact_pair_coverage = {
        role: {
            "available": sum(
                row["original_pair_id"] in known_pairs
                for row in useful
                if row["role"] == role
            ),
            "total": sum(row["role"] == role for row in useful),
        }
        for role in ("confab", "unknown_refused")
    }
    category_sets = {
        role: sorted(
            {
                str(row["category_canon"])
                for row in useful
                if row["role"] == role
            }
        )
        for role in ROLES
    }
    common_categories = sorted(set.intersection(*(set(v) for v in category_sets.values())))

    scalar_only_attempts: list[dict[str, Any]] = []
    attempts: list[dict[str, Any]] = []
    partition_attempts: list[dict[str, Any]] = []
    nested_attempts: list[dict[str, Any]] = []
    manifest_root = HERE / "analysis" / "diagnostics" / model_id

    def evaluate(selected: list[int]) -> tuple[list[dict[str, Any]], float, dict[str, float]]:
        selected_ids = {triad_ids[index] for index in selected}
        flat_indices = sorted(
            row_index[row[role]["row_key"]]
            for index, row in enumerate(triads)
            if triad_ids[index] in selected_ids
            for role in ROLES
        )
        flat_rows = [matched_rows[index] for index in flat_indices]
        maximum_smd = scalar_balance(flat_rows)["maximum_pairwise_scalar_abs_smd"]
        pairwise_auc = grouped_pairwise_classifier(
            features[np.asarray(flat_indices, dtype=int)], flat_rows
        )
        return flat_rows, maximum_smd, pairwise_auc

    for seed in seeds:
        scalar_selected, scalar_search_objective = optimize_subset(
            scalar_standardized, n_select, seed, iterations
        )
        scalar_rows, scalar_smd, scalar_pairwise_auc = evaluate(scalar_selected)
        scalar_maximum_auc = max(scalar_pairwise_auc.values())
        atomic_jsonl(
            manifest_root / f"scalar_only_{n_select}_seed_{seed}.jsonl",
            [
                {
                    "row_id": row["row_key"],
                    "triad_id": row["triad_id"],
                    "role": row["role"],
                }
                for row in scalar_rows
            ],
        )
        scalar_only_attempts.append(
            {
                "seed": seed,
                "n_triads": n_select,
                "search_objective": scalar_search_objective,
                "maximum_pairwise_scalar_abs_smd": scalar_smd,
                "pairwise_best_orientation_aurocs": scalar_pairwise_auc,
                "maximum_pairwise_best_orientation_auroc": scalar_maximum_auc,
                "passes_existing_g2_thresholds": scalar_smd <= 0.10
                and scalar_maximum_auc <= 0.60,
            }
        )

        selected, search_objective = optimize_subset(
            balance_values, n_select, seed, iterations
        )
        flat_rows, maximum_smd, pairwise_auc = evaluate(selected)
        maximum_auc = max(pairwise_auc.values())
        atomic_jsonl(
            manifest_root / f"optimized_{n_select}_seed_{seed}.jsonl",
            [
                {
                    "row_id": row["row_key"],
                    "triad_id": row["triad_id"],
                    "role": row["role"],
                }
                for row in flat_rows
            ],
        )
        attempts.append(
            {
                "seed": seed,
                "n_triads": n_select,
                "search_objective": search_objective,
                "maximum_pairwise_scalar_abs_smd": maximum_smd,
                "pairwise_best_orientation_aurocs": pairwise_auc,
                "maximum_pairwise_best_orientation_auroc": maximum_auc,
                "passes_existing_g2_thresholds": maximum_smd <= 0.10
                and maximum_auc <= 0.60,
            }
        )

        fit, held_out, partition_objective = optimize_partition(
            balance_values, n_select // 2, seed, iterations
        )
        partition_results: dict[str, Any] = {}
        for name, selected_partition in (("fit", fit), ("held_out", held_out)):
            part_rows, part_smd, part_aucs = evaluate(selected_partition)
            part_auc = max(part_aucs.values())
            atomic_jsonl(
                manifest_root / f"partitioned_{n_select}_{name}_seed_{seed}.jsonl",
                [
                    {
                        "row_id": row["row_key"],
                        "triad_id": row["triad_id"],
                        "role": row["role"],
                    }
                    for row in part_rows
                ],
            )
            partition_results[name] = {
                "n_triads": len(selected_partition),
                "maximum_pairwise_scalar_abs_smd": part_smd,
                "pairwise_best_orientation_aurocs": part_aucs,
                "maximum_pairwise_best_orientation_auroc": part_auc,
                "passes_existing_g2_thresholds": part_smd <= 0.10
                and part_auc <= 0.60,
            }
        partition_attempts.append(
            {
                "seed": seed,
                "search_objective": partition_objective,
                "partitions": partition_results,
                "both_partitions_pass": all(
                    result["passes_existing_g2_thresholds"]
                    for result in partition_results.values()
                ),
            }
        )

        sensitivity, sensitivity_objective = optimize_subset(
            scalar_standardized, n_select // 2, seed, iterations
        )
        primary, primary_objective = optimize_extension(
            scalar_standardized,
            sensitivity,
            n_select // 2,
            seed + 1000,
            iterations,
        )
        nested_results: dict[str, Any] = {}
        for name, selected_nested in (
            ("primary", primary),
            ("sensitivity_50pct", sensitivity),
        ):
            nested_rows, nested_smd, nested_aucs = evaluate(selected_nested)
            nested_auc = max(nested_aucs.values())
            atomic_jsonl(
                manifest_root / f"nested_{n_select}_{name}_seed_{seed}.jsonl",
                [
                    {
                        "row_id": row["row_key"],
                        "triad_id": row["triad_id"],
                        "role": row["role"],
                    }
                    for row in nested_rows
                ],
            )
            nested_results[name] = {
                "n_triads": len(selected_nested),
                "maximum_pairwise_scalar_abs_smd": nested_smd,
                "pairwise_best_orientation_aurocs": nested_aucs,
                "maximum_pairwise_best_orientation_auroc": nested_auc,
                "passes_existing_g2_thresholds": nested_smd <= 0.10
                and nested_auc <= 0.60,
            }
        nested_attempts.append(
            {
                "seed": seed,
                "sensitivity_search_objective": sensitivity_objective,
                "primary_search_objective": primary_objective,
                "pools": nested_results,
                "both_pools_pass": all(
                    result["passes_existing_g2_thresholds"]
                    for result in nested_results.values()
                ),
            }
        )

    return {
        "model_id": model_id,
        "generation_role_counts": _role_counts(generation_rows),
        "candidate_triads": len(triads),
        "exact_original_pair_known_coverage": exact_pair_coverage,
        "category_levels_by_role": {role: len(values) for role, values in category_sets.items()},
        "common_category_levels_across_three_roles": len(common_categories),
        "scalar_only_subset_attempts": scalar_only_attempts,
        "scalar_only_subset_pass_count": sum(
            attempt["passes_existing_g2_thresholds"]
            for attempt in scalar_only_attempts
        ),
        "optimized_subset_attempts": attempts,
        "optimized_subset_pass_count": sum(
            attempt["passes_existing_g2_thresholds"] for attempt in attempts
        ),
        "balanced_partition_attempts": partition_attempts,
        "balanced_partition_pass_count": sum(
            attempt["both_partitions_pass"] for attempt in partition_attempts
        ),
        "nested_primary_and_50pct_attempts": nested_attempts,
        "nested_primary_and_50pct_pass_count": sum(
            attempt["both_pools_pass"] for attempt in nested_attempts
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-select", type=int, default=128)
    parser.add_argument("--seeds", type=int, nargs="+", default=[20260722, 20260723, 20260724])
    parser.add_argument("--iterations", type=int, default=120_000)
    args = parser.parse_args()
    if sklearn.__version__ != EXPECTED_SKLEARN:
        raise RuntimeError(
            f"scikit-learn {sklearn.__version__} does not match {EXPECTED_SKLEARN}"
        )
    payload = {
        "schema_version": 1,
        "kind": "lab_notebook_matching_feasibility",
        "decision_use": "successor_design_only",
        "n_select": args.n_select,
        "seeds": args.seeds,
        "iterations_per_seed": args.iterations,
        "models": {
            model_id: diagnose_model(
                model_id, args.n_select, args.seeds, args.iterations
            )
            for model_id in MODEL_IDS
        },
    }
    out = HERE / "analysis" / "diagnostics" / "matching_feasibility_summary.json"
    atomic_json(out, payload)
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
