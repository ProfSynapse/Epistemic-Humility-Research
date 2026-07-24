# QUALIFY Mode Separability on Base-Model Readout

Status: draft (not signed; do not launch as confirmatory evidence).

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

## Motivation and posture

`fresh-sft-epistemic-mode-token-grpo` (this worktree's governed training cell)
signed a Stage-S SFT to imitate a frozen three-way empirical action policy
(`<ANSWER>`/`<QUALIFY>`/`<ABSTAIN>`) via the model's own first assistant token
(AMENDMENT.md sec 3). The verdict-bearing dev qualification run
(`stage-s-dev-20260723-rerun-f6f1229`) FALSIFIED on two limbs: per-mode recall
collapsed QUALIFY to 0/200 (native policy predicted ABSTAIN 290 / ANSWER 312 /
QUALIFY 0), and answer-quality noninferiority failed (paired StageS-base
correctness -0.239 vs the -0.10 floor), because the checkpoint over-abstains
(AMENDMENT.md sec 10). The outcome section names a *post-hoc, non-binding*
likely mechanism: QUALIFY was only ~8% of training sources (937 of 18,197 train
rows: ABSTAIN 9,556 / ANSWER 7,704 / QUALIFY 937), and proposes that "a
successor design should address class balance and pre-test QUALIFY's
in-representation separability before any retrain" (AMENDMENT.md sec 10,
final sentence).

This experiment is that pre-test. It does not retrain anything. It asks a
narrower, answerable-now question: **is the QUALIFY signal present in the base
model's own pre-generation representation at all**, in a form a class-balanced
retrain could plausibly exploit? Two outcomes are both informative and neither
is assumed:

- If QUALIFY reads out at a certifiable level under a readout that can express
  a *band* (not a naive one-vs-rest linear split), that is evidence the void is
  a training-data-imbalance artifact, and a class-balanced retrain is worth
  trying.
- If QUALIFY does not read out under any of the readouts tried here, that is
  evidence the category itself is not (linearly/banded-linearly) encoded at
  these depths, and a class-balanced retrain alone would not be expected to fix
  it -- a different mechanism (e.g. QUALIFY genuinely straddles ABSTAIN/ANSWER
  in representation space, not just in label frequency) would need to be
  investigated before any retrain.

This is Tier-2/lab-diagnostic exploratory evidence for a single model, single
seed, single fit population. It does not reopen or re-adjudicate the Stage-S
falsifier (`fresh-sft-epistemic-mode-token-grpo/AMENDMENT.md` sec 7/10), which
stands as recorded.

## Design

### Why a naive linear probe would understate the signal

The three-way rule is an ORDINAL BAND over `k` (correct count out of 32 probe
samples), not two independent thresholds: ABSTAIN `k<=10`, QUALIFY
`11<=k<=21`, ANSWER `k>=22` (and greedy-correct)
(`fresh-sft-epistemic-mode-token-grpo/AMENDMENT.md` sec 3.1;
`fresh-sft-epistemic-mode-token-grpo/dataset_builder.yaml` labeling block). If
`k` were perfectly linearly encoded in the hidden state (i.e. some direction
`w` satisfies `hidden . w ~ k`), QUALIFY still would NOT be one-vs-rest
linearly separable: it occupies the *middle* of that linear axis, so no single
hyperplane separates it from {ABSTAIN, ANSWER} on both sides at once. A naive
linear QUALIFY-vs-rest probe would report a weak or null AUROC in exactly this
case, even though the underlying signal is present and strong. This design
therefore reads out with model classes that CAN express a band, and reports
the naive one-vs-rest probe only as a comparison floor to make this
failure mode visible, not as the primary claim.

### Substrate (verified at design time, not assumed)

