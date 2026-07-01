---
title: 'Two-signal trust readout (answerability gate + correctness dial + hallucination veto)'
kg:
  id: experiment:two-signal-readout
  type: experiment
  status: canonical
tags:
  - kg/experiment
status: running
governance: exploratory
phase: phase1
lane: local
est_compute: '~1-3 GPU-hours per model on one RTX 3090 (one mixed-pool extraction pass each); CPU scoring is minutes'
relationships:
  - type: tests
    target: '[[answerability-and-correctness-are-orthogonal-readout-axes]]'
    target_id: mechanism:answerability-and-correctness-are-orthogonal-readout-axes
    confidence: high
  - type: tests
    target: '[[task-training-sharpens-not-creates-hallucination-veto]]'
    target_id: mechanism:task-training-sharpens-not-creates-hallucination-veto
    confidence: high
  - type: tests
    target: '[[per-answer-correctness-linearly-readable-post-generation]]'
    target_id: mechanism:per-answer-correctness-linearly-readable-post-generation
    confidence: high
  - type: tests
    target: '[[answerability-axis-present-without-task-training]]'
    target_id: mechanism:answerability-axis-present-without-task-training
    confidence: high
  - type: builds_on
    target: '[[internal-twosignal-readout--training-free]]'
    target_id: paper:internal-twosignal
    confidence: high
  - type: builds_on
    target: '[[internal-paper3--knows-but-doesnt-say]]'
    target_id: paper:internal-paper3
    confidence: high
related:
  - '[[answerability-and-correctness-are-orthogonal-readout-axes]]'
  - '[[task-training-sharpens-not-creates-hallucination-veto]]'
  - '[[per-answer-correctness-linearly-readable-post-generation]]'
  - '[[answerability-axis-present-without-task-training]]'
  - '[[internal-twosignal-readout--training-free]]'
  - '[[internal-paper3--knows-but-doesnt-say]]'
---

## Question & Hypothesis

**RQ.** Can a small LM emit a surfaced, thresholdable trust signal that tracks whether
*this specific answer* is correct, without task training to install it?

**Hypothesis.** Epistemic state is largely a READOUT of internal representation, not a
training outcome. Two orthogonal linearly-decodable axes compose into a deployable
two-stage trust pipeline:
- **gate** = answerability, read at the prompt anchor (last prompt token), abstain if
  below threshold;
- **dial** = per-answer correctness, read at the post-generation content token, surfaced
  as the trust number;
- **veto** = the dial assigns confident confabulation the lowest trust.

**Falsifier(s).** Per amendment (pre-stated in each protocol doc). Family-level: if the
correctness signal were only readable AFTER training, or if the gate and dial were the
same axis (so fusing helps), or if it failed to replicate off Qwen3-4B, the "training-free
orthogonal readout" framing would be wrong. Governance is exploratory (non-headline);
each cell is a signed Amendment under `experiment/protocol/` referencing the locked
PROTOCOL surface, never pooled with the headline matrix.

## Design

A family of single-model, single-seed probe cells, each a signed Amendment:

| cell | checkpoint | what it establishes | headline metric |
|------|------------|--------------------|-----------------|
| **S** | Qwen3-4B Instruct base | correctness readable post-gen; post beats pre | AUROC 0.834 (L20), +0.065 self-eval |
| **T** | clean-SFT -> GRPO-v2 (deployed) | S readout survives on the deployed checkpoint | AUROC 0.819 (L22); cold-transfer 0.679 |
| **U** | clean-SFT -> GRPO-v2 | the dial vetoes confident hallucinations | veto AUROC 0.980; control 0.93 |
| **Stage 1.5** | (per-item CPU) | gate and dial are orthogonal; fusion HURTS | fusion delta -0.014 |
| **W** | RAW Qwen3-4B base (no adapter) | the WHOLE mechanism is training-free | gate 0.997 / dial 0.834 / veto 0.754 |
| **X** | RAW Qwen3 1.7B/8B/14B | size-generalization of the training-free readout | per-model X-G1/G2/G3 >=0.65 |

