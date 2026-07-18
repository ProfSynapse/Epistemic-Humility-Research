#!/usr/bin/env python3
"""Fit/held-out split freeze for evidence-response-direction-search (M4c).
Step 2 of the execution sequence. Implements the byte-pinned routine from
cell.yaml `fit.split_routine_pinned` EXACTLY:

    sort the 400 confab row-keys lexicographically (byte order)
    perm = numpy.random.default_rng(48260728).permutation(400)
    fit = sorted_keys[perm[:200]]
    held_out = sorted_keys[perm[200:]]

SELF-BLINDING (circularity item ii/iii, gates.yaml SC0 self-blinding
enforcement M-B): this module reads ONLY opaque row-keys from
`test_population.json` (staged, hash-pinned at step 1). It NEVER opens
`analysis-committed/channel1/per_row_projections.jsonl` or any other
projection artifact -- there is no import, no path reference, no read of
that file anywhere in this module. Do not add one.

Writes `analysis-committed/selection/fit_heldout_split.json` BEFORE any
`d_ev` computation (fit_dev.py, step 3, runs after this commits).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import config  # noqa: E402
import common  # noqa: E402

COMMITTED = config.EXPERIMENT_DIR / "analysis-committed"
SELECTION_DIR = COMMITTED / "selection"


def compute_split(confab_row_keys: list[str], seed: int) -> tuple[list[str], list[str]]:
    """The pinned routine, verbatim. `confab_row_keys` must be the raw
    (unsorted) 400 confab row-keys; this function sorts them itself."""
    sorted_keys = np.array(sorted(confab_row_keys), dtype=object)
    if len(sorted_keys) != 400:
        raise SystemExit(f"split_freeze FAIL: expected 400 confab row-keys, got {len(sorted_keys)}")
    rng = np.random.default_rng(seed)
    perm = rng.permutation(400)
    fit = sorted_keys[perm[:200]]
    held_out = sorted_keys[perm[200:]]
    return list(fit), list(held_out)


def main() -> int:
    config.assert_pinned_hashes()

    staging_manifest_path = COMMITTED / "staging_manifest.json"
    if not staging_manifest_path.is_file():
        raise SystemExit(f"split_freeze FAIL: no {staging_manifest_path}; run stage.py first (SC0).")
    staging = common.load_json(staging_manifest_path)
    if not staging.get("test_population", {}).get("matches_pin"):
        raise SystemExit("split_freeze FAIL: staging_manifest.json test_population.matches_pin is not True")

    test_pop = common.load_json(config.TEST_POPULATION_PATH)
    confab_row_keys = list(test_pop["row_keys"]["confab"])
    if len(confab_row_keys) != 400:
        raise SystemExit(f"split_freeze FAIL: test_population.json confab count {len(confab_row_keys)} != 400")

    fit_keys, held_out_keys = compute_split(confab_row_keys, config.SPLIT_SEED)

    if len(set(fit_keys) & set(held_out_keys)) != 0:
        raise SystemExit("split_freeze FAIL: fit/held-out overlap (should be impossible by construction)")
    if len(fit_keys) != config.N_FIT or len(held_out_keys) != config.N_HELD_OUT:
        raise SystemExit(f"split_freeze FAIL: split sizes fit={len(fit_keys)} held_out={len(held_out_keys)} != {config.N_FIT}/{config.N_HELD_OUT}")

    payload = {
        "seed": config.SPLIT_SEED,
        "method": "id-only permutation of the 400 confab row-keys, cell.yaml fit.split_routine_pinned verbatim",
        "counts": {"fit": len(fit_keys), "held_out": len(held_out_keys)},
        "fit_row_keys": sorted(fit_keys),
        "held_out_row_keys": sorted(held_out_keys),
        "self_blinding": {
            "per_row_projections_jsonl_opened": False,
            "note": "split computed from opaque row-keys only (test_population.json), before any projection or d_ev is computed; per_row_projections.jsonl is never referenced by this module.",
        },
    }
    SELECTION_DIR.mkdir(parents=True, exist_ok=True)
    common.write_json(SELECTION_DIR / "fit_heldout_split.json", payload)
    print(f"[split_freeze] wrote {SELECTION_DIR / 'fit_heldout_split.json'}: fit={len(fit_keys)} held_out={len(held_out_keys)} seed={config.SPLIT_SEED}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
