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
- Synthesis: `experiment/paper/two-signal-readout-framework.md` (Paper 3 seed) and the
  internal KG paper nodes `paper:internal-twosignal` + `paper:internal-paper3`.
- These are exploratory, non-headline results; they do NOT feed the locked PROTOCOL
  headline matrix. Promotion to a headline claim requires a pre-registered cross-family /
  held-out replication registered before running.

## Variations

- **By checkpoint:** Instruct base (S/W), deployed clean-SFT->GRPO-v2 (T/U).
- **By read position:** pre-gen anchor (gate) vs post-gen content token (dial); post beats
  pre for correctness.
- **By model size (Amendment X):** Qwen3 1.7B / 4B / 8B / 14B - the controlled size axis.
- **By model family (Amendment Z, SUCCESS):** cross-FAMILY confirmatory on four ungated
  ~3-4B bases - `unsloth/Llama-3.2-3B-Instruct`, `mistralai/Ministral-3-3B-Instruct-2512`,
  `Qwen/Qwen3.5-4B`, `google/gemma-4-E4B-it`. PASSED (veto 3/4): gate + dial family-general
  (4/4), veto replicates (3/4, fragile axis). Promotes the training-free readout to a
  cross-family CLAIM.
- **Deferred:** natural (un-forced) deployment prompt (Amendment V, shelved - data-starved).
- **Next axis (PROPOSED, Paper 4): turn the probe around from reading to WRITING.**
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
- 2026-06-30 (RESULT: SUCCESS): **Amendment Z COMPLETE, 4/4 scored.** Final veto tally
  **3 PASS (Ministral 0.733, Qwen3.5 0.666 marginal, Gemma-4 0.871) / 1 FAIL (Llama-3.2
  0.633)** => meets the pre-registered ≥3/4 bar => **SUCCESS**. Gate + dial pass on ALL FOUR
  families (gate saturated 0.997-0.998; dial 0.82-0.86) — those axes are fully family-general.
  The **veto replicates (3/4) but is the fragile, model-specific axis**: Llama's confident
  hallucinations read as trustworthy to its own dial (dial_mean_halluc 0.476 vs correct 0.707,
  so the veto misses); Gemma's read near-zero trust (0.089 vs 0.593, the cleanest split).
  Mirrors X's non-monotonic veto. **The training-free two-signal readout is promoted from
  W/X exploratory to a cross-FAMILY CLAIM** (Qwen/Llama/Mistral/Gemma). Full roll-up table,
  descriptive gradient, and SUCCESS verdict in
  `experiment/protocol/AMENDMENT-Z-cross-family-confirmatory.md` §7.
