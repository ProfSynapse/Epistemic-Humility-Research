#!/usr/bin/env python3
"""Behavioral leg (Cells A/B/C + within-kuq subtype breakdown) for
placebo-signflip-question-type-analysis.

CPU-only re-slice of already-committed grades by question type (AMENDMENT.md
"Design"/"Cells (behavioral leg...)"). No new grading pass anywhere: every
`refused_final`/`refused_v2` value is read from a persisted row-level log,
never recomputed from generation text.

  Cell A (QH)  qwen35-4b-midband-heldout runlogs, wide grade read from
               abstention-wide-instrument-calibration/analysis/
               row_level_scored.jsonl (cell "QH") joined by (row_key, arm).
  Cell B (MC)  rr2-mistral-adjudicated-refusal-confirm runlogs, refused_final
               reconstructed via RR2's OWN apply_adjudication.py helpers
               (imported, not reimplemented) applied to the staged runlogs +
               the already-committed blinded adjudication join -- the exact
               same computation that produced RR2's committed
               final_report.json (BG0's mc_unanswerable_must_equal check
               verifies bit-for-bit reproduction).
  Cell C (QL)  abstention-wide-instrument-calibration row_level_scored.jsonl
               (cell "QL"), narrow-only (sub_grade.refused_v2): the
               calibration Outcome terminally voided QL's wide lane
               (CG1 clear-positive floor failed twice on QL_shard_07), so
               sub_grade.refused_final is None for every QL row and MUST NOT
               be read here.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from common import (  # noqa: E402
    KUQ_SUBTYPES, combine_active_and_baseline, delta_pts, index_by_row_key,
    load_jsonl, paired_rows, question_type_of, rate_wilson, wilson,
)
from staging import DOUBT_SNAP_DIR, RR2_LOCAL_DIR, STAGED  # noqa: E402

sys.path.insert(0, str(RR2_LOCAL_DIR))
import apply_adjudication as mc_adjudication  # noqa: E402  (RR2's own module, reused read-only)


# ---------------------------------------------------------------------------
# Cell A: QH (qwen heldout)
# ---------------------------------------------------------------------------

def _qh_wide_grade_index() -> dict[tuple[str, str], bool]:
    """calibration/row_level_scored.jsonl, cell "QH" only, keyed by
    (row_key, arm) -> sub_grade.refused_final. Population (which row_keys
    exist per arm/role) is taken from the heldout runlogs, not from this
    index, per AMENDMENT.md Cell A's own join order."""
    out: dict[tuple[str, str], bool] = {}
    for r in load_jsonl(STAGED / "calibration" / "row_level_scored.jsonl"):
        if r["cell"] != "QH":
            continue
        out[(r["row_key"], r["arm"])] = bool(r["sub_grade"]["refused_final"])
    return out


def cell_a_qh() -> dict[str, Any]:
    wide = _qh_wide_grade_index()
    baseline_by_key = index_by_row_key(load_jsonl(STAGED / "qh" / "baseline.jsonl"))
    random_by_key = index_by_row_key(load_jsonl(STAGED / "qh" / "random_direction.jsonl"))

    strata: dict[str, Any] = {}
    subtype_source_rows: dict[str, Any] = {}
    for role, stratum_name in (("confab", "unanswerable"), ("known_correct_answered", "answerable")):
        pairs = paired_rows(random_by_key, baseline_by_key, role=role)
        n = len(pairs)
        b_success = sum(1 for _, b in pairs if wide.get((b["row_key"], "baseline")) is True)
        r_success = sum(1 for a, _ in pairs if wide.get((a["row_key"], "random_direction")) is True)
        b_rate, r_rate = wilson(b_success, n), wilson(r_success, n)
        strata[stratum_name] = {
            "n_paired": n,
            "baseline_refused_final": b_rate, "random_refused_final": r_rate,
            "delta_pts_random_minus_baseline": delta_pts(r_rate, b_rate),
        }
        subtype_source_rows[stratum_name] = pairs

    bg0 = strata["unanswerable"]
    bg0_check = {
        "target": {"baseline": "139/1286", "random": "73/1286", "delta_pts": -5.13},
        "observed": {
            "baseline": f"{bg0['baseline_refused_final']['successes']}/{bg0['baseline_refused_final']['n']}",
            "random": f"{bg0['random_refused_final']['successes']}/{bg0['random_refused_final']['n']}",
            "delta_pts": round(bg0["delta_pts_random_minus_baseline"], 2),
        },
        "match": (
            bg0["baseline_refused_final"]["successes"] == 139 and bg0["baseline_refused_final"]["n"] == 1286
            and bg0["random_refused_final"]["successes"] == 73 and bg0["random_refused_final"]["n"] == 1286
        ),
    }
    strata["answerable"]["note"] = "n=17 dosed, true-power reading, uninformative; RR3 supplies the powered version"

    subtype = subtype_delta_table(
        subtype_source_rows["unanswerable"],
        active_grade=lambda a: wide.get((a["row_key"], "random_direction")),
        baseline_grade=lambda b: wide.get((b["row_key"], "baseline")),
    )
    return {"cell": "A_qh", "family": "qwen35-4b", "strata": strata, "bg0_check": bg0_check, "kuq_subtype_breakdown": subtype}


