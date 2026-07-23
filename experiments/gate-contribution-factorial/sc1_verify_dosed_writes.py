#!/usr/bin/env python3
"""SC1 verification for gate-contribution-factorial's post-generation
integrity phase (gates.yaml `sc1_magnitude_matching`).

NEW script (not pinned; sc1_checks.py itself is untouched and imported
verbatim). Written because run_factorial.py's generation commands do not
call sc1_checks.py during generation (this experiment's SC1 check is a
downstream verification pass over the completed runlogs, not a live
generation-time ledger like placebo-seed-distribution-census's
`run_census.py run-family`), so there is no per-family `sc1_ledger_<family>.
json` to summarize the way census's `sc1_ledger_summary.py` does. This script
performs the check directly against the on-disk generation runlogs and
writes an aggregates-only summary in the same spirit (no text, no row_key,
no question/answer content -- readback deltas and pass/fail counts only).

For each family:
  - randomness bar: check_randomness_bar for each of the K=5 primary seeds
    (config.RANDOM_SEED_BLOCKS), against the family's frozen c_hat/u_d.
  - readback tolerance: check_readback for EVERY row with a non-null
    readback_measured in every dosed-write runlog (permuted_gate_c_hat_final,
    true_gate_random__seed{S}_final x5, permuted_gate_random__seed{S}_final
    x5), against the family's setpoint_dose_abs. Aggregated pass rate plus
    mean/max relative delta, PLUS the full per-row-checked worst-case pulled
    out for the report (rel_delta only, no text).
  - the true_gate_c_hat REUSED arm (RG0 byte-identical reuse of the prior
    experiment's own already-verified write) is checked too, for
    completeness, but flagged as reused_not_fresh so it is not conflated
    with a fresh check of THIS harness's write path.
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

ANALYSIS = HERE / "analysis"
COMMITTED = HERE / "analysis-committed"


def _readback_pass_stats(rows: list[dict[str, Any]], family: str, target: float) -> dict[str, Any]:
    checks = [
        sc1_checks.check_readback(row.get("row_key"), family, row.get("readback_measured"), target)
        for row in rows
        if row.get("readback_measured") is not None
    ]
    n = len(checks)
    n_pass = sum(1 for c in checks if c["passed"])
    rel_deltas = [c["rel_delta"] for c in checks]
    worst = max(checks, key=lambda c: c["rel_delta"]) if checks else None
    return {
        "n_dosed_rows_with_readback": n,
        "n_pass": n_pass,
        "n_fail": n - n_pass,
        "pass_rate": (n_pass / n) if n else None,
        "mean_rel_delta": (sum(rel_deltas) / n) if n else None,
        "max_rel_delta": max(rel_deltas) if rel_deltas else None,
        "worst_case": (
            {"abs_delta": worst["abs_delta"], "rel_delta": worst["rel_delta"],
             "readback_measured": worst["readback_measured"], "target": worst["target"]}
            if worst else None
        ),
        "all_within_tolerance": (n_pass == n) if n else None,
    }


def summarize_family(family: str) -> dict[str, Any]:
    target = config.SETPOINT_DOSE_ABS[family]
    vecs = load_direction_vectors(family)
    c_hat, u_d, hidden_dim = vecs["c_hat"], vecs["u_d"], vecs["hidden_dim"]

    randomness = [
        sc1_checks.check_randomness_bar(seed, hidden_dim, c_hat, u_d)
        for seed in config.RANDOM_SEED_BLOCKS[family]
    ]

    out: dict[str, Any] = {
        "family": family, "setpoint_dose_abs": target,
        "randomness_bar": {
            "bar_cos": sc1_checks.RANDOMNESS_BAR_COS,
            "per_seed": randomness,
            "all_passed": all(r["passed"] for r in randomness),
        },
        "readback": {},
    }

    reused_rows = common.load_jsonl(ANALYSIS / "runlog" / f"{family}__true_gate_c_hat_reused.jsonl")
    out["readback"]["true_gate_c_hat_reused"] = {
        **_readback_pass_stats(reused_rows, family, target),
        "reused_not_fresh": True,
        "note": "text/readback inherited byte-identical from the source experiment's own prior write (RG0), not a fresh write by this harness",
    }

    pgc_rows = common.load_jsonl(ANALYSIS / "runlog" / f"{family}__permuted_gate_c_hat_final.jsonl")
    out["readback"]["permuted_gate_c_hat"] = {**_readback_pass_stats(pgc_rows, family, target), "reused_not_fresh": False}

    for label in ("true_gate_random", "permuted_gate_random"):
        per_seed = {}
        for seed in config.RANDOM_SEED_BLOCKS[family]:
            rows = common.load_jsonl(ANALYSIS / "runlog" / f"{family}__{label}__seed{seed}_final.jsonl")
            per_seed[str(seed)] = {**_readback_pass_stats(rows, family, target), "reused_not_fresh": False}
        out["readback"][label] = per_seed

    fresh_write_checks = [out["readback"]["permuted_gate_c_hat"]]
    for label in ("true_gate_random", "permuted_gate_random"):
        fresh_write_checks.extend(out["readback"][label].values())
    out["all_fresh_dosed_writes_within_tolerance"] = all(
        c["all_within_tolerance"] for c in fresh_write_checks if c["all_within_tolerance"] is not None
    )
    return out


def main() -> int:
    summary = {"families": {family: summarize_family(family) for family in config.FAMILIES}}
    COMMITTED.mkdir(parents=True, exist_ok=True)
    common.write_json(COMMITTED / "sc1_verification_summary.json", summary)
    for family, s in summary["families"].items():
        print(f"[sc1_verify] {family}: randomness_all_passed={s['randomness_bar']['all_passed']} "
              f"fresh_dosed_writes_within_tolerance={s['all_fresh_dosed_writes_within_tolerance']}", flush=True)
        pgc = s["readback"]["permuted_gate_c_hat"]
        print(f"[sc1_verify]   permuted_gate_c_hat: n={pgc['n_dosed_rows_with_readback']} "
              f"pass={pgc['n_pass']} fail={pgc['n_fail']} mean_rel_delta={pgc['mean_rel_delta']}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
