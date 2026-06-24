---
aliases:
- cascading inference
- abstention-triggered cascade
- risk-tolerance cascade
tags:
- kg/method
- concept
- method
kg:
  id: method:abstention-cascading
  type: method
  status: canonical
area: methods
related:
- '[[2511.11500--reinforced-hesitation]]'
- '[[reinforced-hesitation]]'
- '[[abstention]]'
- '[[best-of-n-sampling]]'
- '[[self-consistency]]'
- '[[reward-uncertainty-induces-calibrated-behavioral-diversity]]'
relationships:
- type: proposed_by
  target: '[[2511.11500--reinforced-hesitation]]'
  target_id: paper:2511.11500
  confidence: high
- type: related_to
  target: '[[reinforced-hesitation]]'
  target_id: method:reinforced-hesitation
  confidence: medium
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: medium
- type: related_to
  target: '[[best-of-n-sampling]]'
  target_id: method:best-of-n-sampling
  confidence: medium
- type: related_to
  target: '[[self-consistency]]'
  target_id: method:self-consistency
  confidence: medium
- type: related_to
  target: '[[reward-uncertainty-induces-calibrated-behavioral-diversity]]'
  target_id: mechanism:reward-uncertainty-induces-calibrated-behavioral-diversity
  confidence: medium
---

An inference strategy that routes queries through a sequence of models trained with decreasing risk-tolerance penalties (e.g., lambda=10, 5, 2, 1, 0), where each model's abstention triggers delegation to the next less conservative specialist via early exit. A five-tier cascade of RH-trained models achieves 88.1% accuracy with only 2.2 average queries.

**Why it matters here:** Converts trained abstention from a coverage loss into a coordination signal, achieving Pareto-dominant performance over majority voting and single models with a fraction of the query budget, while keeping computational cost interpretable as a proxy for problem difficulty.

**Lineage:** Contrasts with post-hoc confidence-based cascades (BabyBear, gatekeeper calibration) by building routing behavior into training rather than estimating it at inference time. Self-cascading (re-querying the same model on abstention) is the degenerate homogeneous case that gains 15 accuracy points (77.5% to 92.5%) over budget B=1 to B=64.
