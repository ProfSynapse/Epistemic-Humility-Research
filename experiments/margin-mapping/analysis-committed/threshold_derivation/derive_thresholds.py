#!/usr/bin/env python3
"""Data-grounded derivation of the M1 margin-mapping amendment's sign-time
knobs (Decision record items 1, 4, 5, 6 in AMENDMENT.md), computed from
EXISTING artifacts only. No GPU work, no new generations.

Sources (read-only):
  - gate-contribution-factorial runlog + adjudication_applied.jsonl
    (/home/profsynapse/code/ehr-worktrees/gate-factorial/experiments/
    gate-contribution-factorial/analysis/), replicating the registered
    refused_final merge rule from that experiment's report.py
    (refused_final = detector refused_v2 OR blinded-adjudication
    refused_final for detector-non-refused rows).
  - qwen35-4b-midband-doubt-snap row-level dose-ladder runlog
    (/home/profsynapse/code/ehr-worktrees/qwen35-midband/experiments/
    qwen35-4b-midband-doubt-snap/analysis/runlog/hs20__permuted_gate.jsonl),
    the only row-level multi-dose data available (qwen, hs20, no-gate
    "permuted_gate" arm -- the design closest to M1's ungated ladder).

Statistical conventions matched to the repo: Wilson 95% CI on rates
(common.wilson in the factorial), row-level bootstrap with n_boot=10000 for
CIs on differences and fitted quantities.

Outputs: threshold_derivation_report.json in this directory.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Optional

import numpy as np
from scipy import stats
from scipy.optimize import least_squares

FACTORIAL_ANALYSIS = Path(
    "/home/profsynapse/code/ehr-worktrees/gate-factorial/experiments/"
    "gate-contribution-factorial/analysis"
)
DOUBT_SNAP_RUNLOG = Path(
    "/home/profsynapse/code/ehr-worktrees/qwen35-midband/experiments/"
    "qwen35-4b-midband-doubt-snap/analysis/runlog"
)
OUT_DIR = Path(__file__).resolve().parent

N_BOOT = 10000
SEED = 47260714  # matches gate-contribution-factorial/common.py bootstrap_ci default
Z95 = 1.959963984540054


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def wilson(successes: int, n: int, z: float = Z95) -> dict[str, Any]:
    """Byte-identical formula to gate-contribution-factorial/common.py:wilson."""
    if n == 0:
        return {"n": 0, "successes": 0, "rate": 0.0, "wilson_ci_95": [0.0, 0.0]}
    phat = successes / n
    denom = 1 + z * z / n
    center = (phat + z * z / (2 * n)) / denom
    half = (z * ((phat * (1 - phat) / n + z * z / (4 * n * n)) ** 0.5)) / denom
    return {
        "n": n, "successes": successes, "rate": phat,
        "wilson_ci_95": [max(0.0, center - half), min(1.0, center + half)],
    }


# ---------------------------------------------------------------------------
# Step 1: factorial CDF points, replicating report.py's refused_final rule
# ---------------------------------------------------------------------------

def runlog_tag(family: str, arm: str, seed: Optional[int] = None) -> str:
    if arm == "baseline":
        return f"{family}__baseline_reused"
    if arm == "true_gate_c_hat":
        return f"{family}__true_gate_c_hat_reused"
    if arm == "permuted_gate_c_hat":
        return f"{family}__permuted_gate_c_hat_final"
    raise ValueError(f"unknown arm {arm!r}")


def load_runlog_by_key(family: str, arm: str) -> dict[str, dict[str, Any]]:
    path = FACTORIAL_ANALYSIS / "runlog" / f"{runlog_tag(family, arm)}.jsonl"
    return {r["row_key"]: r for r in load_jsonl(path)}


def load_fired_keys(family: str, arm: str) -> set[str]:
    """Fired row_key sets per arm.

    permuted_gate_c_hat: the fired-only runlog file (no _final/_reused
    suffix) lists exactly the rows dosed under this arm (verified: qwen
    1025 confab + 278 known = 1303; mistral 1006 confab + 297 known = 1303,
    matching the factorial AMENDMENT.md Outcome "Fired counts" text).

    true_gate_c_hat: there is no analogous fired-only runlog file (the
    _reused file already contains the full population with dosed-if-fired
    text). The fired set instead lives in
    analysis/staged_inputs/{family}/gated.jsonl, verified against the
    Outcome's cited fired counts: qwen 1286 confab + 17 known = 1303
    (matches analysis/staged_inputs/qwen35_4b/fire_decisions_heldout.jsonl
    fire=True rows exactly); mistral 1303 confab + 0 known = 1303 (matches
    the Outcome's "Fired counts: true gate 1303 (1303 confab, 0 known)").
    """
    if arm == "permuted_gate_c_hat":
        path = FACTORIAL_ANALYSIS / "runlog" / f"{family}__{arm}.jsonl"
        return {r["row_key"] for r in load_jsonl(path)}
    if arm == "true_gate_c_hat":
        path = FACTORIAL_ANALYSIS / "staged_inputs" / family / "gated.jsonl"
        return {r["row_key"] for r in load_jsonl(path)}
    raise ValueError(f"unknown arm {arm!r}")


_APPLIED_ROWS_CACHE: Optional[list[dict[str, Any]]] = None


def load_applied_rows() -> list[dict[str, Any]]:
    global _APPLIED_ROWS_CACHE
    if _APPLIED_ROWS_CACHE is None:
        _APPLIED_ROWS_CACHE = load_jsonl(FACTORIAL_ANALYSIS / "adjudication_applied.jsonl")
    return _APPLIED_ROWS_CACHE


def index_adjudicated(family: str, arm: str) -> dict[str, dict[str, Any]]:
    return {
        r["row_key"]: r for r in load_applied_rows()
        if r["cell"] == family and r["arm"] == arm and r.get("seed") is None
    }


def merge_refused_final(runlog_by_key: dict[str, dict[str, Any]],
                         adjudicated_by_key: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Exact port of report.py:merge_refused_final."""
    out: dict[str, dict[str, Any]] = {}
    for rk, lr in runlog_by_key.items():
        if lr.get("refused_v2"):
            out[rk] = {"row_key": rk, "refused_final": True}
        else:
            adj = adjudicated_by_key.get(rk)
            if adj is not None and adj.get("refused_final") is not None:
                out[rk] = {"row_key": rk, "refused_final": bool(adj["refused_final"])}
    return out


def load_arm_merged(family: str, arm: str) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    runlog_by_key = load_runlog_by_key(family, arm)
    adjudicated_by_key = index_adjudicated(family, arm)
    merged = merge_refused_final(runlog_by_key, adjudicated_by_key)
    return merged, runlog_by_key


def paired_bootstrap_diff(arm_bool: np.ndarray, base_bool: np.ndarray,
                           n_boot: int = N_BOOT, seed: int = SEED) -> dict[str, Any]:
    """Row-level bootstrap (paired: same resampled indices for arm and
    baseline arrays, since both are indexed over the identical row set) on
    the rate difference arm - baseline."""
    assert len(arm_bool) == len(base_bool)
    n = len(arm_bool)
    if n == 0:
        return {"point": None, "n": 0, "bootstrap_ci_95": [None, None],
                "n_boot": n_boot, "seed": seed, "empty_population": True}
    point = float(arm_bool.mean() - base_bool.mean())
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(n_boot, n))
    boots = arm_bool[idx].mean(axis=1) - base_bool[idx].mean(axis=1)
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return {"point": point, "n": n, "bootstrap_ci_95": [float(lo), float(hi)],
            "n_boot": n_boot, "seed": seed}