**Probe recipe (shared).** StandardScaler + LogisticRegression(C=1.0, max_iter=2000);
5-fold stratified out-of-fold for honest reference scores; full-fit dial applied COLD to
external groups; AUROC via roc_auc_score with a 2000-sample bootstrap CI. Dual-position
extraction: ONE forward over [prompt+answer], pre-gen = last prompt token (gate read),
post-gen = last answer content token (dial read). Greedy decode (deterministic).

**Datasets.** PopQA + TriviaQA (answerable, graded vs gold aliases -> correct/wrong);
SelfAware (intrinsic answerable/unanswerable -> known/unknown gate + unknown-answered =
hallucination). Models pinned per cell (raw `unsloth/Qwen3-*-bnb-4bit` for the
training-free cells).

## Prerequisites & Gating

- Datasets present under `datasets/` (popqa, triviaqa-rc-nocontext, selfaware).
- Frozen SelfAware known/unknown pool from a prior gate extraction
  (`experiment/phase1/probe/qwen3-4b-clean-sft-grpo-v2-seed1-selfaware/`).
- Single RTX 3090 free (no parallel GPU cells); free any resident LM Studio model first.
- **Data-adequacy precondition (per model, before scoring):** >=30 wrong AND >=50
  hallucinations; the scorer returns DATA_STAGE_STOP below floor (not a probe verdict).
- Launch/cancel requires explicit user approval naming the exact models/lane.

## Runbook

1. **Sign the Amendment** under `experiment/protocol/` (prediction + falsifier + locked
   gates) before any run.
2. **Extract (GPU, per model).** Training-free cells use the raw-base extractors:
   `experiment/phase1/probe/amendment_w_base_model_extract.py` (4B SelfAware surface) and
   `experiment/phase1/probe/amendment_x_cross_model_extract.py` (cross-size mixed pool,
   `--base-model`). The dial source surface is
   `experiment/phase1/probe/amendment_s_correctness_probe_extract.py`. Run detached in
   Docker with `--entrypoint python`; output dirs need world-write (chmod 777).
3. **Score (CPU, per model).** `experiment/phase1/probe/amendment_x_cross_model_score.py`
   (X), `experiment/phase1/probe/amendment_w_base_model_score.py` (W),
   `experiment/phase1/probe/amendment_u_two_signal_score.py` (U/dial+veto),
   `experiment/phase1/probe/amendment_s_correctness_probe_score.py` (S dial). Write to
   `--out` directly, then read the JSON (do not pipe the scorer into an inline reader -
   known race).
4. **Document.** Write the §7 verdict in the Amendment doc; copy the result JSON to the
   probe root as `amendment_*_result.json` (model_tag subtrees are gitignored); add a
   checkpoint to the active `docs/sessions/` note.

## Validation contract

- **Pre-run:** datasets + frozen pool resolve; model resolvable in cache/hub.
- **Post-run:** per model `rows.jsonl` + per-row `{pre,post}.safetensors` + `manifest.json`
  exist; adequacy floor met (else DATA_STAGE_STOP, reported as a data finding).
- **Definition of done (per cell):** the locked gates have a recorded verdict with
  bootstrap CIs, no goalpost moved; the cross-size SUCCESS/PARTIAL/FALSIFIER roll-up is
  assembled in `experiment/protocol/AMENDMENT-X-cross-model-size-sweep.md` §7.

## Outputs & provenance

- Per-cell result JSONs at the probe root (`experiment/phase1/probe/amendment_*_result.json`);
  tensor/rows artifacts stay local under gitignored `qwen3-*/` model_tag subtrees.
- Episodic record: `docs/sessions/` (session 0030 tracks this arc).
- Synthesis: `experiment/paper/two-signal-readout-framework.md` (Paper 4 seed) and the
  internal KG paper nodes `paper:internal-twosignal` + `paper:internal-paper3`.
- These are exploratory, non-headline results; they do NOT feed the locked PROTOCOL
  headline matrix. Promotion to a headline claim requires a pre-registered cross-family /
  held-out replication registered before running.

