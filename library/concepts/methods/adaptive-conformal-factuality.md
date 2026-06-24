---
aliases:
- adaptive conformal prediction for LLMs
- two-stage adaptive conformal
- conditional quantile conformal prediction
tags:
- kg/method
- concept
- method
kg:
  id: method:adaptive-conformal-factuality
  type: method
  status: canonical
area: methods
related:
- '[[2604.13991--adaptive-conformal-factuality]]'
- '[[claim-conditioned-probability]]'
- '[[conditional-coverage]]'
- '[[calibration]]'
- '[[hallucination]]'
- '[[selective-classification-auc]]'
relationships:
- type: proposed_by
  target: '[[2604.13991--adaptive-conformal-factuality]]'
  target_id: paper:2604.13991
  confidence: high
- type: related_to
  target: '[[claim-conditioned-probability]]'
  target_id: method:claim-conditioned-probability
  confidence: medium
- type: related_to
  target: '[[conditional-coverage]]'
  target_id: term:conditional-coverage
  confidence: medium
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: medium
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: medium
- type: related_to
  target: '[[selective-classification-auc]]'
  target_id: metric:selective-classification-auc
  confidence: medium
---

A two-stage conformal prediction pipeline for LLM factuality evaluation. In the first stage a conditional quantile estimator is trained on prompt embeddings (via pinball loss) to predict the expected nonconformity score for each prompt. In the second stage each nonconformity score is divided by its predicted conditional quantile before standard split-conformal calibration, producing a normalized score whose quantile is approximately prompt-invariant. The method preserves finite-sample marginal coverage guarantees while improving conditional coverage across heterogeneous prompt categories.

**Why it matters here:** Global conformal thresholds mask category-level miscalibration. This method exposes per-domain coverage gaps after any training intervention and provides a principled post-training evaluation harness for factuality across heterogeneous knowledge domains, making it directly applicable as a conditional evaluation wrapper for Phase 1 training arms.

**Lineage:** Extends score-transformation methods from regression (normalized conformal prediction, quantile regression forests) to long-form LLM generation. Builds on Conformal Factuality (Mohri et al. 2024) as the non-adaptive baseline.
