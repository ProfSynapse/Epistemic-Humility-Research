#!/usr/bin/env python3
"""Materialize the LOCAL, gitignored, full row pool
(`analysis/rows_with_text.jsonl`) that `capture_family_atlas_cell.py`'s
`--row-pool` argument reads, by joining this cell's COMMITTED ID-only
manifests (row_key/role/split -- NO question text) against question text
fetched at run time. Mirrors
`experiments/doubt-gated-caution-tighten/materialize_rows.py`'s containment
scheme EXACTLY (read in full before writing this), extended to also cover
this cell's third role, `unknown_refused`, which that sibling script does
not need.

This repo is PUBLIC. Dataset/pool/question-text row content is never
committed (see `.skills/pr-workflow/SKILL.md` "Datasets are never
committed"). The OUTPUT of this script, and every intermediate holding
question text, stays under this experiment's own gitignored `analysis/`
(see `.gitignore`: `analysis/`). This script itself contains no row text and
is safe to commit.

Row-key sources (ID-only, already committed in this repo):
  - confab, known_correct_answered:
    `experiments/common/doubt-gated-caution-tighten-heldout-split/split_manifest.json`
  - unknown_refused:
    `experiments/qwen3-4b-family-atlas/unknown_refused_manifest.json`
    (this cell's own derived, ID-only manifest; see NOTEBOOK.md and
    `derive_unknown_refused_manifest.py`)

Question-text sources (fetched/derived at run time, never committed):
  - confab, known_correct_answered: same HF staging pool the sibling
    experiment uses, `hf_hub_download(repo_id="professorsynapse/eh-al-prep-staging",
    filename="pools/a0_pool_v21_questions.jsonl", repo_type="dataset")`.
    Covers confab 309/309 by row_key, but only 89/430 known_correct_answered
    row_keys directly.
  - known_correct_answered's remaining 341 row_keys (all `ahx::triviaqa::*`,
    per the 430-key breakdown: ahx::triviaqa 370, ah::kuq_ku_known 26,
    ah::selfaware_answerable 22, ahx::popqa 12 -- the staging pool already
    covers all but the triviaqa segment): recovered via
    `rebuild_expansion_candidates.py`, a deterministic CPU rebuild of the
    Amendment AH stage-0 candidate chain (AF-600 pool -> candidates.jsonl ->
    expansion_candidates.jsonl) from local dataset files, seeded and
    verified against the original run's own committed manifests
    (`professorsynapse/eh-doubt-on-command:metadata/*_manifest.json`) --
    see that script's docstring and NOTEBOOK.md for the full recovery
    provenance and gate results. All 430 known_correct_answered keys resolve
    from the union of its `candidates` (ah:: rows) and `expansion` (ahx::
    rows) outputs; only entries NOT already covered by the staging pool are
    used (`setdefault`), so the staging pool's already-verified text is
    never overridden.
  - unknown_refused: the cached staging pool this cell's own
    `derive_unknown_refused_manifest.py` already reads,
    `pools/ak_stage1_pool.jsonl` (same STAGING_REPO), which carries a
    `question` field directly for all 1,338 of its rows (a superset covering
    all 1,029 unknown_refused row_keys).

Aliases: NOT needed by this cell. Unlike the sibling experiment (which grades
false-refusal correctness and needs gold-answer aliases), this atlas cell's
render function (`render_qwen3_atlas.py`) and capture script
(`capture_family_atlas_cell.py`) only ever read `row["question"]`,
`row["row_key"]`, `row["role"]`, `row["split"]` (plus optional `source` /
`category_canon` for bookkeeping) -- see both files. This script does not
join or emit an `aliases` field.

Usage:
  python materialize_rows.py
    (writes analysis/rows_with_text.jsonl, gitignored)

Exit status mirrors the sibling script's hard-fail discipline: nonzero if any
row_key in either committed manifest has no resolvable question text after
the join. A full row pool is still written even on failure so a partial
count can be inspected, but this cell must NOT proceed to `capture` while
any row_key remains textless.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
ANALYSIS = HERE / "analysis"

SPLIT_MANIFEST_PATH = (
    REPO_ROOT
    / "experiments/common/doubt-gated-caution-tighten-heldout-split/split_manifest.json"
)
UNKNOWN_REFUSED_MANIFEST_PATH = HERE / "unknown_refused_manifest.json"
OUT_PATH = ANALYSIS / "rows_with_text.jsonl"

STAGING_REPO = "professorsynapse/eh-al-prep-staging"
QUESTION_POOL_IN_REPO = "pools/a0_pool_v21_questions.jsonl"
AK_STAGE1_POOL_IN_REPO = "pools/ak_stage1_pool.jsonl"

sys.path.insert(0, str(HERE))
import rebuild_expansion_candidates as _rebuild  # noqa: E402


def load_jsonl(p: Path) -> list[dict]:
    return [json.loads(ln) for ln in p.open(encoding="utf-8") if ln.strip()]


def fetch_from_hub(filename: str) -> Path:
    from huggingface_hub import hf_hub_download

    p = hf_hub_download(repo_id=STAGING_REPO, filename=filename, repo_type="dataset")
    return Path(p)


def load_committed_rows() -> list[dict]:
    if not SPLIT_MANIFEST_PATH.is_file():
        print(f"[materialize] ERROR: split manifest not found at {SPLIT_MANIFEST_PATH}.",
              file=sys.stderr)
        raise SystemExit(1)
    if not UNKNOWN_REFUSED_MANIFEST_PATH.is_file():
        print(f"[materialize] ERROR: unknown_refused manifest not found at "
              f"{UNKNOWN_REFUSED_MANIFEST_PATH}. Run derive_unknown_refused_manifest.py first.",
              file=sys.stderr)
        raise SystemExit(1)

    split_manifest = json.loads(SPLIT_MANIFEST_PATH.read_text())
    unknown_refused_manifest = json.loads(UNKNOWN_REFUSED_MANIFEST_PATH.read_text())

    rows: list[dict] = []
    rows.extend(split_manifest["rows"])  # confab, known_correct_answered
    rows.extend(unknown_refused_manifest["rows"])  # unknown_refused
    return rows


def main() -> int:
    rows = load_committed_rows()
    print(f"[materialize] loaded {len(rows)} row assignments "
          f"({SPLIT_MANIFEST_PATH.name} + {UNKNOWN_REFUSED_MANIFEST_PATH.name})")

    question_by_key: dict[str, str] = {}

    a0_pool_path = fetch_from_hub(QUESTION_POOL_IN_REPO)
    print(f"[materialize] fetched a0 question pool -> {a0_pool_path}")
    for r in load_jsonl(a0_pool_path):
        rk, q = r.get("row_key"), r.get("question")
        if rk is not None and q:
            question_by_key[rk] = q

    print("[materialize] running rebuild_expansion_candidates's deterministic "
          "AH stage-0 chain to cover known_correct_answered keys the staging "
          "pool doesn't (see that script's own docstring + NOTEBOOK.md)...")
    af600_pool = _rebuild.build_af600_pool()
    af600_questions = {_rebuild.norm_question(r["question"]) for r in af600_pool}
    rebuilt_candidates = _rebuild.build_candidates(af600_questions)
    rebuilt_expansion, _new_ku, _tqa, _pqa = _rebuild.build_expansion(af600_questions, rebuilt_candidates)
    n_rebuilt = 0
    for r in rebuilt_candidates + rebuilt_expansion:
        rk, q = r.get("row_key"), r.get("question")
        if rk is not None and q and rk not in question_by_key:
            question_by_key[rk] = q
            n_rebuilt += 1
    print(f"[materialize] {n_rebuilt} question(s) newly resolved from the "
          f"rebuilt AH stage-0 chain (candidates.jsonl {len(rebuilt_candidates)} rows "
          f"+ expansion_candidates.jsonl {len(rebuilt_expansion)} rows); "
          "does not override staging-pool-sourced text.")

    ak_pool_path = fetch_from_hub(AK_STAGE1_POOL_IN_REPO)
    print(f"[materialize] fetched ak_stage1 pool -> {ak_pool_path}")
    n_ak = 0
    for r in load_jsonl(ak_pool_path):
        rk, q = r.get("row_key"), r.get("question")
        if rk is not None and q:
            question_by_key.setdefault(rk, q)
            n_ak += 1
    print(f"[materialize] {n_ak} question(s) available from ak_stage1 pool "
          "(used for unknown_refused; does not override a0-sourced text)")

    ANALYSIS.mkdir(parents=True, exist_ok=True)
    n_missing_q = 0
    missing_by_role: dict[str, int] = {}
    with OUT_PATH.open("w", encoding="utf-8") as fh:
        for rec in rows:
            rk = rec["row_key"]
            question = question_by_key.get(rk)
            if not question:
                n_missing_q += 1
                missing_by_role[rec["role"]] = missing_by_role.get(rec["role"], 0) + 1
            out_rec = {
                "row_key": rk,
                "role": rec["role"],
                "split": rec["split"],
                "source": rec.get("source"),
                "category_canon": rec.get("category_canon"),
                "question": question,
            }
            fh.write(json.dumps(out_rec, ensure_ascii=False) + "\n")

    print(f"[materialize] WROTE {OUT_PATH} ({len(rows)} rows); "
          f"missing_question={n_missing_q} missing_by_role={missing_by_role}")
    if n_missing_q:
        print(f"[materialize] ERROR: {n_missing_q} rows have no question text "
              "after the join. Cell cannot proceed to capture until this is "
              "closed.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
