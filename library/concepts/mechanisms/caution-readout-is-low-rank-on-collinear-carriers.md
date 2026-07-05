---
aliases:
- caution is a low-rank readout riding on many collinear raw carriers
- the refusal hydra is collinearity, not many independent heads
- rank-one-to-two caution cliff in PCA-128 versus 40-removal survival in raw space
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:caution-readout-is-low-rank-on-collinear-carriers
  type: mechanism
  status: canonical
cause: "Recomputing direction-removal robustness in a label-agnostic randomized PCA-128 basis instead of the raw 2,560-dimensional activation space."
effect: "The caution (refused versus answered) and propensity (confab versus unref) readouts collapse to the permutation floor after one to three direction removals (caution rank one-to-two, AUROC about 0.95 to about 0.60 after the first removal), whereas raw-space removal needed about 40 removals to degrade caution. The apparent many-headedness is the collinearity of many carriers of one low-rank signal, not a population of independent discriminative heads; an ICA head hunt on the caution-residualised space finds zero reproducing candidate heads."
polarity: mediates
related:
- '[[internal-hydra-census-stage1--true-checkpoint]]'
- '[[refusal-hydra-effect]]'
- '[[representational-independence]]'
- '[[flavor-specific-doubt-residuals-persist]]'
- '[[safety-finetuning-low-rank-activation-changes]]'
- '[[known-unknown-direction]]'
- '[[linear-probe]]'
- '[[auroc]]'
- '[[compound-caution-theory]]'
relationships:
- type: supported_by
  target: '[[internal-hydra-census-stage1--true-checkpoint]]'
  target_id: paper:internal-hydra-census-stage1
  confidence: high
- type: related_to
  target: '[[refusal-hydra-effect]]'
  target_id: term:refusal-hydra-effect
  confidence: high
- type: related_to
  target: '[[representational-independence]]'
  target_id: term:representational-independence
  confidence: high
- type: related_to
  target: '[[flavor-specific-doubt-residuals-persist]]'
  target_id: mechanism:flavor-specific-doubt-residuals-persist
  confidence: medium
- type: related_to
  target: '[[safety-finetuning-low-rank-activation-changes]]'
  target_id: mechanism:safety-finetuning-low-rank-activation-changes
  confidence: medium
- type: related_to
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
  confidence: high
- type: related_to
  target: '[[compound-caution-theory]]'
  target_id: term:compound-caution-theory
  confidence: medium
---

The session-0038 Stage 1 census on the Amendment AI TRUE A0 pre-generation
surface (1,662 rows, seed 20260705) found that caution and propensity are each
low-rank discriminative readouts: in PCA-128 space their permutation-controlled
deflation curves are sharp cliffs that hit the null floor after one to three
direction removals at every layer L8 to L36, and an ICA panel on the
caution-residualised space produced zero reproducing candidate heads. This
reconciles with the earlier MI observation that caution survives about 40
removals in the raw 2,560-dimensional space: those 40 near-degenerate carriers
are collinear projections of one signal, so peeling them one at a time only
removes thin slivers. The correct unified statement is that caution and refusal
form a low-rank readout riding on many collinear carriers in the native basis,
not a many-headed compound of independent discriminative axes; doubt reads as a
correlate of that readout rather than a separable removable element.
</content>
</invoke>
