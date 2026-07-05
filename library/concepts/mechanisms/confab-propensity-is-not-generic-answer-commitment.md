---
aliases:
- confab propensity is not generic answer commitment
- the fabricate-vs-refuse direction does not transfer to answerable questions
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:confab-propensity-is-not-generic-answer-commitment
  type: mechanism
  status: canonical
cause: "Fitting the fabricate-vs-refuse direction within unanswerables and the answer-vs-refuse direction within answerables on the same caution-residualized feature space, then testing each on the other population."
effect: "The directions are negatively aligned (cosine -0.35) and neither transfers: at matched caution both cross-population AUROCs are chance (0.46 and 0.51), and raw transfer is inverted (0.30 both ways). The direction that pushes confabulation on unknowns is therefore confabulation-specific, not a generic commitment-to-answer state, and pushing against it is not expected to suppress legitimate answering."
polarity: prevents
related:
- '[[internal-al-prep-confab-cloud--true-checkpoint]]'
- '[[confabulation-propensity-direction]]'
- '[[pre-generation-commitment-signal-predicts-confabulation]]'
- '[[confab-propensity-push-reaches-confab-cloud]]'
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
  target: '[[pre-generation-commitment-signal-predicts-confabulation]]'
  target_id: mechanism:pre-generation-commitment-signal-predicts-confabulation
  confidence: high
- type: related_to
  target: '[[confab-propensity-push-reaches-confab-cloud]]'
  target_id: mechanism:confab-propensity-push-reaches-confab-cloud
  confidence: high
---

Session-0038 scope check (analysis/amendment_al_prep/commitment_scope_check_report.json,
TRUE A0 surface, L24 pre-gen, caution-residualized PCA-128). The "commitment"
name coined in session 0037 carried an untested generality claim: that the
direction encodes commitment to producing an answer as such. On answerable
rows (210 answered vs 114 refused) that reading fails. The in-population
answer-vs-refuse direction is strong (OOF 0.83) but it is a different, weakly
anti-aligned direction. This is favorable for steering: an anti-confabulation
push along the propensity direction is geometrically neutral-to-positive for
answering on answerable questions, consistent with the low collateral observed
in the radial ceiling sims. Single surface, single seed, readout-not-causal.
