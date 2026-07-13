---
title: 'The Confab Cloud: Gate Blind Spot, Familiarity-vs-Knowing, and the Confabulation-Propensity Handle (session 0038 AL prep, TRUE checkpoint)'
tags:
- kg/paper
- paper
- epistemic-humility
- internal
kg:
  id: paper:internal-al-prep-confab-cloud
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
- qwen3-4b
metrics:
- auroc
fulltext: ../../docs/sessions/20260705T090000Z-amendment-ai-null-verdict-al-prep-true-internals.md
provenance: 'Internal exploratory synthesis (Tier-1 lab notebook, not a paper draft). Source of truth: docs/sessions/20260705T090000Z-amendment-ai-null-verdict-al-prep-true-internals.md plus analysis/amendment_al_prep/ (doubt_axis_check_report.json, radial_ceiling_true/, radial_ceiling_true_gate_meandiff/, familiarity_vs_knowing_report.json, commitment_scope_check_report.json). Surface: AL-prep A0 pre-generation full-stack extracts (L0-L36) on the Amendment AI TRUE-mapping GRPO checkpoint (clean-SFT base), 1662 rows, single seed. Scripts committed on branch amendment-al-radial-steering. Ungated exploratory evidence feeding the Amendment AL control-law design.'
related:
- '[[confab-cloud]]'
- '[[confabulation-propensity-direction]]'
- '[[answer-protecting-gate-shelters-confab-cloud]]'
- '[[confab-boundary-elevation-lacks-knowledge-signal]]'
- '[[text-surface-form-predicts-boundary-elevation]]'
- '[[confab-propensity-is-not-generic-answer-commitment]]'
- '[[confab-propensity-push-reaches-confab-cloud]]'
- '[[pre-generation-commitment-signal-predicts-confabulation]]'
- '[[question-familiarity-draws-confabulation-at-matched-doubt]]'
- '[[known-unknown-direction]]'
- '[[unanswerable-questions]]'
- '[[linear-probe]]'
- '[[auroc]]'
- '[[internal-confab-mechanics--cpu-fleet]]'
relationships:
- type: proposes
  target: '[[confab-cloud]]'
  target_id: term:confab-cloud
  confidence: high
- type: proposes
  target: '[[confabulation-propensity-direction]]'
  target_id: term:confabulation-propensity-direction
  confidence: high
- type: supports
  target: '[[answer-protecting-gate-shelters-confab-cloud]]'
  target_id: mechanism:answer-protecting-gate-shelters-confab-cloud
  confidence: high
- type: supports
  target: '[[confab-boundary-elevation-lacks-knowledge-signal]]'
  target_id: mechanism:confab-boundary-elevation-lacks-knowledge-signal
  confidence: high
- type: supports
  target: '[[text-surface-form-predicts-boundary-elevation]]'
  target_id: mechanism:text-surface-form-predicts-boundary-elevation
  confidence: high
- type: supports
  target: '[[confab-propensity-is-not-generic-answer-commitment]]'
  target_id: mechanism:confab-propensity-is-not-generic-answer-commitment
  confidence: high
- type: supports
  target: '[[confab-propensity-push-reaches-confab-cloud]]'
  target_id: mechanism:confab-propensity-push-reaches-confab-cloud
  confidence: high
- type: related_to
  target: '[[pre-generation-commitment-signal-predicts-confabulation]]'
  target_id: mechanism:pre-generation-commitment-signal-predicts-confabulation
  confidence: high
- type: related_to
  target: '[[question-familiarity-draws-confabulation-at-matched-doubt]]'
  target_id: mechanism:question-familiarity-draws-confabulation-at-matched-doubt
  confidence: high
- type: studies
  target: '[[unanswerable-questions]]'
  target_id: term:unanswerable-questions
  confidence: high
- type: studies
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
  confidence: high
- type: uses
  target: '[[linear-probe]]'
  target_id: method:linear-probe
  confidence: high
- type: measures
  target: '[[auroc]]'
  target_id: metric:auroc
  confidence: high
- type: related_to
  target: '[[internal-confab-mechanics--cpu-fleet]]'
  target_id: paper:internal-confab-mechanics
  confidence: high
---

## Summary

Session-0038 CPU analyses on the Amendment AI TRUE checkpoint's A0 surface
(1662 questions, full-stack pre-generation extracts), preparing the Amendment
AL radial-steering control law. The composite picture: the checkpoint's 116
residual confabulations form a compact region (the confab cloud) that is
mildly elevated on the knowledge-boundary axis without any actually-knowing
signal behind it; every answer-protecting gate shelters that region rather
than carving it out, robustly across gate constructions; the one channel with
statistically real reach is the confabulation-propensity direction, which a
scope check shows is confabulation-specific rather than a generic
commitment-to-answer state. Net design consequence: Amendment AL should key
its control law on the propensity direction directly (ungated variant) rather
than gating on answerability.

## Claims

- Evidence label: radial ceiling simulation with permutation nulls (logistic
  gate). Baseline 90 correct / 1222 refused / 116 confabs; the zero-collateral
  point is infeasible (3 of 116, half-effect CI includes zero); the balanced
  point kills 46 of 116 at 1 collateral, with gate permutation p=1.0 and
  propensity-push permutation p=0.005 (28 of 46 kills R3-unique).
- Evidence label: gate-construction robustness rerun. A clean-cell mean-diff
  gate separates correct-vs-confab at AUROC 0.926 in the bulk yet reaches
  FEWER confabs at the same collateral (31 vs 46, gate permutation still
  p=1.0): the blind spot is tail overlap, not gate quality.
- Evidence label: two-axis decomposition. Doubt-axis population means run
  correct 2.22, wrong 1.55, confab 0.34, answerable-refused 0.08,
  unanswerable-refused -0.35; on an actually-knowing axis (correct-vs-wrong
  OOF 0.68) confabs read -0.13, at refusal level (0.46 AUROC vs refusals).
- Evidence label: familiarity residualization. Text-surface features soak part
  of the confab boundary elevation (0.84 to 0.68-0.70); the internal
  familiarity direction explains none of it (0.84 to 0.83) and familiarity
  alone is at chance unmatched (0.51), refining the session-0037 matched-doubt
  familiarity result on this trained checkpoint.
- Evidence label: propensity scope check. The fabricate-vs-refuse direction
  (within unanswerables) and the answer-vs-refuse direction (within
  answerables) are negatively aligned (cosine -0.35) and mutually
  non-transferable (matched-caution cross-AUROCs 0.46 and 0.51; raw transfer
  inverted at 0.30), so the direction formerly named "commitment" is
  confabulation-specific.
- Evidence label: axis-transfer check. Reference doubt/caution axes from the
  GRPO-v2 surface transfer weakly to this checkpoint (0.68/0.65, direction
  cosine 0.17/0.05), while TRUE and PERMUTED arm-local axes are near-identical
  (cosine 0.988/0.967/0.946): refit-per-checkpoint holds, and the reward
  mapping does not rotate the local geometry.

## Relevance to experiment

Fixes the Amendment AL control-law choice: the gated radial law inherits a
structural blind spot on this surface, so the registered candidate becomes the
ungated anti-propensity push, with honest gates sized by the aim-small rule
from the ceiling table (balanced point: collateral max 3, at least +3 honest
refusals, at least 3 confabs killed). Also renames the session-0037
"commitment" direction to confabulation propensity on scope-check evidence.
Caveats: simulation-level kill models (oracle and Bernoulli half-effect), one
checkpoint, one seed, readout-not-causal throughout; the causal test is the
AL steering run itself.