- Model: `unsloth/Qwen3-4B-bnb-4bit` @ `cad0bedfdd862093a12af478cb974ab2addd0e0a`
  -- the exact Stage-S starting checkpoint (sec 2 of the target AMENDMENT).
  Verified by direct load test: this exact bnb-4bit revision loads on CPU via
  transformers' generic bitsandbytes dequantization path (no CUDA
  `gemm_4bit_forward` kernel available on this host; falls back to a torch
  dequant forward -- confirmed functionally correct by inspecting
  `output_hidden_states` shapes and a rendered-prompt smoke). **No substrate
  substitution was needed** -- the diagnostic uses the literal checkpoint the
  Stage-S SFT started from, not a dequantized sibling or a different revision.
- `model.config.num_hidden_layers == 36`, `len(hidden_states) == 37`
  (embedding output + 36 blocks), `hidden_size == 2560`. Matches the family
  atlas's plain (non-4bit) `unsloth/Qwen3-4B` sibling capture
  (`docs/atlas/family-layer-map.md`: 36 layers, hidden_size not stated there
  but architecture-identical), consistent with this being the same base
  architecture at a different quantization/repo.
- CPU only, hard requirement (the 3090 is occupied by a signed experiment).
  `CUDA_VISIBLE_DEVICES=""` is set before any torch/transformers import in
  every script entry point; `cell.yaml` records `compute.cuda_forbidden: true`
  as a design-time assertion even though `torch.cuda.is_available()` is `True`
  on this host (nothing is loaded onto it).
- Render: `[system, user]` turns of each row's `conversations`, rendered with
  `tokenizer.apply_chat_template(..., add_generation_prompt=True,
  enable_thinking=False)` -- the same render convention as the target
  experiment's dev qualification runner (`qualify_stage_s.py` line ~307-311,
  `config["generation"]["enable_thinking"]` pinned `false` in
  `qualification.yaml`). Verified by inspecting the rendered prompt tail: it
  includes the closed `<think>\n\n</think>\n\n` block Qwen3's template emits
  when thinking is disabled.
- Extraction anchor: the LAST TOKEN of the rendered prompt (pre-generation),
  i.e. the position immediately before the model would emit the mode token.
  Four depths at 25/50/75/95% of the 36 blocks: hidden_states indices
  `[9, 18, 27, 34]` (`round(fraction * 36)`, computed once at design time and
  pinned in `cell.yaml`, not re-derived per run).

### Data (train/dev only; held-out sealed)

Reuses the exact frozen split artifacts of the target experiment, verified
byte-identical by sha256 at design time:

| file | sha256 (first 12) | rows |
|---|---|---|
| `train.jsonl` | `da473bc05e54` | 18,197 |
| `dev.jsonl` | `dcff3134f22c` | 602 |
| `heldout.jsonl` | `495a908ffd0d` | 1,201 (NEVER opened by this experiment) |

Row schema: `metadata.mode_label` (ground-truth ABSTAIN/QUALIFY/ANSWER),
`metadata.correct_count` (`k`, 0..32, already computed by the frozen probe --
no rederivation from the probe cache needed), `metadata.row_key` (resume key).

**Fit population** (train split only): all 937 QUALIFY rows + a fixed-seed
(20260723), no-replacement matched draw of 937 ABSTAIN and 937 ANSWER rows =
2,811 rows, exactly class-balanced by construction. This population is shared
across all three readouts (a/b/c below) so they are directly comparable.

**Eval population**: the full 602-row dev split (natural 200 ABSTAIN / 200
QUALIFY / 202 ANSWER imbalance, no sampling) -- never touched during fitting.

The 1,201-row held-out split is not referenced by path anywhere in `cell.yaml`
or either script; `extract_hidden_states.py` additionally hard-guards by
refusing to run if any resolved input path contains the substring `heldout`.

### Three readouts, each at each of the four depths, on PCA-128 + standardized features

