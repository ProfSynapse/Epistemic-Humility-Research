---
aliases:
- Cohen's κ
- kappa inter-rater agreement
- chance-corrected agreement
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:cohens-kappa
  type: metric
  status: canonical
area: metrics
related:
- '[[2508.15050--dont-think-twice]]'
- '[[calibration]]'
- '[[expected-calibration-error]]'
- '[[overconfidence]]'
- '[[climatex]]'
relationships:
- type: proposed_by
  target: '[[2508.15050--dont-think-twice]]'
  target_id: paper:2508.15050
  confidence: high
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: medium
- type: related_to
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
  confidence: medium
- type: related_to
  target: '[[overconfidence]]'
  target_id: term:overconfidence
  confidence: medium
- type: related_to
  target: '[[climatex]]'
  target_id: dataset:climatex
  confidence: medium
---

A chance-corrected measure of inter-rater agreement defined as kappa = (p_o - p_e) / (1 - p_e), where p_o is observed agreement and p_e is agreement expected under random guessing. For a four-class task (25% random baseline), kappa corrects raw accuracy for the fraction attributable to chance. A kappa of 0 indicates no better than chance; 1.0 indicates perfect agreement.

**Why it matters here:** Raw accuracy on multi-class calibration tasks is inflated by majority-class prediction. Kappa is the appropriate measure when ground-truth class frequencies are unequal (as in ClimateX, which skews toward high and very high confidence). Reporting kappa alongside accuracy makes model comparisons more meaningful and is standard for inter-rater reliability in scientific labeling studies.

**Lineage:** Cohen (1960). Used as a primary metric in arXiv:2508.15050 for the ClimateX masked-label calibration benchmark.
