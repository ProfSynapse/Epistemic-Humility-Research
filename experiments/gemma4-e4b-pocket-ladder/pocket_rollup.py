#!/usr/bin/env python3
"""Per-arm/per-gate aggregation driver for the pocket ladder (E1/E2/E3 + C0 +
P1/P2/P3).

MINIMAL, PURPOSE-BUILT for this cell -- NOT a copy of the quarantine cell's
`rollup.py`. That module hardcodes an ARM_REGISTRY spanning A1-A6/D1-D4 and
its `build_rollup()` unconditionally loads a `g0_alin_discrimination_
measurement` artifact and a `c1_precondition_summary.json`, both from stages
this cell does not have (no A_lin site-selection step, no OFF arms, no C1).
Carrying that file into this cell's pin surface would mean shipping dead code
that raises on import-time-adjacent use for artifacts that can never exist
here (AMENDMENT.md "Instrument deltas from the quarantine cell", finding B4).
`rollup.py` is dropped from this experiment entirely; this file replaces it.

Reused verbatim from the quarantine cell's `rollup.py` (same arithmetic, same
thresholds, copied rather than imported so this module stays a standalone,
torch-free, CPU-testable script the same way the original was designed to
be): `wilson_ci`, `g1_verdict`, `g2_full_population_verdict`, `arm_pass_rule`,
`g3_verdict`, and the G1/G2/G3 threshold constants.

DROPPED relative to the quarantine cell's `rollup.py`, and why: `c1_verdict`
and `newcombe_diff_interval` (no C1/OFF-model arm here), `alin_discrimination_
verdict` and `primary_contrast_verdict` (no A_lin site-selection step and no
A1-vs-A2 patch contrast here -- this cell has no OFF arms at all).

ADDED relative to the quarantine cell's `rollup.py`: `actuation_claim_verdict`,
which implements THIS cell's own `gates.yaml actuation_claim_rule` -- a rule
that has no analogue in the quarantine cell, where G3 covered only two of nine
arms and D1-D4's lack of a placebo counterpart was an accepted, undecided
limitation rather than a rule with its own arithmetic.
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
G2_ADJUDICABLE_FLOOR = 35  # duplicated from g2_companion.py; see quarantine rollup.py's own note

# --- G3 (gates.yaml g3_direction_specificity, TRANSCRIBED VERBATIM) --------
G3_EFFECT_RATIO_FLOOR = 3.0

#: Arm registry (cell.yaml `arms`). site_hs=None means the arm carries no
#: injection site of its own (C0).
ARM_REGISTRY: dict[str, dict[str, Any]] = {
    "E1": {"site_hs": 25, "site_set": "pocket", "kv_sharing": "on"},
    "E2": {"site_hs": 26, "site_set": "pocket", "kv_sharing": "on"},
    "E3": {"site_hs": 27, "site_set": "pocket", "kv_sharing": "on"},
}
#: Every true arm here has a registered placebo counterpart (cell.yaml
#: registered_control_site_sets: ["pocket"]) -- unlike the quarantine cell,
#: where PLACEBO_MATCH covered only A3/A5 of nine arms.
PLACEBO_MATCH: dict[str, str] = {"P1": "E1", "P2": "E2", "P3": "E3"}


class RollupInputMissing(FileNotFoundError):
    """Raised naming the specific missing artifact/stage. Never caught to
    supply a silent default for a G1/G2 verdict -- a missing TRUE-arm input
    is reported as missing. G3's own NOT-RUN/UNADJUDICATED dispositions are
    the one place a missing artifact is a MEANINGFUL outcome rather than a
    build error; see `build_g3_rollup`."""


def wilson_ci(successes: int, n: int, z: float = _Z95) -> tuple[float, float, float]:
    if n == 0:
        return 0.0, 0.0, 0.0
    phat = successes / n
    denom = 1 + z * z / n
    center = (phat + z * z / (2 * n)) / denom
    half = (z * ((phat * (1 - phat) / n + z * z / (4 * n * n)) ** 0.5)) / denom
    return phat, max(0.0, center - half), min(1.0, center + half)


# ---------------------------------------------------------------------------
# Pure verdict functions (transcribed verbatim from the quarantine cell's
# rollup.py where an equivalent existed)
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
    Full population, unfiltered by fire -- the gating number, transcribed
    verbatim, unchanged by the fired-only companion."""
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
    """gates.yaml g3_direction_specificity, TRANSCRIBED VERBATIM.

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
                    "a pass with the degenerate label attached; may NOT be cited as "
                    "a large effect ratio or reported flatly as direction-specific "
                    "actuation (AMENDMENT.md W2).",
        }
    effect_ratio = lift_true / max_placebo_lift
    disposition = "PASS" if effect_ratio >= G3_EFFECT_RATIO_FLOOR else "FAIL"
    return {
        "lift_true": lift_true, "max_placebo_lift": max_placebo_lift, "k": k,
        "per_draw_lift": per_draw_lift, "effect_ratio": effect_ratio,
        "floor": G3_EFFECT_RATIO_FLOOR, "disposition": disposition,
    }


def actuation_claim_verdict(*, arm: str, arm_pass: bool, g3: dict | None) -> dict:
    """gates.yaml actuation_claim_rule, MANDATORY at every one of E1/E2/E3
    (the scope difference from the quarantine cell's g3_direction_specificity,
    which applied to only two of nine arms). No analogue in the quarantine
    cell's rollup.py.

    g3=None means no G3 artifact could be built at all (RollupInputMissing on
    the placebo summary): this covers BOTH the "no usable placebo dose"
    (NOT-RUN) and the "redraw ledger exhausted before K accepted draws"
    (UNADJUDICATED) cases from AMENDMENT.md "G3 direction-specificity is
    MANDATORY here" -- a missing placebo_summary.<layer>.json artifact cannot
    distinguish the two from the rollup side alone (run_contrast.py never
    writes that artifact in either case), so both are reported under one
    combined disposition rather than one being guessed. Whichever case
    actually occurred is visible in the run log / stderr from the run that
    attempted it, not from this rollup's inputs.
    """
    if not arm_pass:
        return {"arm": arm, "claim": "no_actuation",
                "reason": "G1 and/or G2 did not pass; G3 not evaluated."}
    if g3 is None:
        return {"arm": arm, "claim": "unresolved_gate_clearance",
                "reason": "G1 and G2 passed but no G3 artifact exists (NOT-RUN or "
                          "UNADJUDICATED -- indistinguishable from a missing "
                          "placebo_summary artifact alone). NOT actuation and NOT a "
                          "failed control (gates.yaml actuation_claim_rule)."}
    if g3.get("readback_adjudicated") is False:
        return {"arm": arm, "claim": "unresolved_gate_clearance", "g3": g3,
                "reason": "G1 and G2 passed but at least one accepted placebo draw's "
                          "readback was out of tolerance; G3 is UNADJUDICATED."}
    disposition = g3["disposition"]
    if disposition in ("PASS", "PASS-DEGENERATE"):
        return {"arm": arm, "claim": "direction_specific_actuation", "g3": g3,
                "reason": f"G1, G2, and ADJUDICATED G3 ({disposition}) all pass."}
    return {"arm": arm, "claim": "actuates_not_direction_specific", "g3": g3,
            "reason": "G1 and G2 passed; ADJUDICATED G3 FAILED (effect_ratio < "
                      f"{G3_EFFECT_RATIO_FLOOR}). Reproduces the hs24 pattern "
                      "(NOTEBOOK.md:1600-1606 in the quarantine cell); may NOT be "
                      "cited as evidence of a specific effect."}


# ---------------------------------------------------------------------------
# I/O driver -- fail-closed artifact resolution for G1/G2; G3 is the one
# place a missing artifact is read as a registered disposition, not an error.
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
            f"[pocket_rollup] missing {stage}: {path}. Run the stage that "
            f"produces this artifact before rollup."
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
            f"[pocket_rollup] arm {arm}: {committed / name} has no layer "
            f"{layer_name!r} in its 'layers' block."
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
    """G1 + the three-number G2 block for one TRUE arm. Fails closed
    (RollupInputMissing) if the arm never produced a committed full_summary --
    this is the one part of the pipeline where a missing artifact is always
    an error, never a registered disposition."""
    layer = load_arm_layer_result(committed, arm)
    g1 = g1_verdict(layer["confab_tighten"])
    g2_full = g2_full_population_verdict(layer["known_correct_cost_control"])
    g2_block = layer.get("known_correct_cost_control_g2_block")
    if g2_block is None:
        raise RollupInputMissing(
            f"[pocket_rollup] arm {arm}: layer result has no "
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


def build_g3_rollup(committed: Path, placebo_arm: str) -> dict | None:
    """Returns the G3 verdict dict, or None if no placebo_summary artifact
    exists (NOT-RUN or UNADJUDICATED -- see `actuation_claim_verdict`'s
    docstring for why the two cannot be told apart from this artifact set
    alone). Does NOT raise on a missing placebo summary: unlike a missing
    TRUE-arm result, a missing G3 input is itself a meaningful, pre-stated
    outcome this cell registers (AMENDMENT.md actuation_claim_rule), not a
    build error."""
    true_arm = PLACEBO_MATCH[placebo_arm]
    true_layer = load_arm_layer_result(committed, true_arm)  # fails closed: no verdict without the true arm
    try:
        undosed_layer = load_undosed_layer_result(committed, true_arm)
        placebo_summary = load_placebo_summary(committed, placebo_arm)
    except RollupInputMissing:
        return None
    placebo_rates = [d["confab_tighten"]["rate"] for d in placebo_summary["per_draw"]]
    readback_fracs = [d.get("frac_readback_within_tol") for d in placebo_summary["per_draw"]]
    readback_adjudicated = all(f == 1.0 for f in readback_fracs if f is not None) and bool(readback_fracs)
    verdict = g3_verdict(
        true_confab_tighten_rate=true_layer["confab_tighten"]["rate"],
        undosed_confab_tighten_rate=undosed_layer["confab_tighten"]["rate"],
        placebo_confab_tighten_rates=placebo_rates,
    )
    verdict["readback_adjudicated"] = readback_adjudicated
    return {"placebo_arm": placebo_arm, "matched_true_arm": true_arm, **verdict}


def load_dose_viability(committed: Path, arm: str) -> bool:
    """Read `has_usable_dose` for the arm's site from the committed Stage-1
    dose-calibration artifact. An arm with no usable FIT rung is
    dose-viability NOT-RUN (AMENDMENT.md, transcribed rule: "neither a pass
    nor a fail"); the rollup must represent that registered disposition
    rather than failing closed on the missing full_summary layer."""
    spec = ARM_REGISTRY[arm]
    name = _condition_artifact(
        _site_set_artifact("dose_calibration_summary.json", spec["site_set"]),
        spec["kv_sharing"])
    data = _load_json(committed / name, stage=f"arm {arm} dose calibration ({name})")
    layer_name = f"hs{spec['site_hs']}"
    blk = data.get("layers", {}).get(layer_name) or data.get(layer_name)
    if blk is None or "has_usable_dose" not in blk:
        raise RollupInputMissing(
            f"[pocket_rollup] arm {arm}: {committed / name} has no "
            f"'has_usable_dose' record for {layer_name!r}."
        )
    return bool(blk["has_usable_dose"])


def build_rollup(family: str = "gemma4-e4b", *, root: Path = HERE) -> dict:
    """Top-level driver. Raises RollupInputMissing (never a silent default)
    if a TRUE arm's own artifact is absent; a missing G3 input is instead
    folded into that arm's `actuation_claim` disposition. Arms whose site has
    no usable FIT dose (Stage-1 `has_usable_dose` false) are reported as the
    registered dose-viability NOT-RUN disposition, not as errors."""
    committed = root / "analysis-committed" / family

    out: dict[str, Any] = {"family": family, "arms": {}, "g3": {}, "actuation_claims": {}}
    for arm in ("E1", "E2", "E3"):
        if load_dose_viability(committed, arm):
            out["arms"][arm] = build_arm_rollup(committed, arm)
        else:
            out["arms"][arm] = {
                "arm": arm, "site_hs": ARM_REGISTRY[arm]["site_hs"],
                "kv_sharing": ARM_REGISTRY[arm]["kv_sharing"],
                "status": "NOT-RUN",
                "reason": "dose-viability: no usable FIT rung at this site "
                          "(Stage-1 has_usable_dose false); neither a pass "
                          "nor a fail (transcribed rule).",
            }
    for placebo_arm, true_arm in PLACEBO_MATCH.items():
        if out["arms"][true_arm].get("status") == "NOT-RUN":
            out["g3"][placebo_arm] = {
                "placebo_arm": placebo_arm, "matched_true_arm": true_arm,
                "status": "NOT-RUN",
                "reason": "mirrors the true arm's dose-viability NOT-RUN.",
            }
            out["actuation_claims"][true_arm] = {
                "arm": true_arm, "claim": "not_run",
                "reason": "dose-viability NOT-RUN at Stage 1; no gate was "
                          "evaluated (registered disposition).",
            }
            continue
        out["g3"][placebo_arm] = build_g3_rollup(committed, placebo_arm)
        out["actuation_claims"][true_arm] = actuation_claim_verdict(
            arm=true_arm, arm_pass=out["arms"][true_arm]["arm_pass"],
            g3=out["g3"][placebo_arm],
        )
    return out


def main(argv=None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--family", default="gemma4-e4b")
    args = ap.parse_args(argv)
    rollup = build_rollup(args.family)
    out_path = HERE / "analysis-committed" / args.family / "pocket_rollup.json"
    out_path.write_text(json.dumps(rollup, indent=2))
    print(json.dumps(rollup, indent=2))
    print(f"[pocket_rollup] wrote {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
