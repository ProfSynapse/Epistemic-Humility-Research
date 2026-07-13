# H9 feasibility inventory: propensity reading-gate from cached artifacts

Date: 2026-07-10. CPU-only, read-only inventory. No GPU touched, no commits made.
Canonical checkout: /home/profsynapse/code/Epistemic-Humility-Research (main,
up to date with origin at time of writing).

Purpose: determine whether a registered reading gate for the AL confabulation
-propensity direction can be computed from artifacts already on disk, without
new GPU extraction.

## Verdict

**NO — not computable from cache as a genuine held-out gate, in either
partial or full form.** The frozen direction was, by its own governing
amendment's construction, fit on the FULL 1,662-row surface with no reserved
split. No AI-TRUE-checkpoint extraction exists on disk (in the canonical
checkout or any of the 23 live worktrees under
`/home/profsynapse/code/ehr-worktrees/`) for any row outside that same
1,662-row population. Scoring the frozen direction on any subset of those
1,662 rows would be scoring it on its own fit population, which is exactly
the circularity the reading-gate design is meant to avoid. A genuine
held-out gate requires a new, cheap, local-GPU extraction pass (cost
estimated in Q4 below); it is not a re-analysis task.

## 1. Does the frozen direction artifact exist on disk?

Yes, but as **derived arrays from a script, not as a persisted, portable
scorer object.**

- `experiment/phase1/probe/analysis/amendment_al_prep/amendment_al_run/d_raw.npy`
  — raw-2560-dim unit-norm preimage of the propensity direction, float32,
  shape `(2560,)`. This is the exact object AL AMENDMENT.md section 3.2 calls
  "the raw-2560-dim preimage of the PCA-space propensity direction."
- `experiment/phase1/probe/analysis/amendment_al_prep/amendment_al_run/prop_z.npy`
  — the propensity z-score for each of the 1,662 fit rows, float32, shape
  `(1662,)`.
- `experiment/phase1/probe/analysis/amendment_al_prep/amendment_al_run/caution_z.npy`
  — the caution z-score (used for residualization) for the same 1,662 rows,
  float32, shape `(1662,)`.
- `experiment/phase1/probe/analysis/amendment_al_prep/amendment_al_run/selection_manifest.json`
  — records seed 20260705, layers (propensity L24, caution L35), PCA=128,
  n_splits=5, thresholds, and `readout_quality: {c_oof_auroc_refused: 0.9561,
  prop_incell_oof_auroc: 0.6802}`. This 0.6802 number is the SAME figure the
  provenance census (`docs/review/paper3-direction-provenance-2026-07-10.md`
  section 3) says appears "ONLY in the library term note ... NOT in a
  governed reading-gate amendment" — that caveat is about AL's prose, not
  about this artifact; the number does live in a run artifact this signed
  amendment produced, but it is an **in-sample 5-fold OOF AUROC on the fit
  population**, not a held-out test.
