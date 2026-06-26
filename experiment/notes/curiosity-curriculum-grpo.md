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
  target: '[[grpo-composite-reward-installs-epistemic-output-schema]]'
  target_id: mechanism:grpo-composite-reward-installs-epistemic-output-schema
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
- '[[grpo-composite-reward-installs-epistemic-output-schema]]'
- '[[2606.27326--hallucination-world-models-predictable-preventable]]'
- '[[curiosity-driven-targeted-data-collection]]'
- '[[coverage-aware-training]]'
- '[[group-relative-policy-optimization]]'
- '[[state-action-coverage-gap]]'
- '[[knowledge-boundary]]'
---

## Question & Hypothesis

Can a curiosity-weighted prompt curriculum, which oversamples knowledge-frontier
prompts, improve the GRPO humility arm's known/unknown tradeoff and signal
density versus uniform prompt sampling, without raising known over-refusal?

This is now an experiment about an arm that already exists. The GRPO composite
reward (GRPO v2 from `experiment/protocol/AMENDMENT-E-probe-scaled-response-confidence.md`)
is installed and runs, and `experiment/protocol/AMENDMENT-F-grpo-centered-stacking.md`
(GRPO-centered three-stage stacking) is signed off. The accumulated seed-1
SelfAware evidence shows a consistent failure mode: GRPO is the one downstream
path that materially shifts unknown abstention in the desired direction, but it
leaves **known over-refusal high** (above 60% on the clean seed-1 SelfAware eval,
higher before a DPO recovery stage) and **response confidence behavior-insensitive**
(mean near 0.87, the scalar barely moves). That is the open problem this note
targets, from the data side rather than the reward side.

The borrow is from world-model hallucination
(`library/notes/2606.27326--hallucination-world-models-predictable-preventable.md`),
which uses hallucination predictors as a *curiosity reward* to steer data
collection toward low-coverage state-action regions, adapting with as few as 50
real trajectories. The faithful LLM analog is NOT a reward term: rewarding the
model for seeking or expressing uncertainty would just inflate abstention and
over-refusal, the exact failure above. The analog is a prompt curriculum. The
model's knowledge frontier is the low-coverage region, and GRPO's group-relative
advantage is densest exactly there.

- **Mechanistic reason it should work.** GRPO advantage is the z-score of rewards
  across the G samples of one prompt. On a deep-known prompt (all G correct) or a
  deep-unknown prompt (all G wrong/abstain) the group reward variance collapses,
  so advantage and gradient go to zero, and the policy can drift toward blanket
  refusal without a counter-signal from those prompts. The mixed, frontier
  prompts are where the reward has variance and the known/unknown tradeoff is
  actually taught. The 32-sample probe `p_correct` already estimates that frontier
  per prompt, and `experiment/phase1/grpo/build_grpo_dataset.py` already carries
  `p_correct` on every row.
- **Hypothesis.** Weighting prompt sampling by the Bernoulli information score
  `w = p_correct * (1 - p_correct)` (peaked at 0.5, near-zero at the extremes)
  raises the fraction of GRPO groups with non-zero reward variance, gives more
  usable gradient per rollout, and improves the known-over-refusal / unknown-recall
  tradeoff at fixed compute relative to uniform sampling.
- **Falsifier.** Any of: (a) no rise in advantage-signal density under curiosity
  weighting versus uniform; (b) no improvement in the over-refusal / unknown-recall
  tradeoff once normalized for total rollouts; (c) known over-refusal rises versus
  uniform (the curriculum overfits the frontier and erodes known answering); (d) a
  shuffled-weight control (same weight distribution, random assignment) matches the
  curiosity weighting, meaning the effect is non-uniformity, not the frontier signal.

This is an `exploratory` note: it produces non-headline evidence and is freely
editable. It proposes a curriculum variant orthogonal to the F/G/H/I
stacking-and-scale work; the GRPO reward is unchanged. Promoting any positive
result into a launched arm or into reporting requires a new signed amendment
under `experiment/protocol/amendment-governance.md` (the next free letter after
the current H/I), not an edit to this note.

## Design

Arms (one fixed reward, the curriculum changes only WHICH prompts are sampled):

- **A0 uniform (control).** Existing `experiment/phase1/grpo/build_grpo_dataset.py`
  sampling, GRPO v2 reward. This reproduces the current SFT->GRPO v2 behavior.
