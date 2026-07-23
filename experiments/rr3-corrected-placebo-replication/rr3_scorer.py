#!/usr/bin/env python3
"""Final report assembly for rr3-corrected-placebo-replication: the CORE
mistral RG1 (effect-ratio, max-over-K)/RG2 (benefit)/RG3 (cost) verdict, and
the RIDER family x placebo-sign-map descriptive dose-response report.

Reads `analysis/adjudication_applied.jsonl` (written by `apply_adjudication.py
apply`; per-row {cell, arm, row_key, seed, dose_multiplier, refused_final}
for every core (non-decoy, non-voided-cell) pool row) and joins it back
against the generation run logs to compute `refused_final` = refused_v2 OR
adjudicated_abstention for every row in every registered population,
generalizing RR2's `apply_adjudication.py:apply_final_refusal` /
`combine_with_baseline` to this experiment's per-(cell, arm, seed,
dose_multiplier)-keyed applied map (RR2 only ever needed (row_key, arm) since
it had no K-seed or dose-ladder arms).

Two outputs:
  analysis-committed/core_final_report.json    RG1/RG2/RG3 + falsifier
                                                verdict (this experiment's
                                                ONLY promotion gate).
  analysis-committed/rider_final_report.json   descriptive dose-response,
                                                stratified by source
                                                (triviaqa/popqa = answerable,
                                                kuq = unanswerable), per
                                                family and dose rung; NO
                                                promotion gate
                                                (AMENDMENT.md "Rider").
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import gates_lib  # noqa: E402
import heldout_scorer as hs  # noqa: E402

ANALYSIS = HERE / "analysis"
COMMITTED = HERE / "analysis-committed"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")


def applied_key(r: dict[str, Any]) -> tuple:
    return (r["cell"], r["arm"], r["row_key"], r.get("seed"), r.get("dose_multiplier"))


def load_applied_map(analysis_dir: Path) -> dict[tuple, bool]:
    out: dict[tuple, bool] = {}
    for r in load_jsonl(analysis_dir / "adjudication_applied.jsonl"):
        key = applied_key(r)
        if key in out:
            raise SystemExit(f"duplicate applied key {key}: adjudication_applied.jsonl must be one row per scored generation")
        out[key] = bool(r["refused_final"])
    return out


def load_roster(family: str) -> dict[str, list[str]]:
    manifest = json.loads((COMMITTED / family / "materialize_manifest.json").read_text())
    confab, known = [], []
    for r in manifest["rows"]:
        if r.get("split") != "held_out":
            continue
        if r["role"] == "confab":
            confab.append(r["row_key"])
        elif r["role"] == "known_correct_answered":
            known.append(r["row_key"])
    return {"confab": confab, "known": known}


def attach_refused_final(row: dict[str, Any], cell: str, arm: str, applied_map: dict[tuple, bool],
                          seed: Any = None, dose_multiplier: Any = None) -> Optional[bool]:
    if row.get("refused_v2"):
        return True
    key = (cell, arm, row["row_key"], seed, dose_multiplier)
    return applied_map.get(key)


def full_population(row_keys: list[str], active_by_key: dict[str, dict], baseline_by_key: dict[str, dict],
                     cell: str, active_arm: str, applied_map: dict[tuple, bool],
                     seed: Any = None, dose_multiplier: Any = None) -> list[dict[str, Any]]:
    """Generalizes RR2's `combine_with_baseline` + `apply_final_refusal`: a
    row NOT in `active_by_key` never fired, so its generation text is
    byte-identical to its own baseline row and its refused_final is looked
    up under the baseline arm, not the active arm."""
    out = []
    for rk in row_keys:
        if rk in active_by_key:
            row = active_by_key[rk]
            rf = attach_refused_final(row, cell, active_arm, applied_map, seed, dose_multiplier)
        else:
            row = baseline_by_key[rk]
            rf = attach_refused_final(row, cell, "baseline", applied_map)
        out.append({**row, "refused_final": rf})
    return out


def rate_final(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Wilson rate over `refused_final`, excluding rows whose refused_final
    is None (never adjudicated -- a coverage gap or a voided cell), which
    are reported separately, never silently defaulted."""
    covered = [r for r in rows if r.get("refused_final") is not None]
    result = gates_lib.rate_wilson(covered, "refused_final")
    result["n_uncovered"] = len(rows) - len(covered)
    return result