def step1_factorial_cdf_points() -> dict[str, Any]:
    out: dict[str, Any] = {}
    for family in ("qwen35_4b", "mistral7b_v03"):
        out[family] = {}
        base_merged, _ = load_arm_merged(family, "baseline")
        for arm in ("permuted_gate_c_hat", "true_gate_c_hat"):
            merged, runlog = load_arm_merged(family, arm)
            fired_keys = load_fired_keys(family, arm)
            for role in ("confab", "known_correct_answered"):
                role_keys = [rk for rk in fired_keys if runlog.get(rk, {}).get("role") == role]
                present = [rk for rk in role_keys if rk in merged and rk in base_merged]
                missing = len(role_keys) - len(present)
                arm_bool = np.array([merged[rk]["refused_final"] for rk in present], dtype=bool)
                base_bool = np.array([base_merged[rk]["refused_final"] for rk in present], dtype=bool)
                w_arm = wilson(int(arm_bool.sum()), len(arm_bool))
                w_base = wilson(int(base_bool.sum()), len(base_bool))
                diff = paired_bootstrap_diff(arm_bool, base_bool)
                out[family][f"{arm}__{role}"] = {
                    "n_fired_role": len(role_keys), "n_missing_from_merge_or_baseline": missing,
                    "n_present": len(present),
                    "arm_rate_wilson": w_arm, "baseline_rate_wilson": w_base,
                    "paired_diff_bootstrap": diff,
                    "low_n_flag": len(present) < 30,
                }
    return out


