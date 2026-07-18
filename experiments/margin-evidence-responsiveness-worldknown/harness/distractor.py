#!/usr/bin/env python3
"""Category-matched false-answer distractor mapping for margin-evidence-
responsiveness-worldknown (M4-WK) (cell.yaml `arms.false_answer_placebo`;
gates.yaml SC0).

CPU-only. For every row in the test population (confab + correct_control +
refused_available -- every row that gets a true_answer/false_answer_placebo
arm), draws ONE donor row_key: a DIFFERENT PopQA row in the SAME `prop`
category, drawn from the FULL PopQA pool (not just the test population --
every `prop` bucket has >= 34 rows dataset-wide, so this is always
resolvable, unlike restricting the donor pool to the smaller test subset).
The draw is a per-row seeded permutation: `random.Random(f"{seed}:{row_key}")`
picks uniformly among the category's OTHER row_keys (excludes self),
mirroring `build_calibration_pool.py`'s own per-stratum seeded-shuffle
convention.

Commits the OPAQUE mapping (row_key -> donor_row_key, NO text) to
`analysis-committed/selection/distractor_mapping.json` BEFORE any generation
(SC0).
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
import popqa_pool  # noqa: E402

SELECTION_DIR = config.EXPERIMENT_DIR / "analysis-committed" / "selection"


def build_category_index(pool: dict[str, dict]) -> dict[str, list[str]]:
    by_category: dict[str, list[str]] = {}
    for rk, row in pool.items():
        by_category.setdefault(row["category"], []).append(rk)
    for cat in by_category:
        by_category[cat].sort()
    return by_category


def draw_donor(row_key: str, category: str, by_category: dict[str, list[str]], seed: int) -> str:
    candidates = [rk for rk in by_category[category] if rk != row_key]
    if not candidates:
        raise SystemExit(f"distractor FAIL: category {category!r} has no OTHER row besides {row_key!r} to donate a false answer.")
    rng = random.Random(f"{seed}:{row_key}")
    return rng.choice(candidates)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.parse_args()

    config.assert_pinned_hashes()

    test_path = SELECTION_DIR / "test_population.json"
    if not test_path.is_file():
        raise SystemExit(f"distractor FAIL: no {test_path}; run selection.py first.")
    test_population = common.load_json(test_path)

    target_row_keys: list[str] = []
    for role_short, row_keys in test_population["row_keys"].items():
        target_row_keys.extend(row_keys)
    target_row_keys = sorted(set(target_row_keys))

    pool = popqa_pool.load_pool()
    by_category = build_category_index(pool)

    mapping: dict[str, str] = {}
    donor_category_check = []
    for rk in target_row_keys:
        category = pool[rk]["category"]
        donor = draw_donor(rk, category, by_category, config.DISTRACTOR_PERMUTATION_SEED)
        mapping[rk] = donor
        donor_category_check.append(pool[donor]["category"] == category)

    if not all(donor_category_check):
        raise SystemExit("distractor FAIL: at least one donor is NOT in the same prop category as its row (bug).")
    self_map = [rk for rk, donor in mapping.items() if donor == rk]
    if self_map:
        raise SystemExit(f"distractor FAIL: {len(self_map)} rows mapped to themselves: {self_map[:5]}")

    payload = {
        "seed": config.DISTRACTOR_PERMUTATION_SEED,
        "rule": "per-row seeded draw of a DIFFERENT same-prop-category PopQA row_key, donor pool = full PopQA (not just test population)",
        "n_rows": len(mapping),
        "mapping": mapping,
    }
    common.write_json(SELECTION_DIR / "distractor_mapping.json", payload)

    print(__import__("json").dumps({"n_rows": len(mapping), "all_same_category": all(donor_category_check), "no_self_map": len(self_map) == 0}, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