# ---------------------------------------------------------------------------
# Cell B: MC (mistral RR2)
# ---------------------------------------------------------------------------

def _mc_refused_final_rows() -> dict[str, list[dict[str, Any]]]:
    """Reconstructs row-level refused_final for the full 1,312-row baseline
    and random_direction confab (unanswerable) populations, and the 382-row
    known (answerable) populations, via RR2's OWN apply_adjudication.py
    helpers (`apply_final_refusal`, `combine_with_baseline` for the 9-row
    baseline-fill, `load_id_map`, `load_graded_file`, `load_heldout_roster`)
    -- the exact join that produced RR2's committed final_report.json."""
    id_map = mc_adjudication.load_id_map(STAGED / "mc")
    graded = mc_adjudication.load_graded_file(STAGED / "mc" / "graded.jsonl")
    roster = mc_adjudication.load_heldout_roster(RR2_LOCAL_DIR / "analysis-committed")

    baseline_by_key = index_by_row_key(load_jsonl(STAGED / "mc" / "heldout__baseline.jsonl"))
    random_by_key = index_by_row_key(load_jsonl(STAGED / "mc" / "heldout__random_direction.jsonl"))

    def _apply(rows: list[dict[str, Any]], arm_for: Any) -> list[dict[str, Any]]:
        out = []
        for r in rows:
            arm = arm_for(r)
            out.append(mc_adjudication.apply_final_refusal([r], id_map, graded, arm)[0])
        return out

    baseline_confab = _apply([baseline_by_key[rk] for rk in roster["confab"]], lambda r: "baseline")
    baseline_known = _apply([baseline_by_key[rk] for rk in roster["known"]], lambda r: "baseline")

    rand_confab_combined = combine_active_and_baseline(roster["confab"], random_by_key, baseline_by_key)
    rand_confab = _apply(rand_confab_combined, lambda r: "random_direction" if r["row_key"] in random_by_key else "baseline")

    rand_known_combined = combine_active_and_baseline(roster["known"], random_by_key, baseline_by_key)
    rand_known = _apply(rand_known_combined, lambda r: "random_direction" if r["row_key"] in random_by_key else "baseline")

    return {
        "baseline_confab": baseline_confab, "baseline_known": baseline_known,
        "random_confab": rand_confab, "random_known": rand_known,
    }


def cell_b_mc() -> dict[str, Any]:
    pop = _mc_refused_final_rows()
    b_rate = rate_wilson(pop["baseline_confab"], "refused_final")
    r_rate = rate_wilson(pop["random_confab"], "refused_final")

    bg0_check = {
        "target": {"baseline": "368/1312", "random": "465/1312", "delta_pts": 7.39},
        "observed": {
            "baseline": f"{b_rate['successes']}/{b_rate['n']}", "random": f"{r_rate['successes']}/{r_rate['n']}",
            "delta_pts": round(delta_pts(r_rate, b_rate), 2),
        },
        "match": (
            b_rate["successes"] == 368 and b_rate["n"] == 1312
            and r_rate["successes"] == 465 and r_rate["n"] == 1312
        ),
    }

    strata = {
        "unanswerable": {
            "n_paired": r_rate["n"], "baseline_refused_final": b_rate, "random_refused_final": r_rate,
            "delta_pts_random_minus_baseline": delta_pts(r_rate, b_rate),
        },
        "answerable": {"n_dosed": 0, "note": "registered coverage gap; RR3 supplies the powered version"},
    }

    baseline_by_key = index_by_row_key(pop["baseline_confab"])
    random_by_key = index_by_row_key(pop["random_confab"])
    pairs = [(random_by_key[rk], baseline_by_key[rk]) for rk in baseline_by_key if rk in random_by_key]
    subtype = subtype_delta_table(
        pairs,
        active_grade=lambda a: a.get("refused_final"),
        baseline_grade=lambda b: b.get("refused_final"),
    )
    return {"cell": "B_mc", "family": "mistral7b-v03", "strata": strata, "bg0_check": bg0_check, "kuq_subtype_breakdown": subtype}


# ---------------------------------------------------------------------------
# Cell C: QL (qwen ladder, narrow-only)
# ---------------------------------------------------------------------------