# ---------------------------------------------------------------------------
# Step 2 & 3: doubt-snap qwen hs20 permuted_gate row-level dose ladder
# ---------------------------------------------------------------------------

DOSE_MULTIPLIERS = [2, 4, 6, 8, 12, 16, 20]

# Empirically, hs20 well_formed collapses to 0.000 at mult=16 for BOTH roles
# (checked directly from the runlog: mult=12 well_formed 0.771 confab /
# 0.858 known; mult=16 well_formed 0.000 / 0.000 -- a sheer cliff, not a
# gradual decline). Below that cliff "refused" stops meaning "clean semantic
# refusal" and starts meaning "degenerate/garbled, incidentally not matching
# the refusal pattern", so including mult 16/20 in a monotone dose-response
# fit is invalid (it drags empirical rates back to 0 at the top rungs,
# breaking monotonicity). Fit only over rungs where well_formed >= 0.80 for
# that specific role (the same floor the doubt-snap g1 gate itself used).
WELL_FORMED_FLOOR = 0.80


def load_doubt_snap_ladder() -> dict[str, Any]:
    """Returns per-role: row_key -> {dose_multiplier: (dose_abs, refused, well_formed)}"""
    rows = load_jsonl(DOUBT_SNAP_RUNLOG / "hs20__permuted_gate.jsonl")
    by_role: dict[str, dict[str, dict[int, dict[str, Any]]]] = {}
    dose_abs_by_mult: dict[int, float] = {}
    for r in rows:
        role = r["role"]
        rk = r["row_key"]
        m = r["dose_multiplier"]
        dose_abs_by_mult[m] = r["dose_abs"]
        by_role.setdefault(role, {}).setdefault(rk, {})[m] = {
            "refused": bool(r["refused"]), "well_formed": bool(r["well_formed"]),
        }
    return {"by_role": by_role, "dose_abs_by_mult": dose_abs_by_mult}


def per_dose_rates(by_role_rk: dict[str, dict[int, dict[str, Any]]]) -> dict[int, tuple[int, int]]:
    """dose_multiplier -> (n_refused, n_total) across all rows for a role."""
    out: dict[int, tuple[int, int]] = {}
    for m in DOSE_MULTIPLIERS:
        vals = [by_role_rk[rk][m]["refused"] for rk in by_role_rk if m in by_role_rk[rk]]
        out[m] = (sum(vals), len(vals))
    return out


def probit_fit(doses: np.ndarray, rates: np.ndarray, weights: np.ndarray) -> tuple[float, float]:
    """Weighted least squares fit of probit(rate) = a + b*ln(dose); returns
    (mu, sigma) of the implied log-normal margin distribution, where
    P(refused | dose) = Phi((ln(dose) - mu) / sigma), i.e. b = 1/sigma,
    a = -mu/sigma."""
    eps = 1e-4
    clipped = np.clip(rates, eps, 1 - eps)
    y = stats.norm.ppf(clipped)
    x = np.log(doses)
    w = np.sqrt(weights)
    A = np.vstack([np.ones_like(x), x]).T
    Aw = A * w[:, None]
    yw = y * w
    coef, *_ = np.linalg.lstsq(Aw, yw, rcond=None)
    a, b = coef
    sigma = 1.0 / b
    mu = -a * sigma
    return float(mu), float(sigma)


def logistic_fit(doses: np.ndarray, rates: np.ndarray, weights: np.ndarray) -> tuple[float, float]:
    """Weighted least squares fit of logit(rate) = a + b*ln(dose); returns
    (mu, s) of the implied logistic-in-log-dose margin distribution."""
    eps = 1e-4
    clipped = np.clip(rates, eps, 1 - eps)
    y = np.log(clipped / (1 - clipped))
    x = np.log(doses)
    w = np.sqrt(weights)
    A = np.vstack([np.ones_like(x), x]).T
    Aw = A * w[:, None]
    yw = y * w
    coef, *_ = np.linalg.lstsq(Aw, yw, rcond=None)
    a, b = coef
    s = 1.0 / b
    mu = -a * s
    return float(mu), float(s)


def usable_dose_multipliers(by_role_rk: dict[str, dict[int, dict[str, Any]]]) -> list[int]:
    """Rungs where this role's well_formed rate is still >= WELL_FORMED_FLOOR
    (i.e. pre-collapse). Excludes overdrive rungs where 'refused' no longer
    means clean semantic refusal."""
    usable = []
    for m in DOSE_MULTIPLIERS:
        vals = [by_role_rk[rk][m]["well_formed"] for rk in by_role_rk if m in by_role_rk[rk]]
        wf_rate = sum(vals) / len(vals) if vals else 0.0
        if wf_rate >= WELL_FORMED_FLOOR:
            usable.append(m)
    return usable


