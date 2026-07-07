# Doubt-Gated Caution Tighten Held-Out Split

This directory promotes the ID-only split manifest from
`experiments/doubt-gated-caution-tighten/analysis-committed/split_manifest.json`
for reuse by downstream experiments.

Promoted for:

- `experiments/j-space-midband-write-sweep-qwen3-4b`

Contents:

- `split_manifest.json`: row keys, roles, and FIT/HELD-OUT assignments only.

Containment:

- No question text, aliases, generations, answers, or row-level eval text are
  stored here.
- Runtime materialization must join these IDs against private/local sources and
  keep the resulting row text under gitignored `analysis/`.

Origin:

- Source experiment: `doubt-gated-caution-tighten`
- Source path:
  `experiments/doubt-gated-caution-tighten/analysis-committed/split_manifest.json`
- Origin amendment verdict: exploratory pass on bf16 raw-base Qwen3-4B, with
  selectivity supplied by the doubt gate rather than by a selective write.
