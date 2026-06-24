---
aliases:
- tokenized Brier loss
- TBS
- verbalized calibration loss
tags:
- kg/method
- concept
- method
kg:
  id: method:tokenized-brier-score
  type: method
  status: canonical
area: methods
related:
- '[[2508.18847--conftuner]]'
- '[[brier-score]]'
- '[[conftuner]]'
- '[[verbalized-confidence]]'
- '[[bounded-proper-scoring-rule-incentivizes-accuracy-and-calibration]]'
- '[[expected-calibration-error]]'
relationships:
- type: proposed_by
  target: '[[2508.18847--conftuner]]'
  target_id: paper:2508.18847
  confidence: high
- type: related_to
  target: '[[brier-score]]'
  target_id: metric:brier-score
  confidence: medium
- type: related_to
  target: '[[conftuner]]'
  target_id: method:conftuner
  confidence: medium
- type: related_to
  target: '[[verbalized-confidence]]'
  target_id: method:verbalized-confidence
  confidence: medium
- type: related_to
  target: '[[bounded-proper-scoring-rule-incentivizes-accuracy-and-calibration]]'
  target_id: mechanism:bounded-proper-scoring-rule-incentivizes-accuracy-and-calibration
  confidence: medium
- type: related_to
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
  confidence: medium
---

A loss function for fine-tuning LLMs on verbalized confidence that sums, over each confidence token i in the predefined set {0, 1/N, ..., 1}, the product of the model's predicted probability q_i for that token and the squared error (y - i/N)^2 where y is the binary correctness indicator; proven in Theorem 1 to be a proper scoring rule for verbalized calibration.

**Why it matters here:** The theoretical result (Theorem 1) guarantees that minimizing this loss drives the model to concentrate probability mass on the confidence token closest to the true conditional correctness probability, providing a principled calibration incentive absent from cross-entropy training and sampling-based proxy methods.

**Lineage:** Introduced in 2508.18847 as the core training objective of ConfTuner; adapts the classical Brier score (proper scoring rule for classifiers) to the tokenized output setting; related to the RLCR calibration reward (2507.16806) which uses Brier score in an RL objective rather than SFT.
