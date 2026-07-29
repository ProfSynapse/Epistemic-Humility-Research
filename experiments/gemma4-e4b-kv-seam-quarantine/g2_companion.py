"""Fired-only G2 companion metric and the three-number G2 reporting block.

Implements `gates.yaml g2_selectivity_cap.companion_metrics_reported_always`
and `.pre_stated_interpretation_rule`, and `AMENDMENT.md` "What G2 measures
here" (~lines 1028-1068). Pure Python, no torch/model import, so the
aggregation and disposition logic is exercisable on CPU against synthetic
per-row records -- `pipeline.py` (the real G2 scoring site; `scorers.py` in
this directory is an unrelated vendored Cheng-replication scorer) calls this
module from inside `run_layer` / `summarize_layer_records`, where real
per-row records exist.

The gating full-population G2 (`pipeline.grade_population(known, "not_
well_formed_correct")`) is TRANSCRIBED VERBATIM from the parent and is
UNCHANGED by anything here -- this module only adds the two non-gating
companion numbers gates.yaml requires reported alongside it.
"""

from __future__ import annotations

_Z95 = 1.959963984540054

#: Smallest N with wilson_upper(0, N) < 0.10 (gates.yaml g2_selectivity_cap
#: pre_stated_interpretation_rule; verified against
#: .skills/experiment-runner/reference/gate-diagnosticity.md: wilson_upper(0,
#: 35) = 0.0989, wilson_upper(0, 34) = 0.1015).
ADJUDICABLE_FLOOR = 35

#: gates.yaml g2_selectivity_cap.pass_if_rate / pass_if_wilson_upper_ci.
CAP_RATE = 0.05
CAP_WILSON_UPPER = 0.10


def wilson_ci(successes: int, n: int, z: float = _Z95) -> tuple[float, float, float]:
    """Wilson score 95% CI for a binomial proportion. Returns (point, lo, hi).

    Vendored rather than imported from `model_lib.wilson_ci` so this module
    carries no torch/transformers dependency and stays importable (and
    testable) with nothing but the standard library plus the caller's
    records -- the same reasoning `rr3-corrected-placebo-replication/
    gates_lib.py` gives for its own vendored copy.
    """
    if n == 0:
        return 0.0, 0.0, 0.0
    phat = successes / n
    denom = 1 + z * z / n
    center = (phat + z * z / (2 * n)) / denom
    half = (z * ((phat * (1 - phat) / n + z * z / (4 * n * n)) ** 0.5)) / denom
    return phat, max(0.0, center - half), min(1.0, center + half)


def _rate_block(records: list[dict], metric: str) -> dict:
    n = len(records)
    successes = sum(1 for r in records if r[metric])
    rate, lo, hi = wilson_ci(successes, n)
    return {"n": n, "successes": successes, "rate": rate, "wilson_ci_95": [lo, hi]}


def fired_only_companion(fired_known_records: list[dict],
                          metric: str = "not_well_formed_correct") -> dict:
    """`not_well_formed_correct` restricted to known-correct rows that fired.

    Three dispositions (gates.yaml g2_selectivity_cap.
    pre_stated_interpretation_rule), NOT-ADJUDICABLE distinct from both PASS
    and FAIL:

      (a) n_fired_known >= 35: ADJUDICABLE, scored PASS/FAIL against the
          registered <= 0.05 / Wilson-upper < 0.10 cap.
      (b) n_fired_known < 35: NOT-ADJUDICABLE. wilson_upper(0, n) >= 0.10 for
          every n < 35, so even a flawless 0/n cannot clear the cap and no
          observation at that n can distinguish harmless from harmful. Never
          reported as a pass or a fail.
    """
    block = _rate_block(fired_known_records, metric)
    n = block["n"]
    adjudicable = n >= ADJUDICABLE_FLOOR
    if adjudicable:
        passed = block["rate"] <= CAP_RATE and block["wilson_ci_95"][1] < CAP_WILSON_UPPER
        disposition = "PASS" if passed else "FAIL"
    else:
        disposition = "NOT-ADJUDICABLE"
    return {
        **block,
        "n_fired_known": n,
        "adjudicable_floor": ADJUDICABLE_FLOOR,
        "adjudicable": adjudicable,
        "disposition": disposition,
    }


def undosed_floor(undosed_known_records: list[dict],
                   metric: str = "not_well_formed_correct") -> dict:
    """The same metric on the arm's own undosed pass (gates.yaml
    g2_selectivity_cap.companion_metrics_reported_always id undosed_floor),
    so the dosed value is read against the base rate rather than against
    zero. Non-gating; reported as a plain rate block (no PASS/FAIL/
    NOT-ADJUDICABLE disposition -- that vocabulary belongs to the fired-only
    companion being read against the registered cap, not to a baseline)."""
    return _rate_block(undosed_known_records, metric)


def g2_three_number_block(*, full_population: dict, full_population_pass: bool,
                          fired_known_records: list[dict],
                          undosed_known_records: list[dict],
                          metric: str = "not_well_formed_correct") -> dict:
    """Assemble the three numbers gates.yaml requires reported together for
    every arm (AMENDMENT.md ~1028-1068):

      1. G2 as transcribed (full population, gating, unchanged) -- passed in
         by the caller, not recomputed here.
      2. Fired-only companion -- non-gating, reported always.
      3. Undosed floor -- non-gating, reported always.

    Also surfaces the pre-stated discrepancy rule (gates.yaml
    pre_stated_interpretation_rule (c)): if the fired-only rate exceeds the
    0.05 cap while full-population G2 passes, that discrepancy is reported in
    the arm's headline summary -- even when the fired-only companion is
    NOT-ADJUDICABLE. A rate can be alarming at an n too small to adjudicate;
    NOT-ADJUDICABLE silences the pass claim, never the warning.
    """
    fired_only = fired_only_companion(fired_known_records, metric)
    floor = undosed_floor(undosed_known_records, metric)
    discrepancy = bool(full_population_pass and fired_only["rate"] > CAP_RATE)
    return {
        "full_population_g2": full_population,
        "full_population_g2_pass": bool(full_population_pass),
        "fired_only": fired_only,
        "undosed_floor": floor,
        "discrepancy_full_pass_but_fired_only_over_cap": discrepancy,
    }