Preprocessing (shared): PCA to 128 components (randomized solver,
`random_state=20260705`, the AL/H9/BB recipe-parity convention from
`radial-anti-propensity-steering/AMENDMENT.md` sec 3.2), fit on the 2,811-row
fit population only, then standardize (zero-mean/unit-variance, fit on the
same population). This keeps the feature/sample ratio sane (2,811 rows vs.
2,560 raw dims) and reuses the program's established fit recipe rather than
inventing a new one.

1. **(a) Linear k-regression** (Ridge, `alpha=10.0`, fixed not tuned): target
   is `correct_count` (`k`, continuous 0..32). Reports on dev: Spearman and
   Pearson correlation of predicted vs. true `k`; a banded-classification
   accuracy/confusion matrix from thresholding predicted `k` at the registered
   10/21 boundaries; and a **QUALIFY-vs-rest AUROC using
   `score = -|predicted_k - 16|`** (distance from the band center -- higher
   score means more QUALIFY-like), which is the natural way to get an honest
   AUROC out of a continuous, non-monotonic-in-QUALIFY score. Parallel
   ABSTAIN-vs-rest (`score=-predicted_k`) and ANSWER-vs-rest
   (`score=predicted_k`) AUROCs are reported for context (monotonic, so a
   plain one-vs-rest AUROC is valid for those two).
   - *Known, flagged approximation*: the registered rule's small carve-out
     (53 `k>=22`-but-greedy-wrong rows routed to QUALIFY instead of ANSWER,
     program-wide) is not modeled by a `k`-only threshold. This diagnostic
     tests whether the dominant `k`-band structure is recoverable, not an
     exact reproduction of the full three-way rule.
2. **(b) Direct 3-way multinomial-logistic readout** (`sklearn
   LogisticRegression`, `lbfgs`, no `multi_class` kwarg -- current sklearn
   fits a true softmax/multinomial model automatically for a >2-class target,
   which is exactly the model class the lead's design note asked for: it can
   express a band via the two decision boundaries around QUALIFY, unlike a
   one-vs-rest linear split). Target is the categorical `mode_label` directly
   (not derived from `k`). Reports the predicted `P(QUALIFY)` AUROC vs. rest,
   plus overall 3-way accuracy/confusion/per-mode recall-precision on dev.
