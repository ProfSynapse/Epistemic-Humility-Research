#!/usr/bin/env python3
"""SC0 self-blinding ENFORCEMENT for evidence-response-direction-search
(M4c). Step 4 of the execution sequence (gates.yaml SC0_provenance_staging,
pre-sign red-team M-B: "promises are not gates"). Two independent
recompute-and-assert checks, run AFTER the split and d_ev are committed:

  (i)  re-derive the fit/held-out split from the pinned routine + seed and
       hard-assert equality with the committed fit_heldout_split.json
  (ii) recompute d_ev from the staged raw tensors + the committed fit
       id-list and hard-assert equality (tolerance 1e-6) with the committed
       d_ev.json vector

Either assertion failing is an SC0 provenance void: this script raises
SystemExit and writes NOTHING further. This is the machine enforcement of
self-blinding, not a promise.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import config  # noqa: E402
import common  # noqa: E402
import split_freeze  # noqa: E402
import fit_dev  # noqa: E402

COMMITTED = config.EXPERIMENT_DIR / "analysis-committed"
SELECTION_DIR = COMMITTED / "selection"
DIRECTIONS_DIR = COMMITTED / "directions" / "hs20"


def check_split_reproduces() -> dict:
    committed = common.load_json(SELECTION_DIR / "fit_heldout_split.json")
    test_pop = common.load_json(config.TEST_POPULATION_PATH)
    confab_row_keys = list(test_pop["row_keys"]["confab"])
    fit_re, held_out_re = split_freeze.compute_split(confab_row_keys, committed["seed"])
    fit_re_sorted = sorted(fit_re)
    held_out_re_sorted = sorted(held_out_re)
    fit_match = fit_re_sorted == sorted(committed["fit_row_keys"])
    held_out_match = held_out_re_sorted == sorted(committed["held_out_row_keys"])
    if not (fit_match and held_out_match):
        raise SystemExit(
            "sc0_enforce FAIL (SC0 VOID): re-derived split does NOT match committed "
            f"fit_heldout_split.json. fit_match={fit_match} held_out_match={held_out_match}"
        )
    return {"fit_match": fit_match, "held_out_match": held_out_match, "seed": committed["seed"]}


def check_d_ev_reproduces(tol: float = 1e-6) -> dict:
    committed = common.load_json(DIRECTIONS_DIR / "d_ev.json")
    split = common.load_json(SELECTION_DIR / "fit_heldout_split.json")
    fit_row_keys = sorted(split["fit_row_keys"])
    fit_result = fit_dev.fit_d_ev(fit_row_keys)
    d_ev_re = fit_result["d_ev"]
    d_ev_committed = np.asarray(committed["vector"], dtype=np.float64)
    max_abs_diff = float(np.max(np.abs(d_ev_re - d_ev_committed)))
    if max_abs_diff > tol:
        raise SystemExit(
            f"sc0_enforce FAIL (SC0 VOID): recomputed d_ev differs from committed d_ev.json "
            f"by max_abs_diff={max_abs_diff} > tol={tol}"
        )
    cos_sim = float(np.dot(d_ev_re, d_ev_committed))
    return {"max_abs_diff": max_abs_diff, "tol": tol, "cos_sim_recomputed_vs_committed": cos_sim, "n_fit": len(fit_row_keys)}


def main() -> int:
    config.assert_pinned_hashes()

    print("[sc0_enforce] (i) re-deriving fit/held-out split from routine + seed...", flush=True)
    split_check = check_split_reproduces()
    print(f"[sc0_enforce] (i) PASS: {split_check}", flush=True)

    print("[sc0_enforce] (ii) recomputing d_ev from staged tensors + committed fit id-list...", flush=True)
    d_ev_check = check_d_ev_reproduces()
    print(f"[sc0_enforce] (ii) PASS: {d_ev_check}", flush=True)

    result = {
        "split_reproduces": split_check,
        "d_ev_reproduces": d_ev_check,
        "sc0_void": False,
    }
    common.write_json(COMMITTED / "sc0_enforcement.json", result)
    print(f"[sc0_enforce] SC0 enforcement PASS on both checks; wrote {COMMITTED / 'sc0_enforcement.json'}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
