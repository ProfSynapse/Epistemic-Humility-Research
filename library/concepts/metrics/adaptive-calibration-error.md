---
aliases:
- ACE
- adaptive calibration error
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:adaptive-calibration-error
  type: metric
  status: canonical
area: metrics
related:
- '[[2509.20088--causal-understanding-uncertainty]]'
- '[[expected-calibration-error]]'
- '[[calibration]]'
- '[[overconfidence]]'
- '[[mcqa-causal]]'
relationships:
- type: proposed_by
  target: '[[2509.20088--causal-understanding-uncertainty]]'
  target_id: paper:2509.20088
  confidence: high
- type: related_to
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
  confidence: medium
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: medium
- type: related_to
  target: '[[overconfidence]]'
  target_id: term:overconfidence
  confidence: medium
- type: related_to
  target: '[[mcqa-causal]]'
  target_id: dataset:mcqa-causal
  confidence: medium
---

A calibration metric that partitions predictions into bins of equal sample count (adaptive binning) rather than equal width, then computes the mean absolute difference between average confidence and average accuracy across bins. ACE addresses the bias-variance tradeoff in fixed-width Expected Calibration Error (ECE): by concentrating bin weight where predictions are dense, it provides a more stable estimate of calibration error across the full confidence distribution. Formally: ACE = (1/R) * sum_r |acc(B_r) - conf(B_r)|, where R is the number of adaptive bins.

**Why it matters here:** ACE supplements ECE when models have skewed confidence distributions (e.g., bimodal or concentrated near 0 or 1), a pattern common in instruction-tuned models. Using both together reveals whether miscalibration is uniform or concentrated in specific confidence regions.

**Lineage:** Proposed by Nixon et al. (2019). Used alongside ECE in Lithgow-Serrano et al. (2025) to characterize instruction-tuning calibration collapse.
