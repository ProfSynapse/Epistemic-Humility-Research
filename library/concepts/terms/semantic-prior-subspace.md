---
aliases:
- concept subspace
- behavioral prior subspace
- steering basis subspace
tags:
- kg/term
- concept
- term
kg:
  id: term:semantic-prior-subspace
  type: term
  status: canonical
area: steering
related:
- '[[2602.07276--steer2adapt-dynamically-composing-steering-vectors-elicits-efficient]]'
- '[[steer2adapt]]'
- '[[activation-steering]]'
relationships:
- type: proposed_by
  target: '[[2602.07276--steer2adapt-dynamically-composing-steering-vectors-elicits-efficient]]'
  target_id: paper:2602.07276
  confidence: high
- type: required_by
  target: '[[steer2adapt]]'
  target_id: method:steer2adapt
---

A semantic prior subspace is a low-dimensional subspace of a language model's residual-stream activation space spanned by a small, pre-selected set of semantic concept steering vectors. In practice the subspace is constructed by collecting contrastive or difference-in-means directions for named behavioral concepts (for example Big Five personality traits for reasoning tasks, or refusal, sycophancy, hallucination, lawfulness, and fairness for safety tasks), then treating their span as the search space for task adaptation. Any new target behavior is represented as a linear combination of these basis vectors, so adaptation collapses from a high-dimensional optimization to a k-dimensional coefficient search.

**Why it matters here:** The semantic prior subspace makes the geometry of epistemic-humility-relevant behaviors explicit and searchable: if abstention, calibration, and honesty each correspond to identifiable directions in this subspace, a single steering framework can address all three simultaneously without task-specific fine-tuning.

**Lineage:** a structural prerequisite for [[steer2adapt]]; the concept vectors that span it are produced by [[activation-steering]] techniques.
