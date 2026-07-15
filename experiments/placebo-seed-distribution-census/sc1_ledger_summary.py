#!/usr/bin/env python3
"""Aggregates the three per-family SC1 ledgers (`run_census.py run-family`,
gitignored `analysis/sc1_ledger_<family>.json`) into ONE committed summary:
`analysis-committed/sc1_ledger_summary.json`.

Run AFTER the full K=15 x S=300 x 3-family sweep completes. Contents are
accepted seeds (bare integers, no text -- containment-safe), voids by reason,
readback relative-delta mean/max, wall-clock, and pass-restart counts per
family -- exactly the fields cell.yaml's SC1 gate is defined over, nothing
else (no row_key, no question/answer text, no aliases).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common  # noqa: E402
import config  # noqa: E402

ANALYSIS = HERE / "analysis"
COMMITTED = HERE / "analysis-committed"


def _readback_rel_delta_stats(ledger: dict[str, Any]) -> dict[str, Any]:
    """Mean/max relative readback delta, pooled over EVERY seed this family
    attempted (accepted seeds implicitly clear the tolerance; voided-on-
    readback seeds are the ones that failed it) -- sourced from the
    `readback_summary.mean_rel_delta`/`max_rel_delta` this ledger already
    recorded per voided seed, plus a fresh recomputation over the accepted
    seeds' own persisted dosed runlogs (their readback passed, but the ledger
    itself does not carry their per-row rel_delta, only pass/fail)."""
    import sc1_checks

    setpoint = ledger.get("setpoint_dose_abs")
    family = ledger["family"]
    rel_deltas: list[float] = []

    for seed in ledger.get("accepted_seeds", []):
        path = ANALYSIS / "runlog" / f"{family}__random_direction__seed{seed}.jsonl"
        for row in common.load_jsonl(path):
            check = sc1_checks.check_readback(seed, family, row.get("readback_measured"), setpoint)
            if check.get("rel_delta") is not None:
                rel_deltas.append(check["rel_delta"])

    for v in ledger.get("voids", []):
        rs = v.get("readback_summary")
        if rs and rs.get("mean_rel_delta") is not None:
            # one summary value per voided seed; weight it once (not per row)
            # since the ledger did not persist per-row deltas for voided seeds
            rel_deltas.append(rs["mean_rel_delta"])

    if not rel_deltas:
        return {"n_readback_checks_pooled": 0, "mean_rel_delta": None, "max_rel_delta": None}
    return {
        "n_readback_checks_pooled": len(rel_deltas),
        "mean_rel_delta": sum(rel_deltas) / len(rel_deltas),
        "max_rel_delta": max(rel_deltas),
    }


def summarize_family(family: str) -> dict[str, Any]:
    ledger_path = ANALYSIS / f"sc1_ledger_{family}.json"
    if not ledger_path.is_file():
        return {"family": family, "ledger_found": False}
    ledger = common.load_json(ledger_path)
    readback_stats = _readback_rel_delta_stats(ledger)
    return {
        "family": family, "ledger_found": True,
        "k_target": ledger["k_target"], "n_accepted": ledger["n_accepted"],
        "accepted_seeds": ledger["accepted_seeds"],
        "n_voids": ledger["n_voids"],
        "n_randomness_voids": ledger["n_randomness_voids"],
        "n_readback_voids": ledger["n_readback_voids"],
        "voids_by_reason_detail": [
            {"seed": v["seed"], "reason": v["reason"]} for v in ledger.get("voids", [])
        ],
        "max_consecutive_readback_voids": ledger["max_consecutive_readback_voids"],
        "aborted": ledger["aborted"], "abort_reason": ledger.get("abort_reason"),
        "n_passes_restarted": ledger["n_passes_restarted"],
        "n_passes_reused_durable": ledger["n_passes_reused_durable"],
        "wall_clock_generation_s": ledger["wall_clock_generation_s"],
        "n_rows_per_seed": ledger["n_rows_per_seed"],
        "batch_size": ledger["batch_size"],
        "setpoint_dose_abs": ledger["setpoint_dose_abs"],
        "readback_relative_delta_stats": readback_stats,
        "rg0_baseline_check_passed": ledger["rg0_baseline_check"]["passed"],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.parse_args()

    summary = {"families": {family: summarize_family(family) for family in config.FAMILIES}}
    common.write_json(COMMITTED / "sc1_ledger_summary.json", summary)
    for family, s in summary["families"].items():
        if not s.get("ledger_found"):
            print(f"[sc1_ledger_summary] {family}: NO LEDGER FOUND (run-family has not been run for this family)", flush=True)
            continue
        print(f"[sc1_ledger_summary] {family}: accepted={s['n_accepted']}/{s['k_target']} "
              f"voids={s['n_voids']} (rand={s['n_randomness_voids']} readback={s['n_readback_voids']}) "
              f"aborted={s['aborted']} restarted={s['n_passes_restarted']} reused={s['n_passes_reused_durable']} "
              f"wall_clock={s['wall_clock_generation_s']:.0f}s readback_mean_rel={s['readback_relative_delta_stats']['mean_rel_delta']}",
              flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