- **A1 static curiosity curriculum.** Per-row sampling weight
  `w = p_correct * (1 - p_correct)` from the model-specific probe split. Reward
  unchanged.
- **A1b shuffled-weight control.** The A1 weight multiset, randomly permuted across
  prompts. Isolates "frontier signal" from "non-uniform sampling."
- **A2 online moving-frontier curriculum (stretch).** Recompute an empirical
  per-prompt reward variance every N optimizer steps and reweight, because the
  frontier moves as the policy learns (the paper re-plans every K steps for the
  same reason). Needs stability controls; gated behind A1 succeeding.

Reward guardrail: curiosity stays OUT of the reward. The GRPO v2 composite reward
in `experiment/phase1/grpo/humility_reward.py` is unchanged across all arms
(this note tests `[[grpo-composite-reward-installs-epistemic-output-schema]]`
under a different prompt diet, not a new reward). This is the central design
invariant and the thing a reviewer should check first.

- **Lineage.** Source from the clean Amendment E SFT, then GRPO v2, matching the
  Amendment F source convention. Seed 1 first; seeds 2/3 and 8B deferred until
  seed 1 clears the falsifier, mirroring the F/G/I gating.
- **Data.** The TriviaQA known/unknown probe split already consumed by the dataset
  builder, including ambiguous rows that carry a real `p_correct`.
- **Comparators.** Clean SFT merged seed 1; clean SFT->GRPO v2 seed 1 (the A0
  reproduction is the direct control); and the Amendment F stacks
  (`[[clean-sft-grpo-dpo]]`, `[[clean-sft-grpo-kto]]`) as context for where the
  tradeoff currently sits.
- **Metric panel (the signed Amendment F SelfAware metrics).** Truthful percentage,
  unknown refusal recall, unknown answer rate, known over-refusal, correct-on-known
  among answered known rows, and response-confidence coverage / mean / unique-value
  count / Brier versus response appropriateness. Plus one curriculum-specific
  readout: advantage-signal density (fraction of GRPO groups with `std(reward) > 0`
  and mean `|advantage|`), the primary mechanistic signal and the cheap pre-training
  falsifier.
- **Primary success target.** Lower known over-refusal than A0 at equal-or-better
  unknown refusal recall. A1 must beat BOTH A0 and A1b to count.

## Prerequisites & Gating

- The model-specific probe split must exist and carry `p_correct` per row (the
  same split `experiment/phase1/grpo/build_grpo_dataset.py` consumes). If it is
  not staged, run the Phase 1 probe first.
- The clean Amendment E SFT and SFT->GRPO v2 seed-1 source checkpoints must exist
  (the Amendment F source lineage); confirm via the source metrics in the
  Amendment E/F session notes before reusing them.
- GPU available (single RTX 3090). The step-4 diagnostic needs no training.
- GRPO training is a signed arm under Amendment F, but a curriculum variant is a
  new exploratory change: a launch still requires a decision naming the exact
  cell, source checkpoint, seed, and lane, and any promotion to reporting needs a
  new signed amendment per `experiment/protocol/amendment-governance.md`.
- The curriculum is implemented as a sampler weight inside
  `experiment/phase1/grpo/build_grpo_dataset.py`; no experiment-specific code goes
  into the `synaptic-tuner` submodule.
- Read `experiment/protocol/PHASE3-control-system-protocol.md` RQ5 gaming controls
  before any online (A2) variant: a probe-readable signal entering the training
  loop must not let the model learn to merely look frontier.

## Runbook

1. Setup: read `experiment/protocol/AMENDMENT-F-grpo-centered-stacking.md` and
   `experiment/phase1/grpo/amendment_e_clean_mainline_runbook.md`; confirm GPU and
   the clean SFT / GRPO v2 source checkpoints; confirm the probe split carries
   `p_correct` (else run the probe).
2. Build weights: extend `experiment/phase1/grpo/build_grpo_dataset.py` to emit a
   per-row curiosity weight `w = p_correct * (1 - p_correct)` and an A1b
   shuffled-weight column. Leave the GRPO v2 reward and row contract unchanged.
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
5. Run (gated on a launch decision): GRPO pilot per arm, seed 1, from the clean
   SFT->GRPO v2 lineage, dispatched through the tuner's existing custom-reward and
   dataset interfaces, with `experiment/phase1/grpo/humility_reward.py` as the
   unchanged reward and the curriculum supplied only through dataset weighting.
