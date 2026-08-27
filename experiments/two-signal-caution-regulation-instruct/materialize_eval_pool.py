#!/usr/bin/env python3
"""Materialize the LOCAL, gitignored, full eval pool
(`analysis/eval_pool_both_tail.jsonl`) that `cell.yaml`'s `surface.rows_path`
reads, by joining the COMMITTED derived-columns-only manifest
(`analysis-committed/eval_pool_manifest.jsonl` -- row_key, cell, gold_class,
projections, gains; NO question text, NO aliases) against question text
fetched at run time from the private HF staging repo, mirroring the
j-space-localization-qwen3-4b containment migration EXACTLY (see
`experiments/j-space-localization-qwen3-4b/jlens.py:fetch_source_pool` /
`analysis-committed/corpus/PROVENANCE.md`, commit 88c98cdc in worktree
`/home/profsynapse/code/ehr-worktrees/j-space`).

This repo is PUBLIC. Dataset/pool/question-text/eval-row text is never
committed (see `.skills/pr-workflow/SKILL.md` "Datasets are never
committed"). `eval_pool_both_tail.jsonl` used to commit `question` (and
`aliases`) directly; that stopped 2026-07-07 (bf16 substrate pivot). Only this
experiment's OWN derived numeric columns are committed now.

Question text: `hf_hub_download(repo_id="professorsynapse/eh-al-prep-staging",
filename="pools/a0_pool_v21_questions.jsonl", repo_type="dataset")` -- verified
(2026-07-07) to cover all 458 of this eval pool's row_keys (both the confab
and answerable_refused cells; confab rows are AH A0 rows too, since the AK
Stage-1 unanswerable-only pool is itself derived from the AH A0 pool) with
question text byte-identical to the local canonical-checkout AH A0 pool
(`experiment/phase1/probe/analysis/ah_main/gen_A0/rows.jsonl`), so a single HF
pool suffices for every row in this eval pool.

Aliases (gold-answer text for the 149 answerable_refused rows' correctness
grading): NOT re-committed and NOT re-staged to HF by this script -- aliases
already originate from this repo's own already-committed, publicly-tracked
`datasets/kuq/knowns_unknowns.jsonl` / `datasets/selfaware/SelfAware.json`
(joined once, upstream, by `amendment_ah_stage0_candidates.py`, into the
canonical-checkout-only gitignored AH A0 pool this script reads locally). This
script therefore still depends on the canonical checkout's local
`experiment/phase1/probe/analysis/ah_main/gen_A0/rows.jsonl` for aliases only
(same local-checkout dependency `extract_l34_anchor.py` and
`build_two_signal_directions.py` already have) -- it does not commit or
re-stage that text; it only reads it locally at run time, same as every other
script in this experiment's build.

Usage:
  python materialize_eval_pool.py
    (writes analysis/eval_pool_both_tail.jsonl, gitignored)
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
COMMITTED = HERE / "analysis-committed"
ANALYSIS = HERE / "analysis"

MANIFEST_PATH = COMMITTED / "eval_pool_manifest.jsonl"
OUT_PATH = ANALYSIS / "eval_pool_both_tail.jsonl"

STAGING_REPO = "professorsynapse/eh-al-prep-staging"
QUESTION_POOL_IN_REPO = "pools/a0_pool_v21_questions.jsonl"

AH_A0_ROWS = Path(
    "/home/profsynapse/code/Epistemic-Humility-Research/experiment/phase1/probe/"
    "analysis/ah_main/gen_A0/rows.jsonl"
)


def load_jsonl(p: Path) -> list[dict]:
    return [json.loads(ln) for ln in p.open(encoding="utf-8") if ln.strip()]


def fetch_question_pool() -> Path:
    """Fetch the AH A0 question pool from the private HF staging repo (the
    ONLY source of question text this script uses) -- requires HF_TOKEN in
    the environment; huggingface_hub reads it automatically."""
    from huggingface_hub import hf_hub_download

    p = hf_hub_download(repo_id=STAGING_REPO, filename=QUESTION_POOL_IN_REPO,
                        repo_type="dataset")
    return Path(p)


def main() -> int:
    if not MANIFEST_PATH.is_file():
        print(f"[materialize] ERROR: committed manifest not found at {MANIFEST_PATH}. "
              "Run build_two_signal_directions.py first.", file=sys.stderr)
        return 1

    manifest_rows = load_jsonl(MANIFEST_PATH)
    print(f"[materialize] loaded {len(manifest_rows)} derived-column rows from "
          f"{MANIFEST_PATH}")

    q_pool_path = fetch_question_pool()
    print(f"[materialize] fetched question pool -> {q_pool_path}")
    question_by_key: dict[str, str] = {}
    for r in load_jsonl(q_pool_path):
        rk = r.get("row_key")
        q = r.get("question")
        if rk is not None and q is not None:
            question_by_key[rk] = q

    aliases_by_key: dict[str, list[str]] = {}
    if AH_A0_ROWS.is_file():
        for r in load_jsonl(AH_A0_ROWS):
            rk = r.get("row_key")
            if rk is not None:
                aliases_by_key[rk] = r.get("aliases", [])
    else:
        print(f"[materialize] WARNING: local AH A0 pool not found at {AH_A0_ROWS}; "
              "answerable_refused rows will have empty aliases (correctness "
              "grading on the release tail will be unreliable). This file is "
              "canonical-checkout-only and gitignored, not fetched from HF -- "
              "see this script's own docstring.", file=sys.stderr)

    ANALYSIS.mkdir(parents=True, exist_ok=True)
    n_missing_q = 0
    n_missing_alias_answerable = 0
    with OUT_PATH.open("w", encoding="utf-8") as fh:
        for rec in manifest_rows:
            rk = rec["row_key"]
            question = question_by_key.get(rk)
            if not question:
                n_missing_q += 1
            aliases = aliases_by_key.get(rk, [])
            if rec["cell"] == "answerable_refused" and not aliases:
                n_missing_alias_answerable += 1
            out_rec = dict(rec)
            out_rec["question"] = question
            out_rec["aliases"] = aliases
            fh.write(json.dumps(out_rec, ensure_ascii=False) + "\n")

    print(f"[materialize] WROTE {OUT_PATH} ({len(manifest_rows)} rows); "
          f"missing_question={n_missing_q} "
          f"missing_alias_on_answerable_refused={n_missing_alias_answerable}")
    if n_missing_q:
        print(f"[materialize] ERROR: {n_missing_q} rows have no question text "
              "after the HF join.", file=sys.stderr)
        return 1
    if n_missing_alias_answerable:
        # HARD-FAIL, not a warning: an answerable_refused row with empty
        # aliases cannot be correctness-graded on the release tail (G1-release
        # needs `well_formed_correct`, which requires a gold alias to check
        # against). A silent warning here would let a broken/missing canonical
        # AH A0 pool produce a clean-looking but vacuous release-tail null
        # (every row ungradeable -> correct=False by default -> G1-release
        # reads as a real failure instead of a missing-input failure). Red-team
        # flagged this 2026-07-07; see NOTEBOOK.md.
        print(
            f"[materialize] ERROR: {n_missing_alias_answerable} answerable_refused "
            "rows have empty aliases after the local AH A0 join -- correctness "
            "grading on the release tail cannot proceed. This is a HARD FAIL, not "
            "a warning: check that the canonical checkout's "
            f"{AH_A0_ROWS} is present and up to date.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
