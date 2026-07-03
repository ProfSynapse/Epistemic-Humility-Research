---
aliases:
- concept subspace hypothesis
- linear concept representation
tags:
- kg/term
- concept
- term
kg:
  id: term:concepts-as-subspaces
  type: term
  status: canonical
area: representations
related:
- '[[linear-representation-hypothesis]]'
- '[[concept-algebra]]'
- '[[activation-steering]]'
- '[[difference-in-means]]'
relationships:
- type: related_to
  target: '[[linear-representation-hypothesis]]'
  target_id: term:linear-representation-hypothesis
- type: related_to
  target: '[[concept-algebra]]'
  target_id: method:concept-algebra
- type: related_to
  target: '[[activation-steering]]'
  target_id: method:activation-steering
- type: related_to
  target: '[[difference-in-means]]'
  target_id: method:difference-in-means
---

The concepts-as-subspaces hypothesis holds that high-level semantic concepts (e.g., sex, artistic style, subject identity) correspond to linear subspaces or directions in a model's internal representation space, extending the classical word-embedding analogy (king - man + woman ≈ queen) to richer, higher-dimensional generative representations. Under this view, any concept can be characterized by a projection matrix onto its subspace, and concept editing reduces to replacing one projection with another while leaving orthogonal components intact. The hypothesis is empirically supported across multiple modalities and architectures.

**Why it matters here:** Concepts-as-subspaces is the geometric foundation for the epistemic-humility research program: reading off uncertainty-related axes such as [[known-unknown-direction]], [[truth-direction]], and [[answerability-subspace]] all assume that these epistemic concepts are linearly encoded and therefore accessible via linear probing or steering.

**Lineage:** precursor to and motivator of the [[linear-representation-hypothesis]]; operationalized by [[concept-algebra]] in score-based models and by [[activation-steering]] and [[difference-in-means]] in language models.
