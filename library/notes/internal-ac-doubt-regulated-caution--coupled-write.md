---
title: 'Doubt-Regulated Caution: A Closed-Loop Erase-and-Write on caution_perp Actuates Selective Refusal Release (Amendment AC)'
tags:
- kg/paper
- paper
- epistemic-humility
- internal
kg:
  id: paper:internal-ac-doubt-regulated-caution
  type: paper
  status: canonical
year: 2026
area: epistemic-humility
status: lab-notebook
source: internal
source_kind: epistemic-humility-research-program
authors:
- Joseph Rosenbaum (Synaptic Labs)
models:
- clean-sft-grpo-v2-seed1
metrics:
- auroc
provenance: 'Internal amendment (Tier-2 exploratory local mechanism evidence under mechinterp-control-system-protocol.md, RQ4 Stage 1). Source of truth: experiments/doubt-regulated-caution/AMENDMENT.md. Checkpoint: clean-SFT -> GRPO-v2 seed1. Rows: frozen behavior overlay analysis/current_selfaware_behavior_rows/clean_sft_grpo_v2/rows.jsonl, cells known_refused (n=168), known_correct_answered (n=373), unknown_refused (n=676), 4868 units across 4 arms. Analysis: analyze_ac_doubt_coupled.py, paired row-level bootstrap, 10k resamples, seed 20260703.'
related:
- '[[ku-readout-coupling-actuates-selective-refusal-release]]'
- '[[caution-residual-ablation-relaxes-overrefusal-asymmetrically]]'
- '[[activation-steering]]'
- '[[known-unknown-direction]]'
- '[[residual-stream]]'
relationships:
- type: supports
  target: '[[ku-readout-coupling-actuates-selective-refusal-release]]'
  target_id: mechanism:ku-readout-coupling-actuates-selective-refusal-release
  confidence: high
- type: related_to
  target: '[[caution-residual-ablation-relaxes-overrefusal-asymmetrically]]'
  target_id: mechanism:caution-residual-ablation-relaxes-overrefusal-asymmetrically
  confidence: medium
- type: uses
  target: '[[activation-steering]]'
  target_id: method:activation-steering
  confidence: high
- type: studies
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
  confidence: medium
- type: related_to
  target: '[[residual-stream]]'
  target_id: term:residual-stream
  confidence: medium
---

## Summary

Amendment AC asks the narrowest causal version of the closed-loop question: on
a checkpoint where the caution gate is causally real but fires largely
independent of doubt (65%+ over-refusal on known items), does making the gate
a live function of the frozen doubt readout carry information beyond simply
deleting the gate? At L35 of clean-SFT -> GRPO-v2 seed1, AC erases the model's
own caution-perp projection and writes a doubt-proportional setpoint instead
(`h' = h - (h . c_hat) c_hat + g_i * sigma_c * c_hat`, with `g_i = -alpha *
z_i` the standardized doubt readout, alpha = 1, clipped to [-2, +2]), and
compares this coupled arm against a permuted-gain control (same gain
distribution, doubt information shuffled across rows) and a constant-ablate
control (`g == 0`). The coupled arm beats the permuted control on a
known-vs-unknown selectivity gap by a margin that clears the pre-registered
gate. This is the first use-the-signal win in the research program after
Amendments M, N, R, and AA (Arm A) all returned nulls: the frozen doubt
readout, written back into the residual stream through this coupling, causally
determines the fabricate-vs-refuse choice, not merely correlates with it.

## Claims

- Evidence label: pre-registered primary gate (AC-G1). Coupled beats permuted
  on the known-vs-unknown selectivity gap (de-refusal on known_refused minus
  de-refusal on unknown_refused, relative to the baseline arm's refusal rate)
  by **+8.7 points, 10k-resample row-level bootstrap 95% CI [+5.6, +12.0]**
  (>= 5pt required, CI excludes 0). PASS. Per-arm selectivity gap: coupled
  +0.068 (kr refusal 0.994->0.506, ur refusal 1.000->0.580); permuted -0.019
  (kr 0.994->0.518, ur 1.000->0.504); constant-ablate -0.039 (kr 0.994->0.536,
  ur 1.000->0.503). (experiments/doubt-regulated-caution/AMENDMENT.md
  section 8.)
- Evidence label: secondary estimate, no gate (AC-G2). Coupled beats constant
  ablate on the same selectivity gap by +10.7 points, CI [+7.1, +14.5]. The
  coupling's edge is specifically on the unknown side: it preserves
  unknown_refused refusal (0.580) where permuted and constant-ablate release
  it indiscriminately (0.504 / 0.503), while matching their known_refused
  release; de-refused correctness is flat across arms (coupled 0.675, permuted
  0.704, constant-ablate 0.705). The doubt signal decides WHICH rows get
  released, not how well the released rows are answered.
- Evidence label: specificity guard (pass/fail). known_correct_answered
  refusal rise -0.3 points (<= 5pt threshold) and correctness drop 2.4 points
  (<= 3pt threshold, close but under). PASS.
- Evidence label: falsifier check. The pre-stated falsifier (permuted approx
  coupled, margin < 5pt or CI includes 0) did not fire. In-frame constant-
  ablate replication held against the prior refined-B1 measurement
  (known_refused refusal 0.994 -> 0.536 here vs 0.994 -> 0.524 in refined B1).
- Caveats: single layer (L35), single checkpoint (clean-SFT -> GRPO-v2 seed1),
  greedy decoding, per-item (not per-token) open-loop gains fit and evaluated
  on the same frozen row population. A pass licenses a mechanism claim on this
  checkpoint and row set, not a deployable controller; a held-out transfer or
  a per-token online controller is Stage-2 material requiring a new signed
  amendment. Exploratory lab-notebook evidence, reported separately from and
  never pooled with the locked headline matrix.

## Relevance to experiment

AC is the standing write-side counterexample against any framing that treats
activation-level writes as uniformly null on this research program's
checkpoints: five prior use-the-signal attempts (M, N, R, and AA's activation
Arm A) had all asked the model to consult a readout through some symbolic or
trained channel and failed; AC instead erases and directly replaces the
caution-perp projection with a doubt-proportional setpoint at generation time,
and that specific write-form succeeds. The later injection nulls in this
family (Amendments AA, AB, AL, AI; see
[[trust-axis-injection-does-not-move-answer-abstain-revise-behavior]],
[[first-person-framed-probe-score-injection-does-not-open-text-channel]],
[[propensity-direction-reads-but-does-not-actuate-fabrication]],
[[probe-agreement-reward-does-not-couple-policy-to-its-own-readout]]) must be
scoped against AC, not read as a general claim that write-side activation
edits fail: the failing channels are additive steering of a probe direction,
CoT text injection, radial subtraction against a caution-residualized
propensity direction, and reward-channel training, each on a different axis
and population; AC's erase-and-write on caution_perp, on the doubt axis, on
this checkpoint, is the one that actuates.