# ---------------------------------------------------------------------------
# CORE: mistral RG1 (effect-ratio, max-over-K) / RG2 (benefit) / RG3 (cost)
# ---------------------------------------------------------------------------

def build_core_report() -> dict[str, Any]:
    cell_yaml = hs.load_cell_yaml()
    seeds = next(a["random_seeds"] for a in cell_yaml["core_cell"]["arms"] if a["name"] == "random_direction")

    applied_map = load_applied_map(ANALYSIS)
    roster = load_roster("mistral")

    baseline_by_key = {r["row_key"]: r for r in load_jsonl(hs.runlog_path("core__baseline"))}
    gated_by_key = {r["row_key"]: r for r in load_jsonl(hs.runlog_path("core__gated"))}

    gated_confab_full = full_population(roster["confab"], gated_by_key, baseline_by_key, "core_mistral", "gated", applied_map)
    gated_known_full = full_population(roster["known"], gated_by_key, baseline_by_key, "core_mistral", "gated", applied_map)
    baseline_confab_full_rows = full_population(roster["confab"], {}, baseline_by_key, "core_mistral", "gated", applied_map)

    gated_confab_fired = [r for rk, r in gated_by_key.items() if r.get("role") == "confab"]
    gated_confab_fired = [{**r, "refused_final": attach_refused_final(r, "core_mistral", "gated", applied_map)} for r in gated_confab_fired]

    gated_confab_rate = rate_final(gated_confab_full)
    baseline_confab_rate = rate_final(baseline_confab_full_rows)
    gated_lift = gated_confab_rate["rate"] - baseline_confab_rate["rate"]

    per_seed = []
    random_lifts_abs = []
    for seed in seeds:
        rand_by_key = {r["row_key"]: r for r in load_jsonl(hs.runlog_path(f"core__random_direction__seed{seed}"))}
        rand_confab_full = full_population(roster["confab"], rand_by_key, baseline_by_key, "core_mistral", "random_direction", applied_map, seed=seed)
        rand_confab_rate = rate_final(rand_confab_full)
        lift = rand_confab_rate["rate"] - baseline_confab_rate["rate"]
        random_lifts_abs.append(abs(lift))
        per_seed.append({
            "seed": seed, "confab_refused_final": rand_confab_rate, "lift_over_baseline": lift,
            "secondary_tolerance": gates_lib.secondary_tolerance_check("mistral7b_instruct_v03", lift * 100),
        })

    rg1 = gates_lib.rg1_effect_ratio(gated_lift, random_lifts_abs)

    confab_final = rate_final(gated_confab_fired)
    confab_well_formed = gates_lib.rate_wilson(gated_confab_fired, "well_formed")
    known_final = rate_final(gated_known_full)

    rg2_refused = gates_lib.rg2_refused_pass(confab_final)
    rg2_well_formed = gates_lib.rg2_well_formed_pass(confab_well_formed)
    rg3 = gates_lib.rg3_cost_pass(known_final)

    verdict = gates_lib.falsifier_verdict(rg1["passed"], rg2_refused, rg2_well_formed, rg3)

    return {
        "gated_fired_confab": {"n": len(gated_confab_fired), "refused_final": confab_final, "well_formed": confab_well_formed},
        "gated_known_full_population": {"n": len(gated_known_full), "refused_final": known_final},
        "gated_confab_full_population": {"n": len(gated_confab_full), "refused_final": gated_confab_rate, "lift_over_baseline": gated_lift},
        "baseline_confab_full_population": {"n": len(baseline_confab_full_rows), "refused_final": baseline_confab_rate},
        "random_direction_per_seed": per_seed,
        "gates": {
            "rg1_direction_specificity": rg1,
            "rg2_benefit": {"refused_pass": rg2_refused, "well_formed_pass": rg2_well_formed},
            "rg3_cost_pass": rg3,
        },
        "verdict": verdict,
    }


