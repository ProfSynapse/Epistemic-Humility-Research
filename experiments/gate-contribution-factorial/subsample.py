#!/usr/bin/env python3
"""Per-family fixed S_confab=300 subsample draw for gate-contribution-
factorial (cell.yaml `subsample.confab.random_condition_arms`; gates.yaml
`sc0_provenance_and_staging.subsample_committed_before_generation`).

Draws, per family, a fixed random subsample of S_confab=300 confab rows from
the FULL confab pool (`row_pool.heldout_row_keys_by_role`) via a SEEDED
permutation (seed 46260714), BEFORE any generation or grading. The SAME
S rows are shared by BOTH K=5-multiplied random-condition arms
(`true_gate__random`, `permuted_gate__random`) and every seed within each
(AMENDMENT.md "Populations, subsample, and grading depth"). The c_hat-
condition arms (baseline, true_gate__c_hat, permuted_gate__c_hat) are graded
at the FULL confab pool, not this subsample.

Draw method: ONE `random.Random(seed)` instance, advanced sequentially across
families in a FIXED sorted order (qwen35_4b, mistral7b_v03), each family's
pool sorted by row_key before shuffling -- mirrors census's own
`subsample.py` convention (byte-identical structure, ported).

Commits the row_key list (bare row_key carries no question/answer content,
this repo's standing convention) to
`analysis-committed/subsample_manifest.json` BEFORE `run_factorial.py` may be
invoked (SC0 gate).
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
import row_pool  # noqa: E402

COMMITTED = HERE / "analysis-committed"

FAMILY_ORDER = ("qwen35_4b", "mistral7b_v03")


def draw_subsample(seed: int = config.SUBSAMPLE_PERMUTATION_SEED, n: int = config.SUBSAMPLE_CONFAB_ROWS_PER_FAMILY) -> dict[str, list[str]]:
    rng = random.Random(seed)
    out: dict[str, list[str]] = {}
    for family in FAMILY_ORDER:
        pool = row_pool.heldout_row_keys_by_role(family)["confab"]  # already sorted
        pool_copy = pool[:]
        rng.shuffle(pool_copy)
        take = min(n, len(pool_copy))
        out[family] = sorted(pool_copy[:take])
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.parse_args()

    subsample = draw_subsample()

    manifest = {
        "permutation_seed": config.SUBSAMPLE_PERMUTATION_SEED,
        "rows_per_family_requested": config.SUBSAMPLE_CONFAB_ROWS_PER_FAMILY,
        "population": "confab",
        "applies_to_arms": ["true_gate__random", "permuted_gate__random"],
        "family_order": list(FAMILY_ORDER),
        "families": {
            family: {
                "n_drawn": len(keys),
                "full_confab_pool_n": config.HELDOUT_POOL[family]["confab"],
                "row_keys": keys,
            }
            for family, keys in subsample.items()
        },
    }
    common.write_json(COMMITTED / "subsample_manifest.json", manifest)
    for family, keys in subsample.items():
        print(f"[subsample] {family}: n={len(keys)} first3={keys[:3]}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
