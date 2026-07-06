---
aliases:
- confabulation propensity direction
- commitment direction (session 0037 name, deprecated)
- fabricate-vs-refuse axis
- confab pull
tags:
- kg/term
- concept
- term
kg:
  id: term:confabulation-propensity-direction
  type: term
  status: canonical
area: epistemic-humility
related:
- '[[internal-al-prep-confab-cloud--true-checkpoint]]'
- '[[internal-confab-mechanics--cpu-fleet]]'
- '[[pre-generation-commitment-signal-predicts-confabulation]]'
- '[[confab-propensity-is-not-generic-answer-commitment]]'
- '[[confab-cloud]]'
- '[[known-unknown-direction]]'
relationships:
- type: proposed_by
  target: '[[internal-al-prep-confab-cloud--true-checkpoint]]'
  target_id: paper:internal-al-prep-confab-cloud
  confidence: high
- type: related_to
  target: '[[pre-generation-commitment-signal-predicts-confabulation]]'
  target_id: mechanism:pre-generation-commitment-signal-predicts-confabulation
  confidence: high
- type: related_to
  target: '[[confab-propensity-is-not-generic-answer-commitment]]'
  target_id: mechanism:confab-propensity-is-not-generic-answer-commitment
  confidence: high
- type: related_to
  target: '[[confab-cloud]]'
  target_id: term:confab-cloud
  confidence: high
---

The confabulation-propensity direction is the pre-generation activation
direction that predicts which unanswerable question will draw a fabricated
answer rather than a refusal, beyond what the doubt or caution level explains
(AUROC 0.834 on caliper-matched pairs in session 0037, 0.67 to 0.68 as a
caution-residualized mean-diff on the session 0038 TRUE surface). It peaks
mid-network (L24 to L28) and is only weakly aligned with the doubt trunk
(whitened cosine 0.32 to 0.64 decaying with depth).

**Why it matters here:** this is the only readout with statistically real
reach into the [[confab-cloud]] (push permutation p=0.005 in the radial
ceiling sims), so it is the working handle for reducing residual
confabulation, and the axis the Amendment AL control law is keyed on.

**Lineage:** named "commitment direction" in session 0037, when it was only
observed on unanswerable rows and a generic commitment-to-answer reading was
indistinguishable from a confabulation-specific one. The session 0038 scope
check separated the readings on answerable rows and the generic reading lost
(see [[confab-propensity-is-not-generic-answer-commitment]]), so the precise
name is confabulation propensity. The old name survives in session 0037
artifacts and the R3 "anti-commitment" region label of the radial control law.
