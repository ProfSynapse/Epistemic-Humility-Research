---
aliases:
- Pre-generation commitment signal predicts confabulation
- activations predict fabricate-vs-refuse beyond the caution threshold
- pre-generation confabulation-propensity signal (session 0038 name)
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:pre-generation-commitment-signal-predicts-confabulation
  type: mechanism
  status: canonical
cause: "Matching confabulating and refusing rows 1-to-1 on caution boundary distance within each unanswerability flavor (removing the threshold explanation), then probing the pre-generation activations."
effect: "The activations still predict which row will confabulate at AUROC 0.834 plus-minus 0.014 (permutation p=0.0099), beating a TF-IDF text baseline by +0.215; the direction is only 0.32 whitened-cosine aligned with the doubt trunk and the signal peaks mid-network (L24-28) then plateaus: a commitment-to-answer state exists before generation, beyond the doubt level."
polarity: enables
related:
- '[[internal-confab-mechanics--cpu-fleet]]'
- '[[refusal-threshold-varies-by-unanswerability-flavor]]'
- '[[known-unknown-direction]]'
- '[[scalar-readout-compression-mimics-second-mechanism]]'
- '[[hidden-state-linearly-encodes-unanswerability-despite-hallucination]]'
- '[[question-familiarity-draws-confabulation-at-matched-doubt]]'
- '[[confabulation-propensity-direction]]'
- '[[confab-propensity-is-not-generic-answer-commitment]]'
relationships:
- type: supported_by
  target: '[[internal-confab-mechanics--cpu-fleet]]'
  target_id: paper:internal-confab-mechanics
  confidence: high
- type: related_to
  target: '[[refusal-threshold-varies-by-unanswerability-flavor]]'
  target_id: mechanism:refusal-threshold-varies-by-unanswerability-flavor
  confidence: high
- type: related_to
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
  confidence: high
- type: related_to
  target: '[[scalar-readout-compression-mimics-second-mechanism]]'
  target_id: mechanism:scalar-readout-compression-mimics-second-mechanism
  confidence: medium
- type: related_to
  target: '[[hidden-state-linearly-encodes-unanswerability-despite-hallucination]]'
  target_id: mechanism:hidden-state-linearly-encodes-unanswerability-despite-hallucination
  confidence: medium
- type: related_to
  target: '[[question-familiarity-draws-confabulation-at-matched-doubt]]'
  target_id: mechanism:question-familiarity-draws-confabulation-at-matched-doubt
  confidence: high
- type: related_to
  target: '[[confabulation-propensity-direction]]'
  target_id: term:confabulation-propensity-direction
  confidence: high
- type: related_to
  target: '[[confab-propensity-is-not-generic-answer-commitment]]'
  target_id: mechanism:confab-propensity-is-not-generic-answer-commitment
  confidence: high
---

Session-0037 arm B
(experiments/confab-mechanics-cpu-fleet/analysis-committed/confab-signature/).
The null model first
confirms threshold dominance: the caution scalar alone separates confab from refusal
at 0.939. The matched design then shows the scalar is not the whole story. On 328
caliper-matched rows (post-match scalar AUROC 0.528, so the threshold explanation is
removed), a pre-generation probe reads fabricate-vs-refuse at 0.834, replicating on
the full 1,338-row population (0.83) and winning all 10 paired folds against text
and familiarity baselines. The mid-network peak argues against terminal decision
leakage, and the raw trunk projection still reads 0.694 after scalar matching, the
mirror of the item-22a lesson: the 1-D scalar compresses away part of the geometry.
Single surface, single seed, readout-not-causal evidence.
