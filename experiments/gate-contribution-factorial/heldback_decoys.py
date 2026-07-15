#!/usr/bin/env python3
"""Held-back clear-negative decoy source for gate-contribution-factorial
(cell.yaml `decoys.clear_negative`; gates.yaml `sc2_grading_integrity.
grader_calibration.clear_negative_decoys_from_held_back_pool`).

Ported (logic) from `placebo-seed-distribution-census/heldback_decoys.py`
(read in full before writing this). CPU-only, no GPU, no new generation
pass.

STRUCTURAL FINDING (see `build_pool.py` module docstring for the full
argument -- restated here because this module is where it becomes
observable): census's design scores only an S=300 confab subsample, so its
ENTIRE known-correct held-out pool is naturally held back and available as a
decoy source. THIS experiment's cell.yaml (`subsample.known_correct_
answered.all_arms: full_pool`) scores the FULL known-correct held-out pool
in EVERY arm -- there is no row_key in the family's own held-out known-
correct population that this experiment's own generation leaves unscored.
Consequently `build_heldback_candidates` filters against `row_pool.
heldout_row_keys_by_role(family)["known_correct_answered"]` (this
experiment's OWN scored known population, not a subsample manifest) and,
by construction, excludes every candidate: `n_qualifying_heldback_candidates
== 0` for both families. This is reported to the lead as a build-time
finding, not silently resolved -- `build_pool.load_heldback_candidates`
raises loudly when the resulting runlog is empty rather than allowing a
pool build to proceed without clear-negative decoys.

Filter (same three registered properties as census, cell.yaml
decoys.clear_negative):
  known-correct           role == "known_correct_answered" AND split ==
                           "held_out".
  committed-answer        this harness's OWN fresh detector_v2 regrade
                           (gen_lib.grade_row, byte-identical pin) finds
                           well_formed_correct_v2 == True.
  detector-v2-non-refused  same regrade: refused_v2 == False.
  never in any scored set  row_key is not a member of THIS experiment's own
                           scored known-correct population (structurally
                           impossible to satisfy under the full-pool design;
                           see above).

OUTPUT: analysis/runlog/heldback__<family>.jsonl (gitignored; expected
EMPTY given the structural finding above). analysis-committed/
heldback_decoy_summary.json (COMMITTED; counts and provenance only -- no
question/answer/generation text, no aliases).
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
STAGED = ANALYSIS / "staged_inputs"
COMMITTED = HERE / "analysis-committed"

FAMILIES = config.FAMILIES


def build_heldback_candidates(family: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    baseline_pool = row_pool.baseline_text_pool(family)
    question_pool = row_pool.question_pool(family)
    scored_known_keys = set(row_pool.heldout_row_keys_by_role(family)["known_correct_answered"])

    baseline_source_path = STAGED / family / "baseline.jsonl"
    baseline_source_sha256 = common.sha256_of_file(baseline_source_path) if baseline_source_path.is_file() else None

    n_known_correct_role = 0
    n_excluded_scored = 0
    n_regraded_refused = 0
    n_regraded_not_well_formed_correct = 0
    out: list[dict[str, Any]] = []

    for row_key, rec in baseline_pool.items():
        if rec.get("role") != "known_correct_answered" or rec.get("split") != "held_out":
            continue
        n_known_correct_role += 1
        if row_key in scored_known_keys:
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
                "regraded_by": "heldback_decoys.build_heldback_candidates (this harness's own gen_lib.grade_row)",
            },
        })

    counters = {
        "family": family,
        "n_known_correct_role_in_staged_baseline": n_known_correct_role,
        "n_excluded_already_in_this_experiments_own_scored_known_pool": n_excluded_scored,
        "n_excluded_regrade_refused_v2": n_regraded_refused,
        "n_excluded_regrade_not_well_formed_correct_v2": n_regraded_not_well_formed_correct,
        "n_qualifying_heldback_candidates": len(out),
        "baseline_source_path": str(baseline_source_path),
        "baseline_source_sha256": baseline_source_sha256,
        "structural_finding": (
            "full-known-pool design (cell.yaml subsample.known_correct_answered."
            "all_arms: full_pool) means every known-correct held-out row is scored "
            "in every arm; this family's own held-out pool has no unscored subset, "
            "so n_qualifying_heldback_candidates == 0 by construction. See module "
            "docstring / build_pool.py docstring."
        ),
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
              f"excluded_already_scored={counters['n_excluded_already_in_this_experiments_own_scored_known_pool']}, "
              f"excluded_refused_v2={counters['n_excluded_regrade_refused_v2']}, "
              f"excluded_not_wfc_v2={counters['n_excluded_regrade_not_well_formed_correct_v2']})",
              flush=True)
    common.write_json(COMMITTED / "heldback_decoy_summary.json", summary)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--family", choices=FAMILIES, default=None, help="default: build all families")
    ap.set_defaults(func=cmd_build)
    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
