---
aliases:
- toy ReLU network superposition model
- superposition toy model
tags:
- kg/method
- concept
- method
kg:
  id: method:toy-model-of-superposition
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[tc2022--toy-models-of-superposition]]'
- '[[superposition-hypothesis]]'
relationships:
- type: proposed_by
  target: '[[tc2022--toy-models-of-superposition]]'
  target_id: paper:tc2022
  confidence: high
- type: related_to
  target: '[[superposition-hypothesis]]'
  target_id: term:superposition-hypothesis
---

The toy model of superposition is a minimal ReLU network of the form ReLU(W^T W x - b) trained to autoencode n synthetic sparse features into m hidden dimensions where m is less than n. Because the ground-truth feature structure is fully known by construction, the model serves as a controlled testbed for directly observing when, how, and which features are stored in superposition versus in dedicated dimensions. Varying sparsity and relative feature importance in the training data yields the full landscape of superposition behavior.

**Why it matters here:** This controlled setting lets researchers isolate exactly when a model fails to represent a feature, which is directly relevant to knowledge-boundary and hallucination research: features that fall below the importance-sparsity threshold will not be recoverable from the model's weights, creating predictable blind spots in model self-knowledge.

**Lineage:** introduced in [[tc2022--toy-models-of-superposition]]; the toy model operationalizes the [[superposition-hypothesis]] and underpins the [[superposition-phase-diagram]] and [[superposition-geometry]] findings.
