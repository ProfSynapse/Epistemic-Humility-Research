#!/usr/bin/env python3
"""SC1 verification v2 for gate-contribution-factorial's post-generation
integrity phase (gates.yaml `sc1_magnitude_matching`), run against the
REGENERATED runlogs (dose-squaring defect fixed, audited repin d4115f57;
regeneration completed 2026-07-16, analysis/logs/generation_master_v2.log).

NEW script (not pinned), a small adaptation of `sc1_verify_dosed_writes.py`
(also not pinned; its own docstring says so -- `sc1_checks.py` itself is the
pinned module and is imported verbatim, unmodified, exactly as by the v1
script). The only substantive change from v1: v1 iterates
`config.RANDOM_SEED_BLOCKS[family]`, the RAW pre-registered primary K=5 seed
block. That block is stale for THIS run: `compute_seed_ledger.py` voided
seeds failing the randomness bar and redrew replacements (per gates.yaml
`sc1_magnitude_matching.on_fail`), so the seeds actually generated and
present on disk are `analysis-committed/random_seed_ledger.json`'s
`accepted_seeds`, not the raw primary block. Checking the raw block against
this run's runlogs would silently look for files that were never generated
(voided seeds) and skip files that were (redrawn seeds) -- this script fixes
that by sourcing seeds from the ledger, and additionally cross-checks the
ledger's accepted-seed set against the seed values actually present as
runlog files on disk (belt-and-suspenders: the ledger says what SHOULD have
been generated, the disk glob says what WAS).

Per-family checks:
  - Ledger/disk cross-check: the ledger's accepted_seeds set for
    true_gate_random and permuted_gate_random each equals the set of seeds
    with a `*_final.jsonl` runlog on disk (no extra, no missing).
  - Randomness bar: check_randomness_bar for each accepted seed (independent
    recomputation against the family's frozen c_hat/u_d; sc1_checks.py
    unmodified), reported alongside the ledger's own recorded value.
  - Readback tolerance: check_readback for EVERY row with a non-null
    readback_measured in every dosed-write runlog (permuted_gate_c_hat_final,
    true_gate_random__seed{S}_final x5 accepted seeds,
    permuted_gate_random__seed{S}_final x5 accepted seeds), against the
    family's setpoint_dose_abs. Full-runlog (not first-batch-only) pass rate
    plus mean/max relative delta and the worst-case row pulled out
    (rel_delta only, no text, no row_key content beyond what sc1_checks
    already returns).
  - The true_gate_c_hat REUSED arm (RG0 byte-identical reuse) is checked too,
    flagged reused_not_fresh, exactly as v1 did.

Writes analysis-committed/sc1_verification_summary_v2.json. Does NOT
overwrite the v1 file (that is the defective first attempt's record and
stays as historical evidence of the caught defect).
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
RUNLOG_DIR = ANALYSIS / "runlog"


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
        "n_rows_in_file": len(rows),
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


def _disk_seeds_for_label(family: str, label: str) -> set[int]:
    """Seeds with a `{family}__{label}__seed{S}_final.jsonl` runlog present
    on disk (glob, not a hardcoded list -- this is the belt-and-suspenders
    half of the ledger/disk cross-check)."""
    prefix = f"{family}__{label}__seed"
    suffix = "_final.jsonl"
    found: set[int] = set()
    for p in RUNLOG_DIR.glob(f"{prefix}*{suffix}"):
        stem = p.name[len(prefix):-len(suffix)]
        try:
            found.add(int(stem))
        except ValueError:
            continue
    return found


def _ledger_disk_cross_check(family: str, ledger_accepted: list[int]) -> dict[str, Any]:
    ledger_set = set(ledger_accepted)
    out: dict[str, Any] = {"ledger_accepted_seeds": sorted(ledger_set)}
    for label in ("true_gate_random", "permuted_gate_random"):
        disk_set = _disk_seeds_for_label(family, label)
        out[label] = {
            "disk_seeds": sorted(disk_set),
            "matches_ledger_exactly": disk_set == ledger_set,
            "extra_on_disk_not_in_ledger": sorted(disk_set - ledger_set),
            "missing_from_disk": sorted(ledger_set - disk_set),
        }
    out["all_labels_match_ledger"] = all(out[label]["matches_ledger_exactly"] for label in ("true_gate_random", "permuted_gate_random"))
    return out


def summarize_family(family: str, ledger: dict[str, Any]) -> dict[str, Any]:
    target = config.SETPOINT_DOSE_ABS[family]
    vecs = load_direction_vectors(family)
    c_hat, u_d, hidden_dim = vecs["c_hat"], vecs["u_d"], vecs["hidden_dim"]

    ledger_entry = ledger[family]
    accepted_seeds: list[int] = ledger_entry["accepted_seeds"]
    if len(accepted_seeds) != config.K_SEEDS_PER_FAMILY:
        raise SystemExit(
            f"SC1-v2 FAIL ({family}): ledger accepted_seeds count {len(accepted_seeds)} "
            f"!= config.K_SEEDS_PER_FAMILY {config.K_SEEDS_PER_FAMILY}"
        )

    cross_check = _ledger_disk_cross_check(family, accepted_seeds)

    # Independent recomputation of the randomness bar for the ACCEPTED seeds
    # (sc1_checks.py unmodified; this is a fresh call, not a copy of the
    # ledger's stored numbers).
    randomness = [sc1_checks.check_randomness_bar(seed, hidden_dim, c_hat, u_d) for seed in accepted_seeds]
    randomness_recheck_all_passed = all(r["passed"] for r in randomness)

    out: dict[str, Any] = {
        "family": family,
        "setpoint_dose_abs": target,
        "seed_source": "analysis-committed/random_seed_ledger.json accepted_seeds (NOT config.RANDOM_SEED_BLOCKS raw primary block)",
        "ledger_disk_cross_check": cross_check,
        "randomness_bar_recheck_on_accepted_seeds": {
            "bar_cos": sc1_checks.RANDOMNESS_BAR_COS,
            "per_seed": randomness,
            "all_passed": randomness_recheck_all_passed,
            # note: the ledger only stores cos values for VOIDED seeds, not
            # accepted ones, so there is nothing in the ledger to diff these
            # fresh per_seed values against; this recheck stands alone.
        },
        "readback": {},
    }

    reused_rows = common.load_jsonl(RUNLOG_DIR / f"{family}__true_gate_c_hat_reused.jsonl")
    out["readback"]["true_gate_c_hat_reused"] = {
        **_readback_pass_stats(reused_rows, family, target),
        "reused_not_fresh": True,
        "note": "text/readback inherited byte-identical from the source experiment's own prior write (RG0), not a fresh write by this harness",
    }

    pgc_rows = common.load_jsonl(RUNLOG_DIR / f"{family}__permuted_gate_c_hat_final.jsonl")
    out["readback"]["permuted_gate_c_hat"] = {**_readback_pass_stats(pgc_rows, family, target), "reused_not_fresh": False}

    for label in ("true_gate_random", "permuted_gate_random"):
        per_seed = {}
        for seed in accepted_seeds:
            rows = common.load_jsonl(RUNLOG_DIR / f"{family}__{label}__seed{seed}_final.jsonl")
            per_seed[str(seed)] = {**_readback_pass_stats(rows, family, target), "reused_not_fresh": False}
        out["readback"][label] = per_seed

    fresh_write_checks = [out["readback"]["permuted_gate_c_hat"]]
    for label in ("true_gate_random", "permuted_gate_random"):
        fresh_write_checks.extend(out["readback"][label].values())
    out["all_fresh_dosed_writes_within_tolerance"] = all(
        c["all_within_tolerance"] for c in fresh_write_checks if c["all_within_tolerance"] is not None
    )
    out["any_fresh_dosed_write_missing_readback"] = any(
        c["n_dosed_rows_with_readback"] == 0 for c in fresh_write_checks
    )
    out["sc1_pass"] = bool(
        cross_check["all_labels_match_ledger"]
        and randomness_recheck_all_passed
        and out["all_fresh_dosed_writes_within_tolerance"]
        and not out["any_fresh_dosed_write_missing_readback"]
    )
    return out


def main() -> int:
    ledger = common.load_json(COMMITTED / "random_seed_ledger.json")
    summary = {
        "source_generation_log": "analysis/logs/generation_master_v2.log",
        "defect_fixed_commit": "d4115f57",
        "families": {family: summarize_family(family, ledger) for family in config.FAMILIES},
    }
    summary["all_families_sc1_pass"] = all(s["sc1_pass"] for s in summary["families"].values())
    COMMITTED.mkdir(parents=True, exist_ok=True)
    common.write_json(COMMITTED / "sc1_verification_summary_v2.json", summary)
    for family, s in summary["families"].items():
        print(
            f"[sc1_verify_v2] {family}: ledger/disk match={s['ledger_disk_cross_check']['all_labels_match_ledger']} "
            f"randomness_recheck_all_passed={s['randomness_bar_recheck_on_accepted_seeds']['all_passed']} "
            f"fresh_dosed_writes_within_tolerance={s['all_fresh_dosed_writes_within_tolerance']} "
            f"sc1_pass={s['sc1_pass']}",
            flush=True,
        )
        pgc = s["readback"]["permuted_gate_c_hat"]
        print(f"[sc1_verify_v2]   permuted_gate_c_hat: n={pgc['n_dosed_rows_with_readback']} "
              f"pass={pgc['n_pass']} fail={pgc['n_fail']} max_rel_delta={pgc['max_rel_delta']}", flush=True)
    print(f"[sc1_verify_v2] all_families_sc1_pass={summary['all_families_sc1_pass']}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
