# jlens_corpus_pool.jsonl provenance

1000 question strings (`{"question": "..."}` per line), one field only --
this file carries no answers, gold labels, or other metadata, only the
question text needed to render a prompt for the J-lens corpus average.

**Source**: sampled (seed 20260707, `jlens.build_corpus`) from this repo's own
`experiment/phase1/probe/analysis/ak_stage1/ak_stage1_pool.jsonl` (the AH/AK
Stage-1 commitment-point pool; itself gitignored, built by
`experiment/phase1/probe/amendment_ak_build_pool.py` from the AH stage-0
question pool). Those questions originate from the KUQ (Known-Unknown
Questions) and SelfAware datasets as staged into this repo's
AbstentionBench-adjacent pipeline (see `datasets/abstentionbench-repo/
dataset.md`, license CC-BY-NC-4.0). No answers, no per-row labels or scores
are included here -- this file is question text only, used purely to render
diverse forward-pass contexts for corpus-averaging a Jacobian-vector
product; the pool's own answerable/unanswerable framing is irrelevant to
this experiment's use of it (see NOTEBOOK.md and jlens.py's `load_corpus`
docstring for why this pool was chosen: no clean pre-existing general-
diversity prompt set was found via `bin/search`, and this pool is diverse in
topic across categories -- ambiguous, controversial, unsolved_problem,
future_unknown, false_assumption, counterfactual).

**Why committed here** (unlike the sibling AK/AP/AM amendments, which stage
their pools to a private HF dataset repo for their Modal containers to
fetch): this experiment commits a modest (1000-row, ~90KB) question-only
sample directly under `analysis-committed/` instead, per this experiment's
own binding invariant ("Only-committed-files-in-inputs... put committed
artifacts under analysis-committed/") and to avoid an out-of-scope external
data-staging decision. This keeps the corpus inside this repo's own git
history rather than introducing a new external destination.

**License note**: CC-BY-NC-4.0 (non-commercial). This repo's use is
non-commercial ML safety research; downstream reuse of this specific file
should preserve that constraint.
