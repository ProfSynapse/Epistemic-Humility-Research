# two-signal-caution-regulation-instruct: analysis-committed/ provenance

This repo is PUBLIC. Dataset/pool/question-text/eval-row text is never
committed (see `.skills/pr-workflow/SKILL.md` "Datasets are never
committed"). This directory used to commit `eval_pool_both_tail.jsonl`
directly, with `question` and `aliases` text embedded per row; that stopped
2026-07-07 (bf16 substrate pivot), mirroring the
`j-space-localization-qwen3-4b` containment migration EXACTLY (commit
`88c98cdc` in worktree `/home/profsynapse/code/ehr-worktrees/j-space`; see
that experiment's `jlens.py:fetch_source_pool` /
`analysis-committed/corpus/PROVENANCE.md` for the sibling pattern).

## What is committed here now

- `eval_pool_manifest.jsonl` -- 458 rows, ID + DERIVED COLUMNS ONLY: `row_key`,
  `safe_key`, `cell` ("confab" | "answerable_refused"), `gold_class`,
  `category_canon`, `source`, `proj_d`, `proj_p`, `proj_c`, `z_d`, `z_p`,
  `g_two_signal`, `marginal_write`, `g_two_signal_unclipped`,
  `marginal_write_unclipped`, `clipped`. No `question`, no `aliases`. Written
  by `build_two_signal_directions.py`.
- `u_d_L34.json`, `c_hat_L34.json`, `source_directions/pos_ctrl_L34.json`,
  `source_directions/neg_ctrl_L34.json` -- this experiment's own fitted
  direction JSONs (our own output, not source data; see each file's
  `provenance` field for fit method/n/substrate).
- `build_manifest.json` -- full fit report (counts, cosines, mu/sigma,
  alpha/clip, marginal-write distribution).
- `PROVENANCE.md` -- this file.

## How the full local eval pool is materialized (never committed)

`cell.yaml`'s `surface.rows_path` points at `analysis/eval_pool_both_tail.jsonl`
(gitignored -- `analysis/` is blanket-ignored by this experiment's
`.gitignore`), NOT at anything under `analysis-committed/`. That file is
produced by `materialize_eval_pool.py`, which:

1. Reads the committed `eval_pool_manifest.jsonl` (derived columns, no text).
2. Fetches question text via `hf_hub_download(repo_id=
   "professorsynapse/eh-al-prep-staging",
   filename="pools/a0_pool_v21_questions.jsonl", repo_type="dataset")` and
   joins by `row_key`. Verified (2026-07-07) to cover all 458 of this eval
   pool's row_keys -- both cells -- with question text byte-identical to the
   local canonical-checkout AH A0 pool (the AK Stage-1 unanswerable-only pool
   is itself derived from AH A0, so a single HF pool suffices for both
   cells).
3. Joins `aliases` (gold-answer text for the 149 `answerable_refused` rows'
   correctness grading) from the LOCAL canonical-checkout
   `experiment/phase1/probe/analysis/ah_main/gen_A0/rows.jsonl` (gitignored,
   never committed or re-staged by this script). Aliases are not source data
   this script introduces: they already originate from this repo's own
   already-committed, publicly-tracked `datasets/kuq/knowns_unknowns.jsonl` /
   `datasets/selfaware/SelfAware.json`, joined once upstream by
   `amendment_ah_stage0_candidates.py` into the AH A0 pool. This script only
   reads that local file at run time; it does not commit or re-stage it.
4. Writes the full-schema local pool (same shape as the pre-migration
   committed file: `row_key`, `safe_key`, `cell`, `question`, `aliases`,
   `gold_class`, `category_canon`, `source`, and every derived column) to
   `analysis/eval_pool_both_tail.jsonl`.

Run `python materialize_eval_pool.py` after `build_two_signal_directions.py`
and before launching `mechinterp steer` or the smoke run. Requires `HF_TOKEN`
in the environment (see this repo's root `.env` / CLAUDE.md for the redacted
export pattern).

## Reproducibility without re-running the GPU extraction

Anyone with access to the private staging repo can re-derive the exact
question text for every row in `eval_pool_manifest.jsonl` via the fetch+join
above. The fitted directions and derived numeric columns are this
experiment's own output and are fully committed, so the eval pool's
projections/gains/gates are auditable without ever holding a local copy of
the question text in this repo's git history.
