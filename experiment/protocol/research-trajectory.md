# Research Trajectory — Epistemic Humility Program

Captured 2026-06-10 from the trajectory conversation. This is the staged
plan that paper 1's §8 will announce and the experiment program executes.
Each phase consumes the previous phase's artifacts.

## Anchor

The meta-analysis (paper 1) verified these gaps; the program is built to
close them in order of leverage:

1. No KTO-for-abstention study exists (gap 1).
2. No SFT/DPO/KTO three-way comparison exists (gap 2).
3. The recall/over-refusal decomposition is almost never reported (§5.3).
4. The central tension — preference training improves abstention while
   damaging calibration — has never been measured on the same training run.
5. No IDK-fraction dose-response curve exists for epistemic abstention
   (gap 5; the Bianchi curve exists only for safety refusal).
6. Probe-transfer of trained humility is untested (gap 4).
7. Small-model and OOD-transfer coverage is thin (gap 6).

## Dataset strategy: reuse the Cheng recipe, not the Cheng labels

- Cheng et al. (2401.13275) is the anchor: released outputs (reanalyzed
  exactly), test set identified as TriviaQA unfiltered.nocontext/validation
  (100% question match), gold aliases staged locally
  (`datasets/triviaqa-rc-nocontext/cheng_test_gold.jsonl`).
- Known/unknown splits are model-specific by construction → regenerate
  labels for our model with their correctness-probing method.
- Mandatory improvement from paper 1's findings: probe with a higher
  sample count than their 10 and run a label-noise sensitivity analysis
  (we measured 43-51% of their "unknown"-labeled questions answered
  correctly).

## Model strategy

- Pin a current open-weights family with a small and a mid size at
  experiment kickoff, then freeze. Criteria: open weights, chat variant,
  two sizes (~3B pilot + ~7-8B confirm), stable HF support. Repo tooling
  currently targets Qwen2.5-3B/7B; substitute the newest equivalent
  generation at kickoff (user note: Llama-2-era models are stale/overused;
  apples-to-oranges vs prior work is acceptable because comparisons are
  within-model across methods).
- PIN DECISION (2026-06-10, frozen for Phase 1 / paper 2): Qwen3, namely
  Qwen3-4B-Instruct (pilot, local RTX 3090) and Qwen3-8B-Instruct (confirm,
  HF Jobs), both Apache 2.0, ungated, text-only; thinking mode pinned OFF
  (enable_thinking=False). Rationale: the only current family that is at once
  text-only, uniformly Apache and ungated, and a near-exact 4B/8B pairing.
  Full survey: `docs/preparation/model-landscape.md`.
- Bridge arm (recommended, pending user confirmation): one replication of
  Idk-SFT + Idk-DPO on Llama-2-7b-chat itself to validate the pipeline
  against Cheng's published numbers before running novel arms on the
  modern model.
- Long-term: the pipeline is re-runnable on any open model (Phase 4).

## Phase 1 — the three-way (paper 2 core)

SFT vs DPO vs KTO on model-specific IDK data, same base model, same data
budget. Fills gaps 1+2 in one design.

Measure everything the literature splits apart, after the same run:
- refusal recall AND over-refusal/abstention precision (the decomposition)
- truthful rate
- token-level ECE / calibration (first study to measure the
  abstention-calibration tension on a single run; KTO unmeasured on both)
- OOD transfer: KUQ, CoCoNot, AbstentionBench subsets (all already local)

Infra: 3B pilot on RTX 3090 (`tuner.py local-run`), 7-8B confirm on HF
Jobs. KTO data per `.skills/fine-tuning/reference/dataset-formats.md`
(interleaving requirement).

## Phase 2 — dose-response and data composition

(a) IDK-fraction sweep on best Phase-1 method + SFT → the field's first
    abstention-precision/over-refusal Pareto curve (gap 5).
(b) C3 boundary-condition test set up by our AbstentionBench reanalysis:
    abstention-targeted SFT vs general SFT mix → is over-refusal a
    data-composition property rather than a method property?
(c) KTO-only ablation no other method supports: desirable/undesirable
    balance is a free knob (unpaired binary labels). First ablation =
    congruence-vs-correctness mapping tension documented in
    `rewardcal-kto-recipe.md` (R1).

## Phase 3 — mechanism

- Probe for an "I don't know" direction before/after each training method;
  test whether the probe transfers OOD when behavior does not (gap 4; the
  essay's "form of ignorance without the substance" made empirical).
- Toolkit: raw report 06's probing line (Azaria-Mitchell, CCS, ITI,
  semantic-entropy probes); caution from 2606.02907 (probes can detect
  task format, not reasoning mode) and the TPR-gaming result (probes
  inside RL reward loops get gamed).
- R2 slots here: run HINT-lab PPO-M/PPO-C checkpoints through our
  abstention suite (does reward calibration transfer to abstention?).

## Phase 4 — generalization program (rolling)

- Cross-architecture re-runs of the full pipeline (model-specific labels +
  three-way training + full metric decomposition) as a rolling result;
  release harness + per-model labels + outputs (the reproducibility
  behavior paper 1 documents the field lacking — only ~5 of 31 corpus
  studies released usable artifacts).
- Sycophancy axis: S1 join was a verified negative (n=1 overlap), so
  construct it ourselves — apply Sharma's 4 mechanical framings
  (none / correct-given / incorrect-given / correct-doubted) to our
  knowledge-labeled questions: does capitulation concentrate at the
  knowledge frontier? (Forward paths documented in
  `evidence/sycophancy-cheng-join.md`.)
- Thinking vs non-thinking axis (REGISTERED 2026-06-10, future material, not
  designed yet): Phase 1 pins the Qwen3 thinking toggle OFF for a clean
  non-reasoning study. The toggle is a free, controlled axis: re-run the
  three-way abstention training (or at least the eval suite) with
  enable_thinking=ON vs OFF on the same Qwen3 model. Question: does an
  explicit reasoning trace change where the knowledge frontier sits, whether
  abstention training transfers, and the abstention-calibration tension
  (does a `<think>` trace let the model verbalize uncertainty it cannot
  express in a direct answer)? This connects to the Phase 3 probing line
  and the 2606.02907 caution that probes can detect task format rather than
  reasoning mode. Reasoning-by-default modern families (e.g. Qwen3.5) are
  the natural cross-architecture extension of this axis in the Phase 4
  rolling re-runs.

## Publication shape

- Paper 2 = Phase 1 (+ cheapest Phase-2 slice if budget allows).
- Paper 3 = Phases 2+3.
- Phase 4 = ongoing infrastructure / community artifact.

## Open decisions (user)

1. Model family pin at kickoff (Qwen2.5 vs newer generation).
2. Llama-2-7b-chat bridge arm: in or out (recommendation: in).
3. How much Phase 2 rides along in paper 2.
4. KTO label mapping for the calibration-flavored arm: congruence vs
   correctness-safe (see rewardcal-kto-recipe.md ablation note).

## Status

- Paper 1 §8 is stubbed pending this trajectory being finalized; v0 text
  parked at `experiment/protocol/future-work-section-v0.md`.
- Pre-register hypotheses in `experiment/protocol/` before any training.
