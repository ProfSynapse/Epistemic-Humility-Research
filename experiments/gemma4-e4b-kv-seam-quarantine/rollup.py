#!/usr/bin/env python3
"""Per-arm/per-gate aggregation driver (cell.yaml integration_status.done
"Still outstanding: ... rollup.py", AMENDMENT.md ~line 1499).

No registered spec beyond the name existed at build time (checked: neither
AMENDMENT.md nor NOTEBOOK.md pins an output schema for this script), so this
is the MINIMAL rollup cell.yaml's own gate list implies: per arm, G1/G2 (the
three-number G2 block: full population + fired-only companion + undosed
floor), G3 for the two P-arm sites, C1, the A_lin Part 2 discrimination band,
and the primary contrast -- every number carrying a Wilson CI where one
applies, and every stage FAIL-CLOSED on a missing input (raises naming the
missing stage; never a silent default).

Two layers:

  * Pure verdict functions (`g1_verdict`, `g2_full_population_verdict`,
    `g3_verdict`, `c1_verdict`, `primary_contrast_verdict`) take
    already-computed rate blocks / summaries and apply the registered
    thresholds. No file I/O, no torch/model import -- directly CPU-testable
    against synthetic per-row aggregates.
  * `build_rollup()` is the thin I/O driver: it locates each arm's committed
    JSON artifact by the naming convention `run_contrast.py` / `alin_sweep.py`
    already use, and raises `RollupInputMissing` (naming the stage that
    produces the missing file) rather than defaulting anything.

Vendors its own Wilson CI and gate thresholds (does not import run_contrast.py
/ pipeline.py / g2_companion.py at module level) so this module carries no
torch/transformers/MechInterp dependency and stays importable and testable
with nothing but the standard library -- the same reasoning
`g2_companion.py` and `rr3-corrected-placebo-replication/gates_lib.py` give
for their own vendored copies. `g2_companion`'s ADJUDICABLE_FLOOR/CAP_RATE/
CAP_WILSON_UPPER constants are duplicated here rather than imported for the
same reason; a change to one must be made in both by hand, which is the
correct friction for a LOCKED, transcribed-verbatim gate.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent

_Z95 = 1.959963984540054

# --- G1 (gates.yaml g1_actuation_floor, TRANSCRIBED VERBATIM) --------------
G1_FLOOR_RATE = 0.50
G1_FLOOR_WILSON_LOWER = 0.40

# --- G2 (gates.yaml g2_selectivity_cap, TRANSCRIBED VERBATIM) --------------
G2_CAP_RATE = 0.05
G2_CAP_WILSON_UPPER = 0.10
G2_ADJUDICABLE_FLOOR = 35  # duplicated from g2_companion.py; see module docstring

# --- G3 (gates.yaml g3_direction_specificity) ------------------------------
G3_EFFECT_RATIO_FLOOR = 3.0

# --- G0-C1 (gates.yaml g0_c1_precondition_control) -------------------------
C1_KNOWN_CORRECT_ABS_DELTA_CAP = 0.05
C1_KNOWN_CORRECT_WILSON_DEGRADE_CAP = 0.10
C1_HEDGE_RATE_CAP = 0.05
C1_NLL_REL_TOLERANCE = 0.10

# --- G0-ALIN Part 2 (gates.yaml g0_alin_discrimination_measurement) --------
ALIN_DISCRIMINATION_BAND = 0.05

#: Arm registry (cell.yaml `arms`). site_hs=None means the arm carries no
#: injection site of its own (C0/C1). A6 and D4 are the SAME cell
#: (cell.yaml arms.A6.coincides_with) -- both keys resolve the same
#: artifact.
ARM_REGISTRY: dict[str, dict[str, Any]] = {
    "A1": {"site_hs": 38, "site_set": "midband", "kv_sharing": "on"},
    "A2": {"site_hs": 38, "site_set": "midband", "kv_sharing": "off"},
    "A3": {"site_hs": 22, "site_set": "seam_pair", "kv_sharing": "on"},
    "A4": {"site_hs": 22, "site_set": "seam_pair", "kv_sharing": "off"},
    "A5": {"site_hs": 24, "site_set": "seam_pair", "kv_sharing": "on"},
    "A6": {"site_hs": 23, "site_set": "shallow_ladder", "kv_sharing": "on"},  # == D4
    "D1": {"site_hs": 15, "site_set": "shallow_ladder", "kv_sharing": "on"},
    "D2": {"site_hs": 18, "site_set": "shallow_ladder", "kv_sharing": "on"},
    "D3": {"site_hs": 20, "site_set": "shallow_ladder", "kv_sharing": "on"},
    "D4": {"site_hs": 23, "site_set": "shallow_ladder", "kv_sharing": "on"},  # == A6
}
#: P-arms are matched to a true arm (cell.yaml k_number_of_draws.
#: scope_of_this_control: hs22/hs24 only).
PLACEBO_MATCH: dict[str, str] = {"P1": "A3", "P2": "A5"}


class RollupInputMissing(FileNotFoundError):
    """Raised naming the specific missing artifact/stage. Never caught to
    supply a silent default -- a missing input is reported as missing."""


def wilson_ci(successes: int, n: int, z: float = _Z95) -> tuple[float, float, float]:
    if n == 0:
        return 0.0, 0.0, 0.0
    phat = successes / n
    denom = 1 + z * z / n
    center = (phat + z * z / (2 * n)) / denom
    half = (z * ((phat * (1 - phat) / n + z * z / (4 * n * n)) ** 0.5)) / denom
    return phat, max(0.0, center - half), min(1.0, center + half)


def newcombe_diff_interval(successes1: int, n1: int, successes2: int, n2: int,
                          z: float = _Z95) -> tuple[float, float, float]:
    """Newcombe (1998) hybrid score interval (method 10) for p1 - p2.

    Built from each proportion's own single-sample Wilson interval via
    `wilson_ci` -- no separate two-proportion CI machinery to duplicate.
    d = p1 - p2; interval = [d - sqrt((p1-l1)^2 + (u2-p2)^2),
                             d + sqrt((u1-p1)^2 + (p2-l2)^2)], where (l1,u1)
    is p1's own Wilson interval and (l2,u2) is p2's.

    Fails closed on n1 == 0 or n2 == 0 rather than delegating to `wilson_ci`'s
    own n=0 special case: that case returns a zero-width (0.0, 0.0, 0.0)
    interval, which here would silently manufacture a confident, un-earned
    PASS on the difference check instead of reporting the input as unusable.
    """
    if n1 <= 0 or n2 <= 0:
        raise ValueError(
            f"newcombe_diff_interval requires n1 > 0 and n2 > 0; got n1={n1}, n2={n2}"
        )
    p1, l1, u1 = wilson_ci(successes1, n1, z)
    p2, l2, u2 = wilson_ci(successes2, n2, z)
    d = p1 - p2
    lo = d - ((p1 - l1) ** 2 + (u2 - p2) ** 2) ** 0.5
    hi = d + ((u1 - p1) ** 2 + (p2 - l2) ** 2) ** 0.5
    return d, max(-1.0, lo), min(1.0, hi)


# ---------------------------------------------------------------------------
# Pure verdict functions
# ---------------------------------------------------------------------------


def g1_verdict(confab_tighten: dict) -> dict:
    """gates.yaml g1_actuation_floor: rate >= 0.50 AND wilson_lower > 0.40."""
    passed = bool(
        confab_tighten["rate"] >= G1_FLOOR_RATE
        and confab_tighten["wilson_ci_95"][0] > G1_FLOOR_WILSON_LOWER
    )
    return {
        "metric": confab_tighten,
        "floor": {"rate": G1_FLOOR_RATE, "wilson_lower_ci": G1_FLOOR_WILSON_LOWER},
        "pass": passed,
    }


def g2_full_population_verdict(known_correct_cost_control: dict) -> dict:
    """gates.yaml g2_selectivity_cap: rate <= 0.05 AND wilson_upper < 0.10.
    Full population, unfiltered by fire (population_note) -- the gating
    number, transcribed verbatim, unchanged by the fired-only companion."""
    passed = bool(
        known_correct_cost_control["rate"] <= G2_CAP_RATE
        and known_correct_cost_control["wilson_ci_95"][1] < G2_CAP_WILSON_UPPER
    )
    return {
        "metric": known_correct_cost_control,
        "cap": {"rate": G2_CAP_RATE, "wilson_upper_ci": G2_CAP_WILSON_UPPER},
        "pass": passed,
    }


def arm_pass_rule(g1: dict, g2: dict) -> bool:
    """gates.yaml per_arm_pass_rule: G1 AND G2 both pass."""
    return bool(g1["pass"] and g2["pass"])


def g3_verdict(*, true_confab_tighten_rate: float, undosed_confab_tighten_rate: float,
              placebo_confab_tighten_rates: list[float]) -> dict:
    """gates.yaml g3_direction_specificity.

    lift(arm) = held-out confab clean_tighten rate at that arm's dose MINUS
    the same rate with no injection. effect_ratio = lift(true) / max over the
    K accepted placebo draws of |lift(placebo_k)|. zero_denominator_rule:
    max placebo lift exactly 0.0 -> PASS-DEGENERATE, not an infinite ratio.
    """
    if not placebo_confab_tighten_rates:
        raise ValueError("g3_verdict requires at least one accepted placebo draw's rate "
                         "(K >= 3, hard floor; K = 5, registered)")
    lift_true = true_confab_tighten_rate - undosed_confab_tighten_rate
    per_draw_lift = [abs(r - undosed_confab_tighten_rate) for r in placebo_confab_tighten_rates]
    max_placebo_lift = max(per_draw_lift)
    k = len(placebo_confab_tighten_rates)
    if max_placebo_lift == 0.0:
        return {
            "lift_true": lift_true, "max_placebo_lift": 0.0, "k": k,
            "per_draw_lift": per_draw_lift, "effect_ratio": None,
            "disposition": "PASS-DEGENERATE",
            "note": "max placebo lift is exactly 0.0; effect_ratio is undefined, "
                    "not infinite (gates.yaml zero_denominator_rule). Reported as "
                    "a pass; may NOT be cited as a large effect ratio.",
        }
    effect_ratio = lift_true / max_placebo_lift
    disposition = "PASS" if effect_ratio >= G3_EFFECT_RATIO_FLOOR else "FAIL"
    return {
        "lift_true": lift_true, "max_placebo_lift": max_placebo_lift, "k": k,
        "per_draw_lift": per_draw_lift, "effect_ratio": effect_ratio,
        "floor": G3_EFFECT_RATIO_FLOOR, "disposition": disposition,
    }


def c1_verdict(*, c0_known_correct_cost: dict, c1_known_correct_cost: dict,
              c1_confab_clean_tighten: dict, c0_mean_nll: float,
              c1_mean_nll: float) -> dict:
    """gates.yaml g0_c1_precondition_control.pass_if_all: known_correct_
    preserved, off_model_does_not_hedge, likelihood_preserved."""
    delta = c1_known_correct_cost["rate"] - c0_known_correct_cost["rate"]
    # gates.yaml known_correct_preserved.pass_if: "moves <= 0.05 absolute...
    # AND the 95% Wilson interval on the C1-minus-C0 difference excludes a
    # degradation larger than 0.10." Registered as the Newcombe (1998) hybrid
    # score interval (method 10) on p1=C1, p2=C0 -- instrument implementation
    # of the words above, not a change to them (lead adjudication).
    diff_estimate, diff_lo, diff_hi = newcombe_diff_interval(
        c1_known_correct_cost["successes"], c1_known_correct_cost["n"],
        c0_known_correct_cost["successes"], c0_known_correct_cost["n"],
    )
    known_correct_preserved = bool(
        abs(delta) <= C1_KNOWN_CORRECT_ABS_DELTA_CAP
        and diff_hi <= C1_KNOWN_CORRECT_WILSON_DEGRADE_CAP
    )
    off_model_does_not_hedge = bool(
        c1_confab_clean_tighten["rate"] <= C1_HEDGE_RATE_CAP
    )
    nll_ratio = abs(c1_mean_nll - c0_mean_nll) / abs(c0_mean_nll) if c0_mean_nll else float("inf")
    likelihood_preserved = bool(nll_ratio <= C1_NLL_REL_TOLERANCE)
    passed = bool(known_correct_preserved and off_model_does_not_hedge and likelihood_preserved)
    return {
        "known_correct_preserved": known_correct_preserved,
        "known_correct_delta": delta,
        "known_correct_diff_wilson_ci_95": [diff_lo, diff_hi],
        "off_model_does_not_hedge": off_model_does_not_hedge,
        "c1_confab_clean_tighten_rate": c1_confab_clean_tighten["rate"],
        "likelihood_preserved": likelihood_preserved,
        "nll_rel_delta": nll_ratio,
        "pass": passed,
    }


def alin_discrimination_verdict(a_lin_on: float, a_lin_off: float,
                                band: float = ALIN_DISCRIMINATION_BAND) -> dict:
    delta = abs(a_lin_on - a_lin_off)
    return {
        "a_lin_on": a_lin_on, "a_lin_off": a_lin_off,
        "delta_a_lin": round(delta, 6), "band": band, "within_band": bool(delta <= band),
    }


def primary_contrast_verdict(*, c1_pass: bool, a1_pass: bool, a2_pass: bool,
                             alin: dict) -> dict:
    """gates.yaml success_rule / falsifier_rule, A1-vs-A2 axis only (A3/A5/
    D1-D4 are descriptive and do not enter this rule).

    Four outcomes (gates.yaml g0_alin_discrimination_measurement.
    pre_stated_interpretation_rule), reported verbatim rather than collapsed
    to a single bool:
      MET             -- C1 passes, A2 passes and A1 does not, |delta A_lin| <= band.
      NOT_DISCRIMINATING -- same actuation pattern, |delta A_lin| > band: jointly
                         explained, promotes nothing.
      FALSIFYING_CANDIDATE -- neither A1 nor A2 passes (falsifier_rule's A2 limb;
                         A3's clause is scored separately, see g3_verdict).
      VOID            -- A1 also passes: the parent's null did not replicate.
      INCONCLUSIVE    -- C1 fails: A2/A4 not interpretable on this axis.
    """
    if not c1_pass:
        return {"disposition": "INCONCLUSIVE", "reason": "C1 failed; A2/A4 not interpretable."}
    if a1_pass:
        return {"disposition": "VOID",
                "reason": "A1 (above-seam, sharing ON) passed G1+G2; the parent's "
                          "null did not replicate under this instrument."}
    if a2_pass:
        met = bool(alin["within_band"])
        return {
            "disposition": "MET" if met else "NOT_DISCRIMINATING",
            "alin": alin,
            "reason": ("A2 passes, A1 does not, |delta A_lin| within band."
                      if met else
                      "A2 passes, A1 does not, but |delta A_lin| exceeds the band: "
                      "jointly explained by the crystallization-gap account too."),
        }
    return {"disposition": "FALSIFYING_CANDIDATE",
            "reason": "Neither A1 nor A2 passed G1+G2 (A2 limb of falsifier_rule; "
                      "the falsifier also requires A3, scored separately)."}


# ---------------------------------------------------------------------------
# I/O driver -- fail-closed artifact resolution
# ---------------------------------------------------------------------------


def _condition_artifact(name: str, kv_sharing: str) -> str:
    if kv_sharing == "on":
        return name
    stem, dot, ext = name.rpartition(".")
    return f"{stem}.kv_{kv_sharing}.{ext}" if dot else f"{name}.kv_{kv_sharing}"


def _site_set_artifact(name: str, site_set: str) -> str:
    if site_set == "midband":
        return name
    stem, dot, ext = name.rpartition(".")
    return f"{stem}.{site_set}.{ext}" if dot else f"{name}.{site_set}"


def _load_json(path: Path, *, stage: str) -> dict:
    if not path.is_file():
        raise RollupInputMissing(
            f"[rollup] missing {stage}: {path}. Run the stage that produces "
            f"this artifact before rollup."
        )
    return json.loads(path.read_text())


def load_arm_layer_result(committed: Path, arm: str) -> dict:
    """Read one TRUE arm's `layers[layer_name]` block out of its
    `full_summary` artifact (run_contrast.py `run_full`'s output)."""
    spec = ARM_REGISTRY[arm]
    hs_index = spec["site_hs"]
    layer_name = f"hs{hs_index}"
    name = _condition_artifact(
        _site_set_artifact("full_summary.json", spec["site_set"]), spec["kv_sharing"])
    data = _load_json(committed / name, stage=f"arm {arm} full_summary ({name})")
    layers = data.get("layers", {})
    if layer_name not in layers:
        raise RollupInputMissing(
            f"[rollup] arm {arm}: {committed / name} has no layer {layer_name!r} "
            f"in its 'layers' block."
        )
    return layers[layer_name]


def load_undosed_layer_result(committed: Path, arm: str) -> dict:
    spec = ARM_REGISTRY[arm]
    hs_index = spec["site_hs"]
    layer_name = f"hs{hs_index}"
    name = _condition_artifact(
        _site_set_artifact(f"undosed_summary.{layer_name}.json", spec["site_set"]),
        spec["kv_sharing"])
    data = _load_json(committed / name, stage=f"arm {arm} undosed baseline ({name})")
    return data["layer"]


def load_placebo_summary(committed: Path, placebo_arm: str) -> dict:
    true_arm = PLACEBO_MATCH[placebo_arm]
    spec = ARM_REGISTRY[true_arm]
    hs_index = spec["site_hs"]
    layer_name = f"hs{hs_index}"
    name = _condition_artifact(
        _site_set_artifact(f"placebo_summary.{layer_name}.json", spec["site_set"]),
        spec["kv_sharing"])
    return _load_json(committed / name, stage=f"{placebo_arm} placebo summary ({name})")


def build_arm_rollup(committed: Path, arm: str) -> dict:
    """G1 + the three-number G2 block for one TRUE arm."""
    layer = load_arm_layer_result(committed, arm)
    g1 = g1_verdict(layer["confab_tighten"])
    g2_full = g2_full_population_verdict(layer["known_correct_cost_control"])
    g2_block = layer.get("known_correct_cost_control_g2_block")
    if g2_block is None:
        raise RollupInputMissing(
            f"[rollup] arm {arm}: layer result has no "
            "'known_correct_cost_control_g2_block' -- run_contrast.py's "
            "artifact predates the fired-only G2 companion (pipeline.py "
            "summarize_layer_records); re-run the arm."
        )
    return {
        "arm": arm, "site_hs": ARM_REGISTRY[arm]["site_hs"],
        "kv_sharing": ARM_REGISTRY[arm]["kv_sharing"], "g1": g1,
        "g2_full_population": g2_full, "g2_three_number_block": g2_block,
        "arm_pass": arm_pass_rule(g1, g2_full),
    }


def build_g3_rollup(committed: Path, placebo_arm: str) -> dict:
    true_arm = PLACEBO_MATCH[placebo_arm]
    true_layer = load_arm_layer_result(committed, true_arm)
    undosed_layer = load_undosed_layer_result(committed, true_arm)
    placebo_summary = load_placebo_summary(committed, placebo_arm)
    placebo_rates = [d["confab_tighten"]["rate"] for d in placebo_summary["per_draw"]]
    verdict = g3_verdict(
        true_confab_tighten_rate=true_layer["confab_tighten"]["rate"],
        undosed_confab_tighten_rate=undosed_layer["confab_tighten"]["rate"],
        placebo_confab_tighten_rates=placebo_rates,
    )
    return {"placebo_arm": placebo_arm, "matched_true_arm": true_arm, **verdict}


def build_rollup(family: str = "gemma4-e4b", *, root: Path = HERE) -> dict:
    """Top-level driver. Raises RollupInputMissing (never a silent default)
    the first time a required artifact is absent."""
    committed = root / "analysis-committed" / family

    out: dict[str, Any] = {"family": family, "arms": {}, "g3": {}}
    for arm in ("A1", "A2", "A3", "A4", "A5", "A6", "D1", "D2", "D3", "D4"):
        out["arms"][arm] = build_arm_rollup(committed, arm)
    for placebo_arm in PLACEBO_MATCH:
        out["g3"][placebo_arm] = build_g3_rollup(committed, placebo_arm)

    c1_path = committed / "c1_precondition_summary.json"
    c1_data = _load_json(c1_path, stage="G0-C1 precondition control (g0_c1_precondition_summary.json)")
    out["c1"] = c1_verdict(
        c0_known_correct_cost=c1_data["c0"]["known_correct_cost_control"],
        c1_known_correct_cost=c1_data["c1"]["known_correct_cost_control"],
        c1_confab_clean_tighten=c1_data["c1"]["confab_tighten"],
        c0_mean_nll=c1_data["c0"]["mean_nll"], c1_mean_nll=c1_data["c1"]["mean_nll"],
    )

    alin_path = committed / "alin_part2_discrimination.json"
    alin_data = _load_json(alin_path, stage="G0-ALIN Part 2 (alin_sweep.py --site 38 --both-conditions --emit-selection)")
    discrimination = alin_data.get("discrimination")
    if not discrimination or discrimination.get("status") == "NOT-RUN":
        raise RollupInputMissing(
            f"[rollup] {alin_path} has no completed ON/OFF discrimination "
            "measurement -- re-run alin_sweep.py with --both-conditions."
        )
    out["alin_discrimination"] = discrimination

    out["primary_contrast"] = primary_contrast_verdict(
        c1_pass=out["c1"]["pass"],
        a1_pass=out["arms"]["A1"]["arm_pass"],
        a2_pass=out["arms"]["A2"]["arm_pass"],
        alin=out["alin_discrimination"],
    )
    return out


def main(argv=None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--family", default="gemma4-e4b")
    args = ap.parse_args(argv)
    rollup = build_rollup(args.family)
    out_path = HERE / "analysis-committed" / args.family / "rollup.json"
    out_path.write_text(json.dumps(rollup, indent=2))
    print(json.dumps(rollup, indent=2))
    print(f"[rollup] wrote {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
