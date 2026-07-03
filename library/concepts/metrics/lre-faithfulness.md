---
aliases:
- faithfulness
- LRE faithfulness score
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:lre-faithfulness
  type: metric
  status: canonical
area: mechanistic-interpretability
related:
- '[[linear-relation-embedding]]'
- '[[lre-causality]]'
relationships:
- type: related_to
  target: '[[linear-relation-embedding]]'
  target_id: method:linear-relation-embedding
- type: related_to
  target: '[[lre-causality]]'
  target_id: metric:lre-causality
---

LRE faithfulness measures how closely the output distribution produced by the learned affine transformation of a Linear Relation Embedding (LRE) matches the language model's true output distribution for a given subject-relation pair. It is computed by comparing the token probabilities predicted by the LRE approximation against those from the full forward pass, capturing whether the linear map is a faithful surrogate for the LM's internal computation. A high faithfulness score indicates that the relation is well-approximated by a linear function of the subject representation; low faithfulness signals that the mapping requires non-linear processing.

**Why it matters here:** Faithfulness scores expose which factual relations are linearly stored in the model, and low faithfulness is an early indicator that a fact may be unreliably recalled, connecting directly to the model's knowledge boundary and its capacity for epistemic humility.

**Lineage:** companion metric to [[lre-causality]], both defined within the [[linear-relation-embedding]] framework.
