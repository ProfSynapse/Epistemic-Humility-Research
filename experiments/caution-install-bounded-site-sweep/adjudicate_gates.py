#!/usr/bin/env python3
"""Stage 9 (CPU, bespoke -- see gap note): adjudication and gate scoring
(AMENDMENT.md Run plan row 9; gates.yaml G0-G4, summary_rule).

CAPABILITY GAP (documented): `MechInterp.stats.evaluator` (read in full
before writing this module) only dispatches four primitives -- count_flips,
kill_diff_vs_control, permutation_p, auroc_floor. This cell's gates.yaml uses
THREE different primitive names -- rate_over_population (G1, G2),
effect_ratio_over_draws (G3), interval_containment (G4) -- none of which
exist in that dispatch table, so `mechinterp score-gates` cannot literally
read this cell's gates.yaml. This script implements those three primitives
directly from gates.yaml's own prose definitions, over the artifacts the
earlier stage scripts already wrote (`held_out_summary.json`,
`controls_summary.json`, `dose_disposition.json`, `build_gate_manifest.json`,
`write_smoke_report.json`), reusing `sweep_lib.wilson_ci` for every interval
rather than re-deriving Wilson's formula.

Every check below is scored literally as gates.yaml states it; no threshold
is loosened and no gate is skipped to reach a pass. A missing upstream
artifact makes its gate UNKNOWN (never silently passed).

Output: `analysis-committed/gate_report.json` (every gate's raw numbers +
pass/fail/adjudicable/UNKNOWN, plus the summary_rule verdict). No row text.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from sweep_lib import (  # noqa: E402
    ANALYSIS,
    COMMITTED,
    load_cell,
    load_gates,
    raw_base_anchor_pool,
    wilson_ci,
    write_json,
)

UNKNOWN = "UNKNOWN_missing_artifact"

# F10 fix: gates.yaml g0f_containment reads "committed row text, questions,
# aliases, generations ... none present in analysis-committed/". This was
# previously a hardcoded string, never actually checked. These are the exact
# field names row-text is written under, verified by grepping every producer
# script in this harness (mine_pool.py, probe_stage_a/b.py,
# probe_census_extension.py, grader_sweep.py, run_pairs.py, sweep_lib.py):
# question, aliases, answer_text, completion, prompt, generation. None of
# these keys belong in any file this harness writes under
# analysis-committed/ (that tree holds only rates, counts, statuses, and
# row_key/split/role index rows -- never the row's own text).
FORBIDDEN_CONTAINMENT_KEYS = frozenset(
    {"question", "aliases", "answer_text", "completion", "prompt", "generation"}
)


def _load(path: Path):
    return json.loads(path.read_text()) if path.exists() else None


def _find_forbidden_keys(obj, path: str = "$") -> list[str]:
    """Recursive scan for any of FORBIDDEN_CONTAINMENT_KEYS at any nesting
    depth. Returns a list of JSON-path-ish locations where a forbidden key
    was found (empty list == clean)."""
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in FORBIDDEN_CONTAINMENT_KEYS:
                hits.append(f"{path}.{k}")
            hits.extend(_find_forbidden_keys(v, f"{path}.{k}"))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits.extend(_find_forbidden_keys(v, f"{path}[{i}]"))
    return hits


def g0f_containment_check() -> dict:
    """F10 fix: a real boolean containment check over this harness's own
    committed output paths (analysis-committed/, i.e. COMMITTED), not a
    hardcoded pass string. Walks every .json/.jsonl file under COMMITTED and
    flags any occurrence of a forbidden row-text field name at any nesting
    depth. gates.yaml pass_if: "none present in analysis-committed/"."""
    if not COMMITTED.exists():
        return {"scanned_files": 0, "violations": [], "pass": UNKNOWN}
    violations = []
    scanned = 0
    for path in sorted(COMMITTED.rglob("*")):
        if not path.is_file() or path.suffix not in (".json", ".jsonl"):
            continue
        scanned += 1
        try:
            if path.suffix == ".jsonl":
                for i, line in enumerate(path.read_text().splitlines()):
                    if not line.strip():
                        continue
                    hits = _find_forbidden_keys(json.loads(line))
                    violations.extend(f"{path}::L{i}:{h}" for h in hits)
            else:
                hits = _find_forbidden_keys(json.loads(path.read_text()))
                violations.extend(f"{path}:{h}" for h in hits)
        except json.JSONDecodeError as exc:
            violations.append(f"{path}:UNPARSEABLE:{exc}")
    return {"scanned_files": scanned, "violations": violations, "pass": scanned > 0 and not violations}


def g0_integrity(cell: dict) -> dict:
    out = {}
    split = _load(COMMITTED / "split_manifest.json")
    if split:
        counts = split.get("counts", {})
        out["g0a_pool_power_confab"] = counts.get("confab", {}).get("n_held_out", 0) >= 150
        out["g0a_pool_power_known"] = counts.get("known_correct_answered", {}).get("n_held_out", 0) >= 250
    else:
        out["g0a_pool_power_confab"] = out["g0a_pool_power_known"] = UNKNOWN

    for substrate in ("trained", "raw_base"):
        manifest = _load(ANALYSIS / f"extract_{substrate}" / "manifest.json")
        if manifest:
            out[f"g0b_answer_capture_{substrate}"] = bool(manifest.get("g0b_answer_capture_pass"))
            # F9 fix: g0b_seam_continuity (gates.yaml: min cosine between
            # adjacent-site captures, floor >= 0.999) is computed and
            # persisted by extract_anchor.py's compute_seam_continuity() into
            # this same manifest; it was never read into the gate report.
            if "g0b_seam_continuity_pass" in manifest:
                out[f"g0b_seam_continuity_{substrate}"] = bool(manifest["g0b_seam_continuity_pass"])
            else:
                out[f"g0b_seam_continuity_{substrate}"] = UNKNOWN
        else:
            out[f"g0b_answer_capture_{substrate}"] = UNKNOWN
            out[f"g0b_seam_continuity_{substrate}"] = UNKNOWN

        build = _load(COMMITTED / substrate / "build_gate_manifest.json")
        if build:
            out[f"g0c_refit_reproducible_{substrate}"] = bool(build.get("g0_overall_pass")) or all(
                s["g0c_reproducible"] for s in build["sites"].values())
            out[f"g0d_gate_auc_{substrate}"] = all(s["g0d_pass"] for s in build["sites"].values())
        else:
            out[f"g0c_refit_reproducible_{substrate}"] = out[f"g0d_gate_auc_{substrate}"] = UNKNOWN

        smoke = _load(COMMITTED / substrate / "write_smoke_report.json")
        out[f"g0e_write_readback_{substrate}"] = bool(smoke["g0e_pass"]) if smoke else UNKNOWN

    containment = g0f_containment_check()
    out["g0f_containment_detail"] = containment
    out["g0f_containment"] = containment["pass"]

    known_bools = [v for v in out.values() if isinstance(v, bool)]
    out["overall_pass"] = (all(known_bools) if known_bools and UNKNOWN not in out.values() else UNKNOWN)
    return out


def g_dose_viability(substrate: str) -> dict:
    disp = _load(COMMITTED / substrate / "dose_disposition.json")
    if not disp:
        return {"status": UNKNOWN}
    cells = {k: v["status"] for k, v in disp["cells"].items()}
    return {"cells": cells, "n_selected": sum(1 for v in cells.values() if v == "SELECTED"),
            "n_not_run": sum(1 for v in cells.values() if v != "SELECTED")}


def g1_actuation(substrate: str) -> dict:
    ho = _load(COMMITTED / substrate / "held_out_summary.json")
    if not ho:
        return {"status": UNKNOWN}
    out = {}
    for cell_key, c in ho["cells"].items():
        if c.get("status") != "RAN":
            out[cell_key] = {"status": c.get("status")}
            continue
        gated = c["arms"].get("gated", {})
        stat = gated.get("confab_held_out", {})
        rate, lower = stat.get("rate"), stat.get("wilson_lower_95")
        passed = (rate is not None and rate >= 0.50) and (lower is not None and lower > 0.40)
        out[cell_key] = {"rate": rate, "wilson_lower_95": lower, "n": stat.get("n"), "pass": passed}
    return out


def g2_selectivity(substrate: str) -> dict:
    """F12 fix: gates.yaml headline_rule -- "if the fired-only rate exceeds
    the cap while the full-population number passes, the fired-only rate
    goes in the headline, not a table". This requires BOTH rates (full
    held-out population and fired-only) with both numerators/denominators,
    which run_held_out.py's F12 fix now persists as
    known_correct_answered_held_out and
    known_correct_answered_held_out_fired_only. Both are read here; the
    headline rate is selected by the registered rule, never a new
    threshold."""
    ho = _load(COMMITTED / substrate / "held_out_summary.json")
    if not ho:
        return {"status": UNKNOWN}
    out = {}
    for cell_key, c in ho["cells"].items():
        if c.get("status") != "RAN":
            out[cell_key] = {"status": c.get("status")}
            continue
        gated = c["arms"].get("gated", {})
        full_stat = gated.get("known_correct_answered_held_out", {})
        fired_stat = gated.get("known_correct_answered_held_out_fired_only", {})
        n_fired_known = gated.get("n_fired_known", 0)
        adjudicable = n_fired_known >= 35

        full_rate, full_upper = full_stat.get("rate"), full_stat.get("wilson_upper_95")
        fired_rate, fired_upper = fired_stat.get("rate"), fired_stat.get("wilson_upper_95")

        full_passed = (full_rate is not None and full_rate <= 0.05) and \
            (full_upper is not None and full_upper < 0.10)
        fired_exceeds_cap = fired_rate is not None and fired_rate > 0.05

        # headline_rule: fired-only rate is the headline exactly when it
        # exceeds the cap while the full-population number passes; otherwise
        # the full-population rate is the headline (the ordinary case this
        # gate's primitive, rate_over_population, is defined over).
        if full_passed and fired_exceeds_cap:
            headline_rate, headline_upper, headline_source = fired_rate, fired_upper, "fired_only"
        else:
            headline_rate, headline_upper, headline_source = full_rate, full_upper, "full_population"

        passed = (headline_rate is not None and headline_rate <= 0.05) and \
            (headline_upper is not None and headline_upper < 0.10)
        out[cell_key] = {
            "full_population": {"rate": full_rate, "wilson_upper_95": full_upper, "n": full_stat.get("n")},
            "fired_only": {"rate": fired_rate, "wilson_upper_95": fired_upper, "n": fired_stat.get("n")},
            "headline_source": headline_source,
            "rate": headline_rate, "wilson_upper_95": headline_upper,
            "n_fired_known": n_fired_known, "adjudicable": adjudicable,
            "verdict": (("PASS" if passed else "FAIL") if adjudicable else "NOT_ADJUDICABLE_vacuous"),
        }
    return out


def g3_direction_specificity(substrate: str, ctrl: dict = None, ho: dict = None) -> dict:
    """F1/F13 fix: gates.yaml criterion is RG1 (see
    .skills/mechinterp-cells/reference/read-then-actuate.md section 5.1's
    worked example: gated lift +40.9 points / max draw lift +21.8 points =
    1.87x -> FAIL, NOT a raw-rate ratio). The previous implementation divided
    raw rates (gated_rate / draw_rate) with no baseline subtraction at all --
    a materially different, unregistered statistic that silently inflates
    the ratio whenever the undosed baseline is non-zero.

    Registered math (gates.yaml g3_direction_specificity + AMENDMENT.md):
      gated_lift = gated_rate - gated_baseline_undosed_rate  (same cell,
                   held_out_summary.json's own baseline_undosed arm)
      draw_lift  = draw_rate  - that SAME draw's own baseline_undosed rate
                   (run_controls.py runs baseline_undosed alongside every
                   random_direction draw; F1's fix to run_controls.py now
                   persists it instead of discarding it)
      ratio = gated_lift / max(draw_lift for draw in >=3 accepted draws)
      pass_if_ratio: >= 3.0, aggregation: "max over draws"

    NEW DEFECT #1 (2026-08-10 lead adjudication): pass now additionally
    requires gated_lift > 0 AND max_draw_lift > 0. This is a guard, not a
    new threshold -- a negative (or zero) gated_lift means the gated arm did
    not raise the confab rate at all, and a non-positive max_draw_lift means
    the random-direction noise floor itself did not raise it either, so the
    ratio in either case cannot represent "installation specific to this
    direction, 3x above the noise floor"; it would be division by a
    near-zero or sign-flipped denominator producing an arithmetically large
    but substantively meaningless number.

    NEW DEFECT #2 (2026-08-10 lead adjudication): a non-finite ratio (only
    reachable when max_draw_lift == 0) must never serialize as bare JSON
    Infinity (not valid JSON per spec, and misleading regardless). It is
    reported as the string sentinel "inf"/"-inf" with an explanatory
    `ratio_note` field; `pass` is computed from the raw float (never the
    sentinel string) and is unreachable here anyway once max_draw_lift > 0
    is required above.

    NEW DEFECT #3 (2026-08-10 lead adjudication): `ctrl`/`ho` are optional
    pre-loaded dicts, shaped exactly like `controls_summary.json` /
    `held_out_summary.json`, so `run_sweep.py`'s CPU smoke can call THIS
    function directly on synthetic worked-example numbers instead of
    re-implementing the lift/ratio/guard math inline (a second copy that
    drifted from the real one, and could pass while the real path fails).
    Passing them in-memory also keeps the smoke's "never touches real
    analysis-committed/*" invariant intact -- no disk I/O happens when both
    are supplied.
    """
    ctrl = ctrl if ctrl is not None else _load(COMMITTED / substrate / "controls_summary.json")
    ho = ho if ho is not None else _load(COMMITTED / substrate / "held_out_summary.json")
    if not ctrl or not ho:
        return {"status": UNKNOWN}
    out = {}
    for cell_key, c in ctrl["cells"].items():
        if c.get("status") != "RAN":
            out[cell_key] = {"status": c.get("status")}
            continue
        ho_arms = ho["cells"].get(cell_key, {}).get("arms", {})
        gated_rate = ho_arms.get("gated", {}).get("confab_held_out", {}).get("rate")
        gated_baseline = ho_arms.get("baseline_undosed", {}).get("confab_held_out", {}).get("rate")
        gated_lift = (gated_rate - gated_baseline) if (gated_rate is not None
                                                         and gated_baseline is not None) else None

        draw_lifts = []
        draw_detail = []
        for draw in c.get("random_direction", []):
            draw_rate = draw.get("random_direction", {}).get("confab_held_out", {}).get("rate")
            draw_baseline = draw.get("baseline_undosed", {}).get("confab_held_out", {}).get("rate")
            lift = (draw_rate - draw_baseline) if (draw_rate is not None
                                                     and draw_baseline is not None) else None
            draw_detail.append({"draw": draw.get("draw"), "rate": draw_rate,
                                 "baseline": draw_baseline, "lift": lift})
            if lift is not None:
                draw_lifts.append(lift)

        max_draw_lift = max(draw_lifts) if draw_lifts else None
        if gated_lift is not None and max_draw_lift is not None:
            if max_draw_lift > 0:
                ratio_raw = gated_lift / max_draw_lift
            elif max_draw_lift == 0:
                ratio_raw = float("inf") if gated_lift > 0 else float("-inf") if gated_lift < 0 else None
            else:  # negative max_draw_lift: registered aggregation is still
                # "max over draws" of the raw lift, then a straight ratio;
                # do not silently reinterpret sign, report the raw quotient
                ratio_raw = gated_lift / max_draw_lift
        else:
            ratio_raw = None

        ratio_note = None
        if ratio_raw is not None and not math.isfinite(ratio_raw):
            ratio_note = (
                f"ratio undefined (division by zero): gated_lift={gated_lift} over "
                f"max_draw_lift=0.0; serialized as a sentinel string, not bare "
                "JSON Infinity. This cell also fails the max_draw_lift > 0 guard "
                "below regardless of this value."
            )
            ratio = "inf" if ratio_raw > 0 else "-inf"
        else:
            ratio = ratio_raw

        # NEW DEFECT #1 guard: gated_lift and max_draw_lift must both be
        # strictly positive, in addition to the registered ratio >= 3.0 and
        # k_draws >= 3 conditions -- see docstring above.
        passed = bool(
            ratio_raw is not None and math.isfinite(ratio_raw)
            and len(draw_lifts) >= 3 and ratio_raw >= 3.0
            and gated_lift is not None and gated_lift > 0
            and max_draw_lift is not None and max_draw_lift > 0
        )

        out[cell_key] = {
            "gated_rate": gated_rate, "gated_baseline_undosed_rate": gated_baseline, "gated_lift": gated_lift,
            "k_draws": len(draw_lifts), "draw_detail": draw_detail, "draw_lifts": draw_lifts,
            "max_draw_lift": max_draw_lift, "ratio": ratio, "ratio_note": ratio_note,
            "pass": passed,
            "companion_permuted_gate": c.get("permuted_gate"),
            "companion_raw_write_pos_ctrl": c.get("raw_write_pos_ctrl"),
        }
    return out


def g4_substrate_anchor(cell: dict) -> dict:
    ho = _load(COMMITTED / "raw_base" / "held_out_summary.json")
    if not ho:
        return {"status": UNKNOWN}
    reference = {"hs23": (194, 221), "hs29": (205, 221)}
    out = {}
    for site_name, (k, n) in reference.items():
        lo, hi = wilson_ci(k, n)
        cell_results = {ck: c for ck, c in ho["cells"].items() if ck.startswith(site_name + ":")}
        site_out = {"reference_rate": k / n, "reference_wilson_95": [lo, hi], "positions": {}}
        for cell_key, c in cell_results.items():
            if c.get("status") != "RAN":
                site_out["positions"][cell_key] = {"status": c.get("status")}
                continue
            rate = c["arms"].get("gated", {}).get("confab_held_out", {}).get("rate")
            site_out["positions"][cell_key] = {
                "observed_rate": rate,
                "contained": bool(rate is not None and lo <= rate <= hi),
            }
        out[site_name] = site_out

    # ALSO(b) (2026-08-10 lead adjudication): raw_base has no registered
    # FIT/HELD-OUT split (raw_base_anchor_pool's docstring), so
    # dose_calibrate.py's calibration_pool() draws its confab rows from the
    # first n_confab_fit_rows (row_key-sorted) of the SAME rep2 221-row pool
    # this gate's denominator scores at Stage 6 -- those rows are
    # dose-selected on AND scored in the G4 denominator, not held out from
    # it. Disclosed here as a count/fraction (re-review measured 24/221 =
    # 10.9%) rather than left implicit; see NOTEBOOK.md 2026-08-10 for the
    # two-sided pre-run caveat (this overlap can bias the observed rate
    # either toward or away from the reference interval, not exclusively
    # toward a false containment pass).
    n_dose_selected = int(cell["dose_ladder"]["calibration_pool"]["n_confab_fit_rows"])
    try:
        n_g4_denominator = raw_base_anchor_pool()["n_confab"]
    except RuntimeError as exc:
        n_g4_denominator = None
        overlap_error = str(exc)
    else:
        overlap_error = None
    dose_selection_overlap = {
        "n_dose_selected_and_scored": n_dose_selected,
        "n_g4_denominator": n_g4_denominator,
        "fraction": (n_dose_selected / n_g4_denominator) if n_g4_denominator else None,
        "error": overlap_error,
        "note": (
            "raw_base's dose-calibration confab pool is the first "
            f"{n_dose_selected} row_keys (sorted) of the SAME rep2 anchor "
            "pool this gate's denominator scores at Stage 6 (n="
            f"{n_g4_denominator}); it is not a held-out subset. Disclosed "
            "pre-run per NOTEBOOK.md 2026-08-10; the bias direction is "
            "two-sided, not exclusively toward false containment."
        ),
    }
    return {"sites": out, "dose_selection_overlap": dose_selection_overlap}


def run(args: argparse.Namespace) -> int:
    cell = load_cell()
    gates = load_gates()

    report = {"gates": {}}
    report["gates"]["g0_integrity"] = g0_integrity(cell)
    for substrate in ("trained", "raw_base"):
        report["gates"].setdefault("g_dose_viability", {})[substrate] = g_dose_viability(substrate)
    report["gates"]["g1_actuation"] = {"trained": g1_actuation("trained")}
    report["gates"]["g2_selectivity"] = {"trained": g2_selectivity("trained")}
    report["gates"]["g3_direction_specificity"] = {"trained": g3_direction_specificity("trained")}
    report["gates"]["g4_substrate_anchor"] = g4_substrate_anchor(cell)

    g1 = report["gates"]["g1_actuation"]["trained"]
    g2 = report["gates"]["g2_selectivity"]["trained"]
    g3 = report["gates"]["g3_direction_specificity"]["trained"]
    g4 = report["gates"]["g4_substrate_anchor"]

    any_falsifier_cell = False
    if isinstance(g1, dict) and g1 != {"status": UNKNOWN}:
        for key, v in g1.items():
            if not v.get("pass"):
                continue
            g2v = g2.get(key, {})
            g3v = g3.get(key, {})
            if g2v.get("verdict") == "PASS" and g3v.get("pass"):
                any_falsifier_cell = True

    # F11 fix: `all()` over an empty sequence returns True. If every raw_base
    # anchor cell is NOT_RUN (e.g. dose-viability failed at both hs23 and
    # hs29, or the raw_base substrate never ran), the filtered generator
    # below was empty and g4_holding silently came out True -- a vacuous
    # pass being read as "G4 holds", exactly the failure mode gates.yaml's
    # own g4 failure_disposition warns against ("a trained-checkpoint null
    # indicts the instrument rather than the checkpoint"). An empty anchor
    # cell set must be reported as instrument-void, not a pass.
    g4_holding = None
    if isinstance(g4, dict) and "status" not in g4:
        anchor_cells = [
            pos for site in g4["sites"].values() for pos in site["positions"].values()
            if "status" not in pos
        ]
        if anchor_cells:
            g4_holding = all(pos.get("contained", False) for pos in anchor_cells)
        else:
            g4_holding = "UNKNOWN_no_ran_anchor_cells_instrument_void"

    report["summary_rule_verdict"] = {
        "any_registered_cell_fires_falsifier": any_falsifier_cell,
        "g4_holding": g4_holding,
        "reading": (
            "FALSIFIER FIRES (G1 pass + G2 adjudicable-pass + G3 pass at >=1 registered cell)"
            if any_falsifier_cell else
            "supports bounded-search null IF g4_holding and every non-selected cell is a "
            "recorded NOT-RUN with its rung table (see g_dose_viability above) -- this script "
            "does not itself confirm the rung-table completeness condition; the lead adjudicates."
        ),
    }

    out_path = COMMITTED / "gate_report.json"
    write_json(out_path, report)
    print(json.dumps(report["summary_rule_verdict"], indent=2))
    print(f"[adjudicate] wrote {out_path}", flush=True)
    return 0


def parse_args(argv=None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    return ap.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
