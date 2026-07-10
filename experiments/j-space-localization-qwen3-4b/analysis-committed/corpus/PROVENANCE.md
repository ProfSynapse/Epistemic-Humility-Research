# jlens corpus provenance

The 1000-question J-lens corpus is NOT committed to this public repo.
Committing dataset/question text into `Epistemic-Humility-Research` is
forbidden by project norm; this experiment follows the same pattern as the
sibling AK/AP/AM amendments: the question pool is staged privately on the
Hugging Face Hub and fetched at run time, then deterministically re-sampled
into the 1000-row corpus this module operates on.

**Source pool**: `professorsynapse/eh-al-prep-staging`
(`repo_type="dataset"`), file `pools/ak_stage1_pool.jsonl` -- the AH/AK
Stage-1 commitment-point pool (built by
`archive/experiment/phase1/probe/amendments/amendment_ak_build_pool.py` from the AH stage-0
question pool; also fetched from this same staging repo by
`experiments/commitment-point/cloud/modal_ak_stage1.py`). Those questions
originate from the KUQ (Known-Unknown Questions) and SelfAware datasets as
staged into this repo's AbstentionBench-adjacent pipeline (see
`datasets/abstentionbench-repo/dataset.md`, license CC-BY-NC-4.0). Each row
carries a `question` field plus a stable `row_key` identifier; no answers,
gold labels, or scores are used by this experiment.

**Sampling**: `jlens.build_corpus` fetches the pool via
`hf_hub_download(repo_id="professorsynapse/eh-al-prep-staging",
filename="pools/ak_stage1_pool.jsonl", repo_type="dataset")`, keeps every
row with a non-empty `question` field in file order, then applies
`random.Random(20260707).shuffle(rows)` and takes the first 1000. This is
fully deterministic given (source pool, seed, n) -- both a local run and a
Modal container re-derive the identical 1000-row sample from the identical
source, so no corpus file ever needs to travel with the repo.

**Reproducibility manifest**: `jlens_corpus_manifest.json` in this
directory records the seed, n, source repo id/filename, and the ordered
list of the 1000 selected rows' `row_key` identifiers (no question text) --
enough for anyone with access to the private staging repo to verify the
exact sample without this repo ever holding question text. Regenerate it
with the same fetch + `random.Random(20260707).shuffle` procedure described
above if it ever needs re-derivation.

**Why this pool was chosen**: no clean pre-existing general-diversity
prompt set was found via `bin/search`; this pool is diverse in topic across
categories (ambiguous, controversial, unsolved_problem, future_unknown,
false_assumption, counterfactual) and the pool's own answerable/unanswerable
framing is irrelevant to this experiment's use of it purely to render
diverse forward-pass contexts for corpus-averaging a Jacobian-vector
product (see NOTEBOOK.md and jlens.py's `load_corpus`/`build_corpus`
docstrings).

**License note**: CC-BY-NC-4.0 (non-commercial). This repo's use is
non-commercial ML safety research; downstream reuse of the source pool
should preserve that constraint. The staging repo, not this repo, is the
canonical holder of the licensed text.