3. **(c) Naive linear QUALIFY-vs-rest floor** (`sklearn LogisticRegression`,
   `class_weight="balanced"` since this relabeling is 937 QUALIFY vs. 1,874
   rest, a 2x imbalance unlike (a)/(b)'s exact 3-way balance): a plain binary
   classifier trained directly to separate QUALIFY from everything else.
   Reported for comparison only -- this is the metric a naive experimenter
   would compute, and is expected (not assumed) to underperform (a)/(b) if the
   band-separability premise above holds.

Every AUROC carries a 1,000-resample percentile bootstrap 95% CI over the
602-row dev population (`bootstrap_seed=20260723`), the same construction BB
used (`bb-base-propensity-fit-read/gates.yaml` `reading_gate`).

### Determinism / mechanical checks

A BB-FID-1-style determinism check (`bb-base-propensity-fit-read/gates.yaml`)
at the single best-performing depth: refit the Ridge k-regression twice on
identical inputs, require coefficient cosine similarity `>=0.999999` and
max-abs elementwise diff `<=1e-5`. Plus mechanical guards: 100% of the
fit+eval population must have all four depths extracted before fitting;
predicted-`k` standard deviation on dev must exceed a trivial floor (a
regression that collapsed to a constant is a pipeline failure, not a null
result); no NaN/Inf anywhere in features or predictions.

### Compute plan and measured throughput (20-row smoke, pre-sign, authorized)

Measured directly with the actual `extract_hidden_states.py` script (not a
throwaway snippet), CPU-only, this host (16 cores, `avx512_bf16`+`avx512f`,
19GB RAM):

- Model+tokenizer load: 7.4s.
- 20-row forward pass (single-row batches, `output_hidden_states=True`, all
  four depths extracted from the same forward pass): 17.4s total, **0.872
  s/row**.
- Extraction is resumable: verified by a dedicated unit test
  (`test_resumable_writer_round_trip_and_resume`) that a fresh
  `ResumableFeatureWriter` instance correctly detects already-written
  `row_key`s from the on-disk index and skips them, and that features
  written across two separate writer instances land in the same
  fixed-record-length binary shard in append order.

Projected full run: `(2,811 fit + 602 dev) = 3,413` rows total, at
0.872 s/row + model load, **~50 minutes wall clock**, comfortably inside a
single sitting. `fit_readouts.py` (PCA + three model fits + 3x1,000-resample
bootstrap, all four depths, on realistic-shaped `2811x2560`/`602x2560`
synthetic data at the real dimensionality) measured **~19s total for the
4-depth loop**, well under the 15-minute short-run persistence threshold
(declared `measured_smoke_wall_clock_s: 30.0` in `experiment.yaml` with
headroom).

`fit_depth`'s full statistics pipeline (Ridge regression, multinomial
logistic, naive floor, all three bootstrap CIs) was validated end-to-end on
synthetic data of the real dimensionality and confirmed to run without error
against the installed `sklearn 1.8.0`/`scipy 1.14.1` (the `multi_class` kwarg
to `LogisticRegression` was removed upstream since this program's other
readout scripts were written; fixed here to rely on `lbfgs`'s automatic
multinomial fit for a >2-class target, noted inline in the script).
`fit_readouts.py`'s outer `run()` assembly (index/feature loading, per-depth
loop, primary-gate/report assembly) was NOT exercised end-to-end pre-sign --
doing so honestly requires either the full 3,413-row extraction or a bespoke
synthetic harness reproducing the exact `cell.yaml` row counts; this is a
known, low-risk gap (all its constituent functions are individually
validated) surfaced here rather than silently assumed clean.

### Reused machinery / deviations from "reuse, don't reinvent"

- Reused: the AL/H9/BB PCA-128 + standardize fit recipe convention, the BB
  bootstrap-CI construction and PASS/FAIL/INCONCLUSIVE AUROC bar (see Gates),
  the BB-FID-1 determinism-check shape, and the dataset builder's own `k`/
  `mode_label` fields (no rederivation from the raw probe cache).
- NOT reused: `shared/utilities/run_log.py` (`RunLog`), the project's
  canonical incremental-writer, per
  `experiments/common/README-runlog.md`. That module lives on the tuner
  branch `feature/runlog`, not on `main`; this worktree's submodule pointer
  (`86b134c...`) does not have it, and a `git submodule update --init` in
  this environment timed out after 2 minutes (network-blocked or
  auth-gated, not investigated further since the diagnostic has no other
  tuner dependency). `extract_hidden_states.py` instead implements a minimal,
  purpose-built equivalent (`ResumableFeatureWriter`): an append-only
  fixed-record-length binary shard plus a companion append-only JSONL index,
  resumed by reading the index for already-done `row_key`s. This is a
  deliberate, narrow substitute for an unavailable shared component, not a
  silent reinvention of a larger system -- flagged here for the record.

## Prediction

Copied to `prediction:` in `experiment.yaml`. The QUALIFY band is
substantially recoverable from base-model hidden states under a band-aware
readout (banded k-regression and/or direct multinomial 3-way readout clear
the primary PASS bar -- AUROC>=0.62 with bootstrap CI lower>0.55 -- at at
least one of the four measured depths), while the naive linear
QUALIFY-vs-rest floor underperforms both band-aware readouts by a nontrivial
margin. This would support a retrain-worth-trying verdict and would confirm
the class-imbalance-during-training mechanism the target AMENDMENT's outcome
section flagged as *post-hoc, non-binding* (sec 10), rather than a
fundamentally unencoded category.

## Falsifier

