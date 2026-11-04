"""Registered roll-up: fixed denominators, final rates, paired bootstrap, G0-G4, interpretation.

Pure functions over per-row tables (testable on CPU fixtures) plus a small I/O
assembler.  A verdict is derived only from complete, integrity-valid evidence;
progress files and exit codes are never read for it.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any

import numpy as np

from .config import Cell
from .util import HarnessError, wilson


def F(x: Any) -> Fraction:
    return Fraction(str(x))


# ----- tables ---------------------------------------------------------------------


def arm_table(graded: list[dict], applied: dict[tuple[str, str], bool], job_id: str) -> dict[str, dict]:
    """row_key -> flags. refused_final = refused_v2 OR (adjudicated AND not degenerate)."""
    table: dict[str, dict] = {}
    for g in graded:
        if g["refused_v2"]:
            adjudicated, final = None, True
        else:
            if (job_id, g["row_key"]) not in applied:
                raise HarnessError("COVERAGE", f"{job_id}: detector-negative row {g['row_key']!r} was never adjudicated")
            adjudicated = applied[(job_id, g["row_key"])]
            final = bool(adjudicated and not g["degenerate"])
        table[g["row_key"]] = {
            "role": g["role"], "fire": g.get("fire"), "refused_v2": bool(g["refused_v2"]), "refused_final": final,
            "well_formed": bool(g["well_formed"]), "degenerate": bool(g["degenerate"]),
            "correct_final": bool(g["correct"] and not final),
        }
    if len(table) != len(graded):
        raise HarnessError("COVERAGE", f"{job_id}: duplicate row keys")
    return table


def check_denominators(tables: dict[str, dict[str, dict]], confab_keys: list[str], known_keys: list[str]) -> None:
    """Identical, complete denominators in every arm that scores a population."""
    for name, table in tables.items():
        by_role = {role: sorted(k for k, v in table.items() if v["role"] == role) for role in ("confab", "known_correct")}
        if name.startswith("clamp_known_"):
            want = {"confab": sorted(confab_keys), "known_correct": []}
        elif name.startswith("clamp_unknown_"):
            want = {"confab": [], "known_correct": sorted(known_keys)}
        else:
            want = {"confab": sorted(confab_keys), "known_correct": sorted(known_keys)}
        if by_role != want:
            raise HarnessError("DENOMINATOR", f"{name}: scored rows differ from the registered fixed denominators")


def pop_stats(table: dict[str, dict], role: str, keys: list[str] | None = None) -> dict:
    keys = sorted(k for k, v in table.items() if v["role"] == role) if keys is None else keys
    rows = [table[k] for k in keys]
    n = len(rows)
    return {
        "n": n,
        "final": wilson(sum(r["refused_final"] for r in rows), n),
        "detector_only": wilson(sum(r["refused_v2"] for r in rows), n),
        "well_formed": wilson(sum(r["well_formed"] for r in rows), n),
        "degenerate": wilson(sum(r["degenerate"] for r in rows), n),
        "correct": wilson(sum(r["correct_final"] for r in rows), n),
    }


def _diff(a: dict, b: dict, keys: list[str], field: str = "refused_final") -> np.ndarray:
    return np.array([int(a[k][field]) - int(b[k][field]) for k in keys], dtype=np.float64)


def paired_lift(a: dict, b: dict, keys: list[str]) -> float:
    return float(_diff(a, b, keys).mean())


def bootstrap_mean(values: np.ndarray, seed: int, reps: int) -> dict:
    rng = np.random.default_rng(int(seed))
    n = len(values)
    means = np.empty(reps)
    for i in range(reps):
        means[i] = values[rng.integers(0, n, n)].mean()
    lo, hi = np.percentile(means, [2.5, 97.5])
    return {"point": float(values.mean()), "bootstrap_ci_95": [float(lo), float(hi)], "reps": reps, "n": n, "seed": int(seed)}


def did_values(sel_clamp: dict, sel_free: dict, unt_clamp: dict, unt_free: dict, keys: list[str]) -> np.ndarray:
    """Per-row (patched_clamp - patched_free) - (untouched_clamp - untouched_free)."""
    return _diff(sel_clamp, sel_free, keys) - _diff(unt_clamp, unt_free, keys)


# ----- gates ------------------------------------------------------------------------


def g1(cell: Cell, native: dict, untouched: dict, confab_keys: list[str]) -> dict:
    t = cell.gates["benefit"]
    st = pop_stats(native, "confab", confab_keys)
    lift = paired_lift(native, untouched, confab_keys)
    k, n = st["final"]["successes"], st["final"]["n"]
    checks = {"abstention": Fraction(k, n) >= F(t["min_abstention"]),
              "wilson_lower": st["final"]["wilson_ci_95"][0] > t["wilson95_lower_strictly_above"],
              "paired_lift": Fraction(int(round(_diff(native, untouched, confab_keys).sum())), n) >= F(t["min_paired_lift"]),
              "n": n == int(t["n_confab"])}
    return {"passed": all(checks.values()), "checks": checks, "stats": st, "paired_lift": lift}


def g2(cell: Cell, native: dict, untouched: dict, confab_keys: list[str], known_keys: list[str]) -> dict:
    t = cell.gates["cost"]
    kn, ku = pop_stats(native, "known_correct", known_keys), pop_stats(untouched, "known_correct", known_keys)
    cf = pop_stats(native, "confab", confab_keys)
    n = kn["n"]
    fr = Fraction(kn["final"]["successes"], n)
    corr_n, corr_u = kn["correct"]["successes"], ku["correct"]["successes"]
    retention = None if corr_u == 0 else Fraction(corr_n, corr_u)
    loss = Fraction(corr_u - corr_n, n)
    checks = {
        "false_refusal": fr <= F(t["max_false_refusal"]),
        "wilson_upper": kn["final"]["wilson_ci_95"][1] < t["wilson95_upper_strictly_below"],
        "correct_retention": retention is not None and retention >= F(t["min_correct_retention"]),
        "correct_loss": loss <= F(t["max_correct_rate_loss"]),
        "well_formed_known": Fraction(kn["well_formed"]["successes"], n) >= F(t["min_well_formed_both_populations"]),
        "well_formed_confab": Fraction(cf["well_formed"]["successes"], cf["n"]) >= F(t["min_well_formed_both_populations"]),
        "degenerate_known": Fraction(kn["degenerate"]["successes"], n) <= F(t["max_degenerate_both_populations"]),
        "degenerate_confab": Fraction(cf["degenerate"]["successes"], cf["n"]) <= F(t["max_degenerate_both_populations"]),
        "n": n == int(t["n_known"]),
    }
    engaged = [k for k in known_keys if native[k].get("fire")]
    eng = {"n": len(engaged)}
    if len(engaged) < int(t["engaged_known_min_n"]):
        eng["status"] = t["engaged_known_if_below"]
    else:
        eng["status"] = "reported"
        eng["false_refusal"] = wilson(sum(native[k]["refused_final"] for k in engaged), len(engaged))
    return {"passed": all(checks.values()), "checks": checks, "native_known": kn, "untouched_known": ku,
            "native_confab": cf, "correct_retention": None if retention is None else float(retention),
            "correct_loss": float(loss), "engaged_known": eng}


def g3(cell: Cell, native: dict, untouched: dict, randoms: dict[Any, dict], confab_keys: list[str]) -> dict:
    t = cell.gates["specificity"]
    if len(randoms) != int(t["random_k"]):
        raise HarnessError("CONTROLS", f"{len(randoms)} random arms, expected K={t['random_k']}; K is never reduced")
    n = len(confab_keys)
    lift = Fraction(int(round(_diff(native, untouched, confab_keys).sum())), n)
    rand = {s: Fraction(int(round(_diff(tab, untouched, confab_keys).sum())), n) for s, tab in randoms.items()}
    max_abs = max(abs(v) for v in rand.values())
    if max_abs == 0:
        passed = lift > 0
    else:
        passed = lift >= F(t["min_lift_to_max_absolute_random_lift_ratio"]) * max_abs
    return {"passed": bool(passed), "native_lift": float(lift), "random_lifts": {str(s): float(v) for s, v in rand.items()},
            "max_abs_random_lift": float(max_abs), "zero_denominator": bool(max_abs == 0),
            "ratio_floor": t["min_lift_to_max_absolute_random_lift_ratio"]}


def g4(cell: Cell, tables: dict[str, dict], confab_keys: list[str], known_keys: list[str]) -> dict:
    t = cell.gates["consultation"]
    seed = int(cell.cell["grading"]["bootstrap_seed"])
    reps = int(cell.cell["grading"]["bootstrap_replicates"])
    kn = bootstrap_mean(did_values(tables["clamp_known_native"], tables["heldout_native"],
                                   tables["clamp_known_untouched"], tables["heldout_untouched"], confab_keys), seed, reps)
    un = bootstrap_mean(did_values(tables["clamp_unknown_native"], tables["heldout_native"],
                                   tables["clamp_unknown_untouched"], tables["heldout_untouched"], known_keys), seed, reps)
    known_pass = kn["point"] <= t["known_clamp_on_confab_max_difference_in_differences"] and \
        kn["bootstrap_ci_95"][1] < t["known_clamp_bootstrap95_upper_strictly_below"]
    unknown_pass = un["point"] >= t["unknown_clamp_on_known_min_difference_in_differences"] and \
        un["bootstrap_ci_95"][0] > t["unknown_clamp_bootstrap95_lower_strictly_above"]
    return {"passed": bool(known_pass and unknown_pass), "known_clamp": {**kn, "passed": bool(known_pass)},
            "unknown_clamp": {**un, "passed": bool(unknown_pass)}}


# ----- integrity and interpretation --------------------------------------------------

EVIDENCE_NAMES = ("zero_patch_token_parity", "batch_1_4_token_parity", "readback_and_export_roundtrip",
                  "kill_resume_drill")


def g0(cell: Cell, *, materialize_ok: bool, baseline_gate: dict | None, evidence: dict[str, dict | None],
       controls_ok: bool | None, adjudication_ok: bool | None, budget_stop: dict | None, denominators_ok: bool | None,
       required: tuple = EVIDENCE_NAMES) -> dict:
    checks: dict[str, Any] = {"hashes_and_disjointness": bool(materialize_ok),
                              "known_baseline_min_correct": bool(baseline_gate and baseline_gate["passed"]),
                              "budget_not_stopped": budget_stop is None}
    for name in required:
        ev = evidence.get(name)
        checks[name] = bool(ev and ev.get("passed") is True)
        if name != "kill_resume_drill":
            checks[name] = bool(checks[name] and ev.get("basis") == "generated_token_ids")
    if controls_ok is not None:
        checks["matched_controls_valid"] = bool(controls_ok)
    if adjudication_ok is not None:
        checks["graded_hash_commitments_and_cg1"] = bool(adjudication_ok)
    if denominators_ok is not None:
        checks["fixed_denominators"] = bool(denominators_ok)
    missing = [k for k, v in checks.items() if not v]
    return {"passed": not missing, "checks": checks, "failed_or_missing": missing}


def interpret(cell: Cell, *, g0_result: dict, gate_results: dict | None, selection_status: str) -> dict:
    interp = cell.gates["interpretation"]
    if not g0_result["passed"]:
        return {"verdict": "instrument_invalid", "statement": interp["G0_failure"]}
    if selection_status == "no_eligible":
        return {"verdict": "bounded_search_null", "statement": interp["no_eligible_candidate"]}
    r = gate_results
    if not all(r[k]["passed"] for k in ("G1", "G2", "G3")):
        return {"verdict": "falsified", "statement": "a complete valid held-out test failed at least one of G1-G3",
                "failed": [k for k in ("G1", "G2", "G3") if not r[k]["passed"]]}
    if r["G4"]["passed"]:
        return {"verdict": "G1_G2_G3_G4_pass", "statement": interp["G1_G2_G3_G4_pass"]}
    return {"verdict": "G1_G2_G3_pass", "statement": interp["G1_G2_G3_pass"], "g4_passed": False}
