---
title: 'Radial Anti-Propensity Steering Is a Use-the-Signal Null in the Injection Channel (Amendment AL, TRUE checkpoint)'
tags:
- kg/paper
- paper
- epistemic-humility
- internal
kg:
  id: paper:internal-al-injection-null
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
provenance: 'Internal amendment (Tier-A causal intervention). Source of truth: experiment/protocol/AMENDMENT-AL-radial-anti-propensity-steering.md (merged PR #214 to main). Surface: the session-0038 AL-prep A0 TRUE-mapping GRPO checkpoint surface (1,662 rows: 90 correct, 120 wrong, 114 answerable-refused, 1,222 unanswerable-refused, 116 confabs). Steering: subtract alpha times the raw-space preimage of the L24 caution-residualized confabulation-propensity direction (PCA-128 randomized seed 20260705) from the residual stream at layer 24, pre-generation anchor onward, selected rows only. Grading commits fa82c629 / 7b4be949 / e9141fff. Ungated exploratory evidence, never pooled with the locked headline matrix.'
related:
- '[[propensity-direction-reads-but-does-not-actuate-fabrication]]'
- '[[confabulation-propensity-direction]]'
- '[[confab-propensity-push-reaches-confab-cloud]]'
- '[[confab-propensity-is-not-generic-answer-commitment]]'
- '[[pre-generation-commitment-signal-predicts-confabulation]]'
- '[[internal-al-prep-confab-cloud--true-checkpoint]]'
- '[[activation-steering]]'
- '[[unanswerable-questions]]'
- '[[linear-probe]]'
- '[[auroc]]'
- '[[internal-ai-probe-as-reward-null--true-vs-permuted]]'
- '[[internal-ac-doubt-regulated-caution--coupled-write]]'
- '[[internal-aa-causal-confidence-steering-null--qwen3.5-4b]]'
- '[[internal-ab-first-person-injection--ambiguous-negative]]'
relationships:
- type: supports
  target: '[[propensity-direction-reads-but-does-not-actuate-fabrication]]'
  target_id: mechanism:propensity-direction-reads-but-does-not-actuate-fabrication
  confidence: high
- type: studies
  target: '[[confabulation-propensity-direction]]'
  target_id: term:confabulation-propensity-direction
  confidence: high
- type: related_to
  target: '[[confab-propensity-push-reaches-confab-cloud]]'
  target_id: mechanism:confab-propensity-push-reaches-confab-cloud
  confidence: high
- type: related_to
  target: '[[confab-propensity-is-not-generic-answer-commitment]]'
  target_id: mechanism:confab-propensity-is-not-generic-answer-commitment
  confidence: high
- type: related_to
  target: '[[pre-generation-commitment-signal-predicts-confabulation]]'
  target_id: mechanism:pre-generation-commitment-signal-predicts-confabulation
  confidence: high
- type: related_to
  target: '[[internal-al-prep-confab-cloud--true-checkpoint]]'
  target_id: paper:internal-al-prep-confab-cloud
  confidence: high
- type: uses
  target: '[[activation-steering]]'
  target_id: method:activation-steering
  confidence: high
- type: uses
  target: '[[linear-probe]]'
  target_id: method:linear-probe
  confidence: high
- type: studies
  target: '[[unanswerable-questions]]'
  target_id: term:unanswerable-questions
  confidence: high
- type: measures
  target: '[[auroc]]'
  target_id: metric:auroc
  confidence: high
- type: related_to
  target: '[[internal-ai-probe-as-reward-null--true-vs-permuted]]'
  target_id: paper:internal-ai-probe-as-reward-null
  confidence: medium
- type: related_to
  target: '[[internal-ac-doubt-regulated-caution--coupled-write]]'
  target_id: paper:internal-ac-doubt-regulated-caution
  confidence: medium
- type: related_to
  target: '[[internal-aa-causal-confidence-steering-null--qwen3.5-4b]]'
  target_id: paper:internal-aa-causal-confidence-steering-null
  confidence: medium
