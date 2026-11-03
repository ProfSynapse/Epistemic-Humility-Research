"""Deterministic FIT-screen eligibility, objective and tie-breaks.

The screen uses only the frozen detector v2 (an exploratory selection statistic,
not an accepted-abstention result).  All thresholds come from cell.yaml and are
compared as exact fractions of counts.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any

from .config import Cell
from .util import HarnessError


def _frac(x: Any) -> Fraction:
    return Fraction(str(x))


def screen_counts(graded: list[dict]) -> dict:
    out = {}
    for role in ("confab", "known_correct"):
        sub = [r for r in graded if r["role"] == role]
        out[role] = {"n": len(sub), "refused": sum(r["refused_v2"] for r in sub),
                     "correct": sum(r["correct"] for r in sub), "well_formed": sum(r["well_formed"] for r in sub),
                     "degenerate": sum(r["degenerate"] for r in sub)}
        if not sub:
            raise HarnessError("SCREEN_EMPTY", f"no {role} rows in a screen job")
    return out


def baseline_gate(cell: Cell, baseline: dict) -> dict:
    """Instrument check: unpatched known-correct rate (over ALL known rows) must reach the floor."""
    k = baseline["known_correct"]
    rate = Fraction(k["correct"], k["n"])
    floor = _frac(cell.gates["integrity"]["known_baseline_min_correct"])
    return {"known_correct_rate": float(rate), "floor": float(floor), "passed": rate >= floor,
            "n": k["n"], "correct": k["correct"]}


def evaluate(cell: Cell, baseline: dict, cand: dict, validation: dict) -> dict:
    s = cell.cell["selection"]
    c, k = cand["confab"], cand["known_correct"]
    bk = baseline["known_correct"]
    confab_refusal = Fraction(c["refused"], c["n"])
    known_refusal = Fraction(k["refused"], k["n"])
    base_correct = Fraction(bk["correct"], bk["n"])
    retention = None if base_correct == 0 else Fraction(k["correct"], k["n"]) / base_correct
    checks = {
        "confab_refusal": confab_refusal >= _frac(s["min_confab_refusal"]),
        "known_false_refusal": known_refusal <= _frac(s["max_known_refusal"]),
        "known_correct_retention": retention is not None and retention >= _frac(s["min_known_correct_retention"]),
        "well_formed_confab": Fraction(c["well_formed"], c["n"]) >= _frac(s["min_well_formed"]),
        "well_formed_known": Fraction(k["well_formed"], k["n"]) >= _frac(s["min_well_formed"]),
    }
    objective = confab_refusal - 2 * known_refusal
    return {"eligible": all(checks.values()), "checks": checks, "objective": float(objective),
            "objective_exact": f"{objective.numerator}/{objective.denominator}",
            "confab_refusal": float(confab_refusal), "known_false_refusal": float(known_refusal),
            "known_correct_retention": None if retention is None else float(retention),
            "delta_frobenius": validation["delta_frobenius"], "block": validation["block"],
            "scale": validation["scale"], "candidate": validation["cand_id"]}


def choose(evaluations: list[dict], *, expected: int | None = None) -> dict:
    """Max objective; ties -> smaller realized delta, lower block, lower scale. No eligible -> stop."""
    if expected is not None and len(evaluations) != expected:
        raise HarnessError("SELECTION_INCOMPLETE", f"{len(evaluations)} evaluated candidates, expected {expected}")
    eligible = [e for e in evaluations if e["eligible"]]
    ranking = sorted(eligible, key=lambda e: (-Fraction(e["objective_exact"]), e["delta_frobenius"], e["block"], e["scale"]))
    if not ranking:
        return {"status": "no_eligible", "winner": None, "ranking": []}
    return {"status": "selected", "winner": ranking[0]["candidate"],
            "ranking": [e["candidate"] for e in ranking]}
