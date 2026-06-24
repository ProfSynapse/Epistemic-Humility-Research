---
aliases:
- category-conditional coverage
- prompt-conditional coverage
- group-conditional coverage
tags:
- kg/term
- concept
- term
kg:
  id: term:conditional-coverage
  type: term
  status: canonical
area: terms
related:
- '[[2604.13991--adaptive-conformal-factuality]]'
- '[[adaptive-conformal-factuality]]'
- '[[calibration]]'
- '[[hallucination]]'
- '[[claim-conditioned-probability]]'
relationships:
- type: proposed_by
  target: '[[2604.13991--adaptive-conformal-factuality]]'
  target_id: paper:2604.13991
  confidence: high
- type: related_to
  target: '[[adaptive-conformal-factuality]]'
  target_id: method:adaptive-conformal-factuality
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
  target: '[[claim-conditioned-probability]]'
  target_id: method:claim-conditioned-probability
  confidence: medium
---

A stronger calibration guarantee than marginal coverage, requiring that a prediction set or filtering rule achieves the target error rate not just in expectation across all inputs but within each input subgroup (e.g., prompt category or knowledge domain). Marginal coverage guarantees can hide systematic over-coverage in easy categories and under-coverage in hard ones.

**Why it matters here:** Standard conformal prediction only guarantees marginal coverage. Conditional coverage exposes whether a factuality filter is uniformly reliable across knowledge domains, which is essential when a single trained model is deployed on heterogeneous queries. This is the central evaluation criterion distinguishing adaptive from non-adaptive conformal methods for LLMs.

**Lineage:** Classical concept from conformal prediction theory. In the LLM context the failure of marginal-only methods to achieve conditional coverage is documented in this paper (2604.13991) and Cherian et al. 2024.
