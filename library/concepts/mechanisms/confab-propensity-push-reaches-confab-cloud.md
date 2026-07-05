---
aliases:
- confab propensity push reaches the confab cloud
- anti-commitment channel is the only handle with reach (session 0037 wording)
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:confab-propensity-push-reaches-confab-cloud
  type: mechanism
  status: canonical
cause: "Adding a push against the confabulation-propensity direction (region R3 of the radial control law) on top of caution-based steering, in the radial ceiling simulation."
effect: "The only statistically real reach into the confab cloud: propensity permutation p=0.005 at the balanced and aggressive operating points, contributing 21-28 of the kills in both gate constructions (about two-thirds of total reach), while the answer-protecting gate contributes nothing beyond chance (p=1.0). Motivates the ungated anti-propensity control law as the Amendment AL candidate."
polarity: enables
related:
- '[[internal-al-prep-confab-cloud--true-checkpoint]]'
- '[[confabulation-propensity-direction]]'
- '[[confab-cloud]]'
- '[[answer-protecting-gate-shelters-confab-cloud]]'
- '[[confab-propensity-is-not-generic-answer-commitment]]'
relationships:
- type: supported_by
  target: '[[internal-al-prep-confab-cloud--true-checkpoint]]'
  target_id: paper:internal-al-prep-confab-cloud
  confidence: high
- type: related_to
  target: '[[confabulation-propensity-direction]]'
  target_id: term:confabulation-propensity-direction
  confidence: high
- type: related_to
  target: '[[confab-cloud]]'
  target_id: term:confab-cloud
  confidence: high
- type: related_to
  target: '[[answer-protecting-gate-shelters-confab-cloud]]'
  target_id: mechanism:answer-protecting-gate-shelters-confab-cloud
  confidence: high
- type: related_to
  target: '[[confab-propensity-is-not-generic-answer-commitment]]'
  target_id: mechanism:confab-propensity-is-not-generic-answer-commitment
  confidence: high
---

Session-0038 radial ceiling sims (analysis/amendment_al_prep/radial_ceiling_true/
and radial_ceiling_true_gate_meandiff/, TRUE A0 surface). At the balanced
point the R3 propensity push accounts for 28 of 46 oracle kills (logistic
gate) and 21 of 31 (mean-diff gate); the aggressive point gives 28 of 41. The
scope-check finding that the propensity direction is anti-aligned with the
answer-vs-refuse direction explains why this reach comes at low collateral (1
of 90 correct answers at balanced). Simulation-level evidence: oracle and
Bernoulli half-effect kill models, single checkpoint, single seed; the causal
test is the Amendment AL steering run.
