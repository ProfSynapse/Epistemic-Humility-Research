#!/usr/bin/env python3
"""Held-back clear-negative decoy source for placebo-seed-distribution-census
(cell.yaml `decoys.clear_negative`; gates.yaml `sc2_grading_integrity.
grader_calibration.clear_negative_decoys_from_held_back_pool`).

build_pool.py expects `analysis/runlog/heldback__<family>.jsonl`: committed-
answer, detector-v2-non-refused, known-correct rows that never enter any
scored rate (successor fix (a), RR3 cell.yaml 191-196). CPU-only, no GPU, no
new generation pass.

Source: the family's ALREADY-STAGED baseline runlog (`analysis/staged_inputs/
<family>/baseline.jsonl`, SC0), which carries BOTH the scored `confab` role
rows AND `known_correct_answered` role rows from the SAME generation pass.
Census scored rates use ONLY the S=300 confab subsample rows (`row_pool.
paired_confab_row_keys` / the committed subsample manifest), so every
`known_correct_answered` row in the staged baseline is structurally held back
from every scored set ALREADY, by role alone -- this module does not invent a
new population, it selects and re-grades the one that was already sitting
unused in the staged baseline.

Filter (three registered properties, cell.yaml decoys.clear_negative):
  known-correct           role == "known_correct_answered" AND split ==
                           "held_out" (the harness that generated this
                           baseline already verified the ground-truth
                           correctness of this row's answer_value).
  committed-answer        this census's OWN fresh detector_v2 regrade
                           (gen_lib.grade_row, byte-identical pin to the rest
                           of the harness) finds well_formed_correct_v2 ==
                           True: the row committed to a specific answer value
                           that regrades as correct under THIS census's own
                           detector, not just the source harness's original
                           grade.
  detector-v2-non-refused  same regrade: refused_v2 == False.
  never in any scored set  row_key is not a member of the family's committed
                           S-row subsample manifest (belt-and-suspenders on
                           top of the structural role separation above).

OUTPUT: analysis/runlog/heldback__<family>.jsonl (gitignored; one row per
qualifying candidate, `_normalize`-compatible: row_key, role, source,
category_canon, answer_text, refused_v2, plus provenance fields recording
where the row came from and that it was regraded fresh by this module).
analysis-committed/heldback_decoy_summary.json (COMMITTED; counts and
provenance only -- no question/answer/generation text, no aliases).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import config  # noqa: E402
import common  # noqa: E402
import row_pool  # noqa: E402
import gen_lib  # noqa: E402

ANALYSIS = HERE / "analysis"
COMMITTED = HERE / "analysis-committed"

FAMILIES = ("qwen35_4b", "mistral7b_v03", "llama32_3b")


def _subsample_row_keys(family: str) -> set[str]:
    manifest_path = COMMITTED / "subsample_manifest.json"
    if not manifest_path.is_file():
        return set()
    manifest = common.load_json(manifest_path)
    return set(manifest["families"][family]["row_keys"])


def build_heldback_candidates(family: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Returns (candidate_rows, counters). candidate_rows carry the fields
    build_pool.py's `_normalize` needs (row_key, role, source, answer_text,
    refused_v2) plus provenance. counters is a build-time report dict (no
    text) for the committed summary."""
    baseline_pool = row_pool.baseline_text_pool(family)  # row_key -> staged baseline record (has answer_text)
    question_pool = row_pool.question_pool(family)  # row_key -> {aliases, category_canon, source, question}
    scored_keys = _subsample_row_keys(family)

    baseline_source_path = config.BASELINE_RUNLOG[family]
    baseline_source_sha256 = common.sha256_of_file(baseline_source_path)

    n_known_correct_role = 0
    n_excluded_scored = 0
    n_regraded_refused = 0
    n_regraded_not_well_formed_correct = 0
    out: list[dict[str, Any]] = []

    for row_key, rec in baseline_pool.items():
        if rec.get("role") != "known_correct_answered" or rec.get("split") != "held_out":
            continue
        n_known_correct_role += 1
        if row_key in scored_keys:
            n_excluded_scored += 1
            continue
        q = question_pool.get(row_key, {})
        aliases = q.get("aliases") or []
        text = rec.get("answer_text", "")
        grade = gen_lib.grade_row(text, bool(rec.get("terminated_naturally", True)), aliases)
        if grade["refused_v2"]:
            n_regraded_refused += 1
            continue
        if not grade["well_formed_correct_v2"]:
            n_regraded_not_well_formed_correct += 1
            continue
        out.append({
            "row_key": row_key, "role": rec.get("role"), "source": q.get("source") or rec.get("source"),
            "category_canon": q.get("category_canon") or rec.get("category_canon"),
            "answer_text": text, "terminated_naturally": bool(rec.get("terminated_naturally", True)),
            **grade,
            "provenance": {
                "family": family, "origin": "staged_baseline_known_correct_role",
                "baseline_source_path": str(baseline_source_path),
                "baseline_source_sha256": baseline_source_sha256,
                "regraded_by": "heldback_decoys.build_heldback_candidates (this census's own gen_lib.grade_row)",
            },
        })

    counters = {
        "family": family,
        "n_known_correct_role_in_staged_baseline": n_known_correct_role,
        "n_excluded_already_in_scored_subsample": n_excluded_scored,
        "n_excluded_regrade_refused_v2": n_regraded_refused,
        "n_excluded_regrade_not_well_formed_correct_v2": n_regraded_not_well_formed_correct,
        "n_qualifying_heldback_candidates": len(out),
        "baseline_source_path": str(baseline_source_path),
        "baseline_source_sha256": baseline_source_sha256,
    }
    return out, counters


def runlog_path(tag: str) -> Path:
    return ANALYSIS / "runlog" / f"{tag}.jsonl"


def cmd_build(args: argparse.Namespace) -> int:
    families = [args.family] if args.family else list(FAMILIES)
    summary: dict[str, Any] = {"families": {}}
    for family in families:
        candidates, counters = build_heldback_candidates(family)
        out_path = runlog_path(f"heldback__{family}")
        common.write_jsonl(out_path, candidates)
        summary["families"][family] = counters
        print(f"[heldback_decoys] {family}: {counters['n_qualifying_heldback_candidates']} qualifying "
              f"rows written to {out_path.relative_to(HERE)} "
              f"(role-eligible={counters['n_known_correct_role_in_staged_baseline']}, "
              f"excluded_scored={counters['n_excluded_already_in_scored_subsample']}, "
              f"excluded_refused_v2={counters['n_excluded_regrade_refused_v2']}, "
              f"excluded_not_wfc_v2={counters['n_excluded_regrade_not_well_formed_correct_v2']})",
              flush=True)
    common.write_json(COMMITTED / "heldback_decoy_summary.json", summary)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--family", choices=FAMILIES, default=None, help="default: build all three families")
    ap.set_defaults(func=cmd_build)
    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