def bootstrap_probit_fit(by_role_rk: dict[str, dict[int, dict[str, Any]]],
                          dose_abs_by_mult: dict[int, float],
                          n_boot: int = N_BOOT, seed: int = SEED) -> dict[str, Any]:
    row_keys = list(by_role_rk.keys())
    n = len(row_keys)
    mults = usable_dose_multipliers(by_role_rk)
    doses = np.array([dose_abs_by_mult[m] for m in mults])
    # matrix: rows x usable-doses of refused booleans (collapse-regime rungs excluded)
    mat = np.array([[by_role_rk[rk][m]["refused"] for m in mults] for rk in row_keys], dtype=bool)

    def fit_from_mat(m: np.ndarray) -> tuple[float, float, float, float]:
        rates = m.mean(axis=0)
        weights = np.full(len(mults), m.shape[0])
        mu_p, sigma_p = probit_fit(doses, rates, weights)
        mu_l, s_l = logistic_fit(doses, rates, weights)
        return mu_p, sigma_p, mu_l, s_l

    point_mu_p, point_sigma_p, point_mu_l, point_s_l = fit_from_mat(mat)

    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(n_boot, n))
    boot_mu_p = np.empty(n_boot)
    boot_sigma_p = np.empty(n_boot)
    n_degenerate = 0
    for i in range(n_boot):
        m_i = mat[idx[i]]
        rates_i = m_i.mean(axis=0)
        weights_i = np.full(len(mults), m_i.shape[0])
        mu_p, sigma_p = probit_fit(doses, rates_i, weights_i)
        if not np.isfinite(mu_p) or not np.isfinite(sigma_p) or sigma_p <= 0:
            n_degenerate += 1
            boot_mu_p[i] = np.nan
            boot_sigma_p[i] = np.nan
        else:
            boot_mu_p[i] = mu_p
            boot_sigma_p[i] = sigma_p

    valid = np.isfinite(boot_mu_p) & np.isfinite(boot_sigma_p)
    median_dose = math.exp(point_mu_p) if point_sigma_p > 0 else float("nan")
    boot_median_valid = np.exp(boot_mu_p[valid])
    lo, hi = np.percentile(boot_median_valid, [2.5, 97.5])
    lo_sigma, hi_sigma = np.percentile(boot_sigma_p[valid], [2.5, 97.5])

    return {
        "n_rows": n,
        "usable_dose_multipliers": mults,
        "excluded_collapse_multipliers": [m for m in DOSE_MULTIPLIERS if m not in mults],
        "doses_abs": doses.tolist(),
        "empirical_rates": mat.mean(axis=0).tolist(),
        "n_bootstrap_degenerate_fits_excluded": n_degenerate,
        "probit_fit": {"mu": point_mu_p, "sigma": point_sigma_p,
                        "valid_point_fit": point_sigma_p > 0,
                        "median_dose_abs": median_dose,
                        "median_dose_abs_ci95": [float(lo), float(hi)],
                        "sigma_ci95": [float(lo_sigma), float(hi_sigma)]},
        "logistic_fit": {"mu": point_mu_l, "s": point_s_l,
                          "median_dose_abs": math.exp(point_mu_l) if point_s_l > 0 else float("nan")},
        "boot_mu_p": boot_mu_p[valid], "boot_sigma_p": boot_sigma_p[valid],  # kept for downstream anchor propagation
    }


def non_monotone_fraction(by_role_rk: dict[str, dict[int, dict[str, Any]]],
                           mults: list[int]) -> dict[str, Any]:
    """Restricted to the pre-collapse (well-formed) rungs: a row that
    'unrefuses' only because the overdrive collapse rung produced garbled
    output (not a clean re-answer) is a COLLAPSE event, not a construct-level
    non-monotonicity, and the AMENDMENT.md design keeps those as separate
    readouts ('Collapse dose' vs 'Monotonicity flag'). Conflating them would
    inflate the non-monotone fraction with an artifact of the overdrive
    regime rather than the margin construct itself."""
    n_total = len(by_role_rk)
    n_nonmono = 0
    for rk, doses in by_role_rk.items():
        seq = [doses[m]["refused"] for m in mults if m in doses]
        # non-monotone: refused True at some dose, then False at a later (higher) dose
        seen_true = False
        flipped = False
        for v in seq:
            if v:
                seen_true = True
            elif seen_true and not v:
                flipped = True
        if flipped:
            n_nonmono += 1
    p = n_nonmono / n_total if n_total else 0.0
    se = math.sqrt(p * (1 - p) / n_total) if n_total else 0.0
    ceiling_raw = p + 3 * se
    ceiling_rounded = math.ceil(ceiling_raw * 20) / 20  # nearest 0.05 up
    return {"n_total": n_total, "n_nonmonotone": n_nonmono, "observed_fraction": p,
            "se": se, "ceiling_observed_plus_3se": ceiling_raw,
            "ceiling_rounded_up_0.05": ceiling_rounded}