Copied to `falsifier:` in `experiment.yaml`. If BOTH the banded k-regression
QUALIFY-vs-rest AUROC and the direct multinomial 3-way QUALIFY-vs-rest AUROC
fail the PASS bar at every one of the four measured depths (point
AUROC<=0.55 OR bootstrap 95% CI upper<0.60), that falsifies recoverability
under this instrument: a class-balanced retrain would not be expected to fix
the QUALIFY-void by this evidence, and the category should be treated as not
(linearly/banded-linearly) encoded in the base model's representation at
these depths.

## Gates

Full pre-stated thresholds and their provenance live in `gates.yaml`
(LOCKS at signing). Summary:

- **Primary gate** (gates the retrain-vs-not decision): QUALIFY-vs-rest AUROC
  from readout (a), `max` over the four depths (not multiplicity-corrected --
  exploratory lab-diagnostic, not a locked headline claim). PASS
  `AUROC>=0.62 AND CI_lower>0.55`; FAIL `AUROC<=0.55 OR CI_upper<0.60`;
  otherwise INCONCLUSIVE. These exact numbers are copied verbatim from the
  program's only prior precedent for "does this base-model readout clear a
  useful, certifiable level" (`bb-base-propensity-fit-read/gates.yaml`
  `reading_gate`, itself derived from AL/H9's readout-quality contrast bar) --
  not re-derived or rounded to a new convenient value.
- **Secondary** (reported, non-gating): readout (b)'s QUALIFY-vs-rest AUROC,
  max over depths; flagged if it diverges from the primary's best value by
  more than 0.07 AUROC (the width of the PASS/FAIL band itself) without being
  silently resolved either way.
- **Naive floor** (reported, non-gating): readout (c)'s QUALIFY-vs-rest AUROC,
  max over depths; the gap `primary - floor` is reported descriptively as the
  direct demonstration of the band-separability premise.
- **Mechanical/fidelity preconditions**: 100% extraction completeness on the
  fit+eval populations; predicted-k dev SD above a trivial floor; no NaN/Inf;
  BB-FID-1-style determinism (cosine`>=0.999999`, maxabs`<=1e-5`) at the
  best-performing depth.

**Flagged for lead adjudication before signing** (mirrors BB's flagged-UNCERTAIN
convention, `bb-base-propensity-fit-read/AMENDMENT.md` sec 10):

1. **Depth selection = max over 4 depths.** This is the standard way this
   program has handled depth uncertainty in prior lab diagnostics (report the
   full profile; e.g. `family-atlas-surface-diversity-control`,
   `j-space-localization-qwen3-4b`), but taking the max over four correlated
   depths for a PASS/FAIL decision does inflate the apparent significance
   slightly versus a single pre-specified depth. Alternative: pre-commit to a
   single depth (e.g. the 75% depth, closest to the family atlas's qwen3-4b
   readable band 61-100% depth, `docs/atlas/family-layer-map.md`) as primary
   and report the other three descriptively only. Proposed default: keep
   max-over-4 (matches program convention for this experiment tier); flagged
   for override.
2. **Primary readout choice = (a) banded k-regression, not (b) multinomial.**
   (a) is the most information-complete readout (ordinal, not just a 3-way
   split) and most directly tests the lead's framing ("is k well encoded").
   (b) is reported as a confirmatory cross-check with a divergence flag rather
   than folded into the primary metric (avoids a max-of-two-readouts
   selection-bias risk). Flagged for override if the lead prefers (b) primary,
   or a combined metric.
3. **AUROC bar reused verbatim from BB, not re-derived for this question.**
   BB's bar answers "does this direction read at a useful, certifiable
   level" for a very different construction (a frozen mean-diff propensity
   direction, not a regularized regression/classifier on PCA features). Using
   the same numeric bar is a **borrowed anchor for cross-experiment
   comparability**, not a claim the two readouts have matched statistical
   power. Flagged for override if the lead wants a bar derived from this
   design's own honest prior instead (e.g. in-cell OOF AUROC on the fit
   population, BB Choice-B style) -- not measured here since it was not
   requested pre-sign.
