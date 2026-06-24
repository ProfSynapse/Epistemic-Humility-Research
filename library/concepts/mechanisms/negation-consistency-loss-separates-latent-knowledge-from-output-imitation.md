---
aliases:
- CCS consistency constraint
- negation-consistency probing
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:negation-consistency-loss-separates-latent-knowledge-from-output-imitation
  type: mechanism
  status: canonical
cause: "Training a linear probe on contrast pairs with a negation-consistency loss plus confidence loss, applied to normalized hidden states"
effect: "The probe recovers a truth-correlated activation direction that remains stable even when model outputs are misled by an incorrect-answer prefix"
polarity: enables
related:
- '[[2212.03827--ccs-discovering-latent-knowledge]]'
- '[[contrast-consistent-search]]'
- '[[truth-direction]]'
- '[[generation-discrimination-gap]]'
- '[[contrastive-representation-clustering]]'
relationships:
- type: supported_by
  target: '[[2212.03827--ccs-discovering-latent-knowledge]]'
  target_id: paper:2212.03827
  confidence: high
- type: related_to
  target: '[[contrast-consistent-search]]'
  target_id: method:contrast-consistent-search
  confidence: high
- type: related_to
  target: '[[truth-direction]]'
  target_id: term:truth-direction
  confidence: high
- type: related_to
  target: '[[generation-discrimination-gap]]'
  target_id: term:generation-discrimination-gap
  confidence: high
- type: related_to
  target: '[[contrastive-representation-clustering]]'
  target_id: method:contrastive-representation-clustering
  confidence: high
---

CCS forms contrast pairs by answering each question as both Yes and No, normalizes the hidden states for each polarity independently to remove surface differences, then optimizes a probe to satisfy two constraints: (1) p(x+) + p(x-) = 1 (negation consistency) and (2) min(p(x+), p(x-))^2 is small (confidence). This dual constraint steers the probe away from degenerate solutions and toward the truth-discriminating direction in activation space. Empirically, when model outputs are disrupted by a misleading prefix (causing calibrated zero-shot to drop 9.5 pp on UnifiedQA), the CCS probe accuracy is unchanged, confirming that the recovered direction is distinct from and more robust than the output distribution.
