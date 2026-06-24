---
aliases:
- popularity-gated retrieval
- selective retrieval augmentation
- threshold-based retrieval routing
tags:
- kg/method
- concept
- method
kg:
  id: method:adaptive-retrieval
  type: method
  status: canonical
area: methods
related:
- '[[2212.10511--popqa-when-not-to-trust]]'
- '[[popqa]]'
- '[[entityquestions]]'
- '[[knowledge-boundary]]'
- '[[adaptive-conformal-factuality]]'
relationships:
- type: proposed_by
  target: '[[2212.10511--popqa-when-not-to-trust]]'
  target_id: paper:2212.10511
  confidence: high
- type: related_to
  target: '[[popqa]]'
  target_id: dataset:popqa
  confidence: medium
- type: related_to
  target: '[[entityquestions]]'
  target_id: dataset:entityquestions
  confidence: medium
- type: related_to
  target: '[[knowledge-boundary]]'
  target_id: term:knowledge-boundary
  confidence: medium
- type: related_to
  target: '[[adaptive-conformal-factuality]]'
  target_id: method:adaptive-conformal-factuality
  confidence: medium
---

A retrieval-augmented generation strategy that routes each query to a non-parametric (retrieved) memory source only when the subject entity's popularity falls below a per-relationship-type threshold tuned on a development set; high-popularity queries rely on the LM's parametric memory. The threshold is calibrated to maximize accuracy on the dev split.

**Why it matters here:** Demonstrates that a simple, training-free routing rule based on input-observable features (entity popularity) recovers most of the accuracy gains of always-retrieve while cutting inference costs substantially. Relevant to the experiment as a deployment-time complement to training-based abstention: Adaptive Retrieval routes at the query level using the same knowledge-boundary signal that abstention training aims to internalize.

**Lineage:** Proposed in Mallen et al. 2023 (2212.10511) as the main algorithmic contribution; builds on the empirical finding that popularity predicts parametric memorization. Conceptually related to adaptive-conformal-factuality and conformal-prediction-for-llm-uncertainty as methods that condition retrieval or abstention on query-observable signals.