6. Eval: full SelfAware eval, then rebuild the comparison with
   `experiment/phase1/eval/analysis/build_selfaware_full_run_comparison.py` and
   read it against
   `experiment/phase1/eval/analysis/selfaware_full_run_comparison_grouped.csv`,
   with the known-over-refusal guardrail front and center.
7. Document: write a run record and a `docs/sessions/` checkpoint via the
   experiment-runner helper; update the Status log below.

Bake in an explicit approval gate before step 5 (training cost). Do not add
experiment-specific code to `synaptic-tuner`.

## Validation contract

- **Pre-run.** The probe split resolves and carries `p_correct`; A1 weights
  normalize correctly; the A1b shuffled weights are distinct from A1; the reward
  preflight (`reward_sanity_table.py`) passes; `humility_reward.py` is byte-for-byte
  identical across arms; the clean SFT / GRPO v2 source lineage is identified.
- **Post-run.** Advantage-signal-density numbers exist for A0/A1/A1b; if training
  ran, each arm has a full SelfAware row in the comparison CSV (truthful, unknown
  recall, unknown answer rate, known over-refusal, correct-on-known, confidence
  coverage/Brier); a run record and session checkpoint are written.
- **Definition of done.** Step 4 reports advantage-signal density per weighting
  (the standalone, no-training result). If training is approved and runs, A1 is
  judged against BOTH A0 (the SFT->GRPO v2 reproduction) and A1b, with the primary
  verdict on known over-refusal at fixed unknown recall.

## Outputs & provenance

- Run records: `experiment/phase1/run_records/`.
- Episodic log: `docs/sessions/` checkpoints via the experiment-runner helper.
- Analysis: rows land in
  `experiment/phase1/eval/analysis/selfaware_full_run_comparison_grouped.csv`
  alongside the Amendment F stacks.
- Meta-analysis: this is exploratory GRPO-arm evidence labeled separately from
  PROTOCOL v0.3, Amendment A, and Amendment E/F headline claims. It does NOT enter
  `meta-analysis/evidence/effects.csv`. The source paper is logged as a v1
  candidate in `meta-analysis/evidence/prisma-flow.md` and ingested in the library.
- Promotion to a launched/reported arm requires the
  `experiment/protocol/amendment-governance.md` 7-point sign-off (a new amendment).

## Variations

- **A0 uniform (control).** Reproduces SFT->GRPO v2; baseline advantage density
  and SelfAware panel.
- **A1 static curiosity.** `w = p_correct * (1 - p_correct)`. The headline arm.
- **A1b shuffled-weight control.** Same weight multiset, permuted. The
  interpretability gate for A1.
- **A2 online moving-frontier.** Recompute per-prompt reward variance every N
  steps and reweight. The closest analog to the paper's online re-planning loop
  and the genuinely novel question (does re-targeting a moving frontier beat a
  static one?). Gated on A1 and on PHASE3 RQ5 controls.
- **V3 coverage-aware resampling (sibling borrow).** The paper's other fix:
  task-uniform resampling so low-density regions are not under-trained. Balance
  the training mix across the difficulty/`p_correct` spectrum rather than only
  known/unknown. Lower risk, applies to SFT/DPO/KTO too, and directly attacks the
  Amendment E scalar-collapse cause (the modal-value target imbalance). Worth
  running as the conservative comparison to curiosity weighting.

## Status log

- 2026-06-26: created (proposed). Originates from the curiosity-reward exploration
  off the 2606.27326 ingest.
- 2026-06-26: reoriented to the post-Amendment-F state after syncing main. GRPO v2
  is the installed composite reward and Amendment F (GRPO-centered stacking) is
  signed; reframed the hypothesis around the live failure mode (high known
  over-refusal plus behavior-insensitive confidence on the clean seed-1 SelfAware
  evals), repointed lineage/comparators/metrics at the clean SFT->GRPO v2 path and
  the Amendment F SelfAware panel, and linked
  `[[grpo-composite-reward-installs-epistemic-output-schema]]`. No runs yet; queued
  for the step-4 diagnostic first.