# ---------------------------------------------------------------------------
# RIDER: descriptive family x placebo-sign-map dose-response
# ---------------------------------------------------------------------------

def build_rider_report(family: str) -> dict[str, Any]:
    applied_map = load_applied_map(ANALYSIS)
    layer = hs.FAMILY_TO_LAYER[family]
    roster = load_roster(family)

    if family == "mistral":
        baseline_by_key = {r["row_key"]: r for r in load_jsonl(hs.runlog_path("core__baseline"))}
        baseline_cell = "core_mistral"
    else:
        baseline_by_key = {r["row_key"]: r for r in load_jsonl(hs.runlog_path(f"rider_{family}__baseline"))}
        baseline_cell = f"rider_{family}"

    family_id = "mistral7b_instruct_v03" if family == "mistral" else "llama32_3b_instruct"
    baseline_confab_full = [attach_refused_final(baseline_by_key[rk], baseline_cell, "baseline", applied_map) for rk in roster["confab"]]
    baseline_confab_rows = [{**baseline_by_key[rk], "refused_final": attach_refused_final(baseline_by_key[rk], baseline_cell, "baseline", applied_map)} for rk in roster["confab"]]
    baseline_confab_rate = rate_final(baseline_confab_rows)

    dose_response = []
    for dose in hs.DOSE_LADDER:
        seed = hs.rider_direction_seed(family, dose)
        confab_active = {r["row_key"]: r for r in load_jsonl(hs.runlog_path(f"rider_{family}__random_direction__dose{dose}__confab"))}
        known_active = {r["row_key"]: r for r in load_jsonl(hs.runlog_path(f"rider_{family}__random_direction__dose{dose}__known_correct_answered"))}

        confab_rung_keys = list(confab_active.keys())
        confab_scored = full_population(confab_rung_keys, confab_active, baseline_by_key, f"rider_{family}", "random_direction", applied_map, seed=seed, dose_multiplier=dose)
        known_scored = full_population(roster["known"], known_active, baseline_by_key, f"rider_{family}", "random_direction", applied_map, seed=seed, dose_multiplier=dose)

        confab_rate = rate_final(confab_scored)
        known_rate = rate_final(known_scored)
        lift = confab_rate["rate"] - baseline_confab_rate["rate"]

        dose_response.append({
            "dose_multiplier": dose, "direction_seed": seed,
            "confab": {"n": len(confab_scored), "refused_final": confab_rate, "by_source": gates_lib.rate_by_source(confab_scored, "refused_final")},
            "known_correct_answered": {"n": len(known_scored), "refused_final": known_rate, "by_source": gates_lib.rate_by_source(known_scored, "refused_final")},
            "lift_over_baseline": lift,
            "secondary_tolerance": gates_lib.secondary_tolerance_check(family_id, lift * 100),
        })

    return {
        "family": family, "layer": layer,
        "baseline_confab_full_population": {"n": len(baseline_confab_rows), "refused_final": baseline_confab_rate},
        "dose_response": dose_response,
        "gates": "NONE (descriptive rider cell, no promotion gate per AMENDMENT.md)",
    }


def cmd_report(args: argparse.Namespace) -> int:
    core = build_core_report()
    write_json(COMMITTED / "core_final_report.json", core)

    rider = {"mistral": build_rider_report("mistral"), "llama": build_rider_report("llama")}
    write_json(COMMITTED / "rider_final_report.json", rider)

    print(json.dumps({"core_verdict": core["verdict"], "core_rg1": core["gates"]["rg1_direction_specificity"]}, indent=2, default=str), flush=True)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.set_defaults(func=cmd_report)
    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
