---
title: 'Curiosity-weighted prompt curriculum for the GRPO humility arm'
kg:
  id: experiment:curiosity-curriculum-grpo
  type: experiment
  status: canonical
tags:
  - kg/experiment
status: proposed
governance: exploratory
phase: phase1
lane: local
est_compute: 'Diagnostic (no training): ~0.5 GPU-hour. Bounded GRPO pilot: ~8-16 GPU-hours on one RTX 3090 per seed. The curriculum adds no training cost; it only reweights prompt sampling.'
relationships:
- type: tests
  target: '[[hallucination-predictors-enable-efficient-adaptation]]'
  target_id: mechanism:hallucination-predictors-enable-efficient-adaptation
  confidence: high
- type: builds_on
  target: '[[2606.27326--hallucination-world-models-predictable-preventable]]'
  target_id: paper:2606.27326
  confidence: high
- type: builds_on
  target: '[[curiosity-driven-targeted-data-collection]]'
  target_id: method:curiosity-driven-targeted-data-collection
  confidence: high
- type: builds_on
  target: '[[coverage-aware-training]]'
  target_id: method:coverage-aware-training
  confidence: medium
- type: builds_on
  target: '[[group-relative-policy-optimization]]'
  target_id: method:group-relative-policy-optimization
  confidence: high
related:
- '[[hallucination-predictors-enable-efficient-adaptation]]'
- '[[2606.27326--hallucination-world-models-predictable-preventable]]'
- '[[curiosity-driven-targeted-data-collection]]'
- '[[coverage-aware-training]]'
- '[[group-relative-policy-optimization]]'
- '[[state-action-coverage-gap]]'
- '[[knowledge-boundary]]'
---

## Question & Hypothesis

Can a curiosity-weighted prompt curriculum, which oversamples knowledge-frontier
prompts, improve the GRPO humility arm's signal density and sample efficiency
versus uniform prompt sampling, without inducing over-refusal?

The borrow is from world-model hallucination
(`library/notes/2606.27326--hallucination-world-models-predictable-preventable.md`):
that paper uses hallucination predictors as a *curiosity reward* to steer data
collection toward low-coverage state-action regions, adapting with as few as 50
real trajectories. The faithful LLM analog is NOT a reward term (rewarding the
model for seeking or expressing uncertainty would just inflate abstention and
hedging, the exact failure `experiment/phase1/grpo/humility_reward.py` already
penalizes). The analog is a prompt curriculum: the model's knowledge frontier is
the low-coverage region, and GRPO's group-relative advantage is densest exactly
there.

- **Mechanistic reason it should work.** GRPO advantage is the z-score of rewards
  across the G samples of one prompt. On a deep-known prompt (all G correct) or a
  deep-unknown prompt (all G wrong/abstain) the group reward variance collapses,
  so advantage and gradient go to zero. The prompts that teach are the mixed,
  frontier ones. The 32-sample probe `p_correct` already estimates that frontier
  per prompt, and `experiment/phase1/grpo/build_grpo_dataset.py` already carries
  `p_correct` on every row.
- **Hypothesis.** Weighting prompt sampling by the Bernoulli information score
  `w = p_correct * (1 - p_correct)` (peaked at 0.5, near-zero at the extremes)
  raises the fraction of GRPO groups with non-zero reward variance, giving more
  usable gradient per rollout, and reaches a target unknown-abstention recall (at
  fixed known-correctness) in fewer prompts/steps than uniform sampling.
- **Falsifier.** Any of: (a) no rise in advantage-signal density under curiosity
  weighting versus uniform; (b) no sample-efficiency gain once normalized for
  total rollouts; (c) known-row over-refusal rises versus uniform (the curriculum
  overfits the frontier and erodes known-row answering); (d) a shuffled-weight
  control (same weight distribution, random assignment) matches the curiosity
  weighting, meaning the effect is non-uniformity, not the frontier signal.

