---
aliases:
- phase change in superposition
- superposition phase change
- phase diagram for superposition
tags:
- kg/method
- concept
- method
kg:
  id: method:superposition-phase-diagram
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[tc2022--toy-models-of-superposition]]'
- '[[toy-model-of-superposition]]'
relationships:
- type: proposed_by
  target: '[[tc2022--toy-models-of-superposition]]'
  target_id: paper:tc2022
  confidence: high
- type: derived_from
  target: '[[toy-model-of-superposition]]'
  target_id: method:toy-model-of-superposition
---

The superposition phase diagram is a theoretical framework that maps when individual features transition between three distinct regimes: not learned at all, learned in superposition (sharing dimensions with other features), or learned with a dedicated dimension. The transitions between regimes are discontinuous (analogous to first-order thermodynamic phase changes) and occur as a function of two axes: feature sparsity and relative feature importance. The resulting diagram forms a phase boundary landscape that predicts which features a network will represent and how.

**Why it matters here:** The phase diagram establishes principled conditions under which a model will or will not encode a feature, which bears on knowledge-boundary research: a feature that sits below the importance-sparsity threshold may be absent from the model's representation even if it appears in training data, contributing to systematic gaps in self-knowledge.

**Lineage:** derives from [[toy-model-of-superposition]]; introduced in [[tc2022--toy-models-of-superposition]].