## Variations

- **By checkpoint:** Instruct base (S/W), deployed clean-SFT->GRPO-v2 (T/U).
- **By read position:** pre-gen anchor (gate) vs post-gen content token (dial); post beats
  pre for correctness.
- **By model size (Amendment X):** Qwen3 1.7B / 4B / 8B / 14B - the controlled size axis.
- **By model family (Amendment Z, RUNNING):** cross-FAMILY confirmatory on four ungated
  ~3-4B bases - `unsloth/Llama-3.2-3B-Instruct`, `mistralai/Ministral-3-3B-Instruct-2512`,
  `Qwen/Qwen3.5-4B`, `google/gemma-4-E4B-it`. The governed replication that would promote
  the training-free readout to a cross-family claim.
- **Deferred:** natural (un-forced) deployment prompt (Amendment V, shelved - data-starved).
- **Next axis (PROPOSED, Paper 5): turn the probe around from reading to WRITING.**
  Causal confidence steering - reuse the probe DIRECTION as a steering vector
  (activation steering) and/or inject the score as text into the CoT, to influence
  thinking + output from the inside. Two modalities x two positions (anchor vs end)
  give a CAUSAL test of the anchor-vs-end "why": probing shows where the signal is
  legible (presence); steering/injection show where it is causally used (use). Design:
  `docs/plans/confidence-steering-experiment.md`. New experiment; first run = a signed
  Tier-2 amendment on its own branch off main. Not yet registered or launched.

## Status log

- 2026-06-30: created (running). S/T/U/Stage-1.5/W complete on Qwen3-4B; framework + KG
  self-ingest done; V shelved. Amendment X (cross-size) signed, gates locked; smoke on
  Qwen3-1.7B GREEN (extractor + scorer end-to-end); full sweep (1.7B/8B/14B) pending the
  authorized launch. Tracked in `docs/sessions/0030 - two-signal-readout-arc-s-t-u-w-cross-size-generalization-amendment-x.md`.
- 2026-06-30 (later): Amendment X COMPLETE - all four sizes (1.7B/4B/8B/14B) PASS all three
  gates; size-robust, scaling non-monotonic (peaks 8B). PR #134. Then **Amendment Z
  (cross-FAMILY) pre-registered and LAUNCHED** on branch `pr/amendment-z-cross-family`
  (stacked on X). Sequential overnight queue (single GPU, local Docker `unsloth-z:latest`
  = unsloth + transformers 5.12.1 for the post-cutoff Gemma4/Qwen3.5 archs). Run order:
  Llama-3.2-3B -> Ministral-3-3B -> Qwen3.5-4B -> Gemma-4-E4B. Per model: compat smoke
  (shape-validated) -> full (3000 attempts) -> CPU score. Failures logged INELIGIBLE, queue
  continues. Loader hardened for multimodal (CausalLM -> ImageTextToText fallback,
  text_config layer counts) with Qwen3 path unchanged. Progress:
  `experiment/phase1/probe/z_logs/PROGRESS.log`; results: `amendment_z_*_result.json`.
- 2026-06-30 (results, in-flight): Amendment Z 2 of 4 scored. **Llama-3.2-3B PARTIAL**
  (gate 0.997 / dial 0.861 / veto 0.633 FAIL); **Ministral-3-3B PASS** (gate 0.997 /
  dial 0.818 / veto 0.733). Veto tally 1 PASS / 1 FAIL; Qwen3.5-4B extracting, Gemma-4-E4B
  queued. Gate + dial family-general (gate saturated ~0.997, dial 0.82-0.86); the **veto is
  the model-dependent axis** - Llama's confident hallucinations read as trustworthy to its own
  dial (dial_mean_halluc 0.476 vs correct 0.707) so the veto misses; Ministral's read low-trust
  (0.278 vs 0.605) so it passes. Mirrors X's non-monotonic veto. Roll-up table + data links in
  `experiment/protocol/AMENDMENT-Z-cross-family-confirmatory.md` §7.