This is an `exploratory` note: it produces non-headline evidence and is freely
editable. It targets the prospective GRPO arm defined in
`experiment/protocol/AMENDMENT-B-stated-confidence-grpo.md`, which is not
launch-authorized. Promoting any result to affect the GRPO arm, training, or
reporting requires the `experiment/protocol/amendment-governance.md` 7-point
sign-off (this would land as a new additive amendment).

## Design

Arms (one fixed reward, the curriculum changes only WHICH prompts are sampled):

- **A0 uniform (control).** Existing `experiment/phase1/grpo/build_grpo_dataset.py`
  sampling. Reward unchanged.
- **A1 static curiosity curriculum.** Per-row sampling weight
  `w = p_correct * (1 - p_correct)` from the model-specific probe split. Reward
  unchanged.
- **A1b shuffled-weight control.** The A1 weight multiset, randomly permuted across
  prompts. Isolates "frontier signal" from "non-uniform sampling."
- **A2 online moving-frontier curriculum (stretch).** Recompute an empirical
  per-prompt reward variance every N optimizer steps and reweight, because the
  frontier moves as the policy learns (the paper re-plans every K steps for the
  same reason). Needs stability controls; gated behind A1 succeeding.

Reward guardrail: curiosity stays OUT of the reward. `humility_reward.py` is
unchanged across all arms. This is the central design invariant and the thing a
reviewer should check first.

- **Models.** Qwen3-4B base for the `grpo` arm; the matched seed-1 SFT-merged
  checkpoint for the `sft_grpo` arm. Seed 1 first, then 2 and 3 only if seed 1
  clears the falsifier.
- **Data.** The TriviaQA known/unknown probe split already consumed by the dataset
  builder, including ambiguous rows that carry a real `p_correct`.
- **Metric panel.**
  - Advantage-signal density: fraction of GRPO groups with `std(reward) > 0` and
    mean `|advantage|`, per arm. This is the primary mechanistic readout and the
    cheap pre-training falsifier.
  - Sample efficiency: prompts/steps to reach a target unknown-abstention recall
    at fixed known-correctness.
  - Humility outcomes (Amendment B metrics): unknown-abstention recall,
    known-correctness, over-refusal rate, stated-confidence Brier versus answer
    correctness.
  - Guardrail: known-row over-refusal must not rise versus A0.
- **Controls.** A0 uniform and A1b shuffled-weight are both mandatory; without
  A1b a positive A1 result is uninterpretable.

## Prerequisites & Gating

- The model-specific probe split must exist and carry `p_correct` per row (the
  same split `experiment/phase1/grpo/build_grpo_dataset.py` consumes). If it is
  not staged, run the Phase 1 probe first.
- GPU available (single RTX 3090). The step-4 diagnostic needs no training.
- GRPO training launch is NOT authorized by this note. It requires the separate
  launch approval named in `experiment/protocol/AMENDMENT-B-stated-confidence-grpo.md`
  section 7 (exact arms, seeds, lane).
- The curriculum is implemented as a sampler weight inside
  `experiment/phase1/grpo/build_grpo_dataset.py`; no experiment-specific code goes
  into the `synaptic-tuner` submodule.
- Read `experiment/protocol/PHASE3-control-system-protocol.md` RQ5 gaming controls
  before any online (A2) variant: a probe-readable signal entering the training
  loop must not let the model learn to merely look frontier.

## Runbook

1. Setup: confirm GPU; confirm the probe split exists and carries `p_correct`
   (else run the probe). Pin the base and the seed-1 SFT-merged model.
2. Build weights: extend `experiment/phase1/grpo/build_grpo_dataset.py` to emit a
   per-row curiosity weight `w = p_correct * (1 - p_correct)` and an A1b
   shuffled-weight column. Leave the reward and row contract otherwise unchanged.
