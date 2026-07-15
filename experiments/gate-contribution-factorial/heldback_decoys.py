#!/usr/bin/env python3
"""Held-back clear-negative decoy source for gate-contribution-factorial
(cell.yaml `decoys.clear_negative`; gates.yaml `sc2_grading_integrity.
grader_calibration.clear_negative_decoys_from_held_back_pool`).

Ported (logic) from `placebo-seed-distribution-census/heldback_decoys.py`
(read in full before writing this). CPU-only against the decoy source and
against the grading logic; the decoy TEXT itself comes from a small, separate
GPU generation pass (`run_factorial.py decoy-baseline`), not from this
module.

STRUCTURAL FINDING (see `build_pool.py` module docstring for the full
argument -- restated here because this module is where it becomes
observable): census's design scores only an S=300 confab subsample, so its
ENTIRE known-correct held-out pool is naturally held back and available as a
decoy source. THIS experiment's cell.yaml (`subsample.known_correct_
answered.all_arms: full_pool`) scores the FULL known-correct held-out pool
in EVERY arm -- there is no row_key in the family's own held-out known-
correct population that this experiment's own generation leaves unscored.
`decoy_source_rows` below therefore CANNOT draw from this family's own
held-out pool (that source is structurally empty, verified by the very
disjointness check in this module).

LEAD DECISION (NOTEBOOK.md 2026-07-15, "harness accepted" entry, item 2;
instrument-input choice, consistent with the registered text "a HELD-BACK
pool of committed-answer, detector-v2-non-refused known-correct rows that
never enter any scored rate"): draw the held-back pool from a fresh
UNSTEERED baseline generation over FIT/atlas-split known-correct rows --
rows that are disjoint from this experiment's held-out pool BY
CONSTRUCTION (the source experiments partition every row into "fit" xor
"held_out"; a row cannot be in both), so they can never enter any scored
rate no matter what this experiment's own generation covers.

  qwen35_4b       `qwen35-4b-midband-doubt-snap`'s own materialized FIT
                  working file (that experiment's `materialize_reused_
                  rows.py`, reused verbatim from `doubt-snap-cross-family-
                  confirmatory`'s qwen35_4b cell): 240 known_correct_
                  answered rows at split=="fit".
  mistral7b_v03   `rr3-corrected-placebo-replication`'s own materialized
                  atlas join (that experiment's `materialize_rows.py
                  cmd_materialize`, which deliberately joins EVERY split --
                  see that module's own docstring, "fit_reuse.py and the
                  held-back decoy pass both need fit-split rows"): 255
                  known_correct_answered rows at split=="fit".

Both source files are PRIVATE (question text + aliases) and live in a
sibling worktree of a DIFFERENT experiment, outside this experiment's own
git tree; read read-only here, never copied into a committed path, never
written to analysis-committed/.

Filter (same two registered properties as census, cell.yaml decoys.
clear_negative, applied to the FRESH unsteered generation over the FIT
source rows, not to any text this experiment scores):
  committed-answer          this harness's OWN fresh detector_v2 regrade
                             (gen_lib.grade_row, byte-identical pin) finds
                             well_formed_correct_v2 == True.
  detector-v2-non-refused   same regrade: refused_v2 == False.
  never in any scored set    row_key is not a member of THIS experiment's
                             own scored known-correct population (checked
                             twice: once structurally in
                             `decoy_source_rows`, once again defensively
                             here against the decoy-baseline runlog).

INPUT: `analysis/runlog/<family>__decoy_baseline.jsonl` (gitignored; written
by `run_factorial.py decoy-baseline`, a small unsteered GPU pass over
`decoy_source_rows(family)`). Raises loudly (not a silent empty pool) if
this runlog is absent -- the GPU pass has to run first.

OUTPUT: `analysis/runlog/heldback__<family>.jsonl` (gitignored; UNCHANGED
output path/shape from the prior version of this module, so `build_pool.py`
`load_heldback_candidates` needs no changes). `analysis-committed/
heldback_decoy_summary.json` (COMMITTED; counts and provenance only -- no
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

# Cross-worktree decoy SOURCE files (question text + aliases; PRIVATE,
# read-only, never staged into this experiment's own tree). Mirrors
# config.py's own `_WT` cross-worktree convention for this repo's worktree
# layout on this machine.
_WT = Path("/home/profsynapse/code/ehr-worktrees")
QWEN_FIT_SOURCE_PATH = (
    _WT / "qwen35-midband" / "experiments" / "qwen35-4b-midband-doubt-snap"
    / "analysis" / "fit_rows_for_anchor.jsonl"
)
MISTRAL_FIT_SOURCE_PATH = (
    _WT / "rr3-corrected-placebo" / "experiments" / "rr3-corrected-placebo-replication"
    / "analysis" / "mistral" / "joined_rows_private.jsonl"
)
DECOY_SOURCE_PATH: dict[str, Path] = {
    "qwen35_4b": QWEN_FIT_SOURCE_PATH,
    "mistral7b_v03": MISTRAL_FIT_SOURCE_PATH,
}


def decoy_source_rows(family: str) -> list[dict[str, Any]]:
    """The held-back clear-negative decoy SOURCE population (lead decision,
    see module docstring): FIT-split known_correct_answered rows from the
    named source file, filtered and verified disjoint from this
    experiment's own scored known-correct population. Returns row dicts
    with exactly the fields `run_factorial.py decoy-baseline` and
    `render.render` need (row_key, question, aliases, category_canon,
    source, role, split) -- no other fields are read from the source file
    (in particular, qwen's source file also carries a PRIOR `baseline_text`
    from a different amendment's own FIT-side run; that text is deliberately
    NOT reused here -- the lead decision calls for a FRESH unsteered
    generation, not a byte-reuse)."""
    path = DECOY_SOURCE_PATH[family]
    if not path.is_file():
        raise SystemExit(
            f"decoy_source_rows FAIL ({family}): FIT-split known-correct decoy source "
            f"file not found at {path}. This is the lead-decided held-back clear-negative "
            f"decoy source (NOTEBOOK.md 2026-07-15 harness-accepted entry, item 2); without "
            f"it there is no clear-negative decoy source and no grading pool can be built."
        )
    rows = common.load_jsonl(path)
    candidates = [
        r for r in rows
        if r.get("role") == "known_correct_answered" and r.get("split") == "fit"
    ]
    if not candidates:
        raise SystemExit(
            f"decoy_source_rows FAIL ({family}): 0 known_correct_answered rows at "
            f"split=='fit' found in {path} ({len(rows)} rows total); the decoy source "
            f"is expected to be non-empty."
        )
    scored_known_keys = set(row_pool.heldout_row_keys_by_role(family)["known_correct_answered"])
    overlap = sorted({r["row_key"] for r in candidates} & scored_known_keys)
    if overlap:
        raise SystemExit(
            f"decoy_source_rows FAIL ({family}): {len(overlap)} FIT-split decoy source "
            f"row_keys overlap this experiment's OWN scored held-out known-correct "
            f"population; sample {overlap[:5]}. A decoy source must never overlap a "
            f"scored row_key (successor fix (a)); refusing to proceed."
        )
    out = []
    for r in candidates:
        out.append({
            "row_key": r["row_key"], "question": r.get("question"),
            "aliases": r.get("aliases") or [], "category_canon": r.get("category_canon"),
            "source": r.get("source"), "role": r.get("role"), "split": r.get("split"),
        })
    return out


def decoy_baseline_runlog_path(family: str) -> Path:
    return ANALYSIS / "runlog" / f"{family}__decoy_baseline.jsonl"


def build_heldback_candidates(family: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    source_rows = decoy_source_rows(family)
    source_by_key = {r["row_key"]: r for r in source_rows}

    decoy_baseline_path = decoy_baseline_runlog_path(family)
    if not decoy_baseline_path.is_file():
        raise SystemExit(
            f"build_heldback_candidates FAIL ({family}): decoy-baseline runlog not found "
            f"at {decoy_baseline_path}. Run `run_factorial.py decoy-baseline --family "
            f"{family} --i-know-this-runs-on-gpu` first (a small unsteered GPU pass over "
            f"decoy_source_rows({family!r}), {len(source_rows)} rows) -- this module never "
            f"generates text itself, and does not silently degrade to an empty pool."
        )
    decoy_baseline_rows = common.load_jsonl(decoy_baseline_path)
    if not decoy_baseline_rows:
        raise SystemExit(
            f"build_heldback_candidates FAIL ({family}): decoy-baseline runlog at "
            f"{decoy_baseline_path} exists but is EMPTY."
        )
    decoy_baseline_sha256 = common.sha256_of_file(decoy_baseline_path)

    scored_known_keys = set(row_pool.heldout_row_keys_by_role(family)["known_correct_answered"])

    n_decoy_baseline_rows = 0
    n_excluded_overlap_scored = 0
    n_excluded_missing_source_row = 0
    n_regraded_refused = 0
    n_regraded_not_well_formed_correct = 0
    out: list[dict[str, Any]] = []

    for rec in decoy_baseline_rows:
        n_decoy_baseline_rows += 1
        row_key = rec["row_key"]
        if row_key in scored_known_keys:
            # Defense in depth: decoy_source_rows() already refuses to
            # proceed on any such overlap, so this branch should be
            # unreachable given a valid decoy-baseline runlog; reported
            # (not silently dropped) in case the runlog was produced by
            # some other means.
            n_excluded_overlap_scored += 1
            continue
        src = source_by_key.get(row_key)
        if src is None:
            n_excluded_missing_source_row += 1
            continue
        aliases = src.get("aliases") or []
        text = rec.get("answer_text", "")
        grade = gen_lib.grade_row(text, bool(rec.get("terminated_naturally", True)), aliases)
        if grade["refused_v2"]:
            n_regraded_refused += 1
            continue
        if not grade["well_formed_correct_v2"]:
            n_regraded_not_well_formed_correct += 1
            continue
        out.append({
            "row_key": row_key, "role": src.get("role") or rec.get("role"),
            "source": src.get("source") or rec.get("source"),
            "category_canon": src.get("category_canon") or rec.get("category_canon"),
            "answer_text": text, "terminated_naturally": bool(rec.get("terminated_naturally", True)),
            **grade,
            "provenance": {
                "family": family, "origin": "decoy_baseline_generation_over_fit_split_known_correct_rows",
                "decoy_baseline_runlog_path": str(decoy_baseline_path),
                "decoy_baseline_runlog_sha256": decoy_baseline_sha256,
                "fit_source_file_path": str(DECOY_SOURCE_PATH[family]),
                "regraded_by": "heldback_decoys.build_heldback_candidates (this harness's own gen_lib.grade_row)",
            },
        })

    counters = {
        "family": family,
        "n_decoy_source_rows": len(source_rows),
        "n_decoy_baseline_rows_generated": n_decoy_baseline_rows,
        "n_excluded_overlap_with_scored_known_pool": n_excluded_overlap_scored,
        "n_excluded_missing_source_row": n_excluded_missing_source_row,
        "n_excluded_regrade_refused_v2": n_regraded_refused,
        "n_excluded_regrade_not_well_formed_correct_v2": n_regraded_not_well_formed_correct,
        "n_qualifying_heldback_candidates": len(out),
        "decoy_baseline_runlog_path": str(decoy_baseline_path),
        "decoy_baseline_runlog_sha256": decoy_baseline_sha256,
        "fit_source_file_path": str(DECOY_SOURCE_PATH[family]),
        "lead_decision": (
            "NOTEBOOK.md 2026-07-15 harness-accepted entry item 2: held-back pool drawn "
            "from a fresh UNSTEERED baseline generation over FIT/atlas-split known-correct "
            "rows, disjoint from the held-out pool by construction."
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
              f"(decoy_source_rows={counters['n_decoy_source_rows']}, "
              f"decoy_baseline_generated={counters['n_decoy_baseline_rows_generated']}, "
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