def main() -> None:
    report: dict[str, Any] = {}

    print("[1/6] Factorial CDF points (exact refused_final merge)...", flush=True)
    report["step1_factorial_cdf_points"] = step1_factorial_cdf_points()

    print("[2/6] Loading doubt-snap qwen hs20 dose ladder...", flush=True)
    ladder = load_doubt_snap_ladder()
    dose_abs_by_mult = ladder["dose_abs_by_mult"]
    by_role = ladder["by_role"]

    print("[2/6] Sanity check against doubt-snap AMENDMENT.md cited rates (dose 8x)...", flush=True)
    sanity = {}
    for role in ("confab", "known_correct_answered"):
        rk_map = by_role[role]
        refs = [rk_map[rk][8]["refused"] for rk in rk_map if 8 in rk_map[rk]]
        sanity[role] = {"n": len(refs), "rate_at_dose8": sum(refs) / len(refs)}
    report["step2_sanity_check_dose8_vs_amendment"] = sanity

    print("[2/6] Probit/logistic fits + bootstrap (qwen, both roles)...", flush=True)
    fits = {}
    for role in ("confab", "known_correct_answered"):
        print(f"    role={role}...", flush=True)
        fits[role] = bootstrap_probit_fit(by_role[role], dose_abs_by_mult)
    report["step2_qwen_fits"] = {
        role: {k: v for k, v in d.items() if k not in ("boot_mu_p", "boot_sigma_p")}
        for role, d in fits.items()
    }

    print("[3/6] Non-monotone fraction (qwen, both roles)...", flush=True)
    nonmono = {
        role: non_monotone_fraction(by_role[role], usable_dose_multipliers(by_role[role]))
        for role in by_role
    }
    report["step3_non_monotone_fraction"] = nonmono

    # -----------------------------------------------------------------
    # Mistral: single-point identification under shared-shape assumption
    # -----------------------------------------------------------------
    print("[2/6] Mistral single-point fit (shared qwen shape)...", flush=True)
    fac = report["step1_factorial_cdf_points"]["mistral7b_v03"]
    mistral_ref_dose = 3.665  # AMENDMENT.md design section, mistral hs16 reference dose_abs
    mistral_points = {
        "confab": fac["permuted_gate_c_hat__confab"]["arm_rate_wilson"]["rate"],
        "known_correct_answered": fac["permuted_gate_c_hat__known_correct_answered"]["arm_rate_wilson"]["rate"],
    }
    mistral_fits = {}
    for role in ("confab", "known_correct_answered"):
        sigma_q = fits[role]["probit_fit"]["sigma"]
        boot_sigma_q = fits[role]["boot_sigma_p"]
        rate_m = mistral_points[role]
        n_m = fac[f"permuted_gate_c_hat__{role}"]["arm_rate_wilson"]["n"]
        mu_m = math.log(mistral_ref_dose) - sigma_q * stats.norm.ppf(np.clip(rate_m, 1e-4, 1 - 1e-4))
        median_m = math.exp(mu_m)
        # propagate: resample mistral rate from its binomial (n_m, rate_m) AND
        # pair with the qwen bootstrap sigma draws
        rng = np.random.default_rng(SEED + 1)
        succ = rng.binomial(n_m, rate_m, size=N_BOOT)
        rate_boot = succ / n_m
        sigma_boot = rng.choice(boot_sigma_q, size=N_BOOT, replace=True)
        mu_boot = np.log(mistral_ref_dose) - sigma_boot * stats.norm.ppf(np.clip(rate_boot, 1e-4, 1 - 1e-4))
        median_boot = np.exp(mu_boot)
        lo, hi = np.percentile(median_boot, [2.5, 97.5])
        mistral_fits[role] = {
            "observed_rate_at_reference_dose": rate_m, "n": n_m,
            "reference_dose_abs": mistral_ref_dose,
            "shared_sigma_from_qwen": sigma_q,
            "implied_mu": mu_m, "implied_median_dose_abs": median_m,
            "median_dose_abs_ci95": [float(lo), float(hi)],
            "assumption": "log-normal shape (sigma) shared with qwen fit; only mu identified from this single point",
        }
    report["step2_mistral_single_point_fit"] = mistral_fits

    # median ratio known/confab per family, with propagated CI
    print("[2/6] Median margin ratios (known/confab) per family...", flush=True)
    ratio_out = {}
    # qwen: joint bootstrap of both roles' mu draws (independent role populations, so independent resample streams -> combine directly)
    boot_median_known_q = np.exp(fits["known_correct_answered"]["boot_mu_p"])
    boot_median_confab_q = np.exp(fits["confab"]["boot_mu_p"])
    ratio_q = boot_median_known_q / boot_median_confab_q
    point_ratio_q = fits["known_correct_answered"]["probit_fit"]["median_dose_abs"] / fits["confab"]["probit_fit"]["median_dose_abs"]
    lo_q, hi_q = np.percentile(ratio_q, [2.5, 97.5])
    ratio_out["qwen35_4b"] = {"point_ratio": point_ratio_q, "bootstrap_ci_95": [float(lo_q), float(hi_q)],
                                "ratio_lower_5pct_quantile": float(np.percentile(ratio_q, 5))}

    # mistral: rebuild median draws from the mu_boot computed above (recompute here for both roles, same rng stream reused per role -> independent by construction since separate rng calls per role loop above, but we did not store; recompute deterministically)
    mistral_boot_medians = {}
    for role in ("confab", "known_correct_answered"):
        sigma_q = fits[role]["probit_fit"]["sigma"]
        boot_sigma_q = fits[role]["boot_sigma_p"]
        rate_m = mistral_points[role]
        n_m = fac[f"permuted_gate_c_hat__{role}"]["arm_rate_wilson"]["n"]
        seed_offset = 1 if role == "confab" else 2
        rng = np.random.default_rng(SEED + seed_offset)
        succ = rng.binomial(n_m, rate_m, size=N_BOOT)
        rate_boot = succ / n_m
        sigma_boot = rng.choice(boot_sigma_q, size=N_BOOT, replace=True)
        mu_boot = np.log(mistral_ref_dose) - sigma_boot * stats.norm.ppf(np.clip(rate_boot, 1e-4, 1 - 1e-4))
        mistral_boot_medians[role] = np.exp(mu_boot)
    ratio_m = mistral_boot_medians["known_correct_answered"] / mistral_boot_medians["confab"]
    point_ratio_m = mistral_fits["known_correct_answered"]["implied_median_dose_abs"] / mistral_fits["confab"]["implied_median_dose_abs"]
    lo_m, hi_m = np.percentile(ratio_m, [2.5, 97.5])
    ratio_out["mistral7b_v03"] = {"point_ratio": point_ratio_m, "bootstrap_ci_95": [float(lo_m), float(hi_m)],
                                    "ratio_lower_5pct_quantile": float(np.percentile(ratio_m, 5)),
                                    "note": "single-point identification; interval driven mostly by qwen sigma uncertainty + mistral binomial n"}
    report["step2_median_ratio_known_over_confab"] = ratio_out

    # recommended separation floor = conservative (lower 5%) quantile of the
    # fitted ratio across BOTH families (min of the two, rounded down to 1dp)
    floor_candidates = [ratio_out["qwen35_4b"]["ratio_lower_5pct_quantile"],
                         ratio_out["mistral7b_v03"]["ratio_lower_5pct_quantile"]]
    floor_raw = min(floor_candidates)
    floor_rounded = math.floor(floor_raw * 10) / 10
    report["step2_recommended_separation_floor"] = {
        "per_family_lower_5pct_quantile": {"qwen35_4b": floor_candidates[0], "mistral7b_v03": floor_candidates[1]},
        "min_across_families": floor_raw, "recommended_floor_rounded_down_1dp": floor_rounded,
    }

    # -----------------------------------------------------------------
    # Step 4: retrodiction tolerance
    # -----------------------------------------------------------------
    print("[4/6] Retrodiction tolerances per anchor...", flush=True)
    anchors: dict[str, Any] = {}

    def fit_predicted_rate_ci(role: str, family: str, dose_abs: float) -> dict[str, Any]:
        if family == "qwen35_4b":
            mu_boot = fits[role]["boot_mu_p"]
            sigma_boot = fits[role]["boot_sigma_p"]
        else:
            seed_offset = 1 if role == "confab" else 2
            sigma_q = fits[role]["probit_fit"]["sigma"]
            boot_sigma_q = fits[role]["boot_sigma_p"]
            rate_m = mistral_points[role]
            n_m = fac[f"permuted_gate_c_hat__{role}"]["arm_rate_wilson"]["n"]
            rng = np.random.default_rng(SEED + seed_offset)
            succ = rng.binomial(n_m, rate_m, size=N_BOOT)
            rate_boot = succ / n_m
            sigma_boot = rng.choice(boot_sigma_q, size=N_BOOT, replace=True)
            mu_boot = np.log(mistral_ref_dose) - sigma_boot * stats.norm.ppf(np.clip(rate_boot, 1e-4, 1 - 1e-4))
        pred_boot = stats.norm.cdf((math.log(dose_abs) - mu_boot) / sigma_boot)
        lo, hi = np.percentile(pred_boot, [2.5, 97.5])
        return {"predicted_rate_point": float(np.median(pred_boot)),
                "predicted_rate_ci95": [float(lo), float(hi)],
                "predicted_half_width": float((hi - lo) / 2)}

    qwen_setpoint = dose_abs_by_mult[8]  # 12.608
    for family, dose in (("qwen35_4b", qwen_setpoint), ("mistral7b_v03", mistral_ref_dose)):
        role_map = {"confab": "confab", "known_correct_answered": "known_correct_answered"}
        for arm in ("permuted_gate_c_hat", "true_gate_c_hat"):
            for role in role_map:
                key = f"{family}__{arm}__{role}"
                obs = report["step1_factorial_cdf_points"][family][f"{arm}__{role}"]["arm_rate_wilson"]
                obs_half_width = (obs["wilson_ci_95"][1] - obs["wilson_ci_95"][0]) / 2
                pred = fit_predicted_rate_ci(role, family, dose)
                tol = obs_half_width + pred["predicted_half_width"]
                anchors[key] = {"observed_rate": obs["rate"], "observed_n": obs["n"],
                                 "observed_wilson_half_width": obs_half_width,
                                 **pred, "tolerance": tol,
                                 "note": "true_gate_c_hat is NOT predictable from the no-gate margin CDF alone (fired-set composition differs); reported for completeness, tolerance treated as a diagnostic not a criterion input for that arm"}

    # doubt-snap permuted knowns anchor (0.056, hs20 dose 8, qwen) -- this IS
    # the same data the qwen fit was trained on, so its "prediction" is in-
    # sample; reported honestly as such.
    obs_ds = wilson(sanity["known_correct_answered"]["n"] * 0 + int(sanity["known_correct_answered"]["rate_at_dose8"] * sanity["known_correct_answered"]["n"]), sanity["known_correct_answered"]["n"])
    pred_ds = fit_predicted_rate_ci("known_correct_answered", "qwen35_4b", qwen_setpoint)
    obs_half_width_ds = (obs_ds["wilson_ci_95"][1] - obs_ds["wilson_ci_95"][0]) / 2
    anchors["doubt_snap__qwen35_4b__permuted_known_dose8"] = {
        "observed_rate": obs_ds["rate"], "observed_n": obs_ds["n"],
        "observed_wilson_half_width": obs_half_width_ds,
        **pred_ds, "tolerance": obs_half_width_ds + pred_ds["predicted_half_width"],
        "note": "IN-SAMPLE: this is the same qwen hs20 dose-ladder data the fit was trained on; not an independent retrodiction test",
    }

    report["step4_retrodiction_tolerances"] = anchors
    tol_values_for_uniform = [v["tolerance"] for k, v in anchors.items() if "true_gate" not in k]
    uniform_tol_raw = max(tol_values_for_uniform)
    uniform_tol_rounded = math.ceil(uniform_tol_raw * 20) / 20
    report["step4_recommended_uniform_tolerance"] = {
        "max_over_permuted_and_doubt_snap_anchors": uniform_tol_raw,
        "rounded_up_nearest_0.05": uniform_tol_rounded,
        "excluded_true_gate_anchors_reason": "true_gate arms are not predictable from a no-gate margin CDF; their tolerances are reported in step4_retrodiction_tolerances for reference but excluded from the uniform recommendation",
    }

    # -----------------------------------------------------------------
    # Step 5: power / subsample check
    # -----------------------------------------------------------------
    print("[5/6] Power / subsample check...", flush=True)
    power = {}
    for n_confab in (200, 400, 600):
        hw = {}
        for p in (0.1, 0.5, 0.9):
            w = wilson(int(round(p * n_confab)), n_confab)
            hw[str(p)] = (w["wilson_ci_95"][1] - w["wilson_ci_95"][0]) / 2
        power[str(n_confab)] = hw
    n_known_qwen, n_known_mistral = 360, 382
    for label, n in (("known_qwen_360", n_known_qwen), ("known_mistral_382", n_known_mistral)):
        hw = {}
        for p in (0.1, 0.5, 0.9):
            w = wilson(int(round(p * n)), n)
            hw[str(p)] = (w["wilson_ci_95"][1] - w["wilson_ci_95"][0]) / 2
        power[label] = hw
    report["step5_power_wilson_half_widths"] = power

    floor = report["step2_recommended_separation_floor"]["recommended_floor_rounded_down_1dp"]
    # rung quantization: doses in the M1 ladder are factor-2 steps (0.125..64x
    # per the drafter proposal); check whether floor is distinguishable from
    # 1.0 given the qwen/mistral bootstrap ratio CIs already computed
    distinguishable_from_1 = {
        "qwen35_4b": ratio_out["qwen35_4b"]["bootstrap_ci_95"][0] > 1.0,
        "mistral7b_v03": ratio_out["mistral7b_v03"]["bootstrap_ci_95"][0] > 1.0,
    }
    report["step5_floor_distinguishable_from_1.0"] = distinguishable_from_1
    # recommended n_confab: smallest of {200,400,600} whose Wilson half-width
    # at p=0.5 (worst case) is comfortably (<=0.5x) smaller than the
    # separation-floor-implied rate gap; use 400 unless 200 already clears a
    # conservative 0.05 half-width bar at p=0.5
    n_confab_rec = 400
    if power["200"]["0.5"] <= 0.05:
        n_confab_rec = 200
    report["step5_recommended_n_confab"] = {
        "value": n_confab_rec,
        "basis": "smallest evaluated n whose Wilson half-width at p=0.5 (worst case) is <=0.05; 400 is the drafter proposal and clears this comfortably (half-width computed above)",
    }

    # -----------------------------------------------------------------
    # Step 6: ladder span check
    # -----------------------------------------------------------------
    print("[6/6] Ladder span check...", flush=True)
    span = {}
    for family, fit_source in (("qwen35_4b", "direct_fit"), ("mistral7b_v03", "single_point_shared_shape")):
        if family == "qwen35_4b":
            mu_c, sigma_c = fits["confab"]["probit_fit"]["mu"], fits["confab"]["probit_fit"]["sigma"]
            mu_k, sigma_k = fits["known_correct_answered"]["probit_fit"]["mu"], fits["known_correct_answered"]["probit_fit"]["sigma"]
            ref_dose = qwen_setpoint
        else:
            mu_c, sigma_c = mistral_fits["confab"]["implied_mu"], mistral_fits["confab"]["shared_sigma_from_qwen"]
            mu_k, sigma_k = mistral_fits["known_correct_answered"]["implied_mu"], mistral_fits["known_correct_answered"]["shared_sigma_from_qwen"]
            ref_dose = mistral_ref_dose
        dose_p05_confab = math.exp(mu_c + sigma_c * stats.norm.ppf(0.05))
        dose_p95_known = math.exp(mu_k + sigma_k * stats.norm.ppf(0.95))
        ladder_bottom = 0.125 * ref_dose
        ladder_top = 64.0 * ref_dose
        span[family] = {
            "fit_source": fit_source,
            "dose_at_confab_cdf_0.05": dose_p05_confab,
            "dose_at_known_cdf_0.95": dose_p95_known,
            "ladder_bottom_0.125x": ladder_bottom, "ladder_top_64x": ladder_top,
            "bottom_covers_with_spare_rung": dose_p05_confab >= ladder_bottom * 2,
            "top_covers_with_spare_rung": dose_p95_known <= ladder_top / 2,
            "note": "collapse boundary is NOT derivable from existing data; needs the GPU preflight diagnostic per the amendment's own gates section",
        }
    report["step6_ladder_span_check"] = span

    # strip large arrays before dumping
    def clean(obj):
        if isinstance(obj, dict):
            return {k: clean(v) for k, v in obj.items() if k not in ("boot_mu_p", "boot_sigma_p")}
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        return obj

    report_clean = clean(report)
    out_path = OUT_DIR / "threshold_derivation_report.json"
    out_path.write_text(json.dumps(report_clean, indent=2))
    print(f"Wrote {out_path}", flush=True)


if __name__ == "__main__":
    main()