3. Preflight: run the CPU-side reward and dataset preflight from the Amendment B
   GRPO bootstrap pattern in
   `.agents/skills/experiment-runner/reference/common-patterns.md`
   (`experiment/phase1/grpo/build_grpo_dataset.py`,
   `experiment/phase1/grpo/make_smoke_subset.py`,
   `experiment/phase1/grpo/reward_sanity_table.py`).
4. Diagnostic (no training, the cheap falsifier): use
   `experiment/phase1/grpo/rollout_reward_diagnostic.py` on a fixed prompt sample
   to measure advantage-signal density (fraction of non-zero-variance groups)
   under A0 uniform, A1 curiosity, and A1b shuffled weights. If A1 does not beat
   A0 here, stop: the hypothesis is already falsified without spending training.
5. Run (gated on launch approval): GRPO pilot per arm, seed 1, dispatched through
   the tuner's existing custom-reward and dataset interfaces, with
   `experiment/phase1/grpo/humility_reward.py` as the unchanged reward and the
   curriculum supplied only through dataset weighting.
6. Eval: Amendment B stated-confidence metrics plus the known-row over-refusal
   guardrail.
7. Document: write a run record and a `docs/sessions/` checkpoint via the
   experiment-runner helper; update the Status log below.

Bake in an explicit approval gate before step 5 (training cost). Do not add
experiment-specific code to `synaptic-tuner`.

## Validation contract

- **Pre-run.** The probe split resolves and carries `p_correct`; A1 weights
  normalize correctly; the A1b shuffled weights are distinct from A1; the reward
  preflight (`reward_sanity_table.py`) passes; `humility_reward.py` is byte-for-byte
  identical across arms.
- **Post-run.** Advantage-signal-density numbers exist for A0/A1/A1b; if training
  ran, each arm has an Amendment B eval row (unknown recall, known correctness,
  over-refusal, confidence Brier) and a sample-efficiency curve; a run record and
  session checkpoint are written.
- **Definition of done.** Step 4 reports advantage-signal density per weighting
  (the standalone, no-training result). If training is approved and runs, the
  per-arm humility panel, the sample-efficiency comparison versus A0, and the
  known-row over-refusal guardrail are all reported, with A1 judged against BOTH
  A0 and A1b.

## Outputs & provenance

- Run records: `experiment/phase1/run_records/`.
- Episodic log: `docs/sessions/` checkpoints via the experiment-runner helper.
- Meta-analysis: this is exploratory GRPO-arm evidence. It does NOT enter
  `meta-analysis/evidence/effects.csv` and is NOT a v0.3 headline result. The
  source paper is logged as a v1 candidate in
  `meta-analysis/evidence/prisma-flow.md` and ingested in the library.
- Promotion to affect the GRPO arm requires the Amendment B section-7 launch
  approval and the `experiment/protocol/amendment-governance.md` 7-point sign-off.

## Variations

- **A0 uniform (control).** Baseline advantage density and humility panel.
- **A1 static curiosity.** `w = p_correct * (1 - p_correct)`. The headline arm.
- **A1b shuffled-weight control.** Same weight multiset, permuted. The
  interpretability gate for A1.
- **A2 online moving-frontier.** Recompute per-prompt reward variance every N
  steps and reweight. The closest analog to the paper's online re-planning loop;
  the genuinely novel question (does re-targeting a moving frontier beat a static
  one?). Gated on A1 and on PHASE3 RQ5 controls.
- **V3 coverage-aware resampling (sibling borrow).** The paper's other fix:
  task-uniform resampling so low-density regions are not under-trained. Balance
  the training mix across the difficulty/`p_correct` spectrum rather than only
  known/unknown. Lower risk, applies to SFT/DPO/KTO too, and directly attacks the
  Amendment E scalar-collapse cause (14,395 rows at one confidence value). Worth
  running as the conservative comparison to curiosity weighting.

## Status log

- 2026-06-26: created (proposed). Originates from the curiosity-reward exploration
  off the 2606.27326 ingest. No runs yet; queued for the step-4 diagnostic first.