- type: related_to
  target: '[[internal-ab-first-person-injection--ambiguous-negative]]'
  target_id: paper:internal-ab-first-person-injection
  confidence: medium
---

## Summary

Amendment AL is the causal test of the confabulation-propensity handle that the
session-0038 AL-prep synthesis proposed (see
[[internal-al-prep-confab-cloud--true-checkpoint]]). On the Amendment AI
TRUE-mapping checkpoint, it subtracts the raw-space preimage of the L24
caution-residualized propensity direction from the residual stream at generation
time, on rows whose baseline propensity z-score exceeds the pre-registered
threshold, and asks whether pushed confabulations convert into refusals. They do
not. The push moves the internal propensity readout by exactly the commanded
amount yet does not change the fabricate-vs-refuse choice, so the direction is a
sensor that reads confabulation rather than an actuator that controls it. This is
the sixth use-the-signal null in the research program and the first on the write
side (activation injection); the five prior nulls asked the model to consult its
own readout, whereas AL directly injected the direction and still moved no
behavior. The propensity direction joins the correlate pile as a control handle,
and the write-side steering line needs a different lever. This null is scoped to
the confabulation-propensity axis on the Amendment AI TRUE-mapping checkpoint; it
sits alongside sibling nulls on other axes and write-forms
([[internal-aa-causal-confidence-steering-null--qwen3.5-4b]],
[[internal-ab-first-person-injection--ambiguous-negative]],
[[internal-ai-probe-as-reward-null--true-vs-permuted]]) and against the program's
standing write-side win, [[internal-ac-doubt-regulated-caution--coupled-write]],
which succeeded on a different axis and checkpoint.

## Claims

- Evidence label: pre-registered honesty-floor gate (AL-G1). At most 3 of the 90
  baseline-correct rows were allowed to flip to refusal in the primary arm; 0
  flipped, so AL-G1 PASS. (experiment/protocol/AMENDMENT-AL-radial-anti-propensity-steering.md,
  merged PR #214; grading commits fa82c629 / 7b4be949 / e9141fff.)
- Evidence label: pre-registered reach gate (AL-G2). At least 5 of the 116
  baseline confabulations had to be killed in the primary arm; 0 were killed, so
  AL-G2 MISS. The descriptive dose ladder on the pushed rows (0.5x / 1.0x / 2.0x)
  killed 0 / 0 / 1 of 30 pushed confabs, so even at double the calibrated dose the
  reach is essentially nil. (same amendment doc + grading commits.)
- Evidence label: pre-registered specificity gate (AL-G3). Primary-arm kills
  minus control-arm (permuted-assignment) kills had to be at least 5 with a
  1,000-resample row bootstrap 95% CI excluding zero; the observed difference is 0
  with bootstrap CI [0.00, 0.00], so AL-G3 MISS. (same amendment doc + grading
  commits.)
- Evidence label: injection-verification instrumentation (separates actuation
  failure from injection failure). On pushed rows the propensity projection at the
  steered anchor moved -2.7133 against a commanded -2.7110 (readback ratio 1.0008);
  on unpushed rows the shift was exactly 0.0000 and all 1,564 unpushed rows
  reproduced their baseline grade (1564/1564 parity). The injection landed
  precisely, so the null is causal rather than an instrumentation artifact: moving
  the readout by the commanded amount does not move the behavior (supports
  [[propensity-direction-reads-but-does-not-actuate-fabrication]]).
- Caveats: single checkpoint (Amendment AI TRUE-mapping GRPO on a clean-SFT base,
  Qwen3-4B), single seed; readout-plus-injection evidence on one operating point.
  A gated-logistic secondary arm ran and is reported separately per the amendment
  doc, never pooled with this primary claim. Exploratory lab-notebook evidence,
  reported separately from and never pooled with the locked headline matrix.
</content>
</invoke>
