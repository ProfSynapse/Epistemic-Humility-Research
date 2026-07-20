---
title: correctness-direction-rotation
aliases:
- 'Correctness-direction rotation across training stages'
- CD rotation cell
- correctness dial rotation instrument diagnostic
tags:
- kg/experiment
- experiment
- correctness-readout
kg:
  id: experiment:correctness-direction-rotation
  type: experiment
  status: canonical
related:
- '[[internal--diag-item9-caution-assembly-timeline]]'
- '[[sft-rotates-boundary-readout-rl-rides-it]]'
- '[[per-answer-correctness-linearly-readable-post-generation]]'
- '[[answerability-and-correctness-are-orthogonal-readout-axes]]'
- '[[known-unknown-direction]]'
- '[[correctness-direction-weakly-identified-defeats-cosine-rotation-probe]]'
relationships:
- type: builds_on
  target: '[[internal--diag-item9-caution-assembly-timeline]]'
  target_id: paper:internal-diag-item9
  confidence: high
  evidence:
  - experiments/correctness-direction-rotation/AMENDMENT.md (Design, Method;
    mirrors diag_item9_caution_timeline.py's four-stage shared-PCA-128-on-raw
    protocol, same checkpoints pinned by A3)
- type: tests
  target: '[[sft-rotates-boundary-readout-rl-rides-it]]'
  target_id: mechanism:sft-rotates-boundary-readout-rl-rides-it
  confidence: high
  evidence:
  - experiments/correctness-direction-rotation/AMENDMENT.md (Motivation and
    posture, Prediction, Outcome; tests whether the answerability direction's
    one-rotation-at-SFT-then-stable account extends to the correctness
    direction)
- type: related_to
  target: '[[per-answer-correctness-linearly-readable-post-generation]]'
  target_id: mechanism:per-answer-correctness-linearly-readable-post-generation
  confidence: high
  evidence:
  - experiments/correctness-direction-rotation/AMENDMENT.md (Design, Method
    step 1; probes the same post-generation correctness dial at its native
    readout position)
- type: related_to
  target: '[[answerability-and-correctness-are-orthogonal-readout-axes]]'
  target_id: mechanism:answerability-and-correctness-are-orthogonal-readout-axes
  confidence: medium
  evidence:
  - experiments/correctness-direction-rotation/AMENDMENT.md (Motivation and
    posture; contrasts the correctness dial's own cross-stage rotation
    behavior against the separately-tracked answerability axis)
- type: related_to
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
  confidence: medium
  evidence:
  - experiments/correctness-direction-rotation/AMENDMENT.md (Design; reuses
    the raw-basis PCA-128 shared basis built for the known-unknown/answerability
    diagnostic)
- type: supports
  target: '[[correctness-direction-weakly-identified-defeats-cosine-rotation-probe]]'
  target_id: mechanism:correctness-direction-weakly-identified-defeats-cosine-rotation-probe
  confidence: high
  evidence:
  - experiments/correctness-direction-rotation/AMENDMENT.md#outcome (Outcome,
    Post-hoc interpretation and Caveats)
---

Probe-fit cell asking whether the correctness (dial) direction rotates across
training the way the answerability direction does: one near-orthogonal
rotation at instruction SFT, then stability through both GRPO stages
(the diag-item9 answerability-rotation diagnostic,
[[internal--diag-item9-caution-assembly-timeline]]). Four checkpoints (raw
base, clean-SFT, GRPO-v2, GRPO-par-true) were each probed for a per-stage
correctness (correct-vs-wrong) direction in a shared PCA-128 basis fit once
on the raw stage, method-identical to the answerability diagnostic except
that correctness is stage-dependent: each checkpoint generated its own
forced-best-guess answers, graded per stage, giving each stage its own
population and its own fitted direction. A pre-registered split-half control
on the grpov2 stage bounds within-stage identifiability noise.

Resolved 2026-07-20 (null-result), adjudicated after adversarial red-team
review (8 findings, no blockers). CD-G0 (data adequacy) and CD-G2 (readout
sanity, best-layer OOF AUROC 0.809-0.860 across all four stages) both
passed. CD-G1 (rotation-confirmed) did not meet its conjunction: the
raw->cleansft cosine (0.192) is low, but the later transitions
(cleansft->grpov2 0.449, grpov2->partrue 0.330) sit far below the 0.85
stability floor the answerability diagnostic's GRPO stages cleared, so the
"then stable" half of the pattern is absent. The pre-registered falsifier
(raw->cleansft >= 0.80) did not fire either, so both pre-stated readings are
exhausted without a positive determination.

The post-hoc reading (explicitly not pre-registered): the within-stage
split-half control returns a noise floor of 0.174, meaning the correctness
direction is only weakly identified by this probe. Best-layer AUROC is
stable near 0.80-0.86 across stages while the fitted hyperplane normal is
not, in the same raw-basis PCA-128 construction where the answerability
diagnostic reached cross-stage cosines >= 0.96. The cosine-rotation
instrument therefore cannot discriminate genuine directional rotation from
identifiability noise for the correctness direction at these sample sizes,
detailed in
[[correctness-direction-weakly-identified-defeats-cosine-rotation-probe]].
The answerability-style single-rotation-at-SFT account is neither confirmed
nor falsified for correctness, and the mechanism behind the dial's 0.679
cross-checkpoint cold transfer
(`experiments/correctness-readout-deployment-port/AMENDMENT.md`, section 7)
stays open.

Predictions scoreboard: the orchestrator's pre-registered call (partial
rotation, raw->cleansft cosine 0.3-0.6, later transitions >= 0.85) was wrong
on both counts: the observed raw->cleansft cosine (0.192) fell below the
predicted band and the later transitions fell far below the predicted
floor. Exploratory Tier-2 evidence, reported separately from and never
pooled with the locked Phase 1 headline matrix. Source of truth:
`experiments/correctness-direction-rotation/AMENDMENT.md`, Outcome section,
resolved 2026-07-20.
