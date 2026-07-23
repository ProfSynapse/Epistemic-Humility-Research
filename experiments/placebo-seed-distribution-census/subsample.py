#!/usr/bin/env python3
"""Per-family fixed S=300 subsample draw for placebo-seed-distribution-census
(cell.yaml `census.subsample`; gates.yaml `sc0_provenance_and_staging.
subsample_committed_before_generation`).

Draws, per family, a fixed random subsample of S=300 confab rows from the
paired confab pool (`row_pool.paired_confab_row_keys`) via a SEEDED
permutation (seed 40260714), BEFORE any generation or grading. The SAME S
rows are shared across the family's baseline reuse and all K=15 dosed seeds
(AMENDMENT.md "Per-seed subsample"). llama's pool (872) is capped at
min(300, 872) = 300 (cell.yaml `llama_cap_note`).

Commits the opaque-id (here: bare row_key, since containment only forbids
QUESTION/ANSWER/ALIAS/TOKEN text -- row_key alone carries no question content,
matching this repo's convention elsewhere of committing row_key/role/split/
source/category_canon in ID-only manifests) list to
`analysis-committed/subsample_manifest.json` BEFORE `run_census.py` may be
invoked (SC0 gate).

Draw method: ONE `random.Random(seed)` instance, advanced sequentially across
families in a FIXED sorted order (qwen35_4b, mistral7b_v03, llama32_3b), each
family's pool sorted by row_key before shuffling -- so the draw depends only
on (seed, the registered family order, the row pool), never process/OS
iteration order. Mirrors the QL-style subsample convention this repo already
uses (`rr3-corrected-placebo-replication/heldout_scorer.py:
rider_confab_subsample`, `abstention-wide-instrument-calibration/sources.py:
ql_subsample`).
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

FAMILY_ORDER = ("qwen35_4b", "mistral7b_v03", "llama32_3b")


def draw_subsample(seed: int = config.SUBSAMPLE_PERMUTATION_SEED, n: int = config.SUBSAMPLE_ROWS_PER_FAMILY) -> dict[str, list[str]]:
    rng = random.Random(seed)
    out: dict[str, list[str]] = {}
    for family in FAMILY_ORDER:
        pool = row_pool.paired_confab_row_keys(family)  # already sorted
        pool_copy = pool[:]
        rng.shuffle(pool_copy)
        take = min(n, len(pool_copy))
        out[family] = sorted(pool_copy[:take])  # sorted for a stable, reviewable committed manifest
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.parse_args()

    subsample = draw_subsample()

    manifest = {
        "permutation_seed": config.SUBSAMPLE_PERMUTATION_SEED,
        "rows_per_family_requested": config.SUBSAMPLE_ROWS_PER_FAMILY,
        "population": config.SUBSAMPLE_POPULATION,
        "family_order": list(FAMILY_ORDER),
        "families": {
            family: {
                "n_drawn": len(keys),
                "paired_pool_n": config.PAIRED_CONFAB_POOL_N[family],
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