- No hash/checksum of `d_raw.npy` is pinned anywhere I found (AL AMENDMENT.md
  section 3.2 describes the construction in prose; `experiment.yaml` pins
  only the two cloud script files' SHA-256, not any data artifact). So there
  is no pinned-hash check to verify the on-disk `d_raw.npy` against; provenance
  rests on the fact that it is the sole output of the one script that builds
  it (see below), run once, in this directory.

**Critical finding: the underlying scikit-learn fit objects (PCA components,
StandardScaler, the caution-residualization LinearRegression, the caution
OOF LogisticRegression) are NOT saved to disk anywhere.** The generating
script,
`archive/experiment/phase1/probe/amendments/amendment_al_select_and_direction.py`
(read in full), refits `PCA(128, svd_solver="randomized", random_state=20260705)`
and `StandardScaler()` on `X24` (all 1,662 rows) in-memory each run, and never
calls `joblib.dump` or `pickle` on any of them. It persists only the three
`.npy` arrays and the manifest. This means: to score a genuinely new row
against the FROZEN construction (PCA128 -> standardize -> caution-residualize
-> project onto the mean-diff direction -> z-scale by the training
population's mean/std), someone must re-run this exact deterministic
pipeline with the SAME seed and the SAME 1,662-row training matrix (both of
which are on disk — see Q2), then apply the frozen transforms to the new
row's raw L24/L35 vectors. This is a real re-engineering step (the script as
written only ever scores its own training rows), not a blocker, but it is
not "just load a saved model and call `.transform()`." It is CPU-only and
mechanically well-defined given the raw extraction exists.

A second wrinkle: the caution score `c` used for residualization is itself a
**5-fold out-of-fold** logistic decision function on the 1,662 training rows
(`oof_caution()` in the script) — there is no single "final" caution
classifier fit on all 1,662 and frozen. To score a new row's caution value
consistently, a final (non-OOF) caution classifier would need to be fit once
on the full 1,662 and frozen for this purpose; the script does not currently
produce that artifact either.

## 2. Do row-level extraction artifacts exist for the fit surface, and for any held-out rows?

**For the fit surface (all 1,662 rows): yes, complete.**
`experiment/phase1/probe/analysis/amendment_al_prep/true_a0/extract/data/`
contains 1,662 per-row `.safetensors` files (plus `manifest.json` and
`rows.jsonl`; 1,664 files total) named
`<source>__<split>__<row_index>__pre.safetensors`. Verified by direct
inspection of one file
(`ah__kuq_ku_known__000121__pre.safetensors`): each holds **all 37 layers,
L0 through L36, each a single float32 vector of shape (2560,)** — this is the
pre-generation-anchor hidden state (`anchor_position: "prompt_len-1"` per the
manifest), one vector per layer per row, not per-token. Source-split counts
inside the extraction dir (`ahx__kuq_ku_unknown_x` 751, `ah__kuq_ku_unknown`
455, `ah__selfaware_unanswerable` 132, `ah__selfaware_answerable` 117,
`ahx__triviaqa` 79, `ahx__popqa` 77, `ah__kuq_ku_known` 51 = 1,662) match
`experiment/phase1/probe/analysis/ah_stage0/expansion/pool_v21.jsonl` exactly
(same source breakdown, `wc -l` = 1,662), confirming this extraction is
exactly the AL A0 pool and nothing more.

The extract manifest
(`experiment/phase1/probe/analysis/amendment_al_prep/true_a0/extract/data/manifest.json`)
records the checkpoint identity used to produce these activations:
- `base_model`: `.../scratch/schema_response_confidence/runs/sft_schema_clean_seed1_full/20260623_123624/Qwen3-4B-bnb-4bit/merged-16bit` (4-bit load)
- `adapter_repo`: `.../scratch/schema_response_confidence/runs/amendment_ai_grpo_true_seed1/20260703_234933/final_model`
- both paths verified present on disk in this checkout (base model dir has
  `config.json`, `generation_config.json`, etc.; adapter dir has
  `adapter_config.json` + `adapter_model.safetensors`, 264MB).
- `runtime_sec: 164.1` for the full 1,662-row, 37-layer extraction pass
  (batch_size=1, forward-only, no generation).

Class labels (behavior grades) live alongside in
`experiment/phase1/probe/analysis/amendment_al_prep/true_a0/gen/data/rows_graded.jsonl`
and are also carried per-row in
`experiment/phase1/probe/analysis/amendment_al_prep/amendment_al_run/per_row_exhaust.jsonl`
(1,662 lines, one JSON object per row with `row_key`, `gold_class`,
`category_canon`, `prop_z`, `caution_z`, and `baseline.{answered, refused,
correct, confab}`). Class counts, cross-checked against
`amendment_al_run/gates_report.json` and AL AMENDMENT.md section 3.1: **90
correct / 120 wrong / 114 answerable-refused / 1,222 unanswerable-refused /
116 confab = 1,662 total.**

**For held-out rows (rows NOT used in the AL fit): none exist, on this
checkpoint, anywhere I searched.** Specifically:
- `true_a0/extract/data` contains exactly the 1,662 fit rows, no more (file
  count and source breakdown match `pool_v21.jsonl` exactly).
- `permuted_a0/` (the AL control-arm directory) contains a `pool.jsonl` of
  1,662 lines — this is the SAME row pool with a different pushed-row
  selection for the causal control arm, not a disjoint row set.
  `permuted_a0/extract/data/` and `permuted_a0/gen/data/` similarly key off
  the same 1,662 rows.
- `grpo_v2_extract_union/data/` contains 21,820 `.safetensors` files — a much
  larger extraction, but on the **GRPO-v2 checkpoint, not AI-TRUE**. AL
  AMENDMENT.md section 7 states the propensity direction "needs refit per
  checkpoint (reference axes transferred at cosine 0.17)" — i.e. even if this
  union pool's rows were disjoint from the AI-TRUE 1,662, they carry no
  AI-TRUE activations and cannot be scored by the frozen (AI-TRUE-specific)
  direction without a fresh AI-TRUE forward pass.
- `pool_v21_composition.json` (the pool-construction record for Amendment AH,
  which fed AL's A0 pool) records `union_n: 18496` — a much larger candidate
  question pool existed before the 1,662-row AL surface was selected out of
  it via caution-based caliper matching. This confirms a large supply of
  UNUSED candidate QUESTIONS exists (source counts:
  `kuq_ku_unknown_x` 751 used of a larger KUQ pool, etc.), but **none of
  those unused candidate rows have ever been forward-passed through the
  AI-TRUE checkpoint** — they exist only as question text/metadata in the
  wider union pool, not as cached AI-TRUE activations. This is the raw
  material a fresh extraction would draw from (see Q4), not itself a cached
  held-out extraction.
- Searched all 23 live worktrees under `/home/profsynapse/code/ehr-worktrees/`
  for `*amendment_al*` / `*al_true_a0*` artifacts: only tracked `.py` script
  files turn up (identical copies of the AL-prep scripts, present because
  they predate the branch point and are version-controlled, not gitignored
  data). No worktree carries its own `analysis/amendment_al_prep/` data
  directory — that tree is untracked (`git status --short` on it in the main
  checkout returns `?? experiment/phase1/probe/analysis/`), so it exists only
  where it was generated, confirmed to be the main checkout only.
- One terminology red flag, not evidence of held-out data: the GENERATION
  manifest at
  `true_a0/gen/data/manifest.json` has `"surface": "holdout"` while the
  EXTRACT manifest for the identical 1,662 rows has `"surface": "union"`.
  Both report `n_pool: 1662, n_written: 1662`. This script
  (`amendment_ai_verdict_extract_gen.py`) was originally written for a
  different amendment (AI, probe-as-reward) with its own train/holdout split
  vocabulary, and was reused for AL's A0 generation with a fixed default
  argument left over from that context. It is a leftover label, not a second
  row population — row counts, row keys, and file counts all confirm this is
  the same single 1,662-row pool in both directions.

## 3. Can a held-out reading gate be computed CPU-only from what exists?

**No — ingredient (a), a held-out row population, is absent; this fails the
whole question regardless of (b) and (c).**

| ingredient | status | path |
|---|---|---|
| (a) held-out rows disjoint from the AL fit, on the AI-TRUE checkpoint, with class labels | **ABSENT** | none found; see Q2 |
| (b) caution direction for eval-time residualization | **PRESENT but not as a portable scorer** | caution values for the 1,662 fit rows only: `experiment/phase1/probe/analysis/amendment_al_prep/amendment_al_run/caution_z.npy`; the underlying OOF logistic classifier is not persisted (see Q1) |
| (c) normalization/standardization statistics the frozen fit requires (PCA components, StandardScaler mean/scale, caution-regression coefficients, mean-diff direction, z-scale mean/std) | **NOT PERSISTED as objects** | only derived outputs (`d_raw.npy`, `prop_z.npy`) are saved; the fitting script `archive/experiment/phase1/probe/amendments/amendment_al_select_and_direction.py` refits these in-memory each run and never serializes them |

Row counts per class for the ONLY candidate population found (the AL fit
population itself, NOT usable as held-out): 90 correct / 120 wrong / 114
answerable-refused / 1,222 unanswerable-refused / 116 confab (source:
`amendment_al_run/gates_report.json`, cross-checked against
`amendment_al_run/per_row_exhaust.jsonl`, 1,662 lines, and AL AMENDMENT.md
section 3.1). No other class-labeled AI-TRUE population of any size exists
in cache.

Even setting the circularity problem aside for a moment: if one wanted to
compute a reading number on the EXISTING 1,662 rows honestly labeled as
in-sample (not held-out), the closest already-computed number is the 5-fold
OOF AUROC in `selection_manifest.json`: `prop_incell_oof_auroc: 0.6802`
(propensity vs. confab/unanswerable-refused, in-cell) and
`c_oof_auroc_refused: 0.9561` (caution vs. refused). These are cross-validated
within the fit population, which is a weaker guarantee than a disjoint
held-out set (the final frozen `d_raw` direction was fit on ALL 1,662 rows,
not on 4/5 folds), but they are not zero-effort re-scoring of the frozen
object either — they are a different (already-run) OOF procedure.

## 4. Extraction fallback: what a new held-out pass would need

**Checkpoint identity and location (confirmed present on disk):**
- Base: `/home/profsynapse/code/Epistemic-Humility-Research/scratch/schema_response_confidence/runs/sft_schema_clean_seed1_full/20260623_123624/Qwen3-4B-bnb-4bit/merged-16bit` (Qwen3-4B, clean-SFT merged, load_in_4bit)
- Adapter (the "TRUE" GRPO probe-as-reward LoRA): `/home/profsynapse/code/Epistemic-Humility-Research/scratch/schema_response_confidence/runs/amendment_ai_grpo_true_seed1/20260703_234933/final_model` (264MB `adapter_model.safetensors`, `adapter_config.json` present, revision null/local)
- Both confirmed present via direct `ls` in this checkout.

**Prompt surface:** the same baseline system prompt AL used (schema-contract
JSON with `answer` + `response_confidence` keys; full text recorded in
`true_a0/gen/data/manifest.json`), applied to NEW question rows.

**Row source for new held-out rows:** the wider union pool referenced by
`pool_v21_composition.json` (`union_n: 18496`) is the natural candidate
source — it already has question text/metadata for the same source families
(KUQ known/unknown, SelfAware answerable/unanswerable, TriviaQA, PopQA) at
roughly 11x the volume actually used in the 1,662-row AL surface, so a
disjoint held-out sample can very likely be drawn from it without touching
new external data. I did not verify whether the exact non-selected 16,834
rows are individually recoverable as a clean set (the composition JSON
records aggregate stats, matched pairs, and category splits, not necessarily
an explicit "rows NOT selected" list) — that reconciliation is a next step
for whoever designs the held-out draw, not something this inventory resolved.

**Approximate GPU cost, extrapolated from AL's own manifests (same
checkpoint, same hardware class, local RTX 3090):**
- Extraction only (forward pass, all 37 layers, pre-generation anchor,
  batch_size=1): 164.1 sec / 1,662 rows ≈ **0.099 sec/row**. A few hundred
  held-out rows would extract in well under a minute of GPU time.
- Generation + implicit grading pass (greedy, max_new_tokens=96, batch_size=1,
  needed to produce ground-truth behavior labels — correct / confab / refused
  — for the new rows, since the propensity/caution direction's class labels
  depend on graded behavior, not just the question text): 2,802.4 sec / 1,662
  rows ≈ **1.685 sec/row**. For an illustrative 500-row held-out draw: roughly
  50 seconds of extraction + about 14 minutes of generation, i.e. **on the
  order of 15 GPU-minutes total**, not counting CPU-side grading, dataset
  reconciliation, or the re-engineering of the frozen scorer described in Q1.
- This does NOT include the reproduction cost for the frozen PCA/scaler/
  caution-regression pipeline (Q1), which is a one-time CPU coding task, not
  a GPU cost, but is a real prerequisite step with its own risk of subtle
  mismatch versus the original in-memory fit if not done carefully (e.g. must
  reuse the exact same 1,662-row training matrix and seed 20260705 to
  reproduce `d_raw` bit-for-bit before scoring anything new against it).

## 5. What AL's own doc says about the fit population and exclusions

Read directly from `experiments/radial-anti-propensity-steering/AMENDMENT.md`
(full text):

- Section 3.1: "The existing session-0038 TRUE A0 surface is the baseline arm
  (1,662 rows, graded...). No regeneration of the baseline."
- Section 3.2 (propensity score): "fit on the full baseline surface, frozen;
  z-scaled by the baseline distribution." — explicit: the fit uses ALL 1,662
  rows, no split reserved.
- Section 3.2 (caution score c): "L35 logistic on refused-vs-not, fit on the
  full baseline surface, frozen." — same: full-population fit, no split.
- No sentence anywhere in the document mentions a held-out, dual-exclusion,
  or train/test split for the READING fit. The only "exclusion" concept in
  the document is about which QUESTIONS entered the pool at all (section 1 /
  cloud script comments: "KUQ/SelfAware/TriviaQA/PopQA only, no FalseQA" —
  a dataset-family exclusion at pool-construction time, unrelated to
  held-out-for-evaluation discipline).
- Section 7 (interpretive caveats): "Single checkpoint, single seed; a pass
  licenses a mechanism claim on this checkpoint only, with multi-seed
  replication required before any headline." and "The propensity direction
  needs refit per checkpoint... portability is a separate question from
  actuation." Both caveats are about checkpoint/seed generalization, not
  about a within-checkpoint held-out split.

**Conclusion for H9's design:** AL deliberately used the entire available
AI-TRUE A0 pool to fit and freeze the direction, with no held-out discipline
built in at the time (unlike, e.g., Amendment P's cold KUQ-to-SelfAware
transfer design, which is a genuinely disjoint-dataset held-out test — see
`docs/review/paper3-direction-provenance-2026-07-10.md` section 4 for that
contrast). H9 cannot retroactively carve a "held-out" slice out of the
existing 1,662 rows and call it held-out with a straight face, because every
one of those rows already informed the frozen `d_raw` / `prop_z` / z-scale
statistics. Any design that wants a defensible held-out gate for this
direction needs rows the fit never saw, which means new rows, which means the
extraction fallback in Q4.

## One-line answers to the lead's questions

1. Frozen direction artifact exists (`d_raw.npy`, 2560-dim, plus `prop_z.npy`
   / `caution_z.npy` for the 1,662 fit rows) but as raw derived arrays, not a
   persisted scorer; no pinned hash exists to check it against.
2. Row-level AI-TRUE extraction exists for exactly the 1,662 fit rows
   (37 layers, pre-generation anchor, `true_a0/extract/data/`); zero held-out
   AI-TRUE rows exist anywhere on disk, including all 23 live worktrees.
3. Computable CPU-only from cache: **NO.** The one indispensable ingredient
   (a disjoint held-out population) is absent; the fit-population statistics
   needed to score anything are also not persisted as reusable objects
   (would need re-deriving from the pinned script + raw extraction).
4. Extraction fallback: checkpoint present locally at the two paths above;
   candidate held-out questions likely drawable from the 18,496-row union
   pool (`pool_v21_composition.json`) minus the used 1,662, cost on the order
   of ~15 GPU-minutes for a 500-row draw (extraction ~0.1 s/row, generation
   ~1.7 s/row), plus a one-time CPU task to re-derive and freeze the scoring
   pipeline objects that were never persisted.
5. AL's own document states the direction was "fit on the full baseline
   surface" with no held-out split; its only exclusion language concerns
   dataset-family selection at pool-construction time, not held-out
   evaluation discipline.
