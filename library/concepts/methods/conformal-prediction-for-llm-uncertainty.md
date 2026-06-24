---
aliases:
- conformal uncertainty quantification
- LAC score function
- APS score function
- prediction set uncertainty
tags:
- kg/method
- concept
- method
kg:
  id: method:conformal-prediction-for-llm-uncertainty
  type: method
  status: canonical
area: methods
related:
- '[[2401.12794--llm-uncertainty-bench-conformal]]'
- '[[uncertainty-aware-accuracy]]'
- '[[calibration]]'
- '[[overconfidence]]'
- '[[verbalized-confidence]]'
relationships:
- type: proposed_by
  target: '[[2401.12794--llm-uncertainty-bench-conformal]]'
  target_id: paper:2401.12794
  confidence: high
- type: related_to
  target: '[[uncertainty-aware-accuracy]]'
  target_id: metric:uncertainty-aware-accuracy
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
  target: '[[verbalized-confidence]]'
  target_id: method:verbalized-confidence
  confidence: medium
---

A distribution-free, model-agnostic framework that converts any heuristic uncertainty score (e.g., softmax probabilities) into a statistically rigorous prediction set guaranteed to contain the true label with at least 1-alpha probability. Applied to LLM benchmarking by treating all NLP tasks as multiple-choice and using prediction set size (SS) as the uncertainty metric, calibrated on a held-out set.

**Why it matters here:** Provides a coverage-guaranteed, calibrated uncertainty estimate for LLMs without requiring Bayesian approximation or ensembling, enabling principled comparison of model certainty alongside accuracy across tasks and model families.

**Lineage:** Vovk et al. (2005) foundational theory; Angelopoulos and Bates (2021) tutorial; applied to LLM benchmarking by Ye et al. (2024) in 2401.12794.
