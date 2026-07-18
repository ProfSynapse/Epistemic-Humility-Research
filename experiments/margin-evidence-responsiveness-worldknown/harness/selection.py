#!/usr/bin/env python3
"""Native-fit-split + test-population selection for margin-evidence-
responsiveness-worldknown (M4-WK) (cell.yaml `population.selection`;
gates.yaml SC0/SC3).

CPU-only. Requires the committed census
(analysis-committed/census/qwen35_4b_worldknown_census.jsonl). Draw method
(cell.yaml `population.selection.rule`, mirroring M1's `subsample.py`
convention): ONE `random.Random(seed)` instance, advanced sequentially
across role groups in a FIXED order (confab, correct, refused), each role's
row_keys sorted before shuffling. The NATIVE FIT SPLIT is reserved FIRST
(disjoint), then the TEST population is drawn from the remainder.

Commits OPAQUE row_key lists ONLY (no question/answer/category content) to
`analysis-committed/selection/{native_fit_split,test_population}.json`
BEFORE any direction fit or channel generation (SC0 gate). Asserts
disjointness between the two partitions (SC3).
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import config  # noqa: E402
import common  # noqa: E402

COMMITTED = config.EXPERIMENT_DIR / "analysis-committed"
CENSUS_PATH = COMMITTED / "census" / "qwen35_4b_worldknown_census.jsonl"
SELECTION_DIR = COMMITTED / "selection"

ROLE_ORDER = ("confab_on_answerable", "correct_on_answerable", "refused_on_answerable")
ROLE_SHORT = {"confab_on_answerable": "confab", "correct_on_answerable": "correct", "refused_on_answerable": "refused"}


def load_role_groups() -> dict[str, list[str]]:
    if not CENSUS_PATH.is_file():
        raise SystemExit(f"selection FAIL: no committed census at {CENSUS_PATH}; run census.py first.")
    rows = common.load_jsonl(CENSUS_PATH)
    groups: dict[str, list[str]] = {role: [] for role in ROLE_ORDER}
    for r in rows:
        if r["role"] in groups:
            groups[r["role"]].append(r["row_key"])
    for role in ROLE_ORDER:
        groups[role].sort()
    return groups


def draw_partitions(groups: dict[str, list[str]], seed: int = config.SELECTION_PERMUTATION_SEED) -> dict[str, dict[str, list[str]]]:
    rng = random.Random(seed)
    fit_split: dict[str, list[str]] = {}
    test_population: dict[str, list[str]] = {}
    for role in ROLE_ORDER:
        short = ROLE_SHORT[role]
        pool = groups[role][:]
        rng.shuffle(pool)
        fit_target = config.NATIVE_FIT_SPLIT_TARGETS[short]
        if len(pool) < fit_target:
            raise SystemExit(f"selection FAIL: role {role!r} has {len(pool)} rows, below native_fit_split target {fit_target}")
        fit_rows = sorted(pool[:fit_target])
        remainder = pool[fit_target:]
        if short == "confab":
            test_target = config.TEST_CONFAB_N
        elif short == "correct":
            test_target = config.TEST_CORRECT_N
        else:
            test_target = len(remainder)  # refused: "as available" (census remainder)
        if len(remainder) < test_target:
            raise SystemExit(f"selection FAIL: role {role!r} remainder has {len(remainder)} rows, below test target {test_target}")
        test_rows = sorted(remainder[:test_target])
        fit_split[short] = fit_rows
        test_population[short] = test_rows
    return {"native_fit_split": fit_split, "test_population": test_population}


def assert_disjoint(partitions: dict[str, dict[str, list[str]]]) -> dict:
    fit_all: set[str] = set()
    for v in partitions["native_fit_split"].values():
        fit_all |= set(v)
    test_all: set[str] = set()
    for v in partitions["test_population"].values():
        test_all |= set(v)
    intersection = sorted(fit_all & test_all)
    result = {
        "n_fit_split": len(fit_all), "n_test_population": len(test_all),
        "n_intersection": len(intersection), "intersection_sample": intersection[:10],
        "passed": len(intersection) == 0,
    }
    if not result["passed"]:
        raise SystemExit(f"selection FAIL: native_fit_split and test_population are NOT disjoint: {result}")
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.parse_args()

    config.assert_pinned_hashes()

    groups = load_role_groups()
    group_sizes = {role: len(v) for role, v in groups.items()}
    partitions = draw_partitions(groups)
    disjoint = assert_disjoint(partitions)

    SELECTION_DIR.mkdir(parents=True, exist_ok=True)
    fit_payload = {
        "seed": config.SELECTION_PERMUTATION_SEED, "targets": config.NATIVE_FIT_SPLIT_TARGETS,
        "counts": {k: len(v) for k, v in partitions["native_fit_split"].items()},
        "row_keys": partitions["native_fit_split"],
    }
    test_payload = {
        "seed": config.SELECTION_PERMUTATION_SEED,
        "targets": {"confab": config.TEST_CONFAB_N, "correct": config.TEST_CORRECT_N, "refused": "as_available"},
        "counts": {k: len(v) for k, v in partitions["test_population"].items()},
        "row_keys": partitions["test_population"],
    }
    common.write_json(SELECTION_DIR / "native_fit_split.json", fit_payload)
    common.write_json(SELECTION_DIR / "test_population.json", test_payload)
    common.write_json(SELECTION_DIR / "disjointness_check.json", disjoint)

    census_role_totals = group_sizes
    summary = {
        "census_role_totals": census_role_totals,
        "native_fit_split_counts": fit_payload["counts"],
        "test_population_counts": test_payload["counts"],
        "disjointness_check": disjoint,
    }
    print(__import__("json").dumps(summary, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