4. **Ridge alpha=10.0 fixed, not tuned.** No cross-validation sweep was run
   (the lead's brief explicitly forbids tuning to pass a gate). This is a
   single reasonable default for 2,811 rows / 128 PCA components, not
   selected by performance. Flagged only for visibility, not proposed as a
   knob to change.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator (harness-builder subagent) | Primary gate PASSES at at least one depth (best guess: 75% or 95% depth, following the cross-family pattern that epistemic axes read out best in the post-dimensionality-peak interior/late band, `docs/atlas/family-layer-map.md` "Cross-family pattern" sec) but the point estimate sits closer to the PASS floor (0.62-0.70) than to ceiling, given QUALIFY is a genuinely narrow band (11 of 33 possible k values) built from a small, class-imbalanced training source. The naive floor (c) underperforms the primary by a visible but not enormous margin (a partial, not total, vindication of the band-separability premise). |
| user | (record at sign-off) |

## Outcome

Resolved 2026-07-23. Extraction 3,413/3,413 rows (2,811 balanced fit /
602 dev), one designed resume event (the 20 pre-sign smoke rows skipped via
the index), fit_readouts ran on the signed pinned bytes with zero
post-sign changes. Determinism check exact (cosine 1.0, maxabs 0.0).
Held-out never opened. Full aggregates:
`analysis-committed/fit_report.json`.

**PRIMARY GATE: INCONCLUSIVE** by the pre-registered bands. Best depth
hs27 (75%): banded k-regression QUALIFY-vs-rest AUROC 0.5690, 95% CI
[0.5228, 0.6138] — the point sits between the FAIL ceiling (0.55) and
the PASS floor (0.62), and the CI straddles both lines. Falsifier NOT
fired: the confirmatory multinomial readout reaches 0.6171 [0.5662,
0.6642] at hs27, above the FAIL band, so "both band-capable readouts
fail at all depths" is false.

Per-depth (a) banded k-regression QUALIFY AUROC: 0.5447 / 0.5576 /
0.5690 / 0.5388 at hs9/18/27/34. Linear k readout: Spearman 0.300 ->
0.443 rising with depth (all p < 1e-13). Context: the scale ENDS read
substantially better than the middle at every depth (ABSTAIN-vs-rest up
to 0.716, ANSWER-vs-rest up to 0.758, vs QUALIFY's 0.54-0.62 band).

**Pre-registered premise check, reported straight:** the naive linear
floor (c) was NOT meaningfully below the band-capable readouts —
at best depths the ordering is (b) 0.6171 > (c) 0.5897 > (a) 0.5690.
The design's motivating hypothesis (QUALIFY under-separates naively
because a well-encoded k makes the middle band linearly inseparable)
is not supported: k itself is only moderately encoded (r ~0.44), and
the middle band is weak under every readout class. The banded
classifier over-predicts QUALIFY broadly (recall 0.64-0.74, precision
~0.36): the representation supports a fuzzy graded capability signal,
not a crisp middle category.

**Scoreboard adjudication:** the drafting subagent's call (primary
PASSES at >=1 depth, naive floor visibly underperforms) MISSED on both
limbs — the primary landed in the inconclusive band and the floor did
not underperform. No user call was recorded at sign (sign happened in
the same session hours after the draft; the omission is procedural,
noted here rather than backfilled).

**Reading for the successor decision (non-binding):** neither the
clean "retrain justified" nor "category not encoded" answer obtained.
The evidence pattern — graded k signal real but weak in the middle,
crisp band absent — favors an ordinal-aware redesign of the QUALIFY
supervision (or a 2-way policy plus the already-working confidence
scalar) over a plain class-rebalanced retrain of the same discrete
3-way rule.