def _ql_category_canon_index() -> dict[str, str]:
    """QL's dosed population is the qwen35-4b-midband-doubt-snap ladder's
    FIT split (887 confab + 240 known_correct_answered, VERIFIED: QL's own
    baseline arm role counts in row_level_scored.jsonl are exactly 887/240),
    not the held-out pool QH uses -- row_level_scored.jsonl carries no
    category_canon field for QL rows at all (verified: absent from its
    schema), so the subtype label is read from the ladder's COMMITTED
    reused_rows_manifest.json ("confab_fit" list; row_key -> category_canon),
    which is provenance for the exact same FIT rows, not a re-derivation."""
    manifest = json.loads((DOUBT_SNAP_DIR / "analysis-committed" / "reused_rows_manifest.json").read_text())
    return {r["row_key"]: r["category_canon"] for r in manifest["rows"]["confab_fit"]}


def cell_c_ql() -> dict[str, Any]:
    rows = [r for r in load_jsonl(STAGED / "calibration" / "row_level_scored.jsonl") if r["cell"] == "QL"]
    baseline_confab = [r for r in rows if r["arm"] == "baseline" and r["role"] == "confab"]

    dose_response: dict[str, Any] = {}
    for hs_index in sorted({r["hs_index"] for r in rows if r["arm"] == "random_direction"}):
        layer_key = f"hs{hs_index}"
        dose_response[layer_key] = {}
        for dose in sorted({r["dose_multiplier"] for r in rows if r["arm"] == "random_direction" and r["hs_index"] == hs_index}):
            cell_rows = [
                r for r in rows if r["arm"] == "random_direction" and r["hs_index"] == hs_index
                and r["dose_multiplier"] == dose and r["role"] == "confab"
            ]
            dose_response[layer_key][str(dose)] = _rate_wilson_narrow(cell_rows)

    baseline_narrow = _rate_wilson_narrow(baseline_confab)

    category_canon_by_key = _ql_category_canon_index()
    all_random_confab = [r for r in rows if r["arm"] == "random_direction" and r["role"] == "confab"]
    for r in all_random_confab:
        r["category_canon"] = category_canon_by_key.get(r["row_key"])
    subtype = subtype_rate_table(all_random_confab, grade=lambda r: r["sub_grade"]["refused_v2"])

    return {
        "cell": "C_ql", "family": "qwen35-4b",
        "void_note": "QL wide lane terminally voided (calibration CG1 clear-positive fail x2 on QL_shard_07); narrow (detector-v2) rate only",
        "baseline_narrow_refused_v2": baseline_narrow,
        "dose_response_narrow_refused_v2_by_layer_and_dose": dose_response,
        "kuq_subtype_breakdown_narrow_refused_v2_pooled_over_layer_and_dose": subtype,
        "answerable_note": "every dosed QL row is unanswerable (kuq); no answerable stratum exists in QL",
    }


def _rate_wilson_narrow(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return rate_wilson([{"refused_v2": r["sub_grade"]["refused_v2"]} for r in rows], "refused_v2")


# ---------------------------------------------------------------------------
# Within-kuq subtype breakdown (descriptive, no gate; AMENDMENT.md "Secondary
# within-unanswerable descriptive breakdown")
# ---------------------------------------------------------------------------

def subtype_delta_table(pairs, active_grade, baseline_grade) -> dict[str, Any]:
    """pairs: list of (active_row, baseline_row) tuples, both carrying
    category_canon. Restricted to KUQ_SUBTYPES (answerable rows, which also
    carry category_canon == their own source name, are excluded by
    construction since `pairs` here is already the unanswerable stratum)."""
    out: dict[str, Any] = {}
    for subtype in KUQ_SUBTYPES:
        sub_pairs = [(a, b) for a, b in pairs if b.get("category_canon") == subtype]
        n = len(sub_pairs)
        b_success = sum(1 for _, b in sub_pairs if baseline_grade(b) is True)
        r_success = sum(1 for a, _ in sub_pairs if active_grade(a) is True)
        b_rate, r_rate = wilson(b_success, n), wilson(r_success, n)
        out[subtype] = {
            "n_paired": n, "baseline_refused_final": b_rate, "random_refused_final": r_rate,
            "delta_pts_random_minus_baseline": delta_pts(r_rate, b_rate) if n else None,
        }
    covered = sum(v["n_paired"] for v in out.values())
    out["_coverage_note"] = f"{covered}/{len(pairs)} paired rows matched a named kuq subtype"
    return out


def subtype_rate_table(rows: list[dict[str, Any]], grade) -> dict[str, Any]:
    """rows: flat list carrying category_canon; reports rate(grade) per
    subtype, pooled over whatever axis the caller already collapsed (QL:
    pooled over layer and dose)."""
    out: dict[str, Any] = {}
    for subtype in KUQ_SUBTYPES:
        sub_rows = [r for r in rows if r.get("category_canon") == subtype]
        out[subtype] = rate_wilson([{"g": grade(r)} for r in sub_rows], "g")
    covered = sum(v["n"] for v in out.values())
    out["_coverage_note"] = f"{covered}/{len(rows)} rows matched a named kuq subtype"
    return out
