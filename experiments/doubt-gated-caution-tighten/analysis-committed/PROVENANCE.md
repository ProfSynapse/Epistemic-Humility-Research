# doubt-gated-caution-tighten: analysis-committed/ provenance

This repo is PUBLIC. Dataset/pool/question-text/eval-row text is never
committed (see `.skills/pr-workflow/SKILL.md` "Datasets are never
committed"). This scheme is ported from the sibling
`two-signal-caution-regulation-instruct` experiment's own containment
migration (worktree `/home/profsynapse/code/ehr-worktrees/two-signal`,
`analysis-committed/PROVENANCE.md`, itself mirroring the
`j-space-localization-qwen3-4b` migration, commit `88c98cdc`).

## What is committed here

- `split_manifest.json` -- 739 rows (309 confab + 430 known_correct_answered),
  ID + SPLIT ONLY: `row_key`, `role`, `split` ("fit" | "held_out"). No
  `question`, no `aliases`, no `category_canon` (category is looked up from
  the extraction manifest, itself gitignored, at run time). Written by
  `split_fit_heldout.py`.
- `u_d_L34.json` -- doubt-axis direction, fit on the FIT split only.
- `c_hat_L34.json` -- caution write direction (2-D orthogonalized against
  u_d + neg_ctrl), fit on the FIT split only.
- `source_directions/pos_ctrl_L34.json`, `source_directions/neg_ctrl_L34.json`
  -- raw caution/propensity directions feeding c_hat's orthogonalization,
  fit on the FIT split only.
- `random_direction_L34.json` -- fixed-seed random unit direction for the
  G3(i) specificity placebo (not fit from data).
- `build_manifest.json` -- direction-fit report: FIT population counts,
  cosines, mu/sigma (standardization stats used by both the gate and the
  snap), reproducibility-check status.
- `gate_fit.json` -- tau (Youden-J, frozen) + AUC, fit on the FIT split only.
- `full_summary.json` -- aggregate confirmatory gate summary only: per-arm
  denominators, success counts, rates, and Wilson intervals. No row text.
- `baseline_noop_summary.json` -- aggregate no-op baseline summary used to
  adjudicate G3(i)'s random-direction-vs-no-op comparison. No row text.
- `PROVENANCE.md` -- this file.

All of the above are this experiment's OWN fitted/derived output (numeric
vectors, thresholds, counts) -- never source question text or aliases.

## How the local HELD-OUT row pool is materialized (never committed)

`pipeline.py` reads `analysis/rows_with_text.jsonl` (LOCAL, GITIGNORED --
`analysis/` is blanket-ignored by this experiment's `.gitignore`), produced
by `materialize_rows.py`, which:

1. Reads the committed `split_manifest.json` (row_key/role/split, no text).
2. Fetches question text via `hf_hub_download(repo_id=
   "professorsynapse/eh-al-prep-staging",
   filename="pools/a0_pool_v21_questions.jsonl", repo_type="dataset")` and
   joins by `row_key`. Verified (this experiment's own build) to cover the
   original AH A0 rows this experiment uses (known_correct_answered 89/89,
   confab 309/309).
3. Joins `aliases` (gold-answer text, needed to grade known_correct_answered
   rows' correctness after a false-positive dose) from the LOCAL
   canonical-checkout
   `archive/experiment/phase1/probe/analysis/ah_main/gen_A0/rows.jsonl` (gitignored,
   never committed or re-staged). Aliases originate from this repo's own
   already-committed `datasets/kuq/knowns_unknowns.jsonl` /
   `datasets/selfaware/SelfAware.json`; this script only reads them locally.
4. Joins the 341 newly mined known_correct_answered rows from local
   gitignored scratch
   `experiments/doubt-gated-caution-tighten/analysis/mined_a0_known_correct_rows.jsonl`;
   this file carries question text and aliases and is therefore never
   committed. It was produced pre-sign by `mine_known_correct.py` on
   `unsloth/Qwen3-4B` bf16 raw-base using the AH-A0 render surface, scanning
   1,113 TriviaQA-first answerable candidates and filtering to
   `answered=True, correct=True`.
5. Writes the full-schema local pool (row_key, role, split, category_canon,
   question, aliases) to `analysis/rows_with_text.jsonl`.
6. HARD-FAILS (nonzero exit) if any row is missing question text or if any
   known_correct_answered row has empty aliases -- a missing/broken
   canonical pool must not silently produce a vacuous G2 null (same
   discipline the sibling two-signal experiment adopted after a red-team
   finding). Post-mining materialization verified missing_question=0 and
   missing_alias_on_known_correct_answered=0 over all 739 split rows.

Run `python materialize_rows.py` (with `HF_TOKEN` set) after
`split_fit_heldout.py` and before `pipeline.py`.

## Reproducibility without re-running the GPU extraction

Anyone with access to the private staging repo can re-derive the exact
question text for every row in `split_manifest.json` via the fetch+join
above. The fitted directions, the split assignment, and the frozen gate
threshold are this experiment's own output and are fully committed, so the
gate/snap decision for every row is auditable without ever holding a local
copy of the question text in this repo's git history.

## Direction re-fit reproducibility

`build_directions.py --verify-reproducible` fits u_d/pos_ctrl/neg_ctrl/c_hat
TWICE (independent calls into the same fitting code, same FIT-split
activations) and asserts the four vectors are byte-identical before writing
anything, closing the defect confirmed in the sibling two-signal build
(`LogisticRegression(solver="saga", ...)` with no `random_state`, so
neg_ctrl/c_hat were not reproducible run-to-run). `RANDOM_STATE = 20260707`
is pinned at the top of `build_directions.py`.
