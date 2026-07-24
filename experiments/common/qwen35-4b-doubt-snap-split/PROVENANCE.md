# Qwen3.5-4B Doubt-Snap Held-Out Split

This directory promotes the ID-only split manifest from
`experiments/doubt-snap-cross-family-confirmatory/analysis-committed/qwen35_4b/split_manifest.json`
for reuse by downstream experiments on the `Qwen/Qwen3.5-4B` substrate
(revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`).

Promoted for:

- `experiments/qwen35-4b-family-atlas`

Contents:

- `split_manifest.json`: row keys, roles, and FIT/HELD-OUT/FIT-ONLY
  assignments only (row_key / role / split / source / category_canon).
  sha256 `2f622f5abe110349216207424bdbd919775e93f6d92f334b99f6424505f21e5c`
  (byte-identical to the source committed manifest). Role composition:
  confab 2219 (fit 887, held_out 1332), known_correct_answered 600 (fit 240,
  held_out 360), unknown_refused 181 (fit_only). All three family-atlas roles
  carry row-level IDs.

Containment:

- No question text, aliases, generations, answers, or row-level eval text are
  stored here.
- Runtime materialization must join these IDs against private/local sources
  (the doubt-snap qwen35_4b private pool `split_rows_private.jsonl`, sha256
  `42659f4019d0cbe0178bddd6a7e6323299555092ecd8da4c9ac5d58e42b15a58`, on the
  read-only Modal volume `eh-doubt-snap-cross-family`, prefix
  `doubt-snap-cross-family-r1/qwen35_4b/analysis`) and keep the resulting row
  text under gitignored `analysis/`.

Origin:

- Source experiment: `doubt-snap-cross-family-confirmatory` (cell_id
  `qwen35_4b`)
- Source path:
  `experiments/doubt-snap-cross-family-confirmatory/analysis-committed/qwen35_4b/split_manifest.json`
- Origin amendment verdict: resolved cross-family confirmatory doubt-snap;
  the qwen35_4b cell's mid-band actuation was subsequently established on
  held-out at hs20 (`experiments/qwen35-4b-midband-heldout`). Already reused
  once by `experiments/qwen35-4b-midband-doubt-snap` and
  `experiments/qwen35-4b-midband-heldout` via their `reused_rows_manifest.json`.
