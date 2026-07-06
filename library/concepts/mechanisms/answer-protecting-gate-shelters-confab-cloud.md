---
aliases:
- answer-protecting gate shelters the confab cloud
- gate blind spot is robust to gate construction
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:answer-protecting-gate-shelters-confab-cloud
  type: mechanism
  status: canonical
cause: "Thresholding any answerability or knowledge-boundary readout so that correct answers are protected (collateral tolerance about 1 of 90 correct rows), as in the gated radial control law."
effect: "Residual confabulations sit above the threshold and are sheltered from the intervention: the real gate reaches FEWER confabs than a permuted gate at every operating point (permutation p=1.0), for both a logistic answerability gate (AUROC 0.94) and a clean-cell mean-diff gate that separates correct-vs-confab at 0.926 in the bulk. The binding constraint is tail overlap: the least-confident correct answers live inside the confab cloud, so bulk AUROC does not buy low-collateral reach."
polarity: prevents
related:
- '[[internal-al-prep-confab-cloud--true-checkpoint]]'
- '[[confab-cloud]]'
- '[[hidden-state-linearly-encodes-unanswerability-despite-hallucination]]'
- '[[confab-propensity-push-reaches-confab-cloud]]'
relationships:
- type: supported_by
  target: '[[internal-al-prep-confab-cloud--true-checkpoint]]'
  target_id: paper:internal-al-prep-confab-cloud
  confidence: high
- type: related_to
  target: '[[confab-cloud]]'
  target_id: term:confab-cloud
  confidence: high
- type: related_to
  target: '[[hidden-state-linearly-encodes-unanswerability-despite-hallucination]]'
  target_id: mechanism:hidden-state-linearly-encodes-unanswerability-despite-hallucination
  confidence: medium
- type: related_to
  target: '[[confab-propensity-push-reaches-confab-cloud]]'
  target_id: mechanism:confab-propensity-push-reaches-confab-cloud
  confidence: high
---

Session-0038 radial ceiling sims on the TRUE A0 surface
(analysis/amendment_al_prep/radial_ceiling_true/ and
radial_ceiling_true_gate_meandiff/). Baseline 90 correct, 1222 refused, 116
confabs. With the logistic gate the balanced point kills 46 of 116 confabs at
1 collateral; with the mean-diff gate only 31; in both, gate permutation gives
p=1.0 because a random gate exposes more of the cloud than a real one. The
blind spot is therefore a property of answer-protecting gating as a control
strategy on this surface, not of any particular gate construction, and it
motivates the ungated control-law variant keyed directly on the
confabulation-propensity direction. Simulation-level evidence (oracle and
Bernoulli half-effect kills, not actual steering runs).
