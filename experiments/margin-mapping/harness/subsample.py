#!/usr/bin/env python3
"""Per-family confab subsample + full known-pool ID commit for margin-mapping
(M1) (cell.yaml `population`; gates.yaml `SC0_provenance_staging`).

Draws, per family, a fixed random subsample of n=400 confab rows from the
FULL confab pool (`row_pool.heldout_row_keys_by_role`) via a SEEDED
permutation (seed 48260714 -- a NEW, distinct seed from the factorial's own
subsample seed 46260714; "lineage 46260714/47260714" per cell.yaml's
comment, but a different draw), BEFORE any generation. Also records the
FULL known-correct pool (all 360 qwen / 382 mistral row_keys, not a subsample
-- AMENDMENT.md: "the FULL known-correct pool ... knowns are the scarce
population and the H4 retrodiction target").

Draw method: ONE `random.Random(seed)` instance, advanced sequentially
across families in a FIXED sorted order (qwen35_4b, mistral7b_v03), each
family's confab pool sorted by row_key before shuffling -- mirrors the
factorial's own `subsample.py` convention (ported, logic-identical shuffle
mechanics; different seed and n).

Commits OPAQUE row_key lists ONLY (no question/answer content, this repo's
standing containment convention) to
`analysis-committed/subsample_ids_<family>.json` BEFORE any generation may be
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

EXPERIMENT_DIR = HERE.parent
COMMITTED = EXPERIMENT_DIR / "analysis-committed"

FAMILY_ORDER = ("qwen35_4b", "mistral7b_v03")


def draw_confab_subsample(
    seed: int = config.SUBSAMPLE_PERMUTATION_SEED,
    n: int = config.SUBSAMPLE_CONFAB_N_PER_FAMILY,
) -> dict[str, list[str]]:
    rng = random.Random(seed)
    out: dict[str, list[str]] = {}
    for family in FAMILY_ORDER:
        pool = row_pool.heldout_row_keys_by_role(family)["confab"]  # already sorted
        pool_copy = pool[:]
        rng.shuffle(pool_copy)
        take = min(n, len(pool_copy))
        out[family] = sorted(pool_copy[:take])
    return out


def known_full_ids() -> dict[str, list[str]]:
    return {family: row_pool.heldout_row_keys_by_role(family)["known_correct_answered"] for family in FAMILY_ORDER}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.parse_args()

    confab_subsample = draw_confab_subsample()
    known = known_full_ids()

    for family in FAMILY_ORDER:
        expected_known_n = config.POOLS[family]["known_full"]
        if len(known[family]) != expected_known_n:
            raise SystemExit(
                f"subsample FAIL ({family}): known pool has {len(known[family])} rows, "
                f"cell.yaml registers known_full={expected_known_n}."
            )
        payload = {
            "family": family,
            "confab_subsample": {
                "permutation_seed": config.SUBSAMPLE_PERMUTATION_SEED,
                "n_requested": config.SUBSAMPLE_CONFAB_N_PER_FAMILY,
                "n_drawn": len(confab_subsample[family]),
                "full_confab_pool_n": config.POOLS[family]["confab_full"],
                "row_keys": confab_subsample[family],
            },
            "known_full": {
                "n": len(known[family]),
                "row_keys": known[family],
            },
        }
        common.write_json(COMMITTED / f"subsample_ids_{family}.json", payload)
        print(
            f"[subsample] {family}: confab n={len(confab_subsample[family])} "
            f"first3={confab_subsample[family][:3]} | known n={len(known[family])} "
            f"first3={known[family][:3]}",
            flush=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
