"""Paired per-seed delta arithmetic for placebo-seed-distribution-census
(cell.yaml `readouts.per_seed_delta_pts`; gates.yaml `sc3_paired_population_
and_coverage`).

Per-seed delta = dosed refused_final minus baseline refused_final, computed
over the EXACT fixed S rows shared across baseline and every dosed seed
(paired-population rule). A row missing or degenerate for a given seed is
reported separately for that seed, never folded into that seed's delta.
"""

from __future__ import annotations

from typing import Any

from common import wilson


def paired_delta_pts(
    dosed_by_key: dict[str, dict[str, Any]],
    baseline_by_key: dict[str, dict[str, Any]],
    s_row_keys: list[str],
    refused_field: str = "refused_final",
) -> dict[str, Any]:
    """Returns the paired delta in PERCENTAGE POINTS (dosed - baseline),
    Wilson 95% CIs on each arm's rate, paired-n, and the list of row_keys
    missing from either arm (reported separately, never inside the delta)."""
    paired_dosed: list[bool] = []
    paired_baseline: list[bool] = []
    missing: list[str] = []
    for rk in s_row_keys:
        d = dosed_by_key.get(rk)
        b = baseline_by_key.get(rk)
        if d is None or b is None or d.get(refused_field) is None or b.get(refused_field) is None:
            missing.append(rk)
            continue
        paired_dosed.append(bool(d[refused_field]))
        paired_baseline.append(bool(b[refused_field]))

    n = len(paired_dosed)
    dosed_rate = wilson(sum(paired_dosed), n)
    baseline_rate = wilson(sum(paired_baseline), n)
    delta_pts = (dosed_rate["rate"] - baseline_rate["rate"]) * 100.0

    return {
        "n_paired": n, "n_missing": len(missing), "missing_row_keys": missing,
        "dosed_rate": dosed_rate, "baseline_rate": baseline_rate,
        "delta_pts": delta_pts,
    }