- 2026-07-01: **Amendment SR (sampled-decode seed-robustness) pre-registered + LAUNCHED**
  on branch `pr/seed-robustness-sampled-decode` (off main after #136). Hardens the Z
  headline dial+veto magnitudes against the single-greedy-decode confound: identical
  training-free readout under SAMPLED decoding (temp 0.7 / top_p 0.9) × 3 seeds
  (20260701/02/03) on the **4 confirmatory families only** (Qwen3-4B/W excluded so the
  seed pass stays inside the confirmatory set). Scope = dial + veto (gate is
  pre-gen-anchor decode-INVARIANT, emitted as an invariance check only). Extractor gained
  backward-compatible `--do-sample/--temperature/--top-p` (default greedy = X/Z reproduce
  byte-for-byte). Queue driver `amendment_sr_queue.sh`; log `sr_logs/PROGRESS.log`; results
  `amendment_sr_<tag>_seed<N>_result.json`. Pre-reg + gates:
  `experiment/protocol/AMENDMENT-SR-sampled-decode-seed-robustness.md`.
  **Incremental results (updating as cells land):**
  - **Llama-3.2-3B — 3/3 seeds DONE.** veto 0.801 / 0.684 / 0.732 → **seed-stable PASS
    (3/3)**, mean ~0.739. dial 0.827 / 0.853 / 0.865 (all PASS). gate ~0.997 all (invariance
    confirmed). NOTE: Llama's veto was the clean **greedy FAIL (0.633)** in Z; under sampled
    decoding it PASSES on every seed → the Z single-decode veto miss looks like a
    greedy-decode artifact. (n=1 family so far; not read into the verdict yet.)
  - **Ministral-3-3B — 3/3 seeds DONE.** veto 0.606 / 0.696 / 0.742 → **seed-stable PASS
    (2/3)** (seed 701 FAILs at 0.606; greedy Z was 0.733). dial 0.808 / 0.812 / 0.799 (all
    PASS). gate ~0.997 all.
  - **Qwen3.5-4B — 3/3 seeds DONE.** veto 0.659 / 0.807 / 0.794 → **seed-stable PASS (3/3)**
    (seed 701 marginal at 0.659; greedy Z was marginal 0.666). dial 0.830 / 0.864 / 0.862
    (all PASS). gate ~0.998 all.
  - **Gemma-4-E4B — DID NOT RUN → RE-RUN PENDING.** Compat smoke crashed on a transient 9P
    `PermissionError [Errno 13]` at `out_dir.mkdir(...)` BEFORE the model loaded (the queue's
    other 12 in-container dirs created fine; Gemma was last and hit a DrvFS hiccup). This is a
    retryable INFRA fault, NOT a scientific INELIGIBLE — Gemma passed the same greedy smoke in
    Z with the identical `unsloth-z:latest` image. Recorded RE-RUN PENDING, awaiting GPU
    launch approval.
  - **Queue COMPLETE 16:54 UTC — 9/12 scored (3 eligible families).** Roll-up: dial 9/9 PASS
    (seed-stable 3/3 on all 3 families); veto seed-stable PASS on all 3 (Llama 3/3, Ministral
    2/3, Qwen3.5 3/3); gate decode-invariant (per-family across-seed range <0.0011). Llama's Z
    greedy veto FAIL (0.633) and Qwen3.5's Z greedy marginal (0.666) both come up PASS under
    sampled decoding → the single-greedy-decode veto softness was a decode artifact.
    **VERDICT DEFERRED:** the strict per-seed clause (c, ≥3/4 veto PASS on every seed) hinges
    on Gemma — seeds 702/703 are 3/3 but seed 701 is 2/3 (Ministral FAILs), so Gemma-701 must
    PASS to clear ≥3/4. Re-run Gemma before calling the verdict.

- **Amendment Y (pretrain-only base readout) — INTERIM, fleet in flight (2026-07-02).**
  10-cell HF Jobs fleet (a10g-small, pinned 3bb2fc76, seed 20260630 greedy, k-shot base-mode
  surface for bases). Results land in `professorsynapse/epistemic-humility-cloud-results`
  per run-tag; roll-up pending. Landed 5/10, 0 failures, all formally PASS all three gates:
  | cell | year | gate | dial | veto | within-dist control |
  |---|---|---|---|---|---|
  | y-b-gpt2-xl | 2019 | 0.991 (L23) | 0.794 | 0.794 | **0.589** |
  | y-b-pythia-2.8b | 2023 | 0.993 (L10) | 0.821 | 0.751 | **0.596** |
  | y-a-llama-3.2-3b-base | 2024 | 0.997 (L14) | 0.824 | 0.835 | 0.771 |
  | y-a-olmo-3-7b-base | 2025 | 0.998 (L17) | 0.844 | 0.803 | 0.791 |
  | y-a-qwen3.5-4b chat-render sub-cell | 2026 | 0.998 (L21) | 0.851 | 0.867 | 0.796 |
  Arm A official tally 2/4 toward the ≥3/4 H_B1/H_B2 bar (Qwen k-shot primary + Gemma-pt
  still running; chat-render is the report-only confound cell).
  **Two interim findings that shape the paper reading:**
  1. **Era gradient lives in the within-distribution control, not the headline AUROCs.**
     Gate/dial are near-flat back to GPT-2, but the within-SelfAware control (known-answered
     vs hallucination inside one dataset) climbs ~0.59 → ~0.79 across eras: old models
     separate hallucinations mostly via dataset cues; modern pretraining makes the veto hold
     in-distribution.
  2. **Text-only baseline bounds the surface share** (`amendment_y_text_baseline.py`,
     cceaaf76; descriptive, lab-notebook): TF-IDF+LR on question text alone reads gate
     **0.964** on the frozen pool and dial **0.75–0.78** on Z rows. So the era-invariant part
     of the gate is substantially benchmark surface; the model-attributable signal is the
     margin above the text ceiling (error mass 3.6% → ~0.2% on modern bases; margin itself
     grows with era) plus the answer-dependent S/T pre-vs-post gap. Roll-up tables must
     report hidden-state AUROC NEXT TO the text baseline.
  Ops: cloud cells now upload `rows.jsonl` alongside result+manifest (e2fa5c04) — the first
  fleet discarded rows, which blocked per-cell text baselines; per-Y-cell dial baselines are
  therefore not computable for this batch (gate baseline unaffected: shared frozen pool).
- 2026-07-02 (RESULT: Y COMPLETE — H_B1 SUPPORTED 4/4): **Amendment Y fleet all 10 cells
  scored** (9 cloud + OLMo-2-7B local on the 3090 after the cloud cell was benched on
  repeated A10G preemption/download stalls). Arm A: every base reads the gate at 0.997+
  (H_B1 4/4, falsifier 0/4 — the boundary signal predates post-training on all four
  families); base-fit veto passes 4/4 (H_B2; Qwen3.5 marginal 0.666 mirroring its Z greedy
  margin). H_B3 (post-training sharpens) NOT SUPPORTED: deltas <= 0 on every pair — the
  clean within-Y Olmo-3 pair moves veto 0.803 -> 0.731 (other pairs render-confounded).
  Dual-render control: Qwen3.5-Base veto is render-SENSITIVE (k-shot 0.666 vs chat 0.867;
  gate render-invariant) — part of the Z veto fragility is prompting surface, not model.
  Arm B era ladder (descriptive): all three readouts above 0.65 back to GPT-2-XL (2019);
  era signal confirmed to live in the within-SA control (0.589/0.596 old era -> 0.71-0.82
  Llama-2 onward), gate near-flat next to the 0.964 text baseline. Batched-engine
  equivalence cell matches sequential within noise. Roll-up + tables:
  `experiment/protocol/AMENDMENT-Y-pretrain-only-base-readout.md` §9; per-cell artifacts
  `experiment/phase1/probe/amendment_y_results/`. Paper hook: answers the regimen paper's
  §8 open question in the "already present from pretraining" direction (paper text update
  tracked on the paper line, not this branch).
