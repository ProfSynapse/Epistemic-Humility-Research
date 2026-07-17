#!/usr/bin/env python3
"""Random-seed void/redraw ledger for gate-contribution-factorial's K=5
`true_gate__random` / `permuted_gate__random` arms (gates.yaml
`sc1_magnitude_matching.on_fail`; PI directive 2026-07-16, registered
mechanism). Uses `sc1_checks.resolve_seed_ledger` verbatim (sc1_checks.py
itself untouched).

Walks each family's registered primary K=5 seed block (config.
RANDOM_SEED_BLOCKS) against the RANDOMNESS bar only (|cos(r_hat, c_hat)| <=
config.RANDOMNESS_BAR_COS AND |cos(r_hat, u_d)| <= config.RANDOMNESS_BAR_COS);
a seed failing the bar is voided and replaced by the next pre-registered
sequential seed (sc1_checks.redraw_seed: family_seed_floor +
K_SEEDS_PER_FAMILY + attempt), until exactly K_SEEDS_PER_FAMILY seeds are
accepted. Readback is NOT checked here -- this script runs BEFORE any GPU
generation, so there is no readback to check yet; the readback half of SC1
is enforced live during generation by run_factorial.py's own
_live_sc1_after_first_batch / _live_sc1_arm_completion assertions, and
independently re-verified after the fact by sc1_verify_dosed_writes.py.

Writes `analysis-committed/random_seed_ledger.json`: per family, the
accepted seed list (the list run_factorial.py `generate-family` uses in
place of the raw config.RANDOM_SEED_BLOCKS), the full void list with
per-seed cos values and the failure reason, and the worst void margin. No
text, no row_key, no question/answer content -- committed-format, matching
`analysis-committed/sc1_verification_summary.json`'s own convention.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common  # noqa: E402
import config  # noqa: E402
import sc1_checks  # noqa: E402
from run_factorial import load_direction_vectors  # noqa: E402  (CPU-only helper, no GPU/model import)

COMMITTED = HERE / "analysis-committed"


def compute_ledger() -> dict[str, Any]:
    ledger: dict[str, Any] = {}
    for family in config.FAMILIES:
        vecs = load_direction_vectors(family)
        result = sc1_checks.resolve_seed_ledger(
            family, config.RANDOM_SEED_BLOCKS[family], vecs["hidden_dim"], vecs["c_hat"], vecs["u_d"],
        )
        worst_margin = None
        if result["voids"]:
            worst_margin = max(
                max(v["randomness_bar"]["abs_cos_to_c_hat"], v["randomness_bar"]["abs_cos_to_u_d"])
                for v in result["voids"]
            )
        ledger[family] = {**result, "worst_void_margin_cos": worst_margin, "randomness_bar_cos": sc1_checks.RANDOMNESS_BAR_COS}
    return ledger


def main() -> int:
    ledger = compute_ledger()
    COMMITTED.mkdir(parents=True, exist_ok=True)
    common.write_json(COMMITTED / "random_seed_ledger.json", ledger)
    for family, res in ledger.items():
        print(
            f"[compute_seed_ledger] {family}: accepted={res['accepted_seeds']} "
            f"n_voids={res['n_voids']} worst_void_margin_cos={res['worst_void_margin_cos']}",
            flush=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
